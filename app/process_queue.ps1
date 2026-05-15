param(
    [switch]$DisableGooglePush,
    [switch]$DryRun,
    [switch]$NoGooglePush,
    [switch]$AllowTestGooglePush
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "C:\JeffLocal\app\common.ps1"
. "C:\JeffLocal\app\modules\Jeff.Common.ps1"
. "C:\JeffLocal\app\modules\Jeff.RequestType.ps1"
. "C:\JeffLocal\app\modules\Jeff.Validation.ps1"
. "C:\JeffLocal\app\modules\Jeff.Emergency.ps1"
. "C:\JeffLocal\app\detect_flags.ps1"
. "C:\JeffLocal\app\generate_staff_summary.ps1"
. "C:\JeffLocal\app\build_handoff.ps1"

$appSettingsPath = "C:\JeffLocal\config\app_settings.json"
if (-not (Test-Path -LiteralPath $appSettingsPath)) {
    throw "Missing app settings file: $appSettingsPath"
}

$appSettings = Get-Content -LiteralPath $appSettingsPath -Raw | ConvertFrom-Json

function Convert-LookupNameToDisplay {
    param([string]$Name)

    if ([string]::IsNullOrWhiteSpace($Name)) {
        return ""
    }

    $clean = $Name.Trim()
    $clean = [regex]::Replace($clean, "\s*\([^)]*\)\s*", "")

    if ($clean -match "^\s*([^,]+)\s*,\s*(.+?)\s*$") {
        $surname = $matches[1].Trim()
        $firstPart = $matches[2].Trim()
        return "$firstPart $surname".Trim()
    }

    return $clean
}

function Resolve-PatientLookupPath {
    param([object]$AppSettings)

    $candidates = @(
        "C:\JeffLocal\data\patient_lookup\mock_patient_lookup_v3.csv"
    )

    if ($AppSettings.PSObject.Properties["patient_lookup_csv"]) {
        $candidates += "$($AppSettings.patient_lookup_csv)"
    }

    $candidates += @(
        "C:\JeffLocal\data\patient_lookup\patient_lookup.csv",
        "C:\JeffLocal\data\patient_lookup\patients.csv",
        "C:\JeffLocal\data\patient_lookup\patient_lookup_export.csv"
    )

    foreach ($path in $candidates) {
        if (-not [string]::IsNullOrWhiteSpace($path) -and (Test-Path -LiteralPath $path)) {
            return $path
        }
    }

    throw "Could not find patient lookup CSV."
}

function Load-NormalizedPatients {
    param([string]$CsvPath)

    $rows = Import-Csv -LiteralPath $CsvPath
    $patients = @()

    foreach ($row in $rows) {
        $patientRef = Get-FirstValue -Row $row -Names @("patient_ref", "EMIS Number", "EMISNumber", "emis_number", "Patient Ref")
        $rawFullName = Get-FirstValue -Row $row -Names @("full_name", "Full Name", "FullName", "name")
        $fullName = Convert-LookupNameToDisplay $rawFullName
        $dobRaw = Get-FirstValue -Row $row -Names @("dob", "Date of Birth", "DOB", "date_of_birth")
        $age = Get-FirstValue -Row $row -Names @("age", "Age")
        $gender = Get-FirstValue -Row $row -Names @("gender", "Gender", "sex", "Sex")
        $nhsNumber = Get-FirstValue -Row $row -Names @("nhs_number", "NHS Number", "NHSNumber")

        if ([string]::IsNullOrWhiteSpace($fullName)) {
            continue
        }

        $patients += [pscustomobject]@{
            patient_ref          = $patientRef
            full_name            = $fullName
            full_name_normalized = Normalize-Name $fullName
            dob                  = Normalize-DateString $dobRaw
            age                  = $age
            gender               = $gender
            nhs_number           = $nhsNumber
        }
    }

    return @($patients)
}

function Get-AuditLogPath {
    param([string]$AuditDir)

    $datePart = Get-Date -Format "yyyy-MM-dd"
    return (Join-Path $AuditDir "audit_$datePart.jsonl")
}

function Write-AuditEvent {
    param(
        [string]$AuditDir,
        [string]$EventType,
        [string]$Status,
        [string]$FileName = "",
        [string]$CallId = "",
        [hashtable]$Details = @{}
    )

    Ensure-Directory -Path $AuditDir

    $entry = [ordered]@{
        timestamp   = (Get-Date).ToString("s")
        event_type  = $EventType
        status      = $Status
        file_name   = $FileName
        call_id     = $CallId
        details     = $Details
    }

    ($entry | ConvertTo-Json -Depth 10 -Compress) | Add-Content -LiteralPath (Get-AuditLogPath -AuditDir $AuditDir) -Encoding UTF8
}

function Get-AttemptStatePath {
    param(
        [string]$AuditDir,
        [string]$FileName
    )

    $safeName = $FileName -replace '[^a-zA-Z0-9._-]', '_'
    return (Join-Path $AuditDir "$safeName.attempt.json")
}

function Get-AttemptCount {
    param(
        [string]$AuditDir,
        [string]$FileName
    )

    $path = Get-AttemptStatePath -AuditDir $AuditDir -FileName $FileName
    if (Test-Path -LiteralPath $path) {
        try {
            $state = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
            return [int]$state.attempt_count
        }
        catch {
            return 0
        }
    }

    return 0
}

function Save-AttemptCount {
    param(
        [string]$AuditDir,
        [string]$FileName,
        [int]$AttemptCount
    )

    Ensure-Directory -Path $AuditDir
    $path = Get-AttemptStatePath -AuditDir $AuditDir -FileName $FileName

    [ordered]@{
        file_name     = $FileName
        attempt_count = $AttemptCount
        updated_at    = (Get-Date).ToString("s")
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $path -Encoding UTF8
}

function Clear-AttemptCount {
    param(
        [string]$AuditDir,
        [string]$FileName
    )

    $path = Get-AttemptStatePath -AuditDir $AuditDir -FileName $FileName
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Force
    }
}

function Move-ToDeadletter {
    param(
        [string]$ProcessingPath,
        [string]$DeadletterDir,
        [string]$AuditDir,
        [string]$Reason,
        [string]$ErrorMessage,
        [int]$AttemptCount,
        [string]$OriginalFileName
    )

    Ensure-Directory -Path $DeadletterDir

    $targetPath = Join-Path $DeadletterDir $OriginalFileName
    Move-Item -LiteralPath $ProcessingPath -Destination $targetPath -Force

    $manifestPath = Join-Path $DeadletterDir "$OriginalFileName.deadletter.json"
    [ordered]@{
        original_file_name = $OriginalFileName
        deadlettered_at    = (Get-Date).ToString("s")
        reason             = $Reason
        error_message      = $ErrorMessage
        attempt_count      = $AttemptCount
        deadletter_path    = $targetPath
    } | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $manifestPath -Encoding UTF8

    Clear-AttemptCount -AuditDir $AuditDir -FileName $OriginalFileName
}

function Move-ToFailed {
    param(
        [string]$ProcessingPath,
        [string]$FailedDir,
        [string]$AuditDir,
        [string]$ErrorMessage,
        [int]$AttemptCount,
        [string]$OriginalFileName
    )

    Ensure-Directory -Path $FailedDir

    $targetPath = Join-Path $FailedDir $OriginalFileName
    Move-Item -LiteralPath $ProcessingPath -Destination $targetPath -Force

    $manifestPath = Join-Path $FailedDir "$OriginalFileName.failed.json"
    [ordered]@{
        original_file_name = $OriginalFileName
        failed_at          = (Get-Date).ToString("s")
        error_message      = $ErrorMessage
        attempt_count      = $AttemptCount
        failed_path        = $targetPath
    } | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $manifestPath -Encoding UTF8
}

function Test-JeffLocalTestCallId {
    param([string]$CallId)

    return (
        $CallId -like "FRESH-*" -or
        $CallId -like "TEST-*" -or
        $CallId -like "RAWMOCK-*" -or
        $CallId -like "GPDEMO-*"
    )
}

function New-RunControlAuditDetails {
    param([hashtable]$Extra = @{})

    $details = @{
        dry_run                = [bool]$DryRun
        no_google_push         = [bool]($NoGooglePush -or $DisableGooglePush -or $env:JEFFLOCAL_DISABLE_GOOGLE_PUSH -eq "1")
        allow_test_google_push = [bool]$AllowTestGooglePush
    }

    foreach ($key in $Extra.Keys) {
        $details[$key] = $Extra[$key]
    }

    return $details
}

function Test-FileAlreadyProcessed {
    param(
        [string]$ProcessedDir,
        [string]$FileName
    )

    return (Test-Path -LiteralPath (Join-Path $ProcessedDir $FileName))
}

function Test-HandoffAlreadyExists {
    param(
        [string]$HandoffDir,
        [string]$CallId
    )

    $handoffPath = Join-Path $HandoffDir "$CallId`_handoff.json"
    return (Test-Path -LiteralPath $handoffPath)
}

function Get-DuplicateCallIdsInBatch {
    param([object[]]$Calls)

    $ids = @(
        $Calls |
        Where-Object { $null -ne $_ } |
        ForEach-Object { "$($_.call_id)" } |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    )

    $duplicateIds = @(
        $ids |
        Group-Object |
        Where-Object { $_.Count -gt 1 } |
        Select-Object -ExpandProperty Name
    )

    return $duplicateIds
}

$incoming      = $appSettings.queue_incoming
$processing    = $appSettings.queue_processing
$processed     = $appSettings.queue_processed
$failed        = $appSettings.queue_failed
$deadletter    = if ($appSettings.PSObject.Properties["queue_deadletter"]) { "$($appSettings.queue_deadletter)" } else { "C:\JeffLocal\queue\deadletter" }
$handoffOutput = $appSettings.outputs_handoff_json
$pushScript    = "C:\JeffLocal\app\push_to_google_sheet.ps1"
$auditDir      = "C:\JeffLocal\logs\audits"
$maxRetryCount = if ($appSettings.PSObject.Properties["queue_max_retry_count"]) {
    [int]$appSettings.queue_max_retry_count
}
elseif ($appSettings.PSObject.Properties["retry_count_max"]) {
    [int]$appSettings.retry_count_max
}
else {
    2
}

foreach ($folder in @($incoming, $processing, $processed, $failed, $deadletter, $handoffOutput, $auditDir)) {
    Ensure-Directory -Path $folder
}

$patientLookupPath = Resolve-PatientLookupPath -AppSettings $appSettings
$normalizedPatients = Load-NormalizedPatients -CsvPath $patientLookupPath

Write-Host "Loaded patient lookup: $patientLookupPath"
Write-Host "Patient rows loaded: $($normalizedPatients.Count)"
if ($DryRun) {
    Write-Host "DRY RUN - no files moved, no Google push"
}
elseif ($NoGooglePush) {
    Write-Host "Google push disabled by -NoGooglePush for this run."
}
Write-AuditEvent -AuditDir $auditDir -EventType "startup" -Status "ok" -Details (New-RunControlAuditDetails @{
    patient_lookup_path = $patientLookupPath
    patient_count       = $normalizedPatients.Count
    max_retry_count     = $maxRetryCount
})

$files = @(
    Get-ChildItem -LiteralPath $incoming -Filter "*.json" -File |
    Where-Object { Test-JeffQueuePayloadFileName -FileName $_.Name } |
    Sort-Object Name
)

if ($files.Count -eq 0) {
    Write-Host "No files found in incoming queue."
    Write-AuditEvent -AuditDir $auditDir -EventType "queue_scan" -Status "empty" -Details (New-RunControlAuditDetails)
    exit
}

$file = $files[0]

if ((-not $DryRun) -and (Test-FileAlreadyProcessed -ProcessedDir $processed -FileName $file.Name)) {
    Write-AuditEvent -AuditDir $auditDir -EventType "duplicate_file" -Status "deadletter" -FileName $file.Name -Details (New-RunControlAuditDetails @{
        reason = "file_name_already_processed"
    })

    $processingPathTemp = Join-Path $processing $file.Name
    Move-Item -LiteralPath $file.FullName -Destination $processingPathTemp -Force

    Move-ToDeadletter `
        -ProcessingPath $processingPathTemp `
        -DeadletterDir $deadletter `
        -AuditDir $auditDir `
        -Reason "file_name_already_processed" `
        -ErrorMessage "File name already exists in processed queue." `
        -AttemptCount 0 `
        -OriginalFileName $file.Name

    Write-Host "Deadlettered duplicate processed file: $($file.Name)"
    exit 1
}

$processingPath = Join-Path $processing $file.Name
$attemptCount = (Get-AttemptCount -AuditDir $auditDir -FileName $file.Name) + 1

Write-AuditEvent -AuditDir $auditDir -EventType "queue_pickup" -Status "started" -FileName $file.Name -Details (New-RunControlAuditDetails @{
    attempt_count = $attemptCount
})

if ($DryRun) {
    $processingPath = $file.FullName
    Write-Host "DRY RUN - using incoming file in place: $($file.Name)"
}
else {
    Move-Item -LiteralPath $file.FullName -Destination $processingPath -Force
    Write-Host "Moved to processing: $($file.Name)"
}

try {
    $rawQueueText = Get-Content -LiteralPath $processingPath -Raw -Encoding UTF8

    try {
        $queueObject = $rawQueueText | ConvertFrom-Json
    }
    catch {
        $parseStatus = if ($DryRun) { "failed_dry_run" } else { "deadletter" }
        Write-AuditEvent -AuditDir $auditDir -EventType "parse_json" -Status $parseStatus -FileName $file.Name -Details (New-RunControlAuditDetails @{
            reason        = "malformed_json"
            attempt_count = $attemptCount
            error_message = $_.Exception.Message
        })

        if (-not $DryRun) {
            Move-ToDeadletter `
                -ProcessingPath $processingPath `
                -DeadletterDir $deadletter `
                -AuditDir $auditDir `
                -Reason "malformed_json" `
                -ErrorMessage $_.Exception.Message `
                -AttemptCount $attemptCount `
                -OriginalFileName $file.Name
        }

        Write-Host "$(if ($DryRun) { 'DRY RUN malformed JSON - file not moved:' } else { 'Deadlettered malformed JSON:' }) $($file.Name)"
        exit 1
    }

$calls = @()

if ($null -eq $queueObject) {
    $calls = @()
}
elseif ($queueObject -is [System.Array]) {
    $calls = @($queueObject)
}
elseif ($queueObject -is [System.Collections.IEnumerable] -and $queueObject -isnot [string] -and $queueObject -isnot [pscustomobject]) {
    $calls = @($queueObject)
}
else {
    $calls = @($queueObject)
}

if (@($calls).Count -eq 0) {
    throw "Queue file contains no call objects."
}

    foreach ($call in $calls) {
        if (-not $call.PSObject.Properties["call_id"] -or [string]::IsNullOrWhiteSpace("$($call.call_id)")) {
            throw "Call object missing call_id."
        }
    }

    $duplicateBatchIds = @(Get-DuplicateCallIdsInBatch -Calls @($calls))
if (@($duplicateBatchIds).Count -gt 0) {
    throw "Duplicate call_id values found in batch: $($duplicateBatchIds -join ', ')"
}

    foreach ($call in $calls) {
        $callId = "$($call.call_id)"

        if ((-not $DryRun) -and (Test-HandoffAlreadyExists -HandoffDir $handoffOutput -CallId $callId)) {
            throw "Call_id already processed previously: $callId"
        }

        Write-Host "Building handoff: $callId"
        Write-AuditEvent -AuditDir $auditDir -EventType "call_processing" -Status "started" -FileName $file.Name -CallId $callId -Details (New-RunControlAuditDetails @{
            attempt_count = $attemptCount
        })

        $callNormalizedInput = Get-ObjectPropertyValue -Object $call -Name "normalized_input" -Default $null
        $pathwayResponses = Get-ObjectPropertyValue -Object $call -Name "pathway_responses" -Default $null
        $identityResponses = Get-ObjectPropertyValue -Object $pathwayResponses -Name "identity" -Default $null
        $prescriptionResponses = Get-ObjectPropertyValue -Object $pathwayResponses -Name "prescription" -Default $null
        $urgencyAssessment = Get-ObjectPropertyValue -Object $pathwayResponses -Name "urgency_assessment" -Default $null

        $patientNameRaw = Get-FirstNonBlankValue @(
            (Get-ObjectPropertyValue -Object $call -Name "patient_name_raw"),
            (Get-ObjectPropertyValue -Object $call -Name "patient_name"),
            (Get-ObjectPropertyValue -Object $callNormalizedInput -Name "patient_name"),
            (Get-ObjectPropertyValue -Object $identityResponses -Name "patient_name")
        )

        $dobRaw = Get-FirstNonBlankValue @(
            (Get-ObjectPropertyValue -Object $call -Name "dob_raw"),
            (Get-ObjectPropertyValue -Object $call -Name "dob"),
            (Get-ObjectPropertyValue -Object $callNormalizedInput -Name "dob"),
            (Get-ObjectPropertyValue -Object $identityResponses -Name "dob")
        )

        $callbackRaw = Get-FirstNonBlankValue @(
            (Get-ObjectPropertyValue -Object $call -Name "callback_number_raw"),
            (Get-ObjectPropertyValue -Object $call -Name "callback_number"),
            (Get-ObjectPropertyValue -Object $callNormalizedInput -Name "callback_number"),
            (Get-ObjectPropertyValue -Object $identityResponses -Name "callback_number"),
            (Get-ObjectPropertyValue -Object $identityResponses -Name "callback_number_from_caller_id")
        )

        $urgencyNoteRaw = Get-FirstNonBlankValue @(
            (Get-ObjectPropertyValue -Object $call -Name "urgency_note_raw"),
            (Get-ObjectPropertyValue -Object $call -Name "urgency_note"),
            (Get-ObjectPropertyValue -Object $callNormalizedInput -Name "urgency_note")
        )

        $pharmacyRaw = Get-FirstNonBlankValue @(
            (Get-ObjectPropertyValue -Object $call -Name "pharmacy_raw"),
            (Get-ObjectPropertyValue -Object $call -Name "pharmacy"),
            (Get-ObjectPropertyValue -Object $callNormalizedInput -Name "pharmacy"),
            (Get-ObjectPropertyValue -Object $prescriptionResponses -Name "pharmacy")
        )

        $callerForRaw = Get-FirstNonBlankValue @(
            (Get-ObjectPropertyValue -Object $call -Name "caller_for_raw"),
            (Get-ObjectPropertyValue -Object $call -Name "caller_for"),
            (Get-ObjectPropertyValue -Object $callNormalizedInput -Name "caller_for"),
            (Get-ObjectPropertyValue -Object $pathwayResponses -Name "caller_for"),
            "self"
        )

        $postcodeRaw = Get-FirstNonBlankValue @(
            (Get-ObjectPropertyValue -Object $call -Name "postcode_raw"),
            (Get-ObjectPropertyValue -Object $call -Name "postcode"),
            (Get-ObjectPropertyValue -Object $callNormalizedInput -Name "postcode"),
            (Get-ObjectPropertyValue -Object $identityResponses -Name "postcode")
        )

        $suppliedNhsNumberRaw = Get-FirstNonBlankValue @(
            (Get-ObjectPropertyValue -Object $call -Name "supplied_nhs_number"),
            (Get-ObjectPropertyValue -Object $callNormalizedInput -Name "supplied_nhs_number")
        )

        $normalizedInput = [pscustomobject]@{
            patient_name = Normalize-Name ([string]$patientNameRaw)
            dob = Normalize-DateString ([string]$dobRaw)
            postcode = Normalize-Whitespace ([string]$postcodeRaw)
            callback_number = Normalize-Phone ([string]$callbackRaw)
            medications_requested = @()
            urgency_note = Normalize-Whitespace ([string]$urgencyNoteRaw)
            pharmacy = Normalize-Whitespace ([string]$pharmacyRaw)
            caller_for = Normalize-Whitespace ([string]$callerForRaw)
            supplied_nhs_number = Normalize-Whitespace ([string]$suppliedNhsNumberRaw)
        }

        $medicationCandidates = @(
            (Get-ObjectPropertyValue -Object $call -Name "medications_requested" -Default @()),
            (Get-ObjectPropertyValue -Object $call -Name "medications_raw" -Default ""),
            (Get-ObjectPropertyValue -Object $callNormalizedInput -Name "medications_requested" -Default @()),
            (Get-ObjectPropertyValue -Object $prescriptionResponses -Name "medications_requested" -Default @())
        )

        foreach ($medicationCandidate in $medicationCandidates) {
            $normalizedInput.medications_requested += @(Convert-MedsToArray $medicationCandidate)
        }

        $normalizedInput.medications_requested = @($normalizedInput.medications_requested | Select-Object -Unique)

        $callTranscriptSummary = [string](Get-FirstNonBlankValue @(
            (Get-ObjectPropertyValue -Object $call -Name "call_transcript_summary"),
            (Get-ObjectPropertyValue -Object $call -Name "transcript_summary"),
            (Get-ObjectPropertyValue -Object $call -Name "call_summary")
        ))

        $transcriptSummary = if (-not [string]::IsNullOrWhiteSpace($callTranscriptSummary)) {
            Normalize-Whitespace $callTranscriptSummary
        }
        else {
            "Request received from Jeff."
        }

        $rawTranscriptText = [string](Get-FirstNonBlankValue @(
            (Get-ObjectPropertyValue -Object $call -Name "raw_transcript"),
            (Get-ObjectPropertyValue -Object $call -Name "transcript")
        ))

        $normalizedTranscript = if (-not [string]::IsNullOrWhiteSpace($rawTranscriptText)) {
            Normalize-TranscriptText $rawTranscriptText
        }
        else {
            ""
        }

        $originalRequestType = [string](Get-FirstNonBlankValue @(
            (Get-ObjectPropertyValue -Object $call -Name "request_type"),
            (Get-ObjectPropertyValue -Object $callNormalizedInput -Name "request_type"),
            (Get-ObjectPropertyValue -Object $pathwayResponses -Name "selected_pathway")
        ))

        $requestSubtype = if (-not [string]::IsNullOrWhiteSpace($originalRequestType)) {
            $originalRequestType
        }
        else {
            Normalize-JeffRequestType ""
        }

        $pathwayText = ""
        if ($null -ne $pathwayResponses) {
            try {
                $pathwayText = $pathwayResponses | ConvertTo-Json -Depth 30 -Compress
            }
            catch {
                $pathwayText = [string]$pathwayResponses
            }
        }

        $selectedPathway = [string](Get-ObjectPropertyValue -Object $pathwayResponses -Name "selected_pathway" -Default "")
        $classificationText = @(
            $originalRequestType,
            (Get-ObjectPropertyValue -Object $callNormalizedInput -Name "request_type"),
            $selectedPathway,
            $rawTranscriptText,
            $transcriptSummary,
            (Get-ObjectPropertyValue -Object $call -Name "call_summary"),
            (Get-ObjectPropertyValue -Object $call -Name "task_title"),
            (Get-ObjectPropertyValue -Object $call -Name "task_body"),
            $pathwayText
        ) -join " "

        $requestType = if (-not [string]::IsNullOrWhiteSpace($selectedPathway)) {
            Normalize-JeffRequestType $selectedPathway
        }
        else {
            Normalize-JeffRequestType $classificationText
        }

        Set-ObjectPropertyValue -Object $call -Name "request_type" -Value $requestType
        Set-ObjectPropertyValue -Object $call -Name "request_subtype" -Value $requestSubtype
        Set-ObjectPropertyValue -Object $normalizedInput -Name "request_type" -Value $requestType
        Set-ObjectPropertyValue -Object $normalizedInput -Name "request_subtype" -Value $requestSubtype

        if ($null -ne $callNormalizedInput) {
            Set-ObjectPropertyValue -Object $callNormalizedInput -Name "request_type" -Value $requestType
            Set-ObjectPropertyValue -Object $callNormalizedInput -Name "request_subtype" -Value $requestSubtype
        }

        Write-Host "Canonical request_type: $callId $requestSubtype -> $requestType"

        $flags = [pscustomobject]@{
            transcript_quality_flag = ""
            uncertain_fields = @()
            missing_fields = @()
            priority = "routine"
        }

        $flags.missing_fields = @(Get-JeffMissingFields -NormalizedInput $normalizedInput -RequestType $requestType)

# Legacy compatibility fields for build_handoff.ps1
if (-not $call.PSObject.Properties["callback_number"]) {
    $call | Add-Member -NotePropertyName "callback_number" -NotePropertyValue $normalizedInput.callback_number -Force
}

if (-not $call.PSObject.Properties["callback_number_raw"]) {
    $call | Add-Member -NotePropertyName "callback_number_raw" -NotePropertyValue $normalizedInput.callback_number -Force
}

if (-not $call.PSObject.Properties["patient_name_raw"]) {
    $call | Add-Member -NotePropertyName "patient_name_raw" -NotePropertyValue $normalizedInput.patient_name -Force
}

if (-not $call.PSObject.Properties["dob_raw"]) {
    $call | Add-Member -NotePropertyName "dob_raw" -NotePropertyValue $normalizedInput.dob -Force
}

        if (
            -not [string]::IsNullOrWhiteSpace($normalizedInput.urgency_note) -and
            $normalizedInput.urgency_note -match "(?i)\burgent\b|\bsame\s*day\b|\btoday\b|\brun\s*out\b|\brunning\s*out\b|\bno\s*medication\b"
        ) {
            $flags.priority = "urgent_review"
        }

$handoffArgs = @{
    Call = $call
    NormalizedInput = $normalizedInput
    NormalizedPatients = $normalizedPatients
    Flags = $flags
    TranscriptSummary = $transcriptSummary
    NormalizedRawTranscript = $normalizedTranscript
}
$handoff = New-JeffHandoffObject @handoffArgs

        $handoffPath = Join-Path $handoffOutput "$callId`_handoff.json"

$emergencyArgs = @{
    Handoff = $handoff
    ScanObjects = @(
        $handoff,
        $rawTranscriptText,
        $transcriptSummary,
        $normalizedInput,
        $flags,
        $call
    )
}
$emergencyOverrideApplied = Invoke-JeffEmergencyOverride @emergencyArgs

if ($emergencyOverrideApplied) {
    Write-Host "Emergency red-flag override applied: $callId"
}

        if ($DryRun) {
            Write-Host "DRY RUN - handoff preview built for: $callId"
            Write-AuditEvent -AuditDir $auditDir -EventType "handoff_generated" -Status "preview" -FileName $file.Name -CallId $callId -Details (New-RunControlAuditDetails @{
                handoff_path        = ""
                verification_status = "$($handoff.verification_status)"
                priority            = "$($handoff.priority)"
            })
        }
        else {
            $handoff | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $handoffPath -Encoding UTF8

            Write-Host "Saved handoff JSON: $handoffPath"
            Write-AuditEvent -AuditDir $auditDir -EventType "handoff_generated" -Status "ok" -FileName $file.Name -CallId $callId -Details (New-RunControlAuditDetails @{
                handoff_path        = $handoffPath
                verification_status = "$($handoff.verification_status)"
                priority            = "$($handoff.priority)"
            })
        }

        $isTestCallId = Test-JeffLocalTestCallId -CallId $callId
        $googlePushSkippedReason = ""
        if ($DryRun) {
            $googlePushSkippedReason = "dry_run"
        }
        elseif ($NoGooglePush) {
            $googlePushSkippedReason = "no_google_push"
        }
        elseif ($DisableGooglePush -or $env:JEFFLOCAL_DISABLE_GOOGLE_PUSH -eq "1") {
            $googlePushSkippedReason = "disabled_for_test"
        }
        elseif ($isTestCallId -and -not $AllowTestGooglePush) {
            $googlePushSkippedReason = "test_call_id_guard"
        }

        if (-not [string]::IsNullOrWhiteSpace($googlePushSkippedReason)) {
            Write-AuditEvent -AuditDir $auditDir -EventType "google_push" -Status "skipped" -FileName $file.Name -CallId $callId -Details (New-RunControlAuditDetails @{
                reason = $googlePushSkippedReason
                google_push_skipped_reason = $googlePushSkippedReason
                is_test_call_id = [bool]$isTestCallId
            })
            if ($googlePushSkippedReason -eq "dry_run") {
                Write-Host "DRY RUN - Google push skipped."
            }
            elseif ($googlePushSkippedReason -eq "no_google_push") {
                Write-Host "Google push skipped due to -NoGooglePush."
            }
            elseif ($googlePushSkippedReason -eq "test_call_id_guard") {
                Write-Host "Google push skipped for test call_id. Use -AllowTestGooglePush only if explicitly required."
            }
            else {
                Write-Host "Google Sheet push skipped for local test mode."
            }
        }
        elseif ($appSettings.google_sheet_enabled -eq $true) {
            if (-not (Test-Path -LiteralPath $pushScript)) {
                throw "Missing Google push script: $pushScript"
            }

            Write-Host "Pushing to Google Sheet: $callId"
            $pushResponse = & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $pushScript -JsonPath $handoffPath

            if ($LASTEXITCODE -ne 0) {
                throw "Google push script failed for $callId with exit code $LASTEXITCODE"
            }

            Write-AuditEvent -AuditDir $auditDir -EventType "google_push" -Status "ok" -FileName $file.Name -CallId $callId -Details (New-RunControlAuditDetails @{
                response = $pushResponse
            })

            if ($null -ne $pushResponse) {
                $pushResponse | Format-Table -AutoSize
            }

            Write-Host "Google push completed: $callId"
        }
        else {
            Write-AuditEvent -AuditDir $auditDir -EventType "google_push" -Status "skipped" -FileName $file.Name -CallId $callId -Details (New-RunControlAuditDetails @{
                reason = "google_sheet_disabled"
                google_push_skipped_reason = "google_sheet_disabled"
            })
            Write-Host "Google Sheet push disabled."
        }

        Write-AuditEvent -AuditDir $auditDir -EventType "call_processing" -Status "ok" -FileName $file.Name -CallId $callId -Details (New-RunControlAuditDetails @{
            attempt_count = $attemptCount
        })
    }

    if ($DryRun) {
        Write-AuditEvent -AuditDir $auditDir -EventType "file_processing" -Status "preview" -FileName $file.Name -Details (New-RunControlAuditDetails @{
            attempt_count  = $attemptCount
            processed_path = ""
            call_count     = $calls.Count
        })
        Write-Host "DRY RUN - no files moved, no Google push"
        Write-Host "DRY RUN completed: $($file.Name)"
    }
    else {
        $queueObject | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $processingPath -Encoding UTF8

        $processedPath = Join-Path $processed $file.Name
        Move-Item -LiteralPath $processingPath -Destination $processedPath -Force
        Clear-AttemptCount -AuditDir $auditDir -FileName $file.Name

        Write-AuditEvent -AuditDir $auditDir -EventType "file_processing" -Status "ok" -FileName $file.Name -Details (New-RunControlAuditDetails @{
            attempt_count  = $attemptCount
            processed_path = $processedPath
            call_count     = $calls.Count
        })

        Write-Host "Processed successfully: $($file.Name)"
    }
}
catch {
    $errorMessage = $_.Exception.Message
    $isPermanent = (
        $errorMessage -like "*missing call_id*" -or
        $errorMessage -like "*contains no call objects*" -or
        $errorMessage -like "*Missing Google push script*" -or
        $errorMessage -like "*Duplicate call_id values found in batch*" -or
        $errorMessage -like "*Call_id already processed previously*" -or
        $errorMessage -like "*file name already exists in processed queue*"
    )

    Write-Host "Processing failed: $($file.Name)"
    Write-Host $errorMessage

    if ($DryRun) {
        Write-AuditEvent -AuditDir $auditDir -EventType "file_processing" -Status "failed_dry_run" -FileName $file.Name -Details (New-RunControlAuditDetails @{
            attempt_count  = $attemptCount
            error_message  = $errorMessage
            max_retry_count = $maxRetryCount
        })
        Write-Host "DRY RUN failed - no files moved."
    }
    elseif ($isPermanent -or $attemptCount -ge $maxRetryCount) {
        Move-ToDeadletter `
            -ProcessingPath $processingPath `
            -DeadletterDir $deadletter `
            -AuditDir $auditDir `
            -Reason ($(if ($isPermanent) { "permanent_failure" } else { "max_retries_exceeded" })) `
            -ErrorMessage $errorMessage `
            -AttemptCount $attemptCount `
            -OriginalFileName $file.Name

        Write-AuditEvent -AuditDir $auditDir -EventType "file_processing" -Status "deadletter" -FileName $file.Name -Details (New-RunControlAuditDetails @{
            attempt_count = $attemptCount
            reason        = $(if ($isPermanent) { "permanent_failure" } else { "max_retries_exceeded" })
            error_message = $errorMessage
        })

        Write-Host "Moved to deadletter: $($file.Name)"
    }
    else {
        Save-AttemptCount -AuditDir $auditDir -FileName $file.Name -AttemptCount $attemptCount

        Move-ToFailed `
            -ProcessingPath $processingPath `
            -FailedDir $failed `
            -AuditDir $auditDir `
            -ErrorMessage $errorMessage `
            -AttemptCount $attemptCount `
            -OriginalFileName $file.Name

        Write-AuditEvent -AuditDir $auditDir -EventType "file_processing" -Status "failed" -FileName $file.Name -Details (New-RunControlAuditDetails @{
            attempt_count  = $attemptCount
            error_message  = $errorMessage
            max_retry_count = $maxRetryCount
        })

        Write-Host "Moved to failed: $($file.Name)"
    }

    exit 1
}






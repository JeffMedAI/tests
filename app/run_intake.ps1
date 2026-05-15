param(
    [string]$Model = "gemma4:e2b",
    [int]$TestIndex = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "C:\JeffLocal\app\common.ps1"
. "C:\JeffLocal\app\call_ollama.ps1"
. "C:\JeffLocal\app\detect_flags.ps1"
. "C:\JeffLocal\app\generate_staff_summary.ps1"
. "C:\JeffLocal\app\build_handoff.ps1"



$appSettingsPath = "C:\JeffLocal\config\app_settings.json"
$modelSettingsPath = "C:\JeffLocal\config\model_settings.json"

if (-not (Test-Path -LiteralPath $appSettingsPath)) {
    throw "Missing app settings file: $appSettingsPath"
}
if (-not (Test-Path -LiteralPath $modelSettingsPath)) {
    throw "Missing model settings file: $modelSettingsPath"
}

$appSettings = Get-Content -LiteralPath $appSettingsPath -Raw | ConvertFrom-Json
$modelSettings = Get-Content -LiteralPath $modelSettingsPath -Raw | ConvertFrom-Json

$CallsPath = $appSettings.test_input_json
$PatientsPath = $appSettings.patient_lookup_csv
$IncomingDir = $appSettings.queue_incoming
$OutputsDir = $appSettings.outputs_ollama_raw

Ensure-Dir $IncomingDir
Ensure-Dir $OutputsDir

if (-not (Test-Path -LiteralPath $CallsPath)) {
    throw "Missing calls file at: $CallsPath"
}
if (-not (Test-Path -LiteralPath $PatientsPath)) {
    throw "Missing patient lookup file at: $PatientsPath"
}

$allCalls = Get-Content -LiteralPath $CallsPath -Raw | ConvertFrom-Json
if ($TestIndex -lt 0 -or $TestIndex -ge $allCalls.Count) {
    throw "TestIndex $TestIndex is out of range."
}
$call = $allCalls[$TestIndex]

$patients = Import-Csv -LiteralPath $PatientsPath

$normalizedPatients = foreach ($p in $patients) {
    $displayName = Convert-LookupNameToDisplay "$($p.'Full Name')"

    [pscustomobject]@{
        patient_ref = "$($p.'EMIS Number')"
        full_name = $displayName
        full_name_normalized = Normalize-Name $displayName
        dob = Normalize-DateString "$($p.'Date of Birth')"
        age = "$($p.'Age')"
        gender = "$($p.'Gender')"
        nhs_number = "$($p.'NHS Number')"
    }
}

$result = Invoke-JeffOllamaExtraction -Model $Model -Call $call -OutputsDir $OutputsDir
$llmData = $result.llm_data

function Get-LlmValue {
    param(
        [object]$Object,
        [string]$Name,
        $Default = ""
    )

    if ($null -eq $Object) {
        return $Default
    }

    $prop = $Object.PSObject.Properties[$Name]
    if ($null -ne $prop) {
        return $prop.Value
    }

    return $Default
}

$pathwayResponses = Get-LlmValue -Object $llmData -Name "pathway_responses" -Default $null
$prescriptionResponses = Get-LlmValue -Object $pathwayResponses -Name "prescription" -Default $null
$urgencyAssessment = Get-LlmValue -Object $llmData -Name "urgency_assessment" -Default $null
$selectedPathway = [string](Get-LlmValue -Object $llmData -Name "selected_pathway" -Default "")
$requestType = [string](Get-LlmValue -Object $llmData -Name "request_type" -Default $selectedPathway)
$medicationsRequested = Get-LlmValue -Object $prescriptionResponses -Name "medications_requested" -Default @()
$pharmacy = Get-LlmValue -Object $prescriptionResponses -Name "pharmacy" -Default ""
$urgencyLevel = Get-LlmValue -Object $urgencyAssessment -Name "urgency_level" -Default ""

$normalizedInput = [pscustomobject]@{
    patient_name = Normalize-Whitespace (((Get-LlmValue -Object $llmData -Name "patient_name") | ForEach-Object { "$_" }) -join " ")
    dob = Normalize-DateString "$((Get-LlmValue -Object $llmData -Name "dob"))"
    callback_number = Normalize-Phone "$((Get-LlmValue -Object $llmData -Name "callback_number"))"
    medications_requested = Convert-MedsToArray $medicationsRequested
    urgency_note = Normalize-Whitespace "$urgencyLevel"
    pharmacy = Normalize-Whitespace "$pharmacy"
    caller_for = (Normalize-Whitespace "$((Get-LlmValue -Object $llmData -Name "caller_relationship" -Default "self"))").ToLower()
    request_type = $requestType
    request_subtype = $selectedPathway
}

if ($normalizedInput.caller_for -eq "myself") {
    $normalizedInput.caller_for = "self"
}

$normalizedRawTranscript = Normalize-TranscriptText "$($call.raw_transcript)"
$flags = Get-JeffFlags -NormalizedRawTranscript $normalizedRawTranscript -NormalizedInput $normalizedInput
$transcriptSummary = [string](Get-LlmValue -Object $llmData -Name "transcript_summary" -Default "")
if ([string]::IsNullOrWhiteSpace($transcriptSummary)) {
    $transcriptSummary = New-JeffTranscriptSummary -NormalizedInput $normalizedInput
}

if ($null -ne $pathwayResponses) {
    if ($call.PSObject.Properties["pathway_responses"]) {
        $call.PSObject.Properties["pathway_responses"].Value = $pathwayResponses
    }
    else {
        $call | Add-Member -NotePropertyName "pathway_responses" -NotePropertyValue $pathwayResponses -Force
    }
}

if (-not [string]::IsNullOrWhiteSpace($requestType)) {
    if ($call.PSObject.Properties["request_type"]) {
        $call.PSObject.Properties["request_type"].Value = $requestType
    }
    else {
        $call | Add-Member -NotePropertyName "request_type" -NotePropertyValue $requestType -Force
    }
}

$handoffObject = New-JeffHandoffObject `
    -Call $call `
    -NormalizedInput $normalizedInput `
    -NormalizedPatients $normalizedPatients `
    -Flags $flags `
    -TranscriptSummary $transcriptSummary `
    -NormalizedRawTranscript $normalizedRawTranscript

$queuePath = Join-Path $IncomingDir "$($call.call_id).json"
$handoffObject | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $queuePath -Encoding UTF8

Write-Host ""
Write-Host "Intake complete."
Write-Host "Queue file created at:"
Write-Host $queuePath
Write-Host ""
Write-Host "Raw Ollama output saved to:"
Write-Host $result.raw_output_path
Write-Host ""

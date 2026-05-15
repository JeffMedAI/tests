Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "C:\JeffLocal\app\modules\Jeff.Common.ps1"
. "C:\JeffLocal\app\modules\Jeff.RequestType.ps1"
. "C:\JeffLocal\app\modules\Jeff.Validation.ps1"
. "C:\JeffLocal\app\modules\Jeff.PatientMatch.ps1"
. "C:\JeffLocal\app\modules\Jeff.Handoff.ps1"
. "C:\JeffLocal\app\build_handoff.ps1"

function Assert-True {
    param([string]$Name, [bool]$Condition)
    if (-not $Condition) { throw "$Name expected true" }
}

function Assert-False {
    param([string]$Name, [bool]$Condition)
    if ($Condition) { throw "$Name expected false" }
}

function Assert-Contains {
    param([string]$Name, [string]$Text, [string]$Expected)
    if ($Text -notlike "*$Expected*") { throw "$Name expected to contain '$Expected' but was '$Text'" }
}

function Assert-NotContains {
    param([string]$Name, [string]$Text, [string]$Unexpected)
    if ($Text -like "*$Unexpected*") { throw "$Name expected not to contain '$Unexpected' but was '$Text'" }
}

function Assert-MaxWords {
    param([string]$Name, [string]$Text, [int]$MaxWords)
    $count = @(([string]$Text).Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)).Count
    if ($count -gt $MaxWords) { throw "$Name expected <= $MaxWords words but got $count in '$Text'" }
}

$patients = @(
    [pscustomobject]@{
        patient_ref = "T100"
        full_name = "Julie Chadwick"
        full_name_normalized = "JULIE CHADWICK"
        dob = "1971-05-02"
        age = "55"
        gender = "Female"
        nhs_number = "900 000 0001"
    }
)

function New-TestHandoff {
    param(
        [string]$CallId,
        [string]$PatientName,
        [string]$Dob = "1971-05-02",
        [string]$Callback = "07111000000",
        [string]$CallerFor = "self",
        [array]$Patients = $patients,
        [string]$RawTranscript = "Caller asks for a repeat prescription for amlodipine.",
        [string]$DraftSummary = "Patient called about medication."
    )

    $normalizedInput = [pscustomobject]@{
        patient_name = $PatientName
        dob = $Dob
        postcode = "PR9 7LT"
        callback_number = $Callback
        medications_requested = @("amlodipine")
        urgency_note = ""
        pharmacy = "Test Pharmacy"
        caller_for = $CallerFor
        request_type = "prescription"
        request_subtype = "repeat_prescription"
    }

    $call = [pscustomobject]@{
        call_id = $CallId
        call_timestamp = "2026-05-15T10:00:00Z"
        workflow = "postprocessing_test"
        request_type = "prescription"
        request_subtype = "repeat_prescription"
        source = "test"
        normalized_input = $normalizedInput
        pathway_responses = [pscustomobject]@{
            selected_pathway = "prescription"
            prescription = [pscustomobject]@{
                prescription_type = "repeat"
                medications_requested = @("amlodipine")
                pharmacy = "Test Pharmacy"
                run_out_status = ""
            }
        }
        raw_transcript = $RawTranscript
        transcript_summary = $DraftSummary
        staff_review_required = $false
        red_flags_present = $false
    }

    $missingFields = @(Get-JeffMissingFields -NormalizedInput $normalizedInput -RequestType "prescription")
    return New-JeffHandoffObject `
        -Call $call `
        -NormalizedInput $normalizedInput `
        -NormalizedPatients $Patients `
        -Flags ([pscustomobject]@{ transcript_quality_flag = "ok"; uncertain_fields = @(); missing_fields = $missingFields; priority = "routine" }) `
        -TranscriptSummary $DraftSummary `
        -NormalizedRawTranscript $RawTranscript
}

$matched = New-TestHandoff -CallId "POSTPROC-MATCHED" -PatientName "Julie Chadwick" -RawTranscript "Caller says this is Joolie Chadwik and asks for amlodipine."
Assert-Contains -Name "matched summary uses EMIS" -Text $matched.transcript_summary -Expected "EMIS T100"
Assert-Contains -Name "matched summary uses NHS" -Text $matched.transcript_summary -Expected "NHS 900 000 0001"
Assert-Contains -Name "matched body uses verified identifier" -Text $matched.task_body -Expected "Verified patient: EMIS T100 / NHS 900 000 0001"
Assert-NotContains -Name "matched text drops transcript misspelling" -Text "$($matched.transcript_summary) $($matched.task_body)" -Unexpected "Joolie"
Assert-MaxWords -Name "matched summary word limit" -Text $matched.transcript_summary -MaxWords 22
Assert-MaxWords -Name "matched body word limit" -Text $matched.task_body -MaxWords 45

$possible = New-TestHandoff -CallId "POSTPROC-POSSIBLE" -PatientName "Julie Chaddick"
Assert-Contains -Name "possible status" -Text $possible.verification_status -Expected "possible_match"
Assert-Contains -Name "possible summary cautious" -Text $possible.transcript_summary -Expected "possible match"
Assert-Contains -Name "possible body cautious" -Text $possible.task_body -Expected "Possible match"
Assert-Contains -Name "possible review required" -Text $possible.task_body -Expected "Staff review required"
Assert-NotContains -Name "possible not verified" -Text $possible.task_body -Unexpected "Verified patient"

$weak = Get-JeffVerifiedStaffFacingText `
    -RequestType "prescription" `
    -PathwayResponses ([pscustomobject]@{ prescription = [pscustomobject]@{ medications_requested = @("amlodipine") } }) `
    -VerificationStatus "possible_match_weak" `
    -TopCandidateRef "T100" `
    -CandidateMatches @([pscustomobject]@{ ref = "T100"; nhs_number = "900 000 0001" }) `
    -NormalizedInput ([pscustomobject]@{ patient_name = "Julie Chadwock"; dob = "1971-05-02" }) `
    -SafeToQueue $true `
    -StaffReviewRequired $true `
    -CallbackNumber "07111000000" `
    -CallerFor "self" `
    -MedicationsRequested @("amlodipine")
Assert-Contains -Name "weak match review" -Text $weak.task_body -Expected "Staff review required"
Assert-NotContains -Name "weak not verified" -Text $weak.task_body -Unexpected "Verified patient"

$noMatch = New-TestHandoff -CallId "POSTPROC-NOMATCH" -PatientName "Unknown Person" -Patients @()
Assert-Contains -Name "no match title" -Text $noMatch.task_title -Expected "Unknown Patient"
Assert-Contains -Name "no match body no verified id" -Text $noMatch.task_body -Expected "No verified EMIS/NHS match"
Assert-NotContains -Name "no match no EMIS" -Text "$($noMatch.transcript_summary) $($noMatch.task_body)" -Unexpected "EMIS T100"

$insufficient = New-TestHandoff -CallId "POSTPROC-INSUFFICIENT" -PatientName "" -Dob "" -Callback ""
Assert-Contains -Name "insufficient missing dob" -Text "$($insufficient.transcript_summary) $($insufficient.task_body)" -Expected "DOB missing"
Assert-Contains -Name "insufficient callback" -Text $insufficient.task_body -Expected "Callback missing"
Assert-Contains -Name "insufficient review" -Text $insufficient.task_body -Expected "Staff review required"

$thirdParty = New-TestHandoff -CallId "POSTPROC-THIRD-PARTY" -PatientName "Julie Chadwick" -CallerFor "daughter"
Assert-Contains -Name "caller acting for patient" -Text $thirdParty.task_body -Expected "Caller acting for patient"

$callbackUnconfirmed = New-TestHandoff -CallId "POSTPROC-CALLBACK" -PatientName "Julie Chadwick" -Callback "not confirmed"
Assert-Contains -Name "callback title/body" -Text $callbackUnconfirmed.task_body -Expected "Callback not confirmed"
Assert-Contains -Name "callback summary" -Text $callbackUnconfirmed.transcript_summary -Expected "callback not confirmed"

$messy = New-TestHandoff -CallId "POSTPROC-MESSY" -PatientName "Julie Chadwick" -RawTranscript "Messy transcript with multiple intents." -DraftSummary "Patient called about medication."
Assert-NotContains -Name "vague draft rejected summary" -Text $messy.transcript_summary -Unexpected "Patient called about medication"
Assert-MaxWords -Name "messy summary word limit" -Text $messy.transcript_summary -MaxWords 22
Assert-MaxWords -Name "messy body word limit" -Text $messy.task_body -MaxWords 45

Write-Output "Staff-facing post-processing tests passed."

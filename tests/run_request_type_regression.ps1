Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. "C:\JeffLocal\app\common.ps1"
. "C:\JeffLocal\app\modules\Jeff.Common.ps1"
. "C:\JeffLocal\app\modules\Jeff.RequestType.ps1"
. "C:\JeffLocal\app\modules\Jeff.Validation.ps1"
. "C:\JeffLocal\app\modules\Jeff.Emergency.ps1"
. "C:\JeffLocal\app\modules\Jeff.PatientMatch.ps1"
. "C:\JeffLocal\app\modules\Jeff.Handoff.ps1"
. "C:\JeffLocal\app\build_handoff.ps1"

function Assert-Equal {
    param(
        [string]$Name,
        $Actual,
        $Expected
    )

    if ($Actual -ne $Expected) {
        throw "$Name expected '$Expected' but got '$Actual'"
    }
}

function Assert-True {
    param(
        [string]$Name,
        [bool]$Condition
    )

    if (-not $Condition) {
        throw "$Name expected true"
    }
}

$patients = @(
    [pscustomobject]@{
        patient_ref = "T100"
        full_name = "TEST PATIENT"
        full_name_normalized = "TEST PATIENT"
        dob = "1970-01-01"
        age = "56"
        gender = "Female"
        nhs_number = "999 000 0000"
    }
)

$cases = @(
    @{ request_type = "prescription"; request_subtype = "repeat_prescription"; meds = @("atorvastatin 20mg"); text = "Caller needs repeat prescription tablets." },
    @{ request_type = "sick_note"; request_subtype = "sick_note_request"; meds = @(); text = "Caller needs a sick note for work." },
    @{ request_type = "referral"; request_subtype = "referral_query"; meds = @(); text = "Caller is chasing a hospital referral." },
    @{ request_type = "test_result"; request_subtype = "test_results_query"; meds = @(); text = "Caller asks for blood test result." },
    @{ request_type = "admin"; request_subtype = "admin_query"; meds = @(); text = "Caller asks reception for a letter." },
    @{ request_type = "appointment_redirect"; request_subtype = "appointment_request"; meds = @(); text = "Caller wants to book an appointment." }
)

foreach ($case in $cases) {
    $call = [pscustomobject]@{
        call_id = "REGRESSION-$($case.request_type)"
        call_timestamp = "2026-05-08T00:00:00Z"
        workflow = "regression"
        request_type = $case.request_type
        request_subtype = $case.request_subtype
        source = "test"
        normalized_input = [pscustomobject]@{
            patient_name = "TEST PATIENT"
            dob = "1970-01-01"
            postcode = "PR9 7LT"
            callback_number = "07111000000"
            medications_requested = @($case.meds)
            urgency_note = ""
            pharmacy = "Test Pharmacy"
            caller_for = "self"
            supplied_nhs_number = ""
            request_type = $case.request_type
            request_subtype = $case.request_subtype
        }
        pathway_responses = [pscustomobject]@{
            selected_pathway = $case.request_type
            identity = [pscustomobject]@{
                patient_name = "TEST PATIENT"
                dob = "1970-01-01"
                postcode = "PR9 7LT"
                callback_number_from_caller_id = "07111000000"
            }
        }
        voice_agent = [pscustomobject]@{
            call_duration_seconds = 120
            caller_sentiment = "calm"
            caller_difficulty = "easy"
            transcript_quality = "good"
        }
        quality = [pscustomobject]@{
            handoff_confidence = 0.9
        }
        raw_transcript = $case.text
        transcript_summary = $case.text
        staff_review_required = $false
        red_flags_present = $false
    }

    $normalizedInput = $call.normalized_input
    $missingFields = @(Get-JeffMissingFields -NormalizedInput $normalizedInput -RequestType $case.request_type)

    if ($case.request_type -ne "prescription") {
        Assert-Equal -Name "$($case.request_type) missing medication count" -Actual @($missingFields | Where-Object { $_ -eq "medications_requested" }).Count -Expected 0
    }

    $handoffArgs = @{
        Call = $call
        NormalizedInput = $normalizedInput
        NormalizedPatients = $patients
        Flags = [pscustomobject]@{
            transcript_quality_flag = "ok"
            uncertain_fields = @()
            missing_fields = $missingFields
            priority = "routine"
        }
        TranscriptSummary = $call.transcript_summary
        NormalizedRawTranscript = $call.raw_transcript
    }
    $handoff = New-JeffHandoffObject @handoffArgs

    Assert-Equal -Name "$($case.request_type) request_type" -Actual $handoff.request_type -Expected $case.request_type
    Assert-Equal -Name "$($case.request_type) request_subtype" -Actual $handoff.request_subtype -Expected $case.request_subtype
    Assert-Equal -Name "$($case.request_type) verification" -Actual $handoff.verification_status -Expected "matched"
    Assert-True -Name "$($case.request_type) raw transcript" -Condition (-not [string]::IsNullOrWhiteSpace($handoff.raw_transcript))
    Assert-True -Name "$($case.request_type) pathway responses" -Condition ($null -ne $handoff.pathway_responses)
    Assert-True -Name "$($case.request_type) voice agent" -Condition ($null -ne $handoff.voice_agent)
}

$adminEmergencyCall = [pscustomobject]@{
    call_id = "REGRESSION-ADMIN-EMERGENCY"
    request_type = "admin"
    request_subtype = "urgent_appointment_request"
    raw_transcript = "Caller has chest tightness, sweating and breathlessness."
}

$adminHandoffArgs = @{
    Call = $adminEmergencyCall
    NormalizedInput = [pscustomobject]@{
        patient_name = "TEST PATIENT"
        dob = "1970-01-01"
        callback_number = "07111000000"
        medications_requested = @()
        urgency_note = "Chest tightness, sweating and breathlessness."
        pharmacy = ""
        caller_for = "self"
    }
    NormalizedPatients = $patients
    Flags = [pscustomobject]@{
        transcript_quality_flag = "ok"
        uncertain_fields = @()
        missing_fields = @()
        priority = "routine"
    }
    TranscriptSummary = "Admin caller described possible emergency symptoms."
    NormalizedRawTranscript = $adminEmergencyCall.raw_transcript
}
$adminHandoff = New-JeffHandoffObject @adminHandoffArgs
$emergencyArgs = @{
    Handoff = $adminHandoff
    ScanObjects = @($adminHandoff, $adminEmergencyCall.raw_transcript)
}
$emergencyApplied = Invoke-JeffEmergencyOverride @emergencyArgs

Assert-True -Name "admin emergency override applied" -Condition $emergencyApplied
Assert-Equal -Name "admin emergency request_type" -Actual $adminHandoff.request_type -Expected "admin"
Assert-Equal -Name "admin emergency priority" -Actual $adminHandoff.priority -Expected "999 Emergency"
Assert-Equal -Name "admin emergency safe_to_queue" -Actual $adminHandoff.safe_to_queue -Expected $false
Assert-Equal -Name "admin emergency staff_review_required" -Actual $adminHandoff.staff_review_required -Expected $true
Assert-Equal -Name "admin emergency red_flags_present" -Actual $adminHandoff.red_flags_present -Expected $true

Write-Output "6-request-type regression passed."

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

function Convert-LookupNameToDisplayForTest {
    param([string]$Name)

    if ([string]::IsNullOrWhiteSpace($Name)) {
        return ""
    }

    $clean = $Name.Trim()
    $clean = [regex]::Replace($clean, "\s*\([^)]*\)\s*", "")

    if ($clean -match "^\s*([^,]+)\s*,\s*(.+?)\s*$") {
        return "$($matches[2].Trim()) $($matches[1].Trim())".Trim()
    }

    return $clean
}

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

$callsJsonPath = Join-Path $env:TEMP ("jefflocal_rawmock_calls_" + [guid]::NewGuid().ToString("N") + ".json")
try {
    python -c "import sys,json; sys.path.insert(0, r'C:\JeffLocal\tests\fixtures'); import raw_intake_mock_pack as p; open(r'$callsJsonPath','w',encoding='utf-8').write(json.dumps(p.build_mock_calls()))"
    $parsedCalls = Get-Content -LiteralPath $callsJsonPath -Raw | ConvertFrom-Json
    $calls = @($parsedCalls | ForEach-Object { $_ })
}
finally {
    Remove-Item -LiteralPath $callsJsonPath -Force -ErrorAction SilentlyContinue
}
$expected = Get-Content -LiteralPath "C:\JeffLocal\tests\fixtures\expected_raw_intake_mock_outcomes.json" -Raw | ConvertFrom-Json

$patientRows = Import-Csv -LiteralPath "C:\JeffLocal\data\patient_lookup\mock_patient_lookup_v3.csv" |
    Where-Object { -not [string]::IsNullOrWhiteSpace($_.'Full Name') -and $_.'Full Name' -notmatch '^#' }

$patients = @(
    foreach ($row in $patientRows) {
        $displayName = Convert-LookupNameToDisplayForTest "$($row.'Full Name')"
        if ([string]::IsNullOrWhiteSpace($displayName)) {
            continue
        }

        [pscustomobject]@{
            patient_ref = "$($row.'EMIS Number')"
            full_name = $displayName
            full_name_normalized = Normalize-Name $displayName
            dob = Normalize-DateString "$($row.'Date of Birth')"
            age = "$($row.'Age')"
            gender = "$($row.'Gender')"
            nhs_number = "$($row.'NHS Number')"
        }
    }
)

$results = @()

foreach ($call in $calls) {
    $callId = [string]$call.call_id
    $normalizedInput = $call.normalized_input
    $requestType = Normalize-JeffRequestType ([string]$call.request_type)
    if ([string]$call.request_type -eq "unknown") {
        $requestType = "admin"
    }

    $flags = [pscustomobject]@{
        transcript_quality_flag = ""
        uncertain_fields = @()
        missing_fields = @(Get-JeffMissingFields -NormalizedInput $normalizedInput -RequestType $requestType)
        priority = "routine"
    }

    $handoff = New-JeffHandoffObject `
        -Call $call `
        -NormalizedInput $normalizedInput `
        -NormalizedPatients $patients `
        -Flags $flags `
        -TranscriptSummary ([string]$call.transcript_summary) `
        -NormalizedRawTranscript (Normalize-TranscriptText ([string]$call.raw_transcript))

    $emergencyApplied = Invoke-JeffEmergencyOverride -Handoff $handoff -ScanObjects @($handoff, $call.raw_transcript, $call.transcript_summary, $call.pathway_responses)

    $expectedEntry = $expected.PSObject.Properties[$callId].Value

    Assert-Equal -Name "$callId priority" -Actual $handoff.priority -Expected $expectedEntry.expected_priority
    Assert-Equal -Name "$callId safe_to_queue" -Actual $handoff.safe_to_queue -Expected $expectedEntry.expected_safe_to_queue
    Assert-Equal -Name "$callId staff_review_required" -Actual $handoff.staff_review_required -Expected $expectedEntry.expected_staff_review_required
    Assert-Equal -Name "$callId red_flags_present" -Actual $handoff.red_flags_present -Expected $expectedEntry.expected_red_flags_present

    $results += [pscustomobject]@{
        call_id = $callId
        expected_priority = $expectedEntry.expected_priority
        actual_priority = $handoff.priority
        safe_to_queue = $handoff.safe_to_queue
        staff_review_required = $handoff.staff_review_required
        red_flags_present = $handoff.red_flags_present
        emergency_override_applied = $emergencyApplied
        result = "PASS"
    }
}

$results | Format-Table -AutoSize
Write-Output "RAWMOCK priority comparison passed."

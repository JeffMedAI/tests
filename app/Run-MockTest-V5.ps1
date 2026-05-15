param(
    [string]$PackPath = "C:\JeffLocal\data\test_inputs\run_mock_test_V5.json",
    [string]$JeffLocalRoot = "C:\JeffLocal",
    [switch]$StageOnly,
    [switch]$RunQueue,
    [switch]$OverwriteExisting
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Ensure-Folder {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Resolve-ChildPath {
    param([string]$Base, [string]$Child)
    return [System.IO.Path]::Combine($Base, $Child)
}

function Convert-PackItemToIntakePayload {
    param(
        [Parameter(Mandatory = $true)]
        $Item
    )

    $patientName = "$($Item.patient_name)".Trim()
    $dob = "$($Item.dob)".Trim()
    $callback = "$($Item.callback_number)".Trim()
    $meds = @($Item.medications_requested)
    $urgency = "$($Item.urgency_note)".Trim()
    $pharmacy = "$($Item.pharmacy)".Trim()
    $callerFor = "$($Item.caller_for)".Trim()
    $rawTranscript = "$($Item.raw_transcript)".Trim()

    return [ordered]@{
        call_id               = $Item.call_id
        call_timestamp        = $Item.call_timestamp
        workflow              = "prescription"
        request_type          = "prescription"
        source                = "mock_test_v5"

        # fields your processor is likely expecting
        patient_name_raw      = $patientName
        dob_raw               = $dob
        callback_number_raw   = $callback
        medications_raw       = ($meds -join ", ")
        urgency_note_raw      = $urgency
        pharmacy_raw          = $pharmacy
        caller_for_raw        = $callerFor

        # normalized / convenience fields
        patient_name          = $patientName
        dob                   = $dob
        callback_number       = $callback
        medications_requested = $meds
        urgency_note          = $urgency
        pharmacy              = $pharmacy
        caller_for            = $callerFor

        raw_transcript        = $rawTranscript
        transcript            = $rawTranscript
        transcript_text       = $rawTranscript
    }
}

Write-Step "Checking JeffLocal paths"
$incomingDir   = Resolve-ChildPath $JeffLocalRoot "queue\incoming"
$testInputDir  = Resolve-ChildPath $JeffLocalRoot "data\test_inputs\run_mock_test_V5"
$runIntakePath = Resolve-ChildPath $JeffLocalRoot "app\run_intake.ps1"
$processPath   = Resolve-ChildPath $JeffLocalRoot "app\process_queue.ps1"

Ensure-Folder $incomingDir
Ensure-Folder $testInputDir

if (-not (Test-Path $PackPath)) {
    throw "Pack file not found: $PackPath"
}

Write-Step "Loading pack"
$pack = Get-Content -Path $PackPath -Raw | ConvertFrom-Json
if (-not $pack -or $pack.Count -eq 0) {
    throw "Pack is empty: $PackPath"
}

Write-Step "Staging mock calls"
$staged = @()

foreach ($item in $pack) {
    $payload = Convert-PackItemToIntakePayload -Item $item
    $fileName = "{0}.json" -f $item.call_id
    $testInputFile = Resolve-ChildPath $testInputDir $fileName
    $incomingFile  = Resolve-ChildPath $incomingDir  $fileName

    if (((Test-Path $testInputFile) -or (Test-Path $incomingFile)) -and -not $OverwriteExisting) {
        throw "File already exists for $($item.call_id). Use -OverwriteExisting to replace staged files."
    }

    $json = $payload | ConvertTo-Json -Depth 8

    Set-Content -Path $testInputFile -Value $json -Encoding UTF8
    Set-Content -Path $incomingFile  -Value $json -Encoding UTF8

    $staged += [pscustomobject]@{
        CallId       = $item.call_id
        Expected     = $item.expected_verification_status
        TestInput    = $testInputFile
        Incoming     = $incomingFile
    }
}

$staged | Format-Table -AutoSize

if ($StageOnly) {
    Write-Step "Stage only complete"
    Write-Host "Mock calls staged in:" -ForegroundColor Green
    Write-Host "  $testInputDir"
    Write-Host "  $incomingDir"
    exit 0
}

if (Test-Path $runIntakePath) {
    Write-Step "run_intake.ps1 detected"
    Write-Host "Note: mock call files have already been staged into queue\incoming." -ForegroundColor Yellow
    Write-Host "If your local build expects run_intake.ps1 first, adapt the payload path mapping there." -ForegroundColor Yellow
} else {
    Write-Host "run_intake.ps1 not found at $runIntakePath" -ForegroundColor Yellow
}

if ($RunQueue) {
    if (-not (Test-Path $processPath)) {
        throw "process_queue.ps1 not found: $processPath"
    }

    Write-Step "Running process_queue.ps1"
    & $processPath
}

Write-Step "Done"
Write-Host "Next checks:" -ForegroundColor Green
Write-Host "  1. Confirm 10 new rows reach Staff Handoff"
Write-Host "  2. Confirm Raw Transcripts receives the pack"
Write-Host "  3. Rebuild Call Details sheet"
Write-Host "  4. Compare outputs against run_mock_test_V5_expected.csv"

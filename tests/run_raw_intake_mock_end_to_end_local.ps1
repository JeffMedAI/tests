param(
    [switch]$AllowLiveQueueWrite,
    [switch]$DisableGooglePush,
    [switch]$RefreshRawmockArtifacts
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $AllowLiveQueueWrite) {
    Write-Warning "This script writes encrypted mock calls to C:\JeffLocal\queue\encrypted_raw and runs the local intake cycle."
    Write-Warning "Re-run with -AllowLiveQueueWrite when you are ready to perform the local end-to-end mock run."
    exit 2
}

$basePath = "C:\JeffLocal"
$fixturesPath = Join-Path $basePath "tests\fixtures"
$encryptedRawPath = Join-Path $basePath "queue\encrypted_raw"
$handoffPath = Join-Path $basePath "outputs\handoff_json"

function Move-RawmockArtifactsToArchive {
    param(
        [string]$BasePath
    )

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $archiveRoot = Join-Path $BasePath "backup\rawmock_regeneration_$timestamp"
    $relativeFolders = @(
        "queue\encrypted_raw",
        "queue\incoming",
        "queue\processed",
        "queue\failed",
        "queue\deadletter",
        "outputs\handoff_json",
        "outputs\debug",
        "outputs\ollama_raw",
        "logs\transcripts"
    )

    $summary = @()
    $totalMoved = 0

    foreach ($relativeFolder in $relativeFolders) {
        $sourceFolder = Join-Path $BasePath $relativeFolder
        $count = 0

        if (Test-Path -LiteralPath $sourceFolder) {
            $files = @(Get-ChildItem -LiteralPath $sourceFolder -Filter "*RAWMOCK*" -File -ErrorAction SilentlyContinue)

            foreach ($file in $files) {
                if ($file.Name -notlike "*RAWMOCK*") {
                    throw "Safety check failed: refusing to archive non-RAWMOCK file $($file.FullName)"
                }

                $targetFolder = Join-Path $archiveRoot $relativeFolder
                New-Item -ItemType Directory -Force -Path $targetFolder | Out-Null
                Move-Item -LiteralPath $file.FullName -Destination (Join-Path $targetFolder $file.Name)
                $count += 1
                $totalMoved += 1
            }
        }

        $summary += [pscustomobject]@{
            folder = $relativeFolder
            archived_count = $count
        }
    }

    Write-Host "RAWMOCK refresh archive: $archiveRoot"
    foreach ($item in $summary) {
        Write-Host ("  {0}: {1}" -f $item.folder, $item.archived_count)
    }

    if ($totalMoved -eq 0) {
        Write-Host "No existing RAWMOCK artifacts found to archive."
    }
}

if ($RefreshRawmockArtifacts) {
    Move-RawmockArtifactsToArchive -BasePath $basePath
}

Write-Host "Writing encrypted Raw Intake mock calls to: $encryptedRawPath"
python (Join-Path $fixturesPath "raw_intake_mock_pack.py") --output-dir $encryptedRawPath

Write-Host "Running local encrypted intake cycle."
$cycleArgs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", (Join-Path $basePath "app\run_encrypted_intake_cycle.ps1"))
if ($DisableGooglePush) {
    $cycleArgs += "-DisableGooglePush"
}
powershell.exe @cycleArgs

Write-Host "Building Raw Intake rows from produced handoff JSON files."
$rowBuilder = Join-Path $basePath "app\build_raw_intake_row.py"
$expected = Get-Content -LiteralPath (Join-Path $fixturesPath "expected_raw_intake_mock_outcomes.json") -Raw | ConvertFrom-Json
$callIds = @($expected.PSObject.Properties.Name)
$missing = @()

foreach ($callId in $callIds) {
    $path = Join-Path $handoffPath "$callId`_handoff.json"
    if (-not (Test-Path -LiteralPath $path)) {
        $missing += $callId
        continue
    }

    python $rowBuilder $path | Out-Null
}

if ($missing.Count -gt 0) {
    throw "Missing handoff JSON for call ids: $($missing -join ', ')"
}

Write-Host "Raw Intake mock end-to-end local run completed."

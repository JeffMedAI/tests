param(
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$basePath = "C:\JeffLocal"
$runner = Join-Path $basePath "tests\run_raw_intake_mock_end_to_end_local.ps1"
$resetDashboard = Join-Path $basePath "tests\reset_dashboard_test_history.ps1"
$importDashboard = Join-Path $basePath "tests\import_dashboard_handoffs.ps1"
$priorityComparison = Join-Path $basePath "tests\run_rawmock_priority_comparison.ps1"
$columnContract = Join-Path $basePath "tests\run_raw_intake_column_contract.ps1"
$requestRegression = Join-Path $basePath "tests\run_request_type_regression.ps1"
$safeUniversalSmoke = Join-Path $basePath "tests\run_safe_universal_smoke.ps1"
$safeIntakeSmoke = Join-Path $basePath "tests\run_safe_intake_mode_smoke.ps1"
$googlePushSmoke = Join-Path $basePath "tests\run_google_push_disable_smoke.ps1"
$refreshSmoke = Join-Path $basePath "tests\run_rawmock_refresh_safety_smoke.ps1"
$dashboardTests = Join-Path $basePath "dashboard\.venv\Scripts\python.exe"
$dashboardPytestArgs = @("-m", "pytest", (Join-Path $basePath "dashboard\tests"), "-q")
$dashboardDb = Join-Path $basePath "dashboard\data\dashboard.sqlite"
$handoffDir = Join-Path $basePath "outputs\handoff_json"

function Count-MatchingAuditEntries {
    param([string[]]$CallIds)

    $auditDir = Join-Path $basePath "logs\audits"
    if (-not (Test-Path -LiteralPath $auditDir)) {
        return 0
    }

    $count = 0
    foreach ($path in Get-ChildItem -LiteralPath $auditDir -Filter *.jsonl -File -ErrorAction SilentlyContinue) {
        foreach ($line in Get-Content -LiteralPath $path.FullName) {
            if ($line -match '"event_type":"google_push"' -and $line -match '"status":"skipped"') {
                foreach ($callId in $CallIds) {
                    if ($line -match [regex]::Escape($callId)) {
                        $count += 1
                        break
                    }
                }
            }
        }
    }

    return $count
}

function Invoke-CheckedScript {
    param(
        [string]$Path,
        [string[]]$Arguments = @()
    )

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Path @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Script failed: $Path (exit code $LASTEXITCODE)"
    }
}

if (-not $Force) {
    $prompt = Read-Host "This will reset the dashboard test DB, archive RAWMOCK artifacts, and run a fresh local mock batch. Type YES to continue"
    if ($prompt -ne "YES") {
        Write-Host "Batch cancelled."
        exit 2
    }
}

Write-Host "Resetting dashboard test history."
Invoke-CheckedScript -Path $resetDashboard -Arguments @("-Force")

$expected = Get-Content -LiteralPath (Join-Path $basePath "tests\fixtures\expected_raw_intake_mock_outcomes.json") -Raw | ConvertFrom-Json
$callIds = @($expected.PSObject.Properties.Name)
$auditBefore = Count-MatchingAuditEntries -CallIds $callIds

Write-Host "Running RAWMOCK batch with Google push disabled."
Invoke-CheckedScript -Path $runner -Arguments @("-AllowLiveQueueWrite", "-DisableGooglePush", "-RefreshRawmockArtifacts")

$handoffCount = @(Get-ChildItem -LiteralPath $handoffDir -Filter "RAWMOCK*_handoff.json" -File -ErrorAction SilentlyContinue).Count
$processedCount = @(Get-ChildItem -LiteralPath (Join-Path $basePath "queue\processed") -Filter "RAWMOCK*" -File -ErrorAction SilentlyContinue).Count
$failedCount = @(Get-ChildItem -LiteralPath (Join-Path $basePath "queue\failed") -Filter "RAWMOCK*" -File -ErrorAction SilentlyContinue).Count
$deadletterCount = @(Get-ChildItem -LiteralPath (Join-Path $basePath "queue\deadletter") -Filter "RAWMOCK*" -File -ErrorAction SilentlyContinue).Count
$auditAfter = Count-MatchingAuditEntries -CallIds $callIds
$auditDelta = $auditAfter - $auditBefore

if ($handoffCount -ne 12 -or $processedCount -ne 12 -or $failedCount -ne 0 -or $deadletterCount -ne 0) {
    throw "RAWMOCK batch counts invalid. Handoffs=$handoffCount Processed=$processedCount Failed=$failedCount Deadletter=$deadletterCount"
}

if ($auditDelta -lt 12) {
    Write-Warning "Could not confirm 12 fresh google_push skipped audit events from existing log history."
}

Write-Host "Importing only fresh RAWMOCK handoffs into dashboard."
Invoke-CheckedScript -Path $importDashboard -Arguments @("-Pattern", "RAWMOCK*_handoff.json", "-Force")

Write-Host "Running validation checks."
Invoke-CheckedScript -Path $requestRegression
Invoke-CheckedScript -Path $safeUniversalSmoke
Invoke-CheckedScript -Path $safeIntakeSmoke
Invoke-CheckedScript -Path $columnContract
Invoke-CheckedScript -Path $priorityComparison
Invoke-CheckedScript -Path $googlePushSmoke
Invoke-CheckedScript -Path $refreshSmoke
& $dashboardTests @dashboardPytestArgs
if ($LASTEXITCODE -ne 0) {
    throw "Dashboard pytest failed with exit code $LASTEXITCODE"
}

$dashboardCount = 0
if (Test-Path -LiteralPath $dashboardDb) {
    $pythonFile = Join-Path $env:TEMP ("jefflocal_dashboard_count_" + [guid]::NewGuid().ToString("N") + ".py")
    $pythonCode = @'
import sqlite3
from pathlib import Path

db = Path(r"C:\JeffLocal\dashboard\data\dashboard.sqlite")
conn = sqlite3.connect(db)
try:
    print(conn.execute("SELECT COUNT(*) FROM cases WHERE call_id LIKE 'RAWMOCK-%'").fetchone()[0])
finally:
    conn.close()
'@
    try {
        $pythonCode | Set-Content -LiteralPath $pythonFile -Encoding UTF8
        $dashboardCount = [int](& python $pythonFile)
    }
    finally {
        Remove-Item -LiteralPath $pythonFile -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "Fresh RAWMOCK batch complete."
Write-Host ("  Handoffs: {0}" -f $handoffCount)
Write-Host ("  Processed: {0}" -f $processedCount)
Write-Host ("  Failed: {0}" -f $failedCount)
Write-Host ("  Deadletter: {0}" -f $deadletterCount)
Write-Host ("  Google push skipped audit delta: {0}" -f $auditDelta)
Write-Host ("  Dashboard RAWMOCK cases: {0}" -f $dashboardCount)

<#
.SYNOPSIS
    Deploy a git branch to the JeffLocal production directory.
.DESCRIPTION
    Pulls the latest code from the specified branch, runs smoke tests,
    restarts the dashboard. Must be approved by Saeed before running.
    Deployment window: Sunday 02:00–04:00 only (non-emergency).

.PARAMETER Branch
    Git branch to deploy. Defaults to main.
#>

param([string]$Branch = "main")

$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
function Log($msg) { Write-Host "[$Timestamp] $msg" }

Log "=== DEPLOY START === branch=$Branch"

# 1. Pull latest code
cd C:\JeffLocal
$Result = git pull origin $Branch 2>&1
Log "Git pull: $Result"
if ($LASTEXITCODE -ne 0) { Log "FAIL: git pull failed"; exit 1 }

# 2. Run smoke test
Log "Running smoke test..."
& "$PSScriptRoot\smoke_test.ps1"
if ($LASTEXITCODE -ne 0) { Log "FAIL: smoke test failed — aborting deploy"; exit 1 }

# 3. Restart dashboard
Log "Restarting dashboard..."
& "C:\JeffLocal\scripts\service_control\watchdog.ps1" -Action restart -Service dashboard
Start-Sleep -Seconds 5

# 4. Verify dashboard is up
$Http = try { Invoke-WebRequest "http://localhost:8765/health" -UseBasicParsing -TimeoutSec 10 } catch { $null }
if ($Http -and $Http.StatusCode -eq 200) {
    Log "=== DEPLOY SUCCESS === Dashboard responding on :8765"
    exit 0
} else {
    Log "=== DEPLOY WARNING === Dashboard did not respond after restart — check logs"
    exit 1
}

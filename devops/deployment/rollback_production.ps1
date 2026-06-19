<#
.SYNOPSIS
    Roll back to the previous git commit and restart services.
.DESCRIPTION
    Runs git reset --hard HEAD~1, restores DB from last backup if needed,
    and restarts the dashboard. Requires Saeed approval.

.PARAMETER Steps
    Number of commits to roll back. Default 1.

.PARAMETER RestoreDB
    Also restore the database from yesterday's backup.
#>

param(
    [int]$Steps    = 1,
    [switch]$RestoreDB
)

$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
function Log($msg) { Write-Host "[$Timestamp] $msg" }

Log "=== ROLLBACK START === steps=$Steps$(if ($RestoreDB) {' +RestoreDB'} else {''})"

cd C:\JeffLocal

# Record where we are before rollback
$Before = git rev-parse HEAD
Log "Current commit: $Before"

# Stop dashboard
Log "Stopping dashboard..."
& "C:\JeffLocal\scripts\service_control\watchdog.ps1" -Action stop -Service dashboard 2>$null
Start-Sleep -Seconds 3

# Roll back code
git reset --hard "HEAD~$Steps" 2>&1 | ForEach-Object { Log $_ }
if ($LASTEXITCODE -ne 0) { Log "FAIL: git reset failed"; exit 1 }

$After = git rev-parse HEAD
Log "Rolled back to: $After"

# Optionally restore DB from latest backup
if ($RestoreDB) {
    Log "Restoring database from latest backup..."
    & "$PSScriptRoot\..\backup_recovery\restore_scripts\restore_from_backup.ps1"
}

# Restart dashboard
Log "Restarting dashboard..."
& "C:\JeffLocal\scripts\service_control\watchdog.ps1" -Action start -Service dashboard
Start-Sleep -Seconds 5

$Http = try { Invoke-WebRequest "http://localhost:8765/health" -UseBasicParsing -TimeoutSec 10 } catch { $null }
if ($Http -and $Http.StatusCode -eq 200) {
    Log "=== ROLLBACK SUCCESS === Dashboard on $After"
    exit 0
} else {
    Log "=== ROLLBACK WARNING === Dashboard did not respond — check logs"
    exit 1
}

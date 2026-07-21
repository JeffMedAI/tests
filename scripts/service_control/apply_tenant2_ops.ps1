# apply_tenant2_ops.ps1
# ONE-TIME elevation step for multi-tenancy step 4 (tenant2 placeholder instance).
# Run ONCE in an ADMINISTRATOR PowerShell window:
#
#     powershell -NoProfile -ExecutionPolicy Bypass -File C:\JeffLocal\scripts\service_control\apply_tenant2_ops.ps1
#
# Does two things a non-elevated session cannot:
#   1. Registers all JeffLocal scheduled tasks (idempotent -Force) - this adds the
#      new "JeffLocal - GDPR Weekly Purge (tenant2)" task and re-applies the other
#      4 unchanged.
#   2. Restarts the Service Watchdog task so it reloads watchdog.ps1 from disk and
#      picks up the new Tenant2Dashboard entry (port 8766). The running watchdog
#      still has the OLD in-memory service list until this happens.
#
# Safe to re-run. Health-checks churchtown (8765) before and after so you can see
# the live production instance was not disrupted.

$ErrorActionPreference = "Stop"

# --- Must be elevated ---
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: not elevated. Right-click PowerShell, choose Run as administrator, then re-run this script." -ForegroundColor Red
    exit 1
}

function Test-Churchtown {
    try {
        $r = Invoke-RestMethod -Uri "http://localhost:8765/api/health" -TimeoutSec 5
        return "ok=$($r.ok) case_count=$($r.checks.case_count)"
    } catch {
        return "UNREACHABLE ($($_.Exception.Message))"
    }
}

Write-Host "=== apply_tenant2_ops.ps1 ===" -ForegroundColor Cyan
Write-Host "Churchtown (8765) BEFORE: $(Test-Churchtown)" -ForegroundColor Yellow

# --- Step 1: register all scheduled tasks (idempotent) ---
Write-Host ""
Write-Host "Step 1 of 2: registering scheduled tasks..." -ForegroundColor Cyan
& powershell -NoProfile -ExecutionPolicy Bypass -File "C:\JeffLocal\scripts\register_scheduled_tasks.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: task registration failed (exit $LASTEXITCODE). Stopping before touching the watchdog." -ForegroundColor Red
    exit 1
}

# Confirm the new tenant2 purge task landed
$tenant2Task = Get-ScheduledTask -TaskPath "\JeffLocal\" -TaskName "JeffLocal - GDPR Weekly Purge (tenant2)" -ErrorAction SilentlyContinue
if ($tenant2Task) {
    Write-Host "Confirmed: 'JeffLocal - GDPR Weekly Purge (tenant2)' registered (State: $($tenant2Task.State))." -ForegroundColor Green
} else {
    Write-Host "WARNING: tenant2 purge task not found after registration - check the output above." -ForegroundColor Red
}

# --- Step 2: restart the watchdog so it reloads watchdog.ps1 from disk ---
Write-Host ""
Write-Host "Step 2 of 2: restarting the Service Watchdog to load the new Tenant2Dashboard entry..." -ForegroundColor Cyan

# Stop-ScheduledTask alone is NOT enough here: observed 2026-07-21, an orphaned
# elevated watchdog.ps1 process (started at an earlier boot) kept running OLD
# in-memory code - its check pass never listed Tenant2Dashboard and 8766 never
# came up. Force-kill EVERY lingering watchdog.ps1 process by PID first, so the
# fresh Start-ScheduledTask genuinely reloads watchdog.ps1 from disk.
Stop-ScheduledTask -TaskPath "\JeffLocal\" -TaskName "JeffLocal - Service Watchdog" -ErrorAction SilentlyContinue
$wdProcs = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
    Where-Object { $_.CommandLine -like "*watchdog.ps1*" }
foreach ($p in $wdProcs) {
    Write-Host "  killing lingering watchdog PID $($p.ProcessId) (created $($p.CreationDate))" -ForegroundColor Yellow
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 3
Start-ScheduledTask -TaskPath "\JeffLocal\" -TaskName "JeffLocal - Service Watchdog"
Start-Sleep -Seconds 5
$wd = Get-ScheduledTask -TaskPath "\JeffLocal\" -TaskName "JeffLocal - Service Watchdog"
Write-Host "Watchdog task State: $($wd.State)" -ForegroundColor Green

# Confirm the running watchdog process is genuinely NEW (created just now, not the old orphan)
$newProc = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
    Where-Object { $_.CommandLine -like "*watchdog.ps1*" } | Select-Object -First 1
if ($newProc) {
    Write-Host "Running watchdog PID $($newProc.ProcessId), created $($newProc.CreationDate)." -ForegroundColor Green
} else {
    Write-Host "WARNING: no watchdog process found after start - check manually." -ForegroundColor Red
}

# --- Verify ---
Write-Host ""
Write-Host "Verifying... (watchdog takes up to ~70s to complete its first check pass and start tenant2)" -ForegroundColor Cyan
Write-Host "Churchtown (8765) AFTER:  $(Test-Churchtown)" -ForegroundColor Yellow
Write-Host "Waiting up to 90s for tenant2 (8766) to come up under the watchdog..." -ForegroundColor Cyan
$tenant2Up = $false
for ($i = 0; $i -lt 18; $i++) {
    Start-Sleep -Seconds 5
    try {
        $t = Invoke-RestMethod -Uri "http://localhost:8766/api/health" -TimeoutSec 3
        Write-Host "Tenant2 (8766) UP: ok=$($t.ok) case_count=$($t.checks.case_count)" -ForegroundColor Green
        $tenant2Up = $true
        break
    } catch { }
}
if (-not $tenant2Up) {
    Write-Host "Tenant2 (8766) not up after 90s. Check: Get-Content C:\JeffLocal\logs\service_control\watchdog.log -Tail 20" -ForegroundColor Red
}
Write-Host ""
Write-Host "Done. Churchtown should read case_count=78 (unchanged); tenant2 should read case_count=0." -ForegroundColor Green

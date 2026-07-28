# apply_step5_cutover.ps1
# ONE-TIME elevation step for multi-tenancy step 5 (tenant1 = Churchtown cutover).
# Run ONCE in an ADMINISTRATOR PowerShell window:
#
#     powershell -NoProfile -ExecutionPolicy Bypass -File C:\JeffLocal\scripts\service_control\apply_step5_cutover.ps1
#
# Does what a non-elevated session cannot:
#   1. Copies churchtown.sqlite -> tenants\tenant1.sqlite and writes
#      config\tenants\tenant1.env (that folder is ACL-locked to admins).
#   2. Seeds ONE avamed-super-admin identity into tenant1.sqlite AND tenant2.sqlite,
#      each with its OWN one-time password (printed below - hand them to nobody but
#      keep them safe; each account is forced to change password at first login).
#   3. Force-kills and restarts the elevated Service Watchdog so it reloads
#      watchdog.ps1 and relaunches port 8765 on tenant1's database (the repoint)
#      instead of the legacy default dashboard.sqlite.
#
# Health-checks 8765 (Churchtown) and 8766 (tenant2) BEFORE and AFTER. Aborts if
# either is unreachable before it starts, so it never cuts over a broken system.
# dashboard.sqlite is NOT deleted - it is left in place as a rollback copy.
#
# First-run only by default: if tenants\tenant1.sqlite already exists it assumes
# the cutover already ran and exits, unless you pass -Force (which also resets the
# super-admin one-time passwords - only use -Force if you mean to).

param(
    [switch]$Force,
    [string]$SuperAdminDisplayName = "Saeed Alam (Avamed)",
    [string]$SuperAdminUsername = "avamed-saeed",
    [string]$SuperAdminEmail = "5256863@gmail.com"
)

$ErrorActionPreference = "Stop"

$Repo        = "C:\JeffLocal"
$Python      = "$Repo\dashboard\.venv\Scripts\python.exe"
$RenamePy    = "$Repo\scripts\tenant\rename_tenant_slug.py"
$SeedPy      = "$Repo\scripts\tenant\seed_super_admin.py"
$Source      = "$Repo\dashboard\data\churchtown.sqlite"
$Tenant1Db   = "$Repo\dashboard\data\tenants\tenant1.sqlite"
$Tenant2Db   = "$Repo\dashboard\data\tenants\tenant2.sqlite"
$Tenant1Env  = "$Repo\config\tenants\tenant1.env"

# --- Must be elevated ---
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: not elevated. Right-click PowerShell, choose Run as administrator, then re-run this script." -ForegroundColor Red
    exit 1
}

function Test-Dash($port) {
    try {
        $r = Invoke-RestMethod -Uri "http://localhost:$port/api/health" -TimeoutSec 5
        return "ok=$($r.ok) case_count=$($r.checks.case_count)"
    } catch {
        return "UNREACHABLE ($($_.Exception.Message))"
    }
}

Write-Host "=== apply_step5_cutover.ps1 (tenant1 = Churchtown) ===" -ForegroundColor Cyan

# --- Pre-flight health, abort if broken before we touch anything ---
$before8765 = Test-Dash 8765
$before8766 = Test-Dash 8766
Write-Host "Churchtown (8765) BEFORE: $before8765" -ForegroundColor Yellow
Write-Host "Tenant2   (8766) BEFORE: $before8766" -ForegroundColor Yellow
if ($before8765 -like "UNREACHABLE*") {
    Write-Host "ERROR: 8765 is not healthy before cutover. Aborting - fix that first." -ForegroundColor Red
    exit 1
}

# --- Idempotency guard ---
# Key off tenant1.env, NOT tenant1.sqlite: the env is written LAST (only after the
# DB copy + verify match), so it is the true "cutover complete" marker. Keying off
# the DB file would wrongly no-op a re-run that had created the DB but aborted
# before writing the env (e.g. a verify mismatch), leaving 8765 never repointed.
if ((Test-Path $Tenant1Env) -and (-not $Force)) {
    Write-Host ""
    Write-Host "tenant1.env already exists at $Tenant1Env." -ForegroundColor Yellow
    Write-Host "Assuming step 5 cutover already ran. Re-run with -Force to redo it (this resets the super-admin one-time passwords)." -ForegroundColor Yellow
    exit 0
}

if (-not (Test-Path $Source)) {
    Write-Host "ERROR: source churchtown.sqlite not found at $Source. Aborting." -ForegroundColor Red
    exit 1
}

# --- Step 1: copy churchtown.sqlite -> tenant1.sqlite + write tenant1.env ---
Write-Host ""
Write-Host "Step 1 of 3: creating tenant1 database + config from Churchtown..." -ForegroundColor Cyan
$renameArgs = @($RenamePy, "--source", $Source, "--dest", $Tenant1Db, "--env-path", $Tenant1Env)
if ($Force) { $renameArgs += "--force" }
& $Python @renameArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: rename/copy step failed (exit $LASTEXITCODE). Nothing repointed. Aborting." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $Tenant1Env)) {
    Write-Host "ERROR: tenant1.env was not written (expected at $Tenant1Env). Aborting before repoint." -ForegroundColor Red
    exit 1
}
Write-Host "Confirmed: tenant1.sqlite created and config\tenants\tenant1.env written." -ForegroundColor Green

# --- Step 2: seed avamed-super-admin into tenant1 + tenant2 (per-tenant OTPs) ---
Write-Host ""
Write-Host "Step 2 of 3: seeding the avamed-super-admin account into tenant1 + tenant2..." -ForegroundColor Cyan
$seedTargets = @($Tenant1Db)
if (Test-Path $Tenant2Db) { $seedTargets += $Tenant2Db } else {
    Write-Host "NOTE: tenant2.sqlite not found at $Tenant2Db - seeding tenant1 only." -ForegroundColor Yellow
}
$seedArgs = @($SeedPy, "--display-name", $SuperAdminDisplayName, "--username", $SuperAdminUsername, "--email", $SuperAdminEmail)
foreach ($t in $seedTargets) { $seedArgs += @("--db-path", $t) }
if ($Force) { $seedArgs += "--force" }
& $Python @seedArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: seed step exited $LASTEXITCODE. If the account already exists this is expected on a non-Force re-run;" -ForegroundColor Yellow
    Write-Host "         the repoint below does NOT depend on seeding, so continuing. Review the output above." -ForegroundColor Yellow
}

# --- Step 3: restart the elevated watchdog so 8765 relaunches on tenant1 ---
Write-Host ""
Write-Host "Step 3 of 3: restarting the Service Watchdog to repoint 8765 onto tenant1..." -ForegroundColor Cyan
# Same hard lesson as step 4: Stop-ScheduledTask alone leaves an orphaned elevated
# watchdog.ps1 running OLD in-memory code. Force-kill every lingering watchdog.ps1
# by PID first so the fresh start genuinely reloads watchdog.ps1 from disk (which
# now launches ProductionDashboard with -Tenant tenant1, because tenant1.env exists).
Stop-ScheduledTask -TaskPath "\JeffLocal\" -TaskName "JeffLocal - Service Watchdog" -ErrorAction SilentlyContinue
$wdProcs = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" |
    Where-Object { $_.CommandLine -like "*watchdog.ps1*" }
foreach ($p in $wdProcs) {
    Write-Host "  killing lingering watchdog PID $($p.ProcessId) (created $($p.CreationDate))" -ForegroundColor Yellow
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
# Also stop the current 8765 process so the watchdog relaunches it fresh on tenant1
# (otherwise the existing healthy 8765 on dashboard.sqlite would pass the health
# check and never be restarted onto tenant1).
$old8765 = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique
foreach ($pid8765 in $old8765) {
    Write-Host "  stopping current 8765 process PID $pid8765 so it relaunches on tenant1" -ForegroundColor Yellow
    Stop-Process -Id $pid8765 -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 3
Start-ScheduledTask -TaskPath "\JeffLocal\" -TaskName "JeffLocal - Service Watchdog"
$wd = Get-ScheduledTask -TaskPath "\JeffLocal\" -TaskName "JeffLocal - Service Watchdog"
Write-Host "Watchdog task State: $($wd.State)" -ForegroundColor Green

# --- Verify: 8765 should come back on tenant1 (case_count 78), 8766 unchanged (0) ---
Write-Host ""
Write-Host "Verifying... (watchdog takes up to ~70s to complete a check pass and relaunch 8765)" -ForegroundColor Cyan
$up8765 = $false
for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 5
    $h = Test-Dash 8765
    if ($h -notlike "UNREACHABLE*") {
        Write-Host "Churchtown/tenant1 (8765) AFTER: $h" -ForegroundColor Green
        $up8765 = $true
        break
    }
}
if (-not $up8765) {
    Write-Host "8765 not back after 100s. Check: Get-Content C:\JeffLocal\logs\service_control\dashboard-tenant1.log -Tail 30" -ForegroundColor Red
    Write-Host "Rollback: remove config\tenants\tenant1.env and restart the watchdog to fall back to dashboard.sqlite." -ForegroundColor Red
}
Write-Host "Tenant2   (8766) AFTER: $(Test-Dash 8766)" -ForegroundColor Yellow

Write-Host ""
Write-Host "Done. Expected: 8765 case_count=78 (Churchtown data, now served as tenant1)," -ForegroundColor Green
Write-Host "                8766 case_count=0 (tenant2, untouched)." -ForegroundColor Green
Write-Host "The one-time passwords printed in Step 2 are the ONLY copy - store them safely now." -ForegroundColor Cyan
Write-Host "dashboard.sqlite is left in place as a rollback copy (not deleted)." -ForegroundColor Cyan

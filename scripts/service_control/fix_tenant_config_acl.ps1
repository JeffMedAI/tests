# fix_tenant_config_acl.ps1
# Run ONCE in an ADMINISTRATOR PowerShell:
#     powershell -NoProfile -ExecutionPolicy Bypass -File C:\JeffLocal\scripts\service_control\fix_tenant_config_acl.ps1
#
# WHY: the tenant launcher (_load_tenant_config.ps1) refuses to start a tenant
# while its config dir grants Write/Modify to Everyone / Users / Authenticated
# Users / INTERACTIVE. C:\JeffLocal\config\tenants currently grants
# "Authenticated Users: Modify" - INHERITED from the C:\ drive root, which is
# why the 2026-07-20 `icacls /remove:g` fix (explicit-only) did not clear it.
# So tenant2 (8766) fails to launch with:
#   [TENANT] REFUSING TO START: C:\JeffLocal\config\tenants is writable by: NT AUTHORITY\Authenticated Users
#
# SCOPE - config\tenants ONLY, deliberately. That folder is READ-ONLY for the
# dashboard (it only reads the tenant .env files, via BUILTIN\Users:Read), so
# removing the Authenticated-Users WRITE grant here is safe and breaks nothing.
# It does NOT touch C:\JeffLocal or dashboard\data\ or logs\, where the app DOES
# rely on write access - fixing those is a separate, more careful task (grant the
# service account explicit write first). See PROJECT_MEMORY open security items.
#
# Safe to re-run.

$ErrorActionPreference = "Stop"
$dir = "C:\JeffLocal\config\tenants"

# --- must be elevated (changing an ACL needs WRITE_DAC / admin) ---
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: not elevated. Run this in an admin PowerShell window." -ForegroundColor Red
    exit 1
}

Write-Host "=== fix_tenant_config_acl.ps1 ===" -ForegroundColor Cyan
Write-Host "BEFORE:" -ForegroundColor Yellow
icacls $dir

# --- break inheritance (copy current inherited ACEs to explicit), then remove
#     the untrusted write-granting principals. /T recurses to the .env files,
#     /C continues past a locked file. BUILTIN\Users:Read is left intact so the
#     dashboard can still READ tenant .env files. ---
Write-Host "`nApplying fix (config\tenants only)..." -ForegroundColor Cyan
icacls $dir /inheritance:d | Out-Null
icacls $dir /remove:g "Authenticated Users" /T /C | Out-Null
icacls $dir /remove:g "*S-1-5-21-3757111369-3529092462-2350175298-2510526684" /T /C | Out-Null

Write-Host "`nAFTER:" -ForegroundColor Yellow
icacls $dir

# --- re-check the launcher's EXACT condition (mirror of _load_tenant_config.ps1) ---
$acl = Get-Acl -LiteralPath $dir
$writers = $acl.Access | Where-Object {
    $_.AccessControlType -eq 'Allow' -and
    $_.IdentityReference -match 'Everyone|BUILTIN\\Users|Authenticated Users|INTERACTIVE' -and
    $_.FileSystemRights  -match 'Write|Modify|FullControl|CreateFiles|AppendData'
}
if ($writers) {
    $who = (($writers.IdentityReference | ForEach-Object { $_.ToString() }) | Select-Object -Unique) -join ', '
    Write-Host "`nSTILL WRITABLE by: $who - tenant will still refuse to start. Stop here and investigate." -ForegroundColor Red
    exit 1
}
Write-Host "`nOK - config\tenants no longer writable by untrusted accounts. Launcher ACL check will pass." -ForegroundColor Green

# --- bring tenant2 up now (watchdog hit its restart cap for the hour, so nudge
#     it manually; once it is UP the watchdog leaves it running). ---
Write-Host "`nStarting tenant2 (8766) in the background..." -ForegroundColor Cyan
Start-Process -FilePath "powershell.exe" `
    -ArgumentList "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File `"C:\JeffLocal\scripts\service_control\_launch_dashboard.ps1`" -Tenant tenant2" `
    -WindowStyle Hidden

$up = $false
for ($i = 0; $i -lt 18; $i++) {
    Start-Sleep -Seconds 5
    try {
        $t = Invoke-RestMethod -Uri "http://localhost:8766/api/health" -TimeoutSec 3
        Write-Host "Tenant2 (8766) UP: ok=$($t.ok) case_count=$($t.checks.case_count)" -ForegroundColor Green
        $up = $true
        break
    } catch { }
}
if (-not $up) {
    Write-Host "Tenant2 still not up after 90s. Check C:\JeffLocal\logs\service_control\dashboard-tenant2.log" -ForegroundColor Red
    exit 1
}

# --- confirm churchtown untouched ---
try {
    $c = Invoke-RestMethod -Uri "http://localhost:8765/api/health" -TimeoutSec 5
    Write-Host "Churchtown (8765): ok=$($c.ok) case_count=$($c.checks.case_count) (should be 78)" -ForegroundColor Green
} catch {
    Write-Host "Churchtown (8765) check failed: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host "`nDone. Tenant2 is up on 8766 and the watchdog will keep it running." -ForegroundColor Green

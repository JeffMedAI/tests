# Regression test for watchdog.ps1's $Services array — specifically the
# Tenant2Dashboard entry added for multi-tenancy step 4.
#
#     powershell -NoProfile -ExecutionPolicy Bypass -File scripts\service_control\tests\test_watchdog_services.ps1
#
# STATIC ONLY, by design. watchdog.ps1 has no "define but don't run" mode —
# merely dot-sourcing or invoking it (even with -Once) executes a real
# Invoke-CheckPass against real ports and can trigger a real Restart
# scriptblock and a real WhatsApp alert. This test never dot-sources or
# invokes watchdog.ps1: it only parses the file into an AST (which does not
# execute anything — scriptblocks are just AST nodes until called) and reads
# it as plain text, so it is always safe to run, including against the real
# production copy.
#
# Exits 0 if all assertions pass, 1 if any fail.

$ErrorActionPreference = 'Stop'
$watchdogPath = Join-Path $PSScriptRoot "..\watchdog.ps1"
$content = Get-Content -Raw $watchdogPath

$failures = @()
function Assert-True([string]$name, [bool]$condition) {
    if ($condition) {
        Write-Host "PASS: $name"
    } else {
        $script:failures += $name
    }
}

Write-Host "=== test_watchdog_services.ps1 ==="

# --- Parses cleanly (catches any syntax error introduced by hand-editing) ---
$errors = $null
$tokens = $null
[System.Management.Automation.Language.Parser]::ParseInput($content, [ref]$tokens, [ref]$errors) | Out-Null
Assert-True "watchdog.ps1 parses with zero syntax errors" ($errors.Count -eq 0)

# --- Both dashboard entries exist ---
Assert-True "ProductionDashboard entry still present" ($content -match 'Name\s*=\s*"ProductionDashboard"')
Assert-True "Tenant2Dashboard entry present" ($content -match 'Name\s*=\s*"Tenant2Dashboard"')

# --- Distinct, non-colliding ports ---
Assert-True "ProductionDashboard checks port 8765" ($content -match 'Test-Port 8765')
Assert-True "Tenant2Dashboard checks port 8766" ($content -match 'Test-Port 8766')
Assert-True "ProductionDashboard health-checks localhost:8765" ($content -match 'http://localhost:8765/api/health')
Assert-True "Tenant2Dashboard health-checks localhost:8766" ($content -match 'http://localhost:8766/api/health')

# --- Tenant2Dashboard's restart passes -Tenant tenant2 (else it would launch
#     on 8765 and collide with ProductionDashboard) ---
Assert-True "Tenant2Dashboard restart passes -Tenant tenant2" ($content -match '-File\s*`"\$launch`"\s*-Tenant\s*tenant2')

# --- ProductionDashboard's own restart must NOT have been changed to pass
#     -Tenant (that would break today's default instance) ---
$prodBlockMatch = [regex]::Match($content, 'Name\s*=\s*"ProductionDashboard".*?(?=\[PSCustomObject\]@\{)', 'Singleline')
Assert-True "ProductionDashboard block found for isolation check" $prodBlockMatch.Success
if ($prodBlockMatch.Success) {
    Assert-True "ProductionDashboard restart does NOT pass -Tenant" ($prodBlockMatch.Value -notmatch '-Tenant')
    Assert-True "ProductionDashboard restart still calls Start-HiddenPS unmodified" ($prodBlockMatch.Value -match 'Start-HiddenPS \$launch')
}

# --- Sanity: the two entries are not accidentally identical (copy-paste that
#     forgot to change the port/name) ---
$tenant2BlockMatch = [regex]::Match($content, 'Name\s*=\s*"Tenant2Dashboard".*?(?=\[PSCustomObject\]@\{|\z)', 'Singleline')
Assert-True "Tenant2Dashboard block found" $tenant2BlockMatch.Success
if ($tenant2BlockMatch.Success -and $prodBlockMatch.Success) {
    Assert-True "Tenant2Dashboard block is not byte-identical to ProductionDashboard's" ($tenant2BlockMatch.Value -ne $prodBlockMatch.Value)
}

Write-Host "===================================="
if ($failures.Count -gt 0) {
    Write-Host "FAILED ($($failures.Count)):"
    $failures | ForEach-Object { Write-Host "  - $_" }
    exit 1
} else {
    Write-Host "ALL PASSED"
    exit 0
}

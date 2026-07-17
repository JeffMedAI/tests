# Regression test for _load_tenant_config.ps1. No Pester in this repo yet —
# this is a plain assert-and-exit-code script, run directly:
#
#     powershell -NoProfile -ExecutionPolicy Bypass -File scripts\service_control\tests\test_load_tenant_config.ps1
#
# Exits 0 if all assertions pass, 1 if any fail. Every scenario here was
# manually verified once during development (2026-07-17) before this file
# existed; this makes that verification repeatable instead of throwaway.

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot "..\_load_tenant_config.ps1")

$testRoot = Join-Path $env:TEMP "jefflocal_tenant_config_test_$(Get-Random)"
New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
$logFile = Join-Path $testRoot "test.log"

$failures = @()
function Assert-Throws([string]$name, [scriptblock]$block) {
    try {
        & $block
        $script:failures += "$name : expected a throw, got none"
    } catch {
        Write-Host "PASS: $name (threw: $($_.Exception.Message))"
    }
}
function Assert-NoThrow([string]$name, [scriptblock]$block) {
    try {
        & $block
        Write-Host "PASS: $name"
    } catch {
        $script:failures += "$name : unexpected throw: $($_.Exception.Message))"
    }
}
function Assert-Equal([string]$name, $expected, $actual) {
    if ($expected -eq $actual) {
        Write-Host "PASS: $name"
    } else {
        $script:failures += "$name : expected '$expected', got '$actual'"
    }
}

# --- Fixture: a config root only this user can write to (the ACL check must pass) ---
$goodRoot = Join-Path $testRoot "good_config"
New-Item -ItemType Directory -Path $goodRoot -Force | Out-Null
icacls $goodRoot /inheritance:r /grant:r "$($env:USERNAME):(OI)(CI)F" "SYSTEM:(OI)(CI)F" "Administrators:(OI)(CI)F" | Out-Null

@"
JEFFLOCAL_TENANT_NAME=Test Fixture
JEFFLOCAL_DB_PATH=C:\fake\path\fixture.sqlite
JEFFLOCAL_PORT=9999
"@ | Set-Content (Join-Path $goodRoot "valid-tenant.env")

# Config with an unrelated key mixed in, to prove the allowlist still applies here.
@"
JEFFLOCAL_TENANT_NAME=Partial
JEFFLOCAL_DB_PATH=C:\fake\path\partial.sqlite
JEFFLOCAL_PORT=9998
PYTHONPATH=/evil
"@ | Set-Content (Join-Path $goodRoot "with-bogus-key.env")

# Config missing JEFFLOCAL_PORT — must be refused as incomplete.
@"
JEFFLOCAL_TENANT_NAME=Incomplete
JEFFLOCAL_DB_PATH=C:\fake\path\incomplete.sqlite
"@ | Set-Content (Join-Path $goodRoot "incomplete-tenant.env")

# --- Fixture: a config root writable by Authenticated Users (the ACL check must refuse) ---
$badRoot = Join-Path $testRoot "writable_config"
New-Item -ItemType Directory -Path $badRoot -Force | Out-Null
icacls $badRoot /grant "Authenticated Users:(OI)(CI)M" | Out-Null
@"
JEFFLOCAL_TENANT_NAME=Should Never Load
JEFFLOCAL_DB_PATH=C:\fake\path\x.sqlite
JEFFLOCAL_PORT=9997
"@ | Set-Content (Join-Path $badRoot "valid-tenant.env")

Write-Host "=== test_load_tenant_config.ps1 ==="

Assert-NoThrow "valid tenant loads without throwing" {
    Import-JeffTenantConfig -Tenant "valid-tenant" -ConfigRoot $goodRoot -LogFile $logFile
}
Assert-Equal "valid tenant sets JEFFLOCAL_DB_PATH" "C:\fake\path\fixture.sqlite" $env:JEFFLOCAL_DB_PATH
Assert-Equal "valid tenant sets JEFFLOCAL_PORT" "9999" $env:JEFFLOCAL_PORT
Assert-Equal "valid tenant sets JEFFLOCAL_TENANT_NAME" "Test Fixture" $env:JEFFLOCAL_TENANT_NAME

Remove-Item Env:JEFFLOCAL_DB_PATH, Env:JEFFLOCAL_PORT, Env:JEFFLOCAL_TENANT_NAME, Env:PYTHONPATH -ErrorAction SilentlyContinue

Assert-NoThrow "tenant with a bogus extra key still loads its allowlisted keys" {
    Import-JeffTenantConfig -Tenant "with-bogus-key" -ConfigRoot $goodRoot -LogFile $logFile
}
Assert-Equal "bogus-key tenant still sets JEFFLOCAL_PORT" "9998" $env:JEFFLOCAL_PORT
Assert-Equal "PYTHONPATH is never set from a tenant file (allowlist holds)" $null $env:PYTHONPATH

Remove-Item Env:JEFFLOCAL_DB_PATH, Env:JEFFLOCAL_PORT, Env:JEFFLOCAL_TENANT_NAME -ErrorAction SilentlyContinue

Assert-Throws "unknown tenant name throws" {
    Import-JeffTenantConfig -Tenant "does-not-exist" -ConfigRoot $goodRoot -LogFile $logFile
}

Assert-Throws "path traversal in tenant name throws" {
    Import-JeffTenantConfig -Tenant "..\..\secrets" -ConfigRoot $goodRoot -LogFile $logFile
}

Assert-Throws "incomplete tenant config (missing PORT) throws" {
    Import-JeffTenantConfig -Tenant "incomplete-tenant" -ConfigRoot $goodRoot -LogFile $logFile
}

Assert-Throws "nonexistent config root throws" {
    Import-JeffTenantConfig -Tenant "valid-tenant" -ConfigRoot (Join-Path $testRoot "no_such_dir") -LogFile $logFile
}

Assert-Throws "config root writable by Authenticated Users is refused" {
    Import-JeffTenantConfig -Tenant "valid-tenant" -ConfigRoot $badRoot -LogFile $logFile
}

# Cleanup
Remove-Item Env:JEFFLOCAL_DB_PATH, Env:JEFFLOCAL_PORT, Env:JEFFLOCAL_TENANT_NAME -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $testRoot -ErrorAction SilentlyContinue

Write-Host "===================================="
if ($failures.Count -gt 0) {
    Write-Host "FAILED ($($failures.Count)):"
    $failures | ForEach-Object { Write-Host "  - $_" }
    exit 1
} else {
    Write-Host "ALL PASSED"
    exit 0
}

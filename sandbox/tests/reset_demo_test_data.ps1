# reset_demo_test_data.ps1
# Resets sandbox test data. Requires explicit confirmation flag.
# Usage: .\reset_demo_test_data.ps1 -ConfirmReset

param(
    [switch]$ConfirmReset
)

if (-not $ConfirmReset) {
    Write-Host "ERROR: You must pass -ConfirmReset to run this script." -ForegroundColor Red
    Write-Host "Usage: .\reset_demo_test_data.ps1 -ConfirmReset"
    exit 1
}

$SandboxRoot = Split-Path -Parent $PSScriptRoot
$ArchiveDir  = Join-Path $SandboxRoot "backup\test_data_archives"
$HandoffDir  = Join-Path $SandboxRoot "outputs\handoff_json"
$Timestamp   = Get-Date -Format "yyyyMMdd_HHmmss"
$ArchiveDest = Join-Path $ArchiveDir "reset_$Timestamp"

Write-Host "Creating archive at: $ArchiveDest"
New-Item -ItemType Directory -Path $ArchiveDest -Force | Out-Null

# Archive current handoff files before reset
if (Test-Path $HandoffDir) {
    Get-ChildItem -Path $HandoffDir -Filter "*_handoff.json" | ForEach-Object {
        Copy-Item $_.FullName -Destination $ArchiveDest
    }
    Remove-Item -Path (Join-Path $HandoffDir "*_handoff.json") -Force
    Write-Host "Cleared handoff_json folder."
}

Write-Host "Reset complete. Archive saved to: $ArchiveDest"

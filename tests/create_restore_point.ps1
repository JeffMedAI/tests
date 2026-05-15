param(
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$basePath = "C:\JeffLocal"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$restoreRoot = Join-Path $basePath "backup\restore_points\restore_point_${timestamp}_dashboard_working_state"

function Ensure-Directory {
    param([string]$Path)
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Get-FileStats {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return [ordered]@{ file_count = 0; total_bytes = 0 }
    }
    $files = @(Get-ChildItem -LiteralPath $Path -Recurse -File -ErrorAction SilentlyContinue)
    $size = ($files | Measure-Object -Property Length -Sum).Sum
    if ($null -eq $size) {
        $size = 0
    }
    return [ordered]@{
        file_count = $files.Count
        total_bytes = [int64]$size
    }
}

function Copy-Tree {
    param(
        [string]$Source,
        [string]$Destination,
        [string[]]$ExcludeDirs = @()
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        return $false
    }

    Ensure-Directory -Path $Destination
    $args = @($Source, $Destination, "/E", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/R:1", "/W:1")
    foreach ($exclude in $ExcludeDirs) {
        $args += "/XD"
        $args += $exclude
    }
    & robocopy @args | Out-Null
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed for $Source with code $LASTEXITCODE"
    }
    return $true
}

function Copy-MatchingFiles {
    param(
        [string]$SourceDir,
        [string]$DestinationDir,
        [string]$Pattern
    )

    if (-not (Test-Path -LiteralPath $SourceDir)) {
        return 0
    }

    Ensure-Directory -Path $DestinationDir
    $files = @(Get-ChildItem -LiteralPath $SourceDir -File -Filter $Pattern -ErrorAction SilentlyContinue)
    foreach ($file in $files) {
        if ($file.Name -eq "local_secrets.json") {
            continue
        }
        Copy-Item -LiteralPath $file.FullName -Destination (Join-Path $DestinationDir $file.Name) -Force
    }
    return $files.Count
}

function Backup-Sqlite {
    param(
        [string]$Source,
        [string]$Destination
    )

    if (-not (Test-Path -LiteralPath $Source)) {
        return $false
    }

    Ensure-Directory -Path (Split-Path -Path $Destination -Parent)
    try {
        Copy-Item -LiteralPath $Source -Destination $Destination -Force
        return $true
    }
    catch {
        $pythonFile = Join-Path $env:TEMP ("jefflocal_sqlite_backup_" + [guid]::NewGuid().ToString("N") + ".py")
        $pythonCode = @"
import sqlite3
from pathlib import Path

src = Path(r"$Source")
dst = Path(r"$Destination")
dst.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(src) as source, sqlite3.connect(dst) as target:
    source.backup(target)
"@
        try {
            $pythonCode | Set-Content -LiteralPath $pythonFile -Encoding UTF8
            python $pythonFile
            if ($LASTEXITCODE -ne 0) {
                throw "sqlite backup failed with exit code $LASTEXITCODE"
            }
        }
        finally {
            Remove-Item -LiteralPath $pythonFile -Force -ErrorAction SilentlyContinue
        }
        return $true
    }
}

function Write-TextFile {
    param(
        [string]$Path,
        [string]$Content
    )

    Ensure-Directory -Path (Split-Path -Path $Path -Parent)
    Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
}

if (-not $Force) {
    $prompt = Read-Host "This will create a timestamped restore point from the current working state. Type YES to continue"
    if ($prompt -ne "YES") {
        Write-Host "Restore point creation cancelled."
        exit 2
    }
}

Ensure-Directory -Path $restoreRoot

Copy-Tree -Source (Join-Path $basePath "app") -Destination (Join-Path $restoreRoot "app") | Out-Null
Copy-Tree -Source (Join-Path $basePath "config") -Destination (Join-Path $restoreRoot "config") -ExcludeDirs @(".pytest_cache", "__pycache__", "backup") | Out-Null
Copy-Tree -Source (Join-Path $basePath "dashboard") -Destination (Join-Path $restoreRoot "dashboard") -ExcludeDirs @(".venv", "data", ".pytest_cache", "__pycache__", "backup") | Out-Null
Copy-Tree -Source (Join-Path $basePath "tests") -Destination (Join-Path $restoreRoot "tests") -ExcludeDirs @(".pytest_cache", "__pycache__") | Out-Null

if (Test-Path -LiteralPath (Join-Path $basePath "docs")) {
    Copy-Tree -Source (Join-Path $basePath "docs") -Destination (Join-Path $restoreRoot "docs") -ExcludeDirs @(".pytest_cache", "__pycache__", "backup") | Out-Null
}

if (Test-Path -LiteralPath (Join-Path $basePath "data\patient_lookup")) {
    Copy-Tree -Source (Join-Path $basePath "data\patient_lookup") -Destination (Join-Path $restoreRoot "data\patient_lookup") -ExcludeDirs @(".pytest_cache", "__pycache__", "backup") | Out-Null
}

$handoffCount = Copy-MatchingFiles -SourceDir (Join-Path $basePath "outputs\handoff_json") -DestinationDir (Join-Path $restoreRoot "outputs\handoff_json") -Pattern "RAWMOCK*_handoff.json"
$processedCount = Copy-MatchingFiles -SourceDir (Join-Path $basePath "queue\processed") -DestinationDir (Join-Path $restoreRoot "queue\processed") -Pattern "RAWMOCK*.json"
$auditCount1 = Copy-MatchingFiles -SourceDir (Join-Path $basePath "logs\audits") -DestinationDir (Join-Path $restoreRoot "logs\audits") -Pattern "audit_*.jsonl"
$auditCount2 = Copy-MatchingFiles -SourceDir (Join-Path $basePath "logs\audits") -DestinationDir (Join-Path $restoreRoot "logs\audits") -Pattern "dashboard_audit_*.jsonl"
$auditCount = $auditCount1 + $auditCount2

$runtimeIncluded = $false
$runtimeSource = Join-Path $basePath "dashboard\data\dashboard.sqlite"
$runtimeDest = Join-Path $restoreRoot "runtime_state_optional\dashboard.sqlite"
if (Test-Path -LiteralPath $runtimeSource) {
    $runtimeIncluded = Backup-Sqlite -Source $runtimeSource -Destination $runtimeDest
}

Get-ChildItem -LiteralPath $restoreRoot -Recurse -File -Filter "local_secrets.json" -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -LiteralPath $restoreRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -LiteralPath $restoreRoot -Recurse -Directory -Filter ".pytest_cache" -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

$includedSummary = [ordered]@{
    app = Get-FileStats -Path (Join-Path $restoreRoot "app")
    config = Get-FileStats -Path (Join-Path $restoreRoot "config")
    dashboard = Get-FileStats -Path (Join-Path $restoreRoot "dashboard")
    tests = Get-FileStats -Path (Join-Path $restoreRoot "tests")
    docs = Get-FileStats -Path (Join-Path $restoreRoot "docs")
    data_patient_lookup = Get-FileStats -Path (Join-Path $restoreRoot "data\patient_lookup")
    rawmock_handoffs = [ordered]@{ file_count = $handoffCount }
    rawmock_processed = [ordered]@{ file_count = $processedCount }
    recent_audit_logs = [ordered]@{ file_count = $auditCount }
    runtime_state_optional = [ordered]@{
        included = $runtimeIncluded
        file_count = if ($runtimeIncluded) { 1 } else { 0 }
    }
}

$manifest = [ordered]@{
    restore_point_name = Split-Path -Path $restoreRoot -Leaf
    created_at = (Get-Date).ToString("o")
    source_root = $basePath
    git_status = "not a git repository"
    files_included_summary = $includedSummary
    files_excluded_summary = @(
        "dashboard\.venv",
        "__pycache__",
        ".pytest_cache",
        "backup folders",
        "local_secrets.json",
        "credential/token files",
        "non-RAWMOCK artifacts from outputs/queue",
        "mixed audit logs not specifically copied"
    )
    verified_state_summary = @(
        "Fresh RAWMOCK batch passed",
        "Dashboard reset/import passed",
        "Dashboard cases: 12",
        "Handoff JSONs: 12",
        "Processed files: 12",
        "Failed: 0",
        "Deadletter: 0",
        "Google push skipped for test run",
        "Priority comparison passed",
        "Dashboard tests: 28 passed",
        "Dashboard UX polish completed",
        "Copy/Copied buttons working",
        "Date filters and request type bars added",
        "Fresh test reset runner created"
    )
    test_commands_last_known_good = @(
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\run_fresh_rawmock_end_to_end_batch.ps1 -Force",
        ".\dashboard\.venv\Scripts\python.exe -m pytest .\dashboard\tests -q",
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\dashboard\run_dashboard.ps1"
    )
    restore_steps = @(
        "Review RESTORE_INSTRUCTIONS.md first.",
        "Run restore_from_this_point.ps1 with -ConfirmRestore after stopping the dashboard.",
        "The script will make a pre-restore backup before copying files back.",
        "Restore the optional runtime_state_optional/dashboard.sqlite only if you want the exact imported dashboard state.",
        "Restart the dashboard and re-run the fresh RAWMOCK batch if you need a regenerated test cycle."
    )
    known_risks = @(
        "The optional dashboard.sqlite may be locked if the dashboard is running.",
        "Restore scripts are test-only and should not be used against live external systems.",
        "Google Sheet push remains available in production paths and is only disabled at test runtime."
    )
}

$manifestPath = Join-Path $restoreRoot "RESTORE_MANIFEST.json"
($manifest | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $manifestPath -Encoding UTF8

$instructions = @"
# JeffLocal Restore Point

Restore point: $($manifest.restore_point_name)
Created at: $($manifest.created_at)

This backup contains the current verified JeffLocal working state, including:
- app
- config
- dashboard
- tests
- docs (if present)
- data\patient_lookup (if present)
- RAWMOCK handoff JSON files
- RAWMOCK processed queue JSON files
- recent audit logs

Optional runtime state:
- runtime_state_optional\dashboard.sqlite

Use RESTORE_MANIFEST.json for the exact inventory and known risks.

Manual restore outline:
1. Stop the dashboard if it is running.
2. Run restore_from_this_point.ps1 with -ConfirmRestore.
3. Restart the dashboard.
4. If you want to reproduce the verified test state, run the fresh RAWMOCK batch command listed in the manifest.

To keep tests local:
- Use `-DisableGooglePush` on the RAWMOCK batch runner.
- Do not enable any cloud bridge or external sender helper.

Recommended post-restore commands:
- powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\run_fresh_rawmock_end_to_end_batch.ps1 -Force
- .\dashboard\.venv\Scripts\python.exe -m pytest .\dashboard\tests -q
- powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\dashboard\run_dashboard.ps1
"@
Write-TextFile -Path (Join-Path $restoreRoot "RESTORE_INSTRUCTIONS.md") -Content $instructions
Write-TextFile -Path (Join-Path $restoreRoot "README.md") -Content @"
JeffLocal restore point.

See RESTORE_INSTRUCTIONS.md for restore steps and RESTORE_MANIFEST.json for the file inventory.
"@

$restoreScript = @"
param(
    [switch]`$ConfirmRestore
)

Set-StrictMode -Version Latest
`$ErrorActionPreference = "Stop"

if (-not `$ConfirmRestore) {
    throw "Pass -ConfirmRestore to restore from this point."
}

`$basePath = "C:\JeffLocal"
`$restoreRoot = "$restoreRoot"
`$preBackupRoot = Join-Path `$restoreRoot ("pre_restore_backup_" + (Get-Date -Format "yyyyMMdd_HHmmss"))

function Ensure-Directory {
    param([string]`$Path)
    New-Item -ItemType Directory -Force -Path `$Path | Out-Null
}

function Backup-Tree {
    param([string]`$Source, [string]`$Destination, [string[]]`$ExcludeDirs = @())
    if (-not (Test-Path -LiteralPath `$Source)) { return }
    Ensure-Directory -Path `$Destination
    `$args = @(`$Source, `$Destination, "/E", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/R:1", "/W:1")
    foreach (`$exclude in `$ExcludeDirs) { `$args += "/XD"; `$args += `$exclude }
    & robocopy @args | Out-Null
    if (`$LASTEXITCODE -ge 8) { throw "Pre-restore backup failed for `$Source with code `$LASTEXITCODE" }
}

function Restore-Tree {
    param([string]`$Source, [string]`$Destination, [string[]]`$ExcludeDirs = @())
    if (-not (Test-Path -LiteralPath `$Source)) { return }
    Ensure-Directory -Path `$Destination
    `$args = @(`$Source, `$Destination, "/E", "/NFL", "/NDL", "/NJH", "/NJS", "/NP", "/R:1", "/W:1")
    foreach (`$exclude in `$ExcludeDirs) { `$args += "/XD"; `$args += `$exclude }
    & robocopy @args | Out-Null
    if (`$LASTEXITCODE -ge 8) { throw "Restore failed for `$Source with code `$LASTEXITCODE" }
}

Write-Host "This restore will copy back:"
Write-Host "  app"
Write-Host "  config (without secrets)"
Write-Host "  dashboard (without .venv or dashboard data directory)"
Write-Host "  tests"
Write-Host "  docs (if present)"
Write-Host "  data\patient_lookup (if present)"
Write-Host "  optional runtime_state_optional\dashboard.sqlite if included"

Write-Host "Creating pre-restore backup at `$preBackupRoot"
Backup-Tree -Source (Join-Path `$basePath "app") -Destination (Join-Path `$preBackupRoot "app") -ExcludeDirs @(".pytest_cache", "__pycache__", "backup")
Backup-Tree -Source (Join-Path `$basePath "config") -Destination (Join-Path `$preBackupRoot "config") -ExcludeDirs @(".pytest_cache", "__pycache__", "backup")
Backup-Tree -Source (Join-Path `$basePath "dashboard") -Destination (Join-Path `$preBackupRoot "dashboard") -ExcludeDirs @(".venv", "data", ".pytest_cache", "__pycache__", "backup")
Backup-Tree -Source (Join-Path `$basePath "tests") -Destination (Join-Path `$preBackupRoot "tests") -ExcludeDirs @(".pytest_cache", "__pycache__")
if (Test-Path -LiteralPath (Join-Path `$basePath "docs")) {
    Backup-Tree -Source (Join-Path `$basePath "docs") -Destination (Join-Path `$preBackupRoot "docs") -ExcludeDirs @(".pytest_cache", "__pycache__", "backup")
}
if (Test-Path -LiteralPath (Join-Path `$basePath "data\patient_lookup")) {
    Backup-Tree -Source (Join-Path `$basePath "data\patient_lookup") -Destination (Join-Path `$preBackupRoot "data\patient_lookup") -ExcludeDirs @(".pytest_cache", "__pycache__", "backup")
}

Restore-Tree -Source (Join-Path `$restoreRoot "app") -Destination (Join-Path `$basePath "app") -ExcludeDirs @(".pytest_cache", "__pycache__", "backup")
Restore-Tree -Source (Join-Path `$restoreRoot "config") -Destination (Join-Path `$basePath "config") -ExcludeDirs @(".pytest_cache", "__pycache__", "backup")
Restore-Tree -Source (Join-Path `$restoreRoot "dashboard") -Destination (Join-Path `$basePath "dashboard") -ExcludeDirs @(".venv", "data", ".pytest_cache", "__pycache__", "backup")
Restore-Tree -Source (Join-Path `$restoreRoot "tests") -Destination (Join-Path `$basePath "tests") -ExcludeDirs @(".pytest_cache", "__pycache__", "backup")
if (Test-Path -LiteralPath (Join-Path `$restoreRoot "docs")) {
    Restore-Tree -Source (Join-Path `$restoreRoot "docs") -Destination (Join-Path `$basePath "docs") -ExcludeDirs @(".pytest_cache", "__pycache__", "backup")
}
if (Test-Path -LiteralPath (Join-Path `$restoreRoot "data\patient_lookup")) {
    Restore-Tree -Source (Join-Path `$restoreRoot "data\patient_lookup") -Destination (Join-Path `$basePath "data\patient_lookup") -ExcludeDirs @(".pytest_cache", "__pycache__", "backup")
}

if (Test-Path -LiteralPath (Join-Path `$restoreRoot "runtime_state_optional\dashboard.sqlite")) {
    Copy-Item -LiteralPath (Join-Path `$restoreRoot "runtime_state_optional\dashboard.sqlite") -Destination (Join-Path `$basePath "dashboard\data\dashboard.sqlite") -Force
}

Write-Host "Restore completed from `$restoreRoot"
"@
Write-TextFile -Path (Join-Path $restoreRoot "restore_from_this_point.ps1") -Content $restoreScript

$verifyScript = @"
Set-StrictMode -Version Latest
`$ErrorActionPreference = "Stop"

function Assert-True {
    param([string]`$Name, [bool]`$Condition)
    if (-not `$Condition) { throw "`$Name expected true" }
}

function Assert-False {
    param([string]`$Name, [bool]`$Condition)
    if (`$Condition) { throw "`$Name expected false" }
}

`$restoreRoot = "$restoreRoot"
`$manifest = Join-Path `$restoreRoot "RESTORE_MANIFEST.json"
`$instructions = Join-Path `$restoreRoot "RESTORE_INSTRUCTIONS.md"
`$restoreScript = Join-Path `$restoreRoot "restore_from_this_point.ps1"

Assert-True -Name "manifest exists" -Condition (Test-Path -LiteralPath `$manifest)
Assert-True -Name "instructions exist" -Condition (Test-Path -LiteralPath `$instructions)
Assert-True -Name "restore script exists" -Condition (Test-Path -LiteralPath `$restoreScript)
Assert-True -Name "app folder exists" -Condition (Test-Path -LiteralPath (Join-Path `$restoreRoot "app"))
Assert-True -Name "config folder exists" -Condition (Test-Path -LiteralPath (Join-Path `$restoreRoot "config"))
Assert-True -Name "dashboard folder exists" -Condition (Test-Path -LiteralPath (Join-Path `$restoreRoot "dashboard"))
Assert-True -Name "tests folder exists" -Condition (Test-Path -LiteralPath (Join-Path `$restoreRoot "tests"))
Assert-True -Name "docs folder exists" -Condition (Test-Path -LiteralPath (Join-Path `$restoreRoot "docs"))
Assert-True -Name "patient_lookup folder exists" -Condition (Test-Path -LiteralPath (Join-Path `$restoreRoot "data\patient_lookup"))

`$handoffCount = @(Get-ChildItem -LiteralPath (Join-Path `$restoreRoot "outputs\handoff_json") -Filter "RAWMOCK*_handoff.json" -File -ErrorAction SilentlyContinue).Count
`$processedCount = @(Get-ChildItem -LiteralPath (Join-Path `$restoreRoot "queue\processed") -Filter "RAWMOCK*.json" -File -ErrorAction SilentlyContinue).Count
Assert-True -Name "rawmock handoff count is 12" -Condition (`$handoffCount -eq 12)
Assert-True -Name "rawmock processed count is 12" -Condition (`$processedCount -eq 12)

Assert-False -Name "dashboard venv excluded" -Condition (Test-Path -LiteralPath (Join-Path `$restoreRoot "dashboard\.venv"))
Assert-False -Name "pycache excluded" -Condition ((@(Get-ChildItem -LiteralPath `$restoreRoot -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue)).Count -gt 0)
Assert-False -Name "pytest cache excluded" -Condition ((@(Get-ChildItem -LiteralPath `$restoreRoot -Recurse -Directory -Filter ".pytest_cache" -ErrorAction SilentlyContinue)).Count -gt 0)
Assert-False -Name "local secrets excluded" -Condition ((@(Get-ChildItem -LiteralPath `$restoreRoot -Recurse -File -Filter "local_secrets.json" -ErrorAction SilentlyContinue)).Count -gt 0)

Write-Host "Restore point verification passed."
"@
Write-TextFile -Path (Join-Path $restoreRoot "verify_restore_point.ps1") -Content $verifyScript

$manifest = [ordered]@{
    restore_point_name = Split-Path -Path $restoreRoot -Leaf
    created_at = (Get-Date).ToString("o")
    source_root = $basePath
    git_status = "not a git repository"
    files_included_summary = [ordered]@{
        app = Get-FileStats -Path (Join-Path $restoreRoot "app")
        config = Get-FileStats -Path (Join-Path $restoreRoot "config")
        dashboard = Get-FileStats -Path (Join-Path $restoreRoot "dashboard")
        tests = Get-FileStats -Path (Join-Path $restoreRoot "tests")
        docs = Get-FileStats -Path (Join-Path $restoreRoot "docs")
        data_patient_lookup = Get-FileStats -Path (Join-Path $restoreRoot "data\patient_lookup")
        rawmock_handoffs = [ordered]@{ file_count = $handoffCount }
        rawmock_processed = [ordered]@{ file_count = $processedCount }
        recent_audit_logs = [ordered]@{ file_count = $auditCount }
        runtime_state_optional = [ordered]@{
            included = $runtimeIncluded
            file_count = if ($runtimeIncluded) { 1 } else { 0 }
        }
    }
    files_excluded_summary = @(
        "dashboard\.venv",
        "__pycache__",
        ".pytest_cache",
        "backup folders",
        "local_secrets.json",
        "credential/token files",
        "non-RAWMOCK artifacts from outputs/queue",
        "mixed audit logs not specifically copied"
    )
    verified_state_summary = @(
        "Fresh RAWMOCK batch passed",
        "Dashboard reset/import passed",
        "Dashboard cases: 12",
        "Handoff JSONs: 12",
        "Processed files: 12",
        "Failed: 0",
        "Deadletter: 0",
        "Google push skipped for test run",
        "Priority comparison passed",
        "Dashboard tests: 28 passed",
        "Dashboard UX polish completed",
        "Copy/Copied buttons working",
        "Date filters and request type bars added",
        "Fresh test reset runner created"
    )
    test_commands_last_known_good = @(
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\tests\run_fresh_rawmock_end_to_end_batch.ps1 -Force",
        ".\dashboard\.venv\Scripts\python.exe -m pytest .\dashboard\tests -q",
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\dashboard\run_dashboard.ps1"
    )
    restore_steps = @(
        "Review RESTORE_INSTRUCTIONS.md first.",
        "Run restore_from_this_point.ps1 with -ConfirmRestore after stopping the dashboard.",
        "The script will make a pre-restore backup before copying files back.",
        "Restore the optional runtime_state_optional/dashboard.sqlite only if you want the exact imported dashboard state.",
        "Restart the dashboard and re-run the fresh RAWMOCK batch if you need a regenerated test cycle."
    )
    known_risks = @(
        "The optional dashboard.sqlite may be locked if the dashboard is running.",
        "Restore scripts are test-only and should not be used against live external systems.",
        "Google Sheet push remains available in production paths and is only disabled at test runtime."
    )
}

($manifest | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath (Join-Path $restoreRoot "RESTORE_MANIFEST.json") -Encoding UTF8

$readme = @"
JeffLocal restore point.

See RESTORE_INSTRUCTIONS.md for restore steps and RESTORE_MANIFEST.json for the file inventory.
"@
Write-TextFile -Path (Join-Path $restoreRoot "README.md") -Content $readme

$sizeInfo = Get-ChildItem -LiteralPath $restoreRoot -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum
Write-Host "Restore point created at: $restoreRoot"
Write-Host "File count: $((Get-ChildItem -LiteralPath $restoreRoot -Recurse -File -ErrorAction SilentlyContinue).Count)"
Write-Host "Size bytes: $($sizeInfo.Sum)"
Write-Host "RAWMOCK handoffs: $handoffCount"
Write-Host "RAWMOCK processed: $processedCount"
Write-Host "Audit logs copied: $auditCount"
Write-Host "Runtime state optional included: $runtimeIncluded"

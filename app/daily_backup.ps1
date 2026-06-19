<#
.SYNOPSIS
    JeffLocal daily backup — creates a timestamped restore point, keeps the last 3 in
    backup/restore_points/, moves older ones to backup/archived_restore_points/.
    Registered by install_scheduled_tasks.ps1 to run daily at 01:00.

.NOTES
    Log: C:\JeffLocal\logs\service_control\backup.log
    Excludes: .venv, node_modules, __pycache__, *.pyc, *.sqlite-wal, *.sqlite-shm
    Keeps: dashboard/ (minus venv), app/, config/, scripts/, data/
#>
$ErrorActionPreference = "SilentlyContinue"

$ROOT         = "C:\JeffLocal"
$BackupBase   = "$ROOT\backup"
$RestorePts   = "$BackupBase\restore_points"
$ArchiveDir   = "$BackupBase\archived_restore_points"
$LogDir       = "$ROOT\logs\service_control"
$LogFile      = "$LogDir\backup.log"
$KEEP_LATEST  = 3

New-Item -ItemType Directory -Path $RestorePts  -Force | Out-Null
New-Item -ItemType Directory -Path $ArchiveDir  -Force | Out-Null
New-Item -ItemType Directory -Path $LogDir      -Force | Out-Null

function blog([string]$msg, [string]$lvl = "INFO") {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') [$lvl] $msg"
    if ((Test-Path $LogFile) -and (Get-Item $LogFile).Length -gt 3MB) {
        Move-Item $LogFile "$LogFile.old" -Force
    }
    Add-Content -Path $LogFile -Value $line -Force
    Write-Host $line
}

blog "=== daily_backup start ==="

# ── Step 1: Create new restore point ────────────────────────────────────────
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$label = "auto_daily_$stamp"
$dest  = "$RestorePts\restore_point_$label"

blog "Creating restore point: $dest"

# Directories to include
$includeDirs = @("app", "config", "scripts", "data", "dashboard")
$excludePats = @(".venv", "__pycache__", "node_modules", "*.pyc", "*.pyo")

foreach ($dir in $includeDirs) {
    $srcPath = "$ROOT\$dir"
    $dstPath = "$dest\$dir"
    if (-not (Test-Path $srcPath)) { continue }

    # Use robocopy for reliable copy with exclusions
    $robArgs = @(
        $srcPath, $dstPath, "/E",
        "/XD", ".venv", "__pycache__", "node_modules",
        "/XF", "*.pyc", "*.pyo", "*.sqlite-wal", "*.sqlite-shm",
        "/NFL", "/NDL", "/NJH", "/NJS", "/NC", "/NS"
    )
    robocopy @robArgs | Out-Null
    $exitCode = $LASTEXITCODE
    if ($exitCode -le 7) {
        blog "  Copied $dir OK (robocopy exit $exitCode)"
    } else {
        blog "  WARNING: robocopy for $dir returned $exitCode" "WARN"
    }
}

# Also snapshot the DB
$dbSrc = "$ROOT\dashboard\data\dashboard.sqlite"
if (Test-Path $dbSrc) {
    New-Item -ItemType Directory -Path "$dest\dashboard\data" -Force | Out-Null
    Copy-Item $dbSrc "$dest\dashboard\data\dashboard.sqlite" -Force
    blog "  Copied dashboard.sqlite"
}

# Write metadata
@{
    created_at  = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
    label       = $label
    type        = "auto_daily"
    jefflocal_version = (git -C $ROOT log -1 --format="%h %s" 2>$null) -replace "`r`n",""
} | ConvertTo-Json | Set-Content "$dest\backup_metadata.json" -Force

blog "Restore point created: $dest"

# ── Step 2: Rotate — keep last N, archive the rest ──────────────────────────
$allPoints = Get-ChildItem -Path $RestorePts -Directory |
    Where-Object { $_.Name -like "restore_point_*" } |
    Sort-Object Name -Descending

$keepCount = 0
foreach ($pt in $allPoints) {
    $keepCount++
    if ($keepCount -gt $KEEP_LATEST) {
        $archDest = "$ArchiveDir\$($pt.Name)"
        blog "Archiving old restore point: $($pt.Name)"
        Move-Item $pt.FullName $archDest -Force
    }
}

blog "Kept $([Math]::Min($keepCount, $KEEP_LATEST)) restore point(s) in $RestorePts"
blog "Archive now holds: $((Get-ChildItem $ArchiveDir -Directory).Count) points"

# ── Step 3: Update LATEST_RESTORE_POINT.txt ─────────────────────────────────
Set-Content "$BackupBase\LATEST_RESTORE_POINT.txt" "$dest`n$(Get-Date -Format 'yyyy-MM-ddTHH:mm:ss')" -Force
blog "LATEST_RESTORE_POINT.txt updated"

blog "=== daily_backup done ==="

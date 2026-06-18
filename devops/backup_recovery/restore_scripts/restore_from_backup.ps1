<#
.SYNOPSIS
    Restore JeffLocal from a dated backup.
.DESCRIPTION
    Stops all services, restores database + config + outputs from
    C:\JeffLocal\backups\YYYY-MM-DD\, then restarts services.
    ALWAYS confirm before running — this overwrites live data.

.PARAMETER BackupDate
    Date of the backup to restore (YYYY-MM-DD). Defaults to latest available.

.PARAMETER DryRun
    List what would be restored without copying anything.

.EXAMPLE
    .\restore_from_backup.ps1 -BackupDate 2026-06-18
    .\restore_from_backup.ps1 -DryRun
#>

param(
    [string]$BackupDate = "",
    [switch]$DryRun
)

$BackupRoot = "C:\JeffLocal\backups"
$Timestamp  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Log($msg) { Write-Host "[$Timestamp] $msg" }

# Resolve backup date
if (-not $BackupDate) {
    $Latest = Get-ChildItem $BackupRoot -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $Latest) { Log "No backups found in $BackupRoot"; exit 1 }
    $BackupDate = $Latest.Name
}

$BackupDir = Join-Path $BackupRoot $BackupDate
if (-not (Test-Path $BackupDir)) { Log "Backup not found: $BackupDir"; exit 1 }

Log "=== RESTORE from $BackupDate $(if ($DryRun) {'(DRY RUN)'} else {''}) ==="

$Restores = @(
    @{ Src = "$BackupDir\database\dashboard.sqlite"; Dest = "C:\JeffLocal\dashboard\data\dashboard.sqlite" },
    @{ Src = "$BackupDir\config";                     Dest = "C:\JeffLocal\config"   },
    @{ Src = "$BackupDir\outputs";                    Dest = "C:\JeffLocal\outputs"  }
)

if (-not $DryRun) {
    # Stop services
    Log "Stopping dashboard and n8n..."
    & "C:\JeffLocal\scripts\service_control\watchdog.ps1" -Action stop -Service dashboard 2>$null
    & "C:\JeffLocal\scripts\service_control\watchdog.ps1" -Action stop -Service n8n        2>$null
    Start-Sleep -Seconds 3
}

foreach ($R in $Restores) {
    if (Test-Path $R.Src) {
        Log "$(if ($DryRun) {'WOULD RESTORE'} else {'RESTORING'}) $($R.Src) -> $($R.Dest)"
        if (-not $DryRun) {
            Copy-Item -Path $R.Src -Destination $R.Dest -Recurse -Force
        }
    } else {
        Log "SKIP (not in backup): $($R.Src)"
    }
}

if (-not $DryRun) {
    # Restart services
    Log "Restarting services..."
    & "C:\JeffLocal\scripts\service_control\watchdog.ps1" -Action start -Service dashboard
    & "C:\JeffLocal\scripts\service_control\watchdog.ps1" -Action start -Service n8n
    Log "=== RESTORE COMPLETE === Verify dashboard at http://localhost:8765"
} else {
    Log "=== DRY RUN COMPLETE === Run without -DryRun to apply ==="
}

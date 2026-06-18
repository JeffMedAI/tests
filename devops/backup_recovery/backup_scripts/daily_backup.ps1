<#
.SYNOPSIS
    Daily backup of all JeffLocal data and config.
.DESCRIPTION
    Backs up SQLite database, config files, queue, outputs, and session logs
    to C:\JeffLocal\backups\YYYY-MM-DD\. Retains 30 days; purges older.
    Run via Task Scheduler at 02:00 daily.
#>

param(
    [string]$BackupRoot = "C:\JeffLocal\backups",
    [int]$RetentionDays = 30
)

$Date       = Get-Date -Format "yyyy-MM-dd"
$Timestamp  = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$BackupDir  = Join-Path $BackupRoot $Date
$LogFile    = "C:\JeffLocal\logs\backup\backup_$Date.log"

function Log($msg) {
    $line = "[$Timestamp] $msg"
    Write-Host $line
    Add-Content -Path $LogFile -Value $line
}

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $LogFile) | Out-Null

Log "=== BACKUP START === $Date"

$Items = @(
    @{ Src = "C:\JeffLocal\dashboard\data\dashboard.sqlite"; Label = "database" },
    @{ Src = "C:\JeffLocal\config";                           Label = "config"   },
    @{ Src = "C:\JeffLocal\queue";                            Label = "queue"    },
    @{ Src = "C:\JeffLocal\outputs";                          Label = "outputs"  },
    @{ Src = "C:\JeffLocal\docs\sessions";                    Label = "sessions" },
    @{ Src = "C:\JeffLocal\docs\reports";                     Label = "reports"  }
)

$Errors = 0
foreach ($Item in $Items) {
    $Dest = Join-Path $BackupDir $Item.Label
    try {
        if (Test-Path $Item.Src) {
            Copy-Item -Path $Item.Src -Destination $Dest -Recurse -Force -ErrorAction Stop
            Log "OK  $($Item.Label) -> $Dest"
        } else {
            Log "SKIP $($Item.Label): path not found ($($Item.Src))"
        }
    } catch {
        Log "FAIL $($Item.Label): $_"
        $Errors++
    }
}

# Purge backups older than RetentionDays
$Cutoff = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -Path $BackupRoot -Directory | Where-Object { $_.LastWriteTime -lt $Cutoff } | ForEach-Object {
    Log "PURGE old backup: $($_.Name)"
    Remove-Item $_.FullName -Recurse -Force
}

if ($Errors -eq 0) {
    Log "=== BACKUP COMPLETE === $BackupDir"
    exit 0
} else {
    Log "=== BACKUP FINISHED WITH $Errors ERRORS ==="
    exit 1
}

<#
.SYNOPSIS
    Registers JeffLocal auto-start, watchdog, health monitor, daily purge, and daily backup.
    Run once as the current user - no admin required.

What gets installed:
  Registry Run key        - launches watchdog when this user logs in
  JeffLocal-Watchdog      - Task Scheduler: crash recovery every 5 minutes
  JeffLocal-HealthMonitor - Task Scheduler: deep health check every 10 minutes
  JeffLocal-DailyPurge    - Task Scheduler: 90-day data purge at 02:00 daily
  JeffLocal-DailyBackup   - Task Scheduler: restore point + rotation at 01:00 daily
#>

$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$Watchdog   = Join-Path $ScriptDir "watchdog.ps1"
$HealthMon  = Join-Path $ScriptDir "health_monitor.ps1"
$Purge      = "C:\JeffLocal\app\purge_old_data.ps1"
$Backup     = "C:\JeffLocal\app\daily_backup.ps1"
$GdprPurge  = "C:\JeffLocal\scripts\daily\gdpr_purge.py"
$GdprPy     = "C:\JeffLocal\dashboard\.venv\Scripts\python.exe"
$GdprDb     = "C:\JeffLocal\dashboard\data\dashboard.sqlite"
$PS         = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

function Make-PSArgs([string]$scriptPath) {
    return "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File ""$scriptPath"""
}

$WatchdogArgs   = Make-PSArgs $Watchdog
$HealthMonArgs  = Make-PSArgs $HealthMon
$PurgeArgs      = Make-PSArgs $Purge
$BackupArgs     = Make-PSArgs $Backup
$GdprPurgeArgs  = """$GdprPurge"" --db ""$GdprDb"" --days 90"

# --- Logon: Registry Run key (no admin needed) ───────────────────────────────
$regPath = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
Set-ItemProperty -Path $regPath -Name "JeffLocal" -Value "$PS $WatchdogArgs"
Write-Host "[OK] Logon auto-start registered (HKCU Run key)"

# --- Task: Watchdog — every 5 minutes ────────────────────────────────────────
$Action   = New-ScheduledTaskAction -Execute $PS -Argument $WatchdogArgs
$Trigger  = New-ScheduledTaskTrigger -Once -At (Get-Date) `
                -RepetitionInterval (New-TimeSpan -Minutes 5)
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -StartWhenAvailable -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName    "JeffLocal-Watchdog" `
    -Action      $Action `
    -Trigger     $Trigger `
    -Settings    $Settings `
    -Description "JeffLocal watchdog - crash-recovery for dashboard and n8n (every 5 min)" `
    -Force | Out-Null

$status1 = if ($?) { "OK" } else { "WARN" }
Write-Host "[$status1] JeffLocal-Watchdog task (every 5 min)"

# --- Task: Health Monitor - every 10 minutes ------------------------------------
$HMAction   = New-ScheduledTaskAction -Execute $PS -Argument $HealthMonArgs
$HMTrigger  = New-ScheduledTaskTrigger -Once -At (Get-Date) `
                -RepetitionInterval (New-TimeSpan -Minutes 10)
$HMSettings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 8) `
    -StartWhenAvailable -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName    "JeffLocal-HealthMonitor" `
    -Action      $HMAction `
    -Trigger     $HMTrigger `
    -Settings    $HMSettings `
    -Description "JeffLocal deep health check - Dashboard, n8n, Ollama, git (every 10 min)" `
    -Force | Out-Null

$status2 = if ($?) { "OK" } else { "WARN" }
Write-Host "[$status2] JeffLocal-HealthMonitor task (every 10 min)"

# --- Task: Daily Purge - at 02:00 daily -----------------------------------------
if (Test-Path $Purge) {
    $PurgeAction  = New-ScheduledTaskAction -Execute $PS -Argument $PurgeArgs
    $PurgeTrigger = New-ScheduledTaskTrigger -Daily -At "02:00"
    $PurgeSettings= New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -StartWhenAvailable

    Register-ScheduledTask `
        -TaskName    "JeffLocal-DailyPurge" `
        -Action      $PurgeAction `
        -Trigger     $PurgeTrigger `
        -Settings    $PurgeSettings `
        -Description "JeffLocal 90-day data purge - queue, handoff JSON, ollama raw (daily at 02:00)" `
        -Force | Out-Null

    $status3 = if ($?) { "OK" } else { "WARN" }
    Write-Host "[$status3] JeffLocal-DailyPurge task (daily at 02:00)"
} else {
    Write-Host "[SKIP] JeffLocal-DailyPurge - $Purge not found"
}

# --- Task: GDPR DB Purge - at 02:30 daily ----------------------------------------
# Purges patient-identifiable fields from PRODUCTION SQLite DB after 90 days.
# GDPR Article 5(1)(e) / UK GDPR compliance. DSPT obligation.
# Target DB: C:\JeffLocal\dashboard\data\dashboard.sqlite (PRODUCTION — not sandbox)
if (Test-Path $GdprPurge) {
    $GdprAction  = New-ScheduledTaskAction -Execute $GdprPy -Argument $GdprPurgeArgs
    $GdprTrigger = New-ScheduledTaskTrigger -Daily -At "02:30"
    $GdprSettings= New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -StartWhenAvailable

    Register-ScheduledTask `
        -TaskName    "JeffLocal-GDPRPurge" `
        -Action      $GdprAction `
        -Trigger     $GdprTrigger `
        -Settings    $GdprSettings `
        -Description "GDPR 90-day purge of patient PII from production DB (UK GDPR Article 5 / DSPT)" `
        -Force | Out-Null

    $statusGdpr = if ($?) { "OK" } else { "WARN" }
    Write-Host "[$statusGdpr] JeffLocal-GDPRPurge task (daily at 02:30) → $GdprDb"
} else {
    Write-Host "[SKIP] JeffLocal-GDPRPurge - $GdprPurge not found"
}

# --- Task: Daily Backup - at 01:00 daily ----------------------------------------
if (Test-Path $Backup) {
    $BackupAction  = New-ScheduledTaskAction -Execute $PS -Argument $BackupArgs
    $BackupTrigger = New-ScheduledTaskTrigger -Daily -At "01:00"
    $BackupSettings= New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 30) -StartWhenAvailable

    Register-ScheduledTask `
        -TaskName    "JeffLocal-DailyBackup" `
        -Action      $BackupAction `
        -Trigger     $BackupTrigger `
        -Settings    $BackupSettings `
        -Description "JeffLocal daily backup - restore point, keep last 3, archive older (daily at 01:00)" `
        -Force | Out-Null

    $status4 = if ($?) { "OK" } else { "WARN" }
    Write-Host "[$status4] JeffLocal-DailyBackup task (daily at 01:00)"
} else {
    Write-Host "[SKIP] JeffLocal-DailyBackup - $Backup not found (will be created; re-run installer after)"
}

Write-Host ""
Write-Host "Running watchdog now to confirm services are up..."
& $Watchdog

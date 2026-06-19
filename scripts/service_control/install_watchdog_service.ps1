<#
.SYNOPSIS
    Registers JeffLocal watchdog and health monitor as scheduled tasks that run at startup.
    Requires Administrator privileges.
    Run this once to enable automatic service monitoring after system reboot (no user login required).

.DESCRIPTION
    Creates two scheduled tasks running under SYSTEM account:
      - JeffLocal-Watchdog      : runs watchdog.ps1 at startup, then every 5 minutes
      - JeffLocal-HealthMonitor : runs health_monitor.ps1 at startup, then every 10 minutes

    Both tasks:
      - Run as SYSTEM account (no user login required)
      - Trigger at Windows startup
      - ExecutionTimeLimit = Unlimited (watchdog runs indefinitely)
      - Battery/network power management disabled
      - StartWhenAvailable = true
      - MultipleInstances = IgnoreNew

    After registration, both tasks are started immediately.
#>

param()

$ErrorActionPreference = "Stop"

# --- Admin check ------------------------------------------------------------------
$currentPrincipal = [System.Security.Principal.WindowsPrincipal][System.Security.Principal.WindowsIdentity]::GetCurrent()
$isAdmin = $currentPrincipal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must run as Administrator." -ForegroundColor Red
    Write-Host "Re-run in an Administrator PowerShell window." -ForegroundColor Red
    exit 1
}

# --- Paths ------------------------------------------------------------------------
$RepoRoot        = "C:\JeffLocal"
$WatchdogScript  = "$RepoRoot\scripts\service_control\watchdog.ps1"
$HealthScript    = "$RepoRoot\scripts\service_control\health_monitor.ps1"
$PSExe           = "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe"

# --- Validate scripts exist -------------------------------------------------------
if (-not (Test-Path $WatchdogScript)) {
    Write-Host "ERROR: Watchdog script not found: $WatchdogScript" -ForegroundColor Red
    exit 1
}

Write-Host "Registering scheduled tasks..." -ForegroundColor Cyan

# --- Task principal (SYSTEM account, highest elevation) --------------------------
$taskPrincipal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# --- Settings for both tasks -----------------------------------------------------
# Note: switch params take no value; battery flags are fixed post-registration
$taskSettings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

# =================================================================================
# TASK 1: JeffLocal-Watchdog
# =================================================================================

Write-Host ""
Write-Host "Registering: JeffLocal-Watchdog" -ForegroundColor White

$trigger1W = New-ScheduledTaskTrigger -AtStartup
$trigger2W = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddSeconds(30) `
    -RepetitionInterval (New-TimeSpan -Minutes 5) `
    -RepetitionDuration (New-TimeSpan -Days 999)

$actionW = New-ScheduledTaskAction `
    -Execute $PSExe `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$WatchdogScript`""

$taskNameW = "JeffLocal-Watchdog"
$existingW = Get-ScheduledTask -TaskName $taskNameW -ErrorAction SilentlyContinue
if ($existingW) {
    Write-Host "  Task exists - unregistering old version..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $taskNameW -Confirm:$false
}

$regW = Register-ScheduledTask `
    -TaskName  $taskNameW `
    -Trigger   @($trigger1W, $trigger2W) `
    -Action    $actionW `
    -Principal $taskPrincipal `
    -Settings  $taskSettings

# Fix battery/power settings (cannot be set via switch params directly)
$fixW = Get-ScheduledTask -TaskName $taskNameW
$fixW.Settings.DisallowStartIfOnBatteries = $false
$fixW.Settings.StopIfGoingOnBatteries     = $false
$fixW.Settings.RunOnlyIfNetworkAvailable  = $false
Set-ScheduledTask -InputObject $fixW | Out-Null

Write-Host "  Registered OK: $($regW.Uri)" -ForegroundColor Green
Write-Host "  Triggers: At Windows startup + every 5 min (crash recovery)" -ForegroundColor Gray
Write-Host "  Run as: SYSTEM account (no login required)" -ForegroundColor Gray
Write-Host "  Execution time limit: Unlimited" -ForegroundColor Gray
Write-Host "  Battery restrictions: disabled" -ForegroundColor Gray

# =================================================================================
# TASK 2: JeffLocal-HealthMonitor (if script exists)
# =================================================================================

Write-Host ""

if (Test-Path $HealthScript) {
    Write-Host "Registering: JeffLocal-HealthMonitor" -ForegroundColor White

    $trigger1H = New-ScheduledTaskTrigger -AtStartup
    $trigger2H = New-ScheduledTaskTrigger `
        -Once `
        -At (Get-Date).AddSeconds(30) `
        -RepetitionInterval (New-TimeSpan -Minutes 10) `
        -RepetitionDuration (New-TimeSpan -Days 999)

    $actionH = New-ScheduledTaskAction `
        -Execute $PSExe `
        -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$HealthScript`""

    $taskNameH = "JeffLocal-HealthMonitor"
    $existingH = Get-ScheduledTask -TaskName $taskNameH -ErrorAction SilentlyContinue
    if ($existingH) {
        Write-Host "  Task exists - unregistering old version..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $taskNameH -Confirm:$false
    }

    $regH = Register-ScheduledTask `
        -TaskName  $taskNameH `
        -Trigger   @($trigger1H, $trigger2H) `
        -Action    $actionH `
        -Principal $taskPrincipal `
        -Settings  $taskSettings

    # Fix battery/power settings
    $fixH = Get-ScheduledTask -TaskName $taskNameH
    $fixH.Settings.DisallowStartIfOnBatteries = $false
    $fixH.Settings.StopIfGoingOnBatteries     = $false
    $fixH.Settings.RunOnlyIfNetworkAvailable  = $false
    Set-ScheduledTask -InputObject $fixH | Out-Null

    Write-Host "  Registered OK: $($regH.Uri)" -ForegroundColor Green
    Write-Host "  Triggers: At Windows startup + every 10 min" -ForegroundColor Gray
    Write-Host "  Run as: SYSTEM account (no login required)" -ForegroundColor Gray
    Write-Host "  Execution time limit: Unlimited" -ForegroundColor Gray
    Write-Host "  Battery restrictions: disabled" -ForegroundColor Gray
} else {
    Write-Host "Skipped: JeffLocal-HealthMonitor (script not found at $HealthScript)" -ForegroundColor Yellow
}

# =================================================================================
# Start tasks immediately
# =================================================================================

Write-Host ""
Write-Host "Starting tasks immediately..." -ForegroundColor Cyan

try {
    Start-ScheduledTask -TaskName "JeffLocal-Watchdog"
    Write-Host "  JeffLocal-Watchdog started OK" -ForegroundColor Green
} catch {
    Write-Host "  Failed to start JeffLocal-Watchdog: $_" -ForegroundColor Red
}

if (Test-Path $HealthScript) {
    try {
        Start-ScheduledTask -TaskName "JeffLocal-HealthMonitor"
        Write-Host "  JeffLocal-HealthMonitor started OK" -ForegroundColor Green
    } catch {
        Write-Host "  Failed to start JeffLocal-HealthMonitor: $_" -ForegroundColor Red
    }
}

# =================================================================================
# Summary
# =================================================================================

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " WATCHDOG SERVICE REGISTRATION COMPLETE" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Both tasks registered and running. They will auto-start on next Windows boot." -ForegroundColor Green
Write-Host ""
Write-Host "Verify with:" -ForegroundColor Gray
Write-Host "  Get-ScheduledTask -TaskName JeffLocal-Watchdog | Get-ScheduledTaskInfo" -ForegroundColor DarkGray
Write-Host "  Get-ScheduledTask -TaskName JeffLocal-HealthMonitor | Get-ScheduledTaskInfo" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Log file: C:\JeffLocal\logs\service_control\watchdog.log" -ForegroundColor Gray

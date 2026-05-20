<#
.SYNOPSIS
    Registers JeffLocal auto-start and watchdog.
    Run once as the current user - no admin required.

What gets installed:
  Registry Run key       - launches watchdog when this user logs in
  JeffLocal-Watchdog     - Task Scheduler task, every 5 minutes
  (the 5-min watchdog also recovers within 5 min of a sleep/wake cycle)
#>

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Watchdog  = Join-Path $ScriptDir "watchdog.ps1"
$PS        = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"
$PSArgs    = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File ""$Watchdog"""

# --- Logon: Registry Run key (no admin needed) ------------------------------
$regPath = "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
Set-ItemProperty -Path $regPath -Name "JeffLocal" -Value "$PS $PSArgs"
Write-Host "[OK] Logon auto-start registered (HKCU Run key)"

# --- Every 5 minutes: Task Scheduler ----------------------------------------
$Action   = New-ScheduledTaskAction -Execute $PS -Argument $PSArgs
$Trigger  = New-ScheduledTaskTrigger -Once -At (Get-Date) `
                -RepetitionInterval (New-TimeSpan -Minutes 5)
$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -StartWhenAvailable `
    -MultipleInstances  IgnoreNew

Register-ScheduledTask `
    -TaskName    "JeffLocal-Watchdog" `
    -Action      $Action `
    -Trigger     $Trigger `
    -Settings    $Settings `
    -Description "JeffLocal watchdog - restarts dashboard and n8n if down (every 5 min)" `
    -Force | Out-Null

if ($?) {
    Write-Host "[OK] JeffLocal-Watchdog task registered (every 5 minutes)"
} else {
    Write-Host "[WARN] JeffLocal-Watchdog task registration failed - run as admin if needed" -ForegroundColor Yellow
    Write-Host "       Logon auto-start via Registry is still active."
}

Write-Host ""
Write-Host "Running watchdog now to confirm services are up..."
& $Watchdog

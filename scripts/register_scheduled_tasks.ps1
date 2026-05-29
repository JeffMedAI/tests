# register_scheduled_tasks.ps1
# Registers all JeffLocal scheduled tasks in Windows Task Scheduler
# Run once as Administrator from C:\JeffLocal\

$ErrorActionPreference = "Stop"

Write-Host "Registering JeffLocal scheduled tasks..." -ForegroundColor Cyan

# --- Task 1: Strategy Agent Daily Report (07:00) ---
$action1 = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -ExecutionPolicy Bypass -File C:\JeffLocal\scripts\daily\strategy_daily.ps1"

$trigger1 = New-ScheduledTaskTrigger -Daily -At "07:00"

$settings1 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "JeffLocal - Strategy Agent Daily Report" `
    -TaskPath "\JeffLocal\" `
    -Action $action1 `
    -Trigger $trigger1 `
    -Settings $settings1 `
    -Description "Generates JeffLocal daily project status report and saves to docs\reports\{date}.md" `
    -RunLevel Highest `
    -Force

Write-Host "Registered: JeffLocal - Strategy Agent Daily Report (daily 07:00)" -ForegroundColor Green

# --- Task 2: Health Check (every 5 minutes) ---
$action2 = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NonInteractive -ExecutionPolicy Bypass -File C:\JeffLocal\scripts\daily\health_check.ps1"

$trigger2 = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At (Get-Date)

$settings2 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 2) `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "JeffLocal - Health Check" `
    -TaskPath "\JeffLocal\" `
    -Action $action2 `
    -Trigger $trigger2 `
    -Settings $settings2 `
    -Description "Checks dashboard, Flask, SQLite, Ollama reachability every 5 minutes" `
    -RunLevel Highest `
    -Force

Write-Host "Registered: JeffLocal - Health Check (every 5 min)" -ForegroundColor Green

# --- Task 3: Watchdog — continuous loop, starts at boot ---
$action3 = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File C:\JeffLocal\scripts\service_control\watchdog.ps1 -IntervalSeconds 60"

# Trigger: at system startup
$trigger3 = New-ScheduledTaskTrigger -AtStartup

$settings3 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Days 365) `
    -RestartCount 5 `
    -RestartInterval (New-TimeSpan -Minutes 2) `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName "JeffLocal - Service Watchdog" `
    -TaskPath "\JeffLocal\" `
    -Action $action3 `
    -Trigger $trigger3 `
    -Settings $settings3 `
    -Description "Monitors all JeffLocal services (dashboard, sandbox, n8n, Ollama, Cloudflare tunnel). Restarts if down. Sends WhatsApp alerts on failure." `
    -RunLevel Highest `
    -Force

Write-Host "Registered: JeffLocal - Service Watchdog (continuous, starts at boot)" -ForegroundColor Green

Write-Host ""
Write-Host "All tasks registered. Verify in Task Scheduler under \JeffLocal\" -ForegroundColor Cyan
Write-Host ""

# List registered tasks
Get-ScheduledTask -TaskPath "\JeffLocal\" | Format-Table TaskName, State -AutoSize

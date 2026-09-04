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

# --- Task 2: Health Check (weekday mornings, 06:45) ---
# REWRITTEN 2026-09-04. This block used to register "JeffLocal - Health Check" on a
# 5-minute repeat pointing at scripts\daily\health_check.ps1 - a script that had
# never been written. From 21 Jul to 4 Sep 2026 that task failed every five minutes
# with exit code -196608 ("the file does not exist") while displaying State: Ready.
# Nobody noticed for 45 days. The script now exists, and the schedule is the one
# Saeed asked for: weekdays at 06:45, fifteen minutes before the 07:00 brief, whose
# health block it feeds.
#
# The 5-minute repeat was never right either. Service monitoring is watchdog.ps1's
# job and it does it every 60 seconds with restarts and WhatsApp alerts. This check
# answers a different question - is work FLOWING - which is a once-a-morning question.
$action2 = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\JeffLocal\scripts\daily\health_check.ps1"'

$trigger2 = New-ScheduledTaskTrigger -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 06:45

$settings2 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "JeffLocal - Weekday Health Check 0645" `
    -TaskPath "\JeffLocal\" `
    -Action $action2 `
    -Trigger $trigger2 `
    -Settings $settings2 `
    -Description "Flow-level health check (queue, unresolved cases, red flags, backups, GDPR purge, unpushed work, failing jobs) feeding the 07:00 morning brief. Mon-Fri 06:45." `
    -RunLevel Highest `
    -Force

Write-Host "Registered: JeffLocal - Weekday Health Check 0645 (Mon-Fri 06:45)" -ForegroundColor Green

# Retire the phantom task this script used to create. Disabled, not deleted, so it
# stays visible and reversible (project rule: never delete without Saeed's say-so).
$OldHealth = Get-ScheduledTask -TaskPath "\JeffLocal\" -TaskName "JeffLocal - Health Check" -ErrorAction SilentlyContinue
if ($OldHealth) {
    Disable-ScheduledTask -TaskPath "\JeffLocal\" -TaskName "JeffLocal - Health Check" -ErrorAction SilentlyContinue | Out-Null
    Write-Host "Disabled: JeffLocal - Health Check (phantom task, script never existed)" -ForegroundColor Yellow
}

# --- Task 2b: Weekday Session Close (18:30) ---
# ADDED 2026-09-04. The session close used to run inside the 19:00 brief; Saeed
# moved it to its own task 30 minutes earlier so the brief REPORTS on a finished
# close instead of performing one and describing itself. Covers BOTH projects.
# Missing from this script until the Security Agent review flagged it - rebuilding
# from here would silently have dropped the close.
$action2b = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument '-NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File "C:\JeffLocal\scripts\daily\session_close.ps1"'

$trigger2b = New-ScheduledTaskTrigger -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At 18:30

$settings2b = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 25) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "JeffLocal - Weekday Session Close 1830" `
    -TaskPath "\JeffLocal\" `
    -Action $action2b `
    -Trigger $trigger2b `
    -Settings $settings2b `
    -Description "Full session close (session log, HANDOFF, PROJECT_MEMORY, commit, push, restore tag) for BOTH Avamed and St Marks. Mon-Fri 18:30, 30 min before the 19:00 brief." `
    -RunLevel Highest `
    -Force

Write-Host "Registered: JeffLocal - Weekday Session Close 1830 (Mon-Fri 18:30)" -ForegroundColor Green

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

# --- Task 4: GDPR weekly purge (Sunday 03:00) ---
# Database Agent — 2026-05-31
# Security Agent review: docs\compliance\security_review_gdpr_purge_2026-05-30.md
# Purges patient PII from the PRODUCTION SQLite older than 90 days.
# Sandbox decommissioned 2026-06-07 — path corrected to production DB to match
# the live registered task (JeffLocal-GDPRPurge). Do NOT point this at sandbox.
$action4 = New-ScheduledTaskAction `
    -Execute "C:\JeffLocal\dashboard\.venv\Scripts\python.exe" `
    -Argument "C:\JeffLocal\scripts\daily\gdpr_purge.py --db C:\JeffLocal\dashboard\data\dashboard.sqlite --days 90" `
    -WorkingDirectory "C:\JeffLocal\scripts\daily"

$trigger4 = New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek Sunday -At "03:00"

$settings4 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 10) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

Register-ScheduledTask `
    -TaskName "JeffLocal - GDPR Weekly Purge" `
    -TaskPath "\JeffLocal\" `
    -Action $action4 `
    -Trigger $trigger4 `
    -Settings $settings4 `
    -Description "Weekly GDPR 90-day patient data purge. Redacts PII from cases/alert_events, deletes call_recordings. Logs to C:\JeffLocal\logs\gdpr\. AUDIT: docs\compliance\gdpr_purge_log.jsonl." `
    -RunLevel Highest `
    -Force

Write-Host "Registered: JeffLocal - GDPR Weekly Purge (weekly Sunday 03:00)" -ForegroundColor Green

# --- Task 5: GDPR weekly purge for tenant2 (placeholder tenant, Sunday 03:15) ---
# Multi-tenancy step 4. gdpr_purge.py itself needs no code change — it already
# takes --db PATH (default: the production database). This is a second,
# independent scheduled action pointed at tenant2's own database, staggered
# 15 minutes after the default instance's purge so they don't contend for the
# same log/CPU window. Rename this task (and the --db path) if/when tenant2
# is renamed for go-live — see governance/TENANT_REGISTRY.md.
$action5 = New-ScheduledTaskAction `
    -Execute "C:\JeffLocal\dashboard\.venv\Scripts\python.exe" `
    -Argument "C:\JeffLocal\scripts\daily\gdpr_purge.py --db C:\JeffLocal\dashboard\data\tenants\tenant2.sqlite --days 90" `
    -WorkingDirectory "C:\JeffLocal\scripts\daily"

$trigger5 = New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek Sunday -At "03:15"

$settings5 = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 10) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable:$false

Register-ScheduledTask `
    -TaskName "JeffLocal - GDPR Weekly Purge (tenant2)" `
    -TaskPath "\JeffLocal\" `
    -Action $action5 `
    -Trigger $trigger5 `
    -Settings $settings5 `
    -Description "Weekly GDPR 90-day purge for the tenant2 (placeholder identity) tenant database. Same logic as the default instance's purge task, different --db path." `
    -RunLevel Highest `
    -Force

Write-Host "Registered: JeffLocal - GDPR Weekly Purge (tenant2) (weekly Sunday 03:15)" -ForegroundColor Green

Write-Host ""
Write-Host "All tasks registered. Verify in Task Scheduler under \JeffLocal\" -ForegroundColor Cyan
Write-Host ""

# List registered tasks
Get-ScheduledTask -TaskPath "\JeffLocal\" | Format-Table TaskName, State -AutoSize

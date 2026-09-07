# register_scheduled_tasks.ps1
# Registers all JeffLocal scheduled tasks in Windows Task Scheduler
# Run once as Administrator from C:\JeffLocal\
#
# ── HOW MUCH OF THIS FILE MATCHES THE REAL MACHINE? ──────────────────────────
# Every Register-ScheduledTask below uses -Force, so running this file REPLACES
# the live tasks with exactly what is written here. That is only safe where the
# text has actually been checked against the machine.
#
# CHECKED 2026-09-07 against the live exported XML: Task 2c (Evening Session Close
# Brief) only. That check found THREE differences in a block written from intent:
# a 25-minute time limit against the live task's 1 hour (would have started
# killing the evening brief mid-run); two invented startup switches; and
# -RunLevel Highest, which would have ELEVATED a task that has run unelevated for
# months. Three defects in one block nobody thought was risky.
#
# NOT CHECKED: every other task in this file. They were written from intent, not
# read off the machine, and the 2c experience says that is not the same thing.
# Note that all seven carry -RunLevel Highest - nobody has confirmed any of them
# actually runs elevated on the machine.
# [UNVERIFIED - confirm before proceeding] Before running this script in anger,
# compare each block against the machine:
#   Export-ScheduledTask -TaskPath "\JeffLocal\" -TaskName "<name>"
# The backup block below captures the live definitions first, so a mismatch is
# recoverable - but recovering is worse than not breaking it.

$ErrorActionPreference = "Stop"

Write-Host "Registering JeffLocal scheduled tasks..." -ForegroundColor Cyan

# ── BACK UP WHAT IS ALREADY THERE, BEFORE ANYTHING IS OVERWRITTEN ────────────
# Every Register-ScheduledTask below uses -Force, which REPLACES a live task
# outright. If a task on this machine was ever tuned by hand, running this script
# silently reverts it and there is no record of what it used to be. That matters
# most for the tasks carrying the alarms: a setting quietly changed back is the
# same class of invisible failure as the 11-19 Aug 2026 outage.
#
# So: export every existing \JeffLocal\ task to XML first. Restore one with
#   Register-ScheduledTask -Xml (Get-Content <file> -Raw) -TaskName "<name>" -TaskPath "\JeffLocal\"
# logs\ is gitignored, so these never reach the repo. Added 2026-09-07.
$BackupDir = "C:\JeffLocal\logs\task-backups\" + (Get-Date).ToString("yyyy-MM-dd-HHmmss")
try {
    $Existing = @(Get-ScheduledTask -TaskPath "\JeffLocal\" -ErrorAction SilentlyContinue)
    if (@($Existing).Count -gt 0) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
        foreach ($t in $Existing) {
            $safe = ($t.TaskName -replace '[\\/:*?"<>|]', '_')
            Export-ScheduledTask -TaskName $t.TaskName -TaskPath "\JeffLocal\" |
                Set-Content -Path (Join-Path $BackupDir "$safe.xml") -Encoding UTF8
        }
        Write-Host "Backed up $(@($Existing).Count) existing task(s) to $BackupDir" -ForegroundColor Yellow
    } else {
        Write-Host "No existing \JeffLocal\ tasks found - nothing to back up." -ForegroundColor Yellow
    }
} catch {
    # A failed backup must not stop the registration, but it must be visible.
    Write-Host "WARNING: could not back up existing tasks - $_" -ForegroundColor Red
}

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

# --- Task 2c: Evening Session Close Brief (19:00, daily) ---
# ADDED 2026-09-07, Saeed's instruction. This was the ONLY JeffLocal scheduled job
# missing from this script, so rebuilding a machine from here produced a system
# with no evening brief - and the evening brief is what tells Saeed a session close
# failed. The gap was found by the Security Agent during the PR #2 review.
#
# It sends the message ONLY. Since 2026-09-04 it performs no close: it reads the
# marker the 18:30 close leaves at logs\close-state\, reports on the last close
# that fell due, and shouts if that close did not complete. See CLAUDE.md,
# "SESSION END PROTOCOL".
#
# VERIFIED against the live machine 2026-09-07 (Saeed ran Get-ScheduledTask and
# sent the output). The action, arguments and the settings below are now copied
# from the real task, NOT reconstructed. My first reconstruction was wrong in a
# way that would have degraded the job:
#   - ExecutionTimeLimit was 25 minutes; the live task allows 1 HOUR. The brief
#     makes several Ollama calls at up to 90s each across two projects, so a
#     25-minute cap could have killed the evening message mid-run. Corrected.
#   - It added -NoProfile and -WindowStyle Hidden, which the live task does not
#     use. Removed: this script exists to REPRODUCE the machine, not to redesign
#     it, and unrequested changes to the job carrying the alarms are exactly what
#     the -Force overwrite makes dangerous.
# Trailing [UNVERIFIED] items are listed above $trigger2c and $settings2c.
#
# -Mode Evening is required: without it combined_brief.ps1 defaults to Morning and
# would send the wrong brief at 19:00.
$action2c = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument '-NonInteractive -ExecutionPolicy Bypass -File C:\JeffLocal\scripts\daily\combined_brief.ps1 -Mode Evening'

# Trigger CONFIRMED from the live XML: CalendarTrigger, ScheduleByDay,
# DaysInterval 1, boundary 19:00 - i.e. daily at 19:00. Matches.
# Daily, not weekdays: the brief goes out at weekends too. It explains in one line
# that no close is scheduled on a Saturday or Sunday, while still reporting on the
# last close that actually fell due - normally Friday's - so a Friday failure is
# not buried by the weekend. Saeed confirmed 2026-09-07 that he wants that Friday
# failure to keep reminding him on Saturday and Sunday until it is fixed.
$trigger2c = New-ScheduledTaskTrigger -Daily -At "19:00"

# Every value here now comes from the live task's exported XML, 2026-09-07.
# Deliberately NOT set, because the live task carries the cmdlet's own defaults
# and setting them explicitly would only invite drift:
#   DisallowStartIfOnBatteries true - StopIfGoingOnBatteries true
#   IdleSettings 10m/1h, StopOnIdleEnd true, RestartOnIdle false
#   UseUnifiedSchedulingEngine true - RestartCount 0
$settings2c = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -MultipleInstances IgnoreNew `
    -StartWhenAvailable

Register-ScheduledTask `
    -TaskName "JeffLocal - Evening Session Close Brief" `
    -TaskPath "\JeffLocal\" `
    -Action $action2c `
    -Trigger $trigger2c `
    -Settings $settings2c `
    -Description "Sends the 19:00 evening WhatsApp brief for BOTH projects. Reports on the last session close that fell due and shouts if it did not complete. Performs no close itself since 2026-09-04. Daily." `
    -Force

Write-Host "Registered: JeffLocal - Evening Session Close Brief (daily 19:00)" -ForegroundColor Green

# NOTE on the two deliberate departures from the live task, both recorded so
# nobody "corrects" them back by accident:
#
# 1. NO -RunLevel Highest, unlike every other task in this file. The live task's
#    XML has no RunLevel element at all, which means LeastPrivilege - it runs
#    UNELEVATED, as the interactive user (LogonType InteractiveToken). Adding
#    -RunLevel Highest would have elevated a job that has run unelevated for
#    months, changing its token, its environment and what it can touch, for no
#    reason anyone asked for. Reproduce, do not redesign.
#    Also deliberately no -User: omitting it registers under whoever runs this
#    script, with InteractiveToken, which is what the live task has. The live
#    UserId is a machine-specific SID and hardcoding it would break on any
#    rebuilt machine - the exact scenario this script exists for.
#
# 2. The Description text differs. The live one reads "Evening session-close
#    brief (7pm). Built from session logs + PROJECT_MEMORY, plain English for
#    Saeed." That predates 2026-09-04 and now misleads: this task performs no
#    close. The text above is the only intentional change to the live task's
#    definition in this block, and it affects nothing but what Task Scheduler
#    displays.

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

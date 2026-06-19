# DEVOPS AGENT TASK — Register Strategy Agent Daily Report in Windows Task Scheduler
# Assigned by: Lead Agent
# Date: 2026-05-29
# Priority: Medium
# Blocking: Strategy Agent daily reports will not auto-run until this is done

---

## TASK

Register `scripts\daily\strategy_daily.ps1` with Windows Task Scheduler.

## ACCEPTANCE CRITERIA

```
[ ] Task exists in Windows Task Scheduler
[ ] Name / Label:  "JeffLocal — Strategy Agent Daily Report"
[ ] Script path:   C:\JeffLocal\scripts\daily\strategy_daily.ps1
[ ] Trigger:       Daily at 07:00 (local time)
[ ] Run as:        The account that owns C:\JeffLocal (confirm with Saeed if unsure)
[ ] On failure:    Log to C:\JeffLocal\scripts\daily\last_run.log and notify Lead Agent
[ ] Confirm task runs successfully on first manual trigger before marking done
```

## COMMAND TO REGISTER (PowerShell, run as Administrator)

```powershell
$Action  = New-ScheduledTaskAction -Execute "powershell.exe" `
             -Argument "-NonInteractive -ExecutionPolicy Bypass -File `"C:\JeffLocal\scripts\daily\strategy_daily.ps1`""
$Trigger = New-ScheduledTaskTrigger -Daily -At "07:00"
$Settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
              -RestartCount 1 -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask `
  -TaskName "JeffLocal — Strategy Agent Daily Report" `
  -Action   $Action `
  -Trigger  $Trigger `
  -Settings $Settings `
  -Description "Generates Strategy Agent daily report and saves to docs\reports\{date}.md"
```

## VERIFY

```powershell
Get-ScheduledTask -TaskName "JeffLocal — Strategy Agent Daily Report"
# Then do a manual test run:
Start-ScheduledTask -TaskName "JeffLocal — Strategy Agent Daily Report"
# Check output:
Get-Content C:\JeffLocal\scripts\daily\last_run.log
```

## REPORT BACK TO LEAD AGENT

Confirm:
- Task registered: yes/no
- Manual test run: passed/failed
- Log output: (paste last line of last_run.log)

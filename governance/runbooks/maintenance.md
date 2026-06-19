# RUNBOOK: Maintenance Procedures
**Owner:** DevOps Agent  
**Last updated:** 2026-06-18

---

## Daily (automated)

| Task | When | How |
|------|------|-----|
| Database backup | 02:00 | Task Scheduler runs `devops/backup_recovery/backup_scripts/daily_backup.ps1` |
| Morning brief | 07:00 | Task Scheduler runs `scripts/daily/strategy_daily.ps1 -Mode Morning` |
| Evening brief | 19:00 | Task Scheduler runs `scripts/daily/strategy_daily.ps1 -Mode Evening` |
| Watchdog health check | Continuous | `watchdog.ps1` checks dashboard and n8n every 60 seconds |

---

## Daily (manual — session start)

1. Check dashboard is up: `http://localhost:8765/health`
2. Check n8n is active: `http://localhost:5678/`
3. Check dead-letter queue: `ls C:\JeffLocal\queue\deadletter\`
4. Read morning brief and session log.

---

## Weekly (every Monday)

1. Review the 7-day backup log: `ls C:\JeffLocal\backups\` — confirm 7 dated folders exist.
2. Check disk space: `Get-PSDrive C` — flag if < 5 GB free.
3. Review CHANGELOG.md for the past week.
4. Run the full test suite: `cd C:\JeffLocal\dashboard && python -m pytest`
5. Check n8n workflow is still active (WF06 "JeffLocal - 06 Test Intake Webhook").
6. Write weekly summary in WhatsApp brief.

---

## Monthly

1. Run GDPR purge manually if the scheduled task has not run:
   ```powershell
   cd C:\JeffLocal\dashboard
   python -c "from app.db import connect; conn = connect(); conn.execute(\"UPDATE cases SET patient_name=NULL, dob=NULL, postcode=NULL, callback_number=NULL, nhs_number=NULL, emis_number=NULL, transcript=NULL, call_summary=NULL, ai_summary=NULL, patient_record_note=NULL WHERE datetime(imported_at) < datetime('now', '-90 days')\"); conn.commit()"
   ```
2. Rotate n8n API key (get Saeed's go-ahead first).
3. Verify backup restore works: `devops/backup_recovery/restore_scripts/restore_from_backup.ps1 -DryRun`

---

## Code Updates (any session)

1. Work on the `sandbox` git branch (or a feature branch).
2. Run tests: `cd C:\JeffLocal\dashboard && python -m pytest`
3. Get Security Agent + Lead Agent sign-off.
4. Get Saeed's explicit "approved" in chat.
5. Merge to `main`: `git checkout main && git checkout sandbox -- <files> && git commit`
6. Restart dashboard: `watchdog.ps1 -Action restart -Service dashboard`
7. Run smoke test: `devops/deployment/smoke_test.ps1`
8. Log in `CHANGELOG.md`.

---

## Checking Service Status

```powershell
# Full status check
& C:\JeffLocal\scripts\service_control\watchdog.ps1 -Action status -Service dashboard
& C:\JeffLocal\scripts\service_control\watchdog.ps1 -Action status -Service n8n

# Quick health checks
Invoke-WebRequest http://localhost:8765/health -UseBasicParsing
Invoke-WebRequest http://localhost:5678/healthz -UseBasicParsing
Invoke-WebRequest http://localhost:11434/api/tags -UseBasicParsing
```

---

## Backup Retention

Backups older than 30 days are automatically purged by `daily_backup.ps1`. Off-site backup is Phase 2.

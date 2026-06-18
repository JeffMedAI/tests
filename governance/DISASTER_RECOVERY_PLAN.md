# DISASTER RECOVERY PLAN — JeffLocal (Avamed)
**Version:** 1.0  
**Date:** 2026-06-18  
**Owner:** Saeed (Human Controller)  
**RTO Target:** 1 hour | **RPO Target:** 24 hours (daily backup)

---

## Plain English Summary

If the system goes down, here is what we do:
- If just the dashboard crashes: the watchdog restarts it automatically within 30 seconds. No action needed.
- If the whole machine or database is corrupted: restore from last night's backup using the restore script. Target: back up within 1 hour.
- If n8n stops: watchdog restarts it. New calls queue in the phone system until it is back.
- During any outage: reception staff continue to take calls manually (see Manual Fallback below).

---

## Scenarios and Response

### Scenario 1 — Dashboard process crash (most common)
**Detection:** Dashboard on :8765 stops responding.  
**Cause:** Python process crash, memory, or uncaught exception.  
**Recovery:**
1. Watchdog detects within 60 seconds and restarts automatically.
2. If watchdog itself has failed: `& C:\JeffLocal\scripts\service_control\watchdog.ps1 -Action start -Service dashboard`
3. Verify: `http://localhost:8765/health` returns 200.
4. Check log: `C:\JeffLocal\logs\dashboard\`
**RTO:** 2 minutes (automated) / 10 minutes (manual).

### Scenario 2 — n8n process crash
**Detection:** Port 5678 not responding. New calls not entering pipeline.  
**Recovery:**
1. Watchdog auto-restarts.
2. Manual: `& C:\JeffLocal\scripts\service_control\watchdog.ps1 -Action start -Service n8n`
3. Verify: `http://localhost:5678/healthz` returns 200.
4. Any calls that arrived during outage: check `queue/incoming/` for unprocessed files.
**RTO:** 5 minutes.

### Scenario 3 — Database corruption
**Detection:** Dashboard errors on startup; SQLite reports corruption.  
**Recovery:**
1. Stop dashboard: `watchdog.ps1 -Action stop -Service dashboard`
2. Backup current (corrupt) DB: `Copy-Item C:\JeffLocal\dashboard\data\dashboard.sqlite C:\JeffLocal\dashboard\data\dashboard.sqlite.corrupt`
3. Run restore: `C:\JeffLocal\devops\backup_recovery\restore_scripts\restore_from_backup.ps1`
4. Restart dashboard.
5. Verify data integrity: check case count in dashboard matches expected.
**RPO:** Up to 24 hours of cases may need re-import from `outputs/handoff_json/` if the backup is from the previous night.

### Scenario 4 — Machine restart / power loss
**Detection:** All services down after unplanned restart.  
**Recovery:**
1. Services are configured to start at boot via Task Scheduler (watchdog task).
2. Wait 3 minutes for auto-start.
3. If auto-start fails: run `watchdog.ps1 -Action start -Service dashboard` and `watchdog.ps1 -Action start -Service n8n` manually.
4. Verify all three: dashboard :8765, n8n :5678, Ollama :11434.

### Scenario 5 — Bad deployment (code regression)
**Detection:** Dashboard errors or tests fail after code deploy.  
**Recovery:**
1. Run rollback: `C:\JeffLocal\devops\deployment\rollback_production.ps1`
2. Smoke test: `C:\JeffLocal\devops\deployment\smoke_test.ps1`
3. Notify Saeed.

---

## Manual Fallback (during any outage)

Reception staff can continue taking calls manually:
1. Take the caller's name, date of birth, postcode, and reason for calling on paper.
2. Note any red-flag symptoms (chest pain, stroke symptoms, suicidal intent) — escalate immediately to a clinician.
3. Once system is back, enter the call manually via the dashboard if no handoff JSON exists.
4. All manual entries must be marked `verification_status = staff_review` in the dashboard.

---

## Off-Site Backup Strategy (Phase 2)
[UNVERIFIED — not yet implemented] Off-site backup (encrypted copy to external drive or cloud) is planned for Phase 2 before wider rollout. Currently: daily backups are local only.

---

## Contacts

| Role | Name | Contact |
|------|------|---------|
| Human Controller / Escalation | Saeed | 07440 333938 |
| Hostcomm UK (voice AI issues) | Support | Via Hostcomm support portal |

---

## Review Schedule
Review after every incident. Mandatory review before Churchtown go-live.

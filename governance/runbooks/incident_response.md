# RUNBOOK: Incident Response
**Owner:** Lead Agent → Saeed  
**Last updated:** 2026-06-18

---

## Severity Levels

| Severity | Definition | Response time | Who acts |
|----------|-----------|---------------|----------|
| P1 — Critical | System down, patient safety impact, data breach, auth bypass | Immediate | Saeed + Lead Agent |
| P2 — High | Dashboard errors, pipeline blocked, data wrong | Within 1 hour | Lead Agent + relevant specialist |
| P3 — Medium | Slow performance, minor display bug | Within 24 hours | Relevant specialist |
| P4 — Low | Cosmetic, documentation | Next session | Relevant specialist |

---

## P1 Response: System Down

1. **Identify which service is down:**
   - Dashboard? → `Invoke-WebRequest http://localhost:8765/health`
   - n8n? → `Invoke-WebRequest http://localhost:5678/healthz`
   - Ollama? → `Invoke-WebRequest http://localhost:11434/api/tags`

2. **Attempt auto-recovery:**
   ```powershell
   & C:\JeffLocal\scripts\service_control\watchdog.ps1 -Action restart -Service dashboard
   & C:\JeffLocal\scripts\service_control\watchdog.ps1 -Action restart -Service n8n
   ```

3. **If restart fails — check logs:**
   - Dashboard: `C:\JeffLocal\logs\dashboard\`
   - n8n: n8n log output in Task Scheduler history
   - Pipeline: `C:\JeffLocal\logs\app\encrypted_intake_cycle_YYYY-MM-DD.log`

4. **If dashboard will not start — restore from backup:**
   ```powershell
   & C:\JeffLocal\devops\backup_recovery\restore_scripts\restore_from_backup.ps1
   ```

5. **Tell Saeed (WhatsApp 07440 333938):**
   - What is down
   - When it went down
   - What we tried
   - Current status
   - ETA for fix

6. **Activate manual fallback:** Tell reception to take calls on paper until system is back. See DISASTER_RECOVERY_PLAN.md.

---

## P1 Response: Safety Invariant Violation

If the LLM has set `verification_status`, `priority`, `safe_to_queue`, or any identity field:

1. **Immediately halt the pipeline:**
   ```powershell
   & C:\JeffLocal\scripts\service_control\watchdog.ps1 -Action stop -Service dashboard
   ```
2. Mark the affected cases as `needs_review` in SQLite directly.
3. Notify Saeed with full details: which case(s), which field, what the LLM set vs. what deterministic code should have set.
4. Do not restart pipeline until the root cause is found and fixed. Security Agent must approve the fix.

---

## P1 Response: Unacknowledged Red-Flag Case

If a `priority = 999 Emergency` case has been on the dashboard for > 10 minutes without staff action:

1. Contact reception directly by phone.
2. Confirm they can see the case on the dashboard.
3. If they cannot access the dashboard, read the task to them verbally and ask them to escalate to the GP immediately.
4. Log the incident in `CHANGE_LOG.md`.

---

## P2 Response: Dead-Letter Queue Growing

1. Check deadletter files: `ls C:\JeffLocal\queue\deadletter\`
2. Inspect one file — look for: decrypt failure, format mismatch, missing fields.
3. If decrypt failure: check JEIE-1 keys are in place (`config/keys/`).
4. If format mismatch: check n8n WF06 payload shape (was it changed?).
5. Note in daily brief. No automatic replay — manual review required.

---

## Incident Log

Write one entry per incident to `CHANGE_LOG.md` with: date, severity, description, affected cases, root cause, fix applied, prevented reoccurrence.

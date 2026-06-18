# RUNBOOK: Daily Health Check
**Owner:** DevOps Agent / Lead Agent  
**Last updated:** 2026-06-18

---

## Quick Health Check (< 2 minutes)

Run this every session start and after any deployment:

```powershell
# 1. Smoke test (all services + DB + config)
& C:\JeffLocal\devops\deployment\smoke_test.ps1

# 2. Dead-letter queue
(Get-ChildItem "C:\JeffLocal\queue\deadletter\" -ErrorAction SilentlyContinue).Count

# 3. Cases imported today
cd C:\JeffLocal\dashboard
python -c "from app.db import connect; conn = connect(); r = conn.execute(\"SELECT COUNT(*) as c FROM cases WHERE date(imported_at) = date('now')\").fetchone(); print(f'{r[\"c\"]} cases imported today')"

# 4. Unresolved red-flag cases
python -c "from app.db import connect; conn = connect(); r = conn.execute(\"SELECT call_id, timestamp FROM cases WHERE priority='999 Emergency' AND status != 'Resolved'\").fetchall(); [print(row['call_id'], row['timestamp']) for row in r] or print('None outstanding')"
```

---

## Full Health Check (weekly or after incidents)

### 1. Services
| Check | Command | Expected |
|-------|---------|---------|
| Dashboard | `Invoke-WebRequest http://localhost:8765/health` | 200 |
| n8n | `Invoke-WebRequest http://localhost:5678/healthz` | 200 |
| Ollama | `Invoke-WebRequest http://localhost:11434/api/tags` | 200 |

### 2. Database
- File exists and non-empty: `Test-Path C:\JeffLocal\dashboard\data\dashboard.sqlite`
- Can connect: `python -c "from app.db import connect; connect()"`
- Row counts reasonable: check cases, audit_events

### 3. Pipeline
- queue/incoming/ should be empty between calls (files process within ~90 seconds)
- queue/deadletter/ should be 0 (or explain why not)
- outputs/handoff_json/ should have a file for each case in the DB

### 4. Safety invariant
Spot-check: pick any case in the DB, confirm:
- `verification_status` is one of: matched / possible_match / no_match / insufficient_id
- `priority` is one of: 999 Emergency / urgent_same_day / routine / review_required
- Red-flag cases have `priority = 999 Emergency` and `safe_to_queue = 0`

### 5. Backup
- Latest backup folder exists: `ls C:\JeffLocal\backups\ | Sort-Object Name -Descending | Select-Object -First 1`
- At least yesterday's backup present

### 6. Logs
- No ERROR lines in dashboard log: `Select-String -Path "C:\JeffLocal\logs\dashboard\*.log" -Pattern "ERROR" | Select-Object -Last 20`
- No FAIL lines in backup log: `Select-String -Path "C:\JeffLocal\logs\backup\*.log" -Pattern "FAIL" | Select-Object -Last 10`

---

## What to Do If Something Fails

See [incident_response.md](incident_response.md) for the response procedure for each failure type.

---

## Expected Baselines (record after first week of go-live)

| Metric | Expected | Actual (fill after go-live) |
|--------|---------|----------------------------|
| Avg cases/day | TBC | — |
| Avg processing time | < 90 seconds | — |
| Dead-letter rate | < 1% | — |
| Uptime | > 99.5% | — |
| Test pass rate | 100% | — |

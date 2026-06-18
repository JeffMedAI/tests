# DATABASE HEALTH — Monitoring Reference
**Owner:** Database Agent  
**Last updated:** 2026-06-18  
**Database:** `C:\JeffLocal\dashboard\data\dashboard.sqlite`

---

## Key Tables and Expected State

| Table | Purpose | Expected row count |
|-------|---------|-------------------|
| cases | One row per processed patient call | Grows daily; purged after 90 days |
| audit_events | Immutable staff action log | Multiple rows per case; never deleted |
| alert_events | System alerts | Low volume |
| staff_users | Reception staff accounts | 5–20 for a single practice |
| sessions | Active login sessions | 1–5 concurrently |
| auth_reset_tokens | Password reset tokens | Very low; expire quickly |
| staff_invitations | Pending staff invites | 0 when fully onboarded |
| call_recordings | Voice recording metadata | One per case (Phase 1: all unavailable) |

---

## Health Checks

```powershell
cd C:\JeffLocal\dashboard

# 1. Can connect
python -c "from app.db import connect; c = connect(); print('OK')"

# 2. Table row counts
python -c "
from app.db import connect
conn = connect()
for t in ['cases','audit_events','alert_events','staff_users','sessions']:
    n = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
    print(f'{t}: {n}')
"

# 3. Cases today
python -c "from app.db import connect; conn = connect(); print(conn.execute(\"SELECT COUNT(*) FROM cases WHERE date(imported_at)=date('now')\").fetchone()[0], 'cases today')"

# 4. Unresolved red flags
python -c "from app.db import connect; conn = connect(); r = conn.execute(\"SELECT call_id, priority, status FROM cases WHERE priority='999 Emergency' AND status != 'Resolved'\").fetchall(); [print(dict(row)) for row in r] or print('None')"

# 5. Audit log not empty
python -c "from app.db import connect; conn = connect(); print(conn.execute('SELECT COUNT(*) FROM audit_events').fetchone()[0], 'audit rows')"

# 6. GDPR: cases older than 90 days with PII still present
python -c "
from app.db import connect
conn = connect()
n = conn.execute(\"SELECT COUNT(*) FROM cases WHERE datetime(imported_at) < datetime('now','-90 days') AND patient_name IS NOT NULL\").fetchone()[0]
print(f'Cases needing GDPR purge: {n}')
"
```

---

## GDPR Purge

Fields containing patient PII are purged after 90 days. The scheduled task runs this automatically. To run manually:

```powershell
cd C:\JeffLocal\dashboard
python -c "
from app.db import connect
conn = connect()
conn.execute('''
    UPDATE cases SET
        patient_name=NULL, dob=NULL, postcode=NULL, callback_number=NULL,
        nhs_number=NULL, emis_number=NULL, transcript=NULL,
        call_summary=NULL, ai_summary=NULL, patient_record_note=NULL,
        open_details=NULL
    WHERE datetime(imported_at) < datetime('now', '-90 days')
''')
conn.commit()
print('Purge complete')
"
```

Fields retained after 90 days: `call_id`, `request_type`, `verification_status`, `priority`, `status`, `resolved_at`, `turnaround_minutes`, `imported_at`. These are needed for audit and reporting.

---

## Backup and Recovery

- Daily backup at 02:00: `devops/backup_recovery/backup_scripts/daily_backup.ps1`
- To restore: `devops/backup_recovery/restore_scripts/restore_from_backup.ps1`
- RPO: 24 hours
- RTO: < 1 hour

---

## Performance Notes

- WAL mode enabled: multiple concurrent readers without locking writer
- Sync = NORMAL: good balance of safety vs speed for SQLite
- 8 MB page cache
- Indexes: `call_id` (primary key), `call_timestamp_sort`, `status`, `priority` are used by dashboard queries

---

## Baseline Metrics (record after Churchtown go-live)

| Metric | Value |
|--------|-------|
| DB file size | — |
| Total cases | — |
| Audit events / case avg | — |
| GDPR purge last run | — |

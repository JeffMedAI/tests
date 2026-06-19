# Security Agent Review — GDPR Purge Script
**Reviewer:** Security Agent (acting)
**Date:** 2026-05-31
**Subject:** `scripts/daily/gdpr_purge.py` v1.0.0
**Verdict:** ✅ APPROVED

---

## Files Reviewed

| File | Purpose |
|------|---------|
| `scripts/daily/gdpr_purge.py` | Main purge script |
| `scripts/daily/test_gdpr_purge.py` | Test suite (7 tests) |
| `scripts/migrations/add_created_at_20260531.sql` | Schema migration |
| `scripts/register_scheduled_tasks.ps1` | Task Scheduler registration |

---

## Checklist

### 1. Does dry-run mode actually prevent writes?

**PASS ✅**

Dry-run is enforced at the function level, not just the caller. All three purge functions (`purge_call_recordings`, `purge_cases_pii`, `purge_alert_events_pii`) accept a `dry_run` parameter and gate their `DELETE`/`UPDATE` statements behind `if not dry_run`. The `run_purge` function additionally bypasses the `BEGIN EXCLUSIVE` transaction entirely in dry-run mode, making it impossible for any write to occur through unintended code paths.

Test T1 verified: data untouched after dry run.

### 2. Is the transaction atomic?

**PASS ✅**

The script uses `BEGIN EXCLUSIVE` before any mutating operation. All three purge steps execute inside a single transaction. On any exception, `conn.rollback()` is called immediately in the `except` block before re-raising. The `finally` block only writes the audit JSONL (not the database), so partial state is never persisted.

Test T4 verified: simulated mid-purge DB error resulted in full rollback — both `call_recordings` deletion and `cases` redaction were reversed. Exit code 2 returned.

VACUUM runs outside the transaction (correct — VACUUM cannot run inside an explicit transaction). VACUUM failure is non-fatal with a warning log.

### 3. Does the audit log contain any PII?

**PASS ✅**

The `write_audit_jsonl` function writes only:
- Metadata: `run_id`, `timestamp_utc`, `dry_run`, `purge_trigger`, `retention_days`, `cutoff_date`, `status`
- Aggregate counts: `cases_total`, `cases_by_pathway`, `call_recordings_total`, `alert_events_total`
- Error string on failure (from `sqlite3.OperationalError` — contains no patient data)

The `cases_by_pathway` grouping uses `request_type` (pathway name: `prescription`, `sick_note`, etc.) — not patient names or IDs. No patient identifier (name, NHS number, DOB, postcode, phone) appears anywhere in the JSONL output.

The log file (`gdpr_purge.log`) logs: run metadata, table operation counts, and error strings. No patient fields are interpolated into log messages at any level.

Test T5 verified: exhaustive PII string scan of both JSONL and log file — zero matches.

### 4. Is the minimum 30-day floor enforced?

**PASS ✅**

`validate_args()` rejects `--days N` where `N < MIN_RETENTION_DAYS` (30). The check runs before any database connection is opened. Exit code 1 is returned. The rejection is logged with a clear message citing UK GDPR.

The constant `MIN_RETENTION_DAYS = 30` is defined at module level, not buried in logic, making it auditable without tracing call paths.

Test T6 verified: values 0, 1, 15, 29 all rejected with exit code 1.

### 5. Are logs written securely — no patient data in log files?

**PASS ✅**

All `logger.info()` and `logger.error()` calls log only: table names, record counts (integers), run IDs (timestamps), and error messages from `sqlite3` exceptions. No patient field values are ever passed to the logger. The PII fields are defined in `CASES_REDACTION_MAP` (used only in SQL `UPDATE` statements) and are never read back into Python variables.

Log file has no permissions hardening in the script (OS-level file permissions are the correct layer for this — the script creates the directory but does not set permissions). **Note: Recommend ensuring `C:\JeffLocal\logs\gdpr\` is not readable by unauthorised users via Windows ACLs — this is a DevOps Agent task, not a code issue.**

### 6. Purge dependency order

**PASS ✅**

`call_recordings` (child, FK to `cases` via `call_id`) is deleted before `cases` PII is redacted. This is correct dependency order. `audit_events` is never touched — confirmed by code review (no SQL targeting that table).

### 7. Idempotency

**PASS ✅**

The purge queries include `AND patient_name != '[REDACTED - GDPR 90-day retention expired]'` guards. Running twice does not double-process or error. Test T7 confirmed second run reports 0 cases to purge.

### 8. Migration safety

**PASS ✅**

`add_created_at_20260531.sql` uses `ALTER TABLE ... ADD COLUMN` (non-destructive) and back-fills from the existing `timestamp` column. A rollback path is documented. The migration is sandbox-only until Saeed approves production deployment.

---

## Non-Blocking Notes

**N1 — Log directory ACLs:** The script creates `C:\JeffLocal\logs\gdpr\` but does not set restrictive ACLs. Recommend DevOps Agent ensure the directory is accessible only to the service account running the task. This is best handled at OS level, not in the script.

**N2 — Python path in Task Scheduler:** The scheduled task uses `python.exe` without an absolute path. If Python is not on the system PATH of the SYSTEM account, the task will fail silently. DevOps Agent should specify the full path to the Python executable when registering on the production machine.

**N3 — `audit_events` old_values/new_values risk:** The existing `audit_events` table schema stores `old_values` and `new_values` as JSON blobs. If the application writes patient PII into these fields, they will persist permanently (this table is never purged, by design). This is outside the scope of this script but should be reviewed by the Backend Agent to ensure only anonymised field names (not values) are written to `audit_events`. Flagged for follow-up.

---

## Summary

| Criterion | Result |
|-----------|--------|
| Dry-run prevents all writes | ✅ PASS |
| Transaction is atomic | ✅ PASS |
| Audit log contains no PII | ✅ PASS |
| Minimum 30-day floor enforced | ✅ PASS |
| Log files contain no patient data | ✅ PASS |
| Purge dependency order correct | ✅ PASS |
| Idempotent | ✅ PASS |
| Migration safe | ✅ PASS |
| All 7 tests pass | ✅ PASS |

**VERDICT: APPROVED for sandbox use.**
Production deployment requires Saeed sign-off per governance framework (Schema Migration → DataVault → GuardRail → Saeed approval chain).

---

*Reviewed by: Security Agent*
*Date: 2026-05-31*
*Next review: On any modification to gdpr_purge.py*

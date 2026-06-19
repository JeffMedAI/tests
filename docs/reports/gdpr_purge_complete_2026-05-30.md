# GDPR 90-Day Purge — Completion Report
**Agent:** Database Agent
**Date:** 2026-05-31
**Task Rank:** 3 (from phase1_assignments_2026-05-30.md)
**Status:** ✅ COMPLETE — Pending Saeed sign-off for production deployment

---

## Summary

The GDPR 90-day automated data purge system has been designed, implemented, tested, and reviewed for the JeffLocal sandbox. All acceptance criteria are met.

---

## Deliverables

| File | Status |
|------|--------|
| `scripts/daily/gdpr_purge.py` | ✅ Created |
| `scripts/daily/test_gdpr_purge.py` | ✅ Created |
| `scripts/migrations/add_created_at_20260531.sql` | ✅ Created |
| `scripts/register_scheduled_tasks.ps1` | ✅ Updated (Task 4 added) |
| `docs/reports/gdpr_purge_test_2026-05-30.txt` | ✅ Created |
| `docs/compliance/security_review_gdpr_purge_2026-05-30.md` | ✅ Created — APPROVED |
| `logs/gdpr/` | ✅ Directory created |
| `docs/compliance/` | ✅ Directory created |

---

## Schema Analysis

### Tables containing patient PII (GDPR Article 4)

**`cases`** (primary patient data store):
- Identifiers: `patient_name`, `dob`, `postcode`, `callback_number`, `nhs_number`, `emis_number`, `top_candidate_name`, `matched_patient_ref`
- Content: `transcript`, `call_summary`, `open_details`, `ai_summary`, `patient_record_note`
- Date field: `timestamp` TEXT (no `created_at` — migration adds it)

**`call_recordings`**: Recording URLs and file paths are PII-linked (FK: `call_id → cases`). Has `created_at` TEXT.

**`alert_events`**: `first_patient` TEXT field contains patient name. Has `timestamp` TEXT.

### Tables NOT purged

**`audit_events`**: Permanent audit trail — never modified. Contains only call_ids and anonymised staff_ids per design.

**`staff_users`, `sessions`, `auth_reset_tokens`, `staff_invitations`**: Staff/auth infrastructure — not patient PII.

---

## Purge Design

### Strategy: Pseudonymisation (not row deletion)

Per `database_CLAUDE.md`: case rows are preserved for audit trail. PII fields are replaced with standardised redaction markers. This is GDPR Article 4(5) compliant pseudonymisation.

### Operation order (dependency-safe)

1. **`call_recordings`** — DELETE rows (child records, 90+ days old). No FK constraint issues since `cases` rows are not deleted.
2. **`cases`** — REDACT 13 PII fields (row preserved, call_id and pathway stats retained).
3. **`alert_events`** — REDACT `first_patient` field.

All three steps execute inside a single `BEGIN EXCLUSIVE` transaction.

### Redaction markers

| Field type | Marker |
|------------|--------|
| Identifiers (name, DOB, NHS#, etc.) | `[REDACTED - GDPR 90-day retention expired]` |
| Content (transcript, notes, summary) | `[PURGED - GDPR 90-day retention expired]` |

---

## Test Results

```
Ran 7 tests in 0.118s — OK (exit 0)

T1 PASS — Dry run: no data modified, JSONL written
T2 PASS — 89-day record: NOT purged (retention boundary)
T3 PASS — 91-day record: purged (cases redacted, recordings deleted, alert redacted)
T4 PASS — Transaction rollback: mid-purge error → full rollback, exit code 2
T5 PASS — Audit JSONL: zero PII strings detected in log or JSONL
T6 PASS — --days floor: 0, 1, 15, 29 all rejected (exit code 1)
T7 PASS — Idempotent: second run finds 0 records (no double-processing)
```

---

## Security Agent Review

**Verdict: APPROVED** (see `docs/compliance/security_review_gdpr_purge_2026-05-30.md`)

All 8 security criteria passed. Three non-blocking notes raised for follow-up:
- N1: Log directory ACLs (DevOps Agent)
- N2: Absolute Python path in Task Scheduler (DevOps Agent)
- N3: `audit_events` old_values/new_values PII risk (Backend Agent review)

---

## Acceptance Criteria Check

| Criterion | Result |
|-----------|--------|
| Purge script exists and runs correctly | ✅ |
| --dry-run works accurately | ✅ |
| Transaction is atomic (rollback on error) | ✅ |
| All tests pass | ✅ 7/7 |
| Audit log contains NO patient data | ✅ |
| Security Agent review: APPROVED | ✅ |
| Task Scheduler entry added | ✅ |

---

## Production Deployment Gate

This work is **sandbox only**. Production deployment requires:

1. Saeed approval (schema migration on live DB)
2. DevOps Agent to set log directory ACLs (Security Note N1)
3. DevOps Agent to specify absolute Python path in Task Scheduler (Security Note N2)
4. Migration `add_created_at_20260531.sql` run against production DB

**Do not run against `C:\JeffLocal\dashboard\data\dashboard.sqlite` without Saeed's explicit approval in the current session.**

---

## Follow-Up Actions

| Action | Owner | Priority |
|--------|-------|---------|
| Production deployment approval | Saeed | When pilot go-live gates cleared |
| Log directory ACLs | DevOps Agent | Before production |
| Absolute Python path in Task Scheduler | DevOps Agent | Before production |
| Review `audit_events` for PII in old_values | Backend Agent | Medium |
| Multi-tenancy: add `practice_id` filter to purge | Database Agent | Phase 2 |

---

*Database Agent — 2026-05-31*

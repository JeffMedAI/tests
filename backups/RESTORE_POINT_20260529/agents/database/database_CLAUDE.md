# DATABASE AGENT — JeffLocal
# Role: SQLite schema, migrations, query optimisation, data integrity
# Assigned by: Lead Agent
# Reviews by: Security Agent (all schema changes)

---

## SCOPE — OWNS THESE, TOUCHES NOTHING ELSE

```
sandbox\db\schema.sql       ← Canonical schema definition
sandbox\db\migrations\      ← Versioned migration files
sandbox\db\seeds\           ← Fake development data only
sandbox\db\queries\         ← Named query files (reusable)
sandbox\scripts\daily\      ← purge_transcripts.py (90-day rule)
```

## NEVER TOUCHES

```
sandbox\backend\            ← Backend Agent owns application code
sandbox\frontend\           ← Frontend Agent
sandbox\tests\              ← Test Agent
production\db\              ← NEVER — read-only for schema comparison only
Any live tenant DB          ← NEVER operated on by agents

C:\JeffLocal\dashboard\     ← PRODUCTION dashboard — NEVER EDIT without
                               explicit Saeed approval in the current session.
                               SANDBOX is: C:\JeffLocal\sandbox\dashboard\ (port 5000)
                               PRODUCTION is port 8765, watchdog-managed.
```

---

## MULTI-TENANCY SCHEMA RULES

Every table that holds practice-specific data MUST have a `practice_id` column.
This is the foundation of multi-tenancy. No exceptions.

```sql
-- Every tenant-scoped table follows this pattern:
CREATE TABLE work_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    practice_id     TEXT NOT NULL,              -- tenant isolation
    call_id         TEXT NOT NULL UNIQUE,       -- from voice agent
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    status          TEXT NOT NULL DEFAULT 'PENDING',
    priority        TEXT NOT NULL DEFAULT 'ROUTINE',
    category        TEXT,
    summary         TEXT,                       -- Gemma output, not raw transcript
    assigned_to     TEXT,                       -- staff_id, anonymised
    resolved_at     DATETIME,
    FOREIGN KEY (practice_id) REFERENCES practices(id)
);

-- Index every practice_id column — queries always filter by tenant
CREATE INDEX idx_work_items_practice ON work_items(practice_id);
CREATE INDEX idx_work_items_status ON work_items(practice_id, status);
```

### Core Tables

```sql
-- Tenants / practices
CREATE TABLE practices (
    id              TEXT PRIMARY KEY,           -- e.g. 'churchtown', 'practice-002'
    name            TEXT NOT NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    config_path     TEXT,                       -- path to tenant config.json
    active          INTEGER DEFAULT 1
);

-- Staff (per tenant)
CREATE TABLE staff (
    id              TEXT PRIMARY KEY,           -- anonymised: STF-00001
    practice_id     TEXT NOT NULL,
    role            TEXT NOT NULL,             -- 'receptionist', 'admin', 'gp'
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    active          INTEGER DEFAULT 1,
    FOREIGN KEY (practice_id) REFERENCES practices(id)
);

-- Call transcripts (90-day retention, then purged)
CREATE TABLE transcripts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    practice_id     TEXT NOT NULL,
    call_id         TEXT NOT NULL UNIQUE,
    raw_text        TEXT NOT NULL,             -- PURGED after 90 days
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    purge_after     DATETIME,                  -- set to created_at + 90 days
    purged          INTEGER DEFAULT 0,
    FOREIGN KEY (practice_id) REFERENCES practices(id)
);
CREATE INDEX idx_transcripts_purge ON transcripts(purged, purge_after);

-- Audit log (permanent — never purged)
CREATE TABLE audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    practice_id     TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    entity_type     TEXT,
    entity_id       TEXT,
    staff_id        TEXT,                      -- anonymised
    old_value       TEXT,
    new_value       TEXT,
    timestamp       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (practice_id) REFERENCES practices(id)
);
```

---

## TRANSCRIPT PURGE — 90-DAY RULE (GDPR)

```python
# scripts\daily\purge_transcripts.py
# Runs every day at 02:00
# Purges raw transcript text after 90 days
# Retains the row (call_id, timestamps, purged=1) for audit purposes
# NEVER deletes the work_item — only the raw text

import sqlite3
from datetime import datetime, timedelta

def purge_expired_transcripts(db_path: str) -> int:
    """
    Sets raw_text to '[PURGED - 90 day retention expired]' for eligible rows.
    Returns count of rows purged.
    Does NOT delete rows — audit trail must be preserved.
    """
    cutoff = datetime.now() - timedelta(days=90)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        UPDATE transcripts
        SET raw_text = '[PURGED - 90 day retention expired]',
            purged = 1
        WHERE purged = 0
          AND purge_after <= ?
    """, (cutoff.isoformat(),))
    count = cur.rowcount
    conn.commit()
    conn.close()
    return count
```

This script must:
- Log how many rows were purged (count only, no content)
- Write result to reports\daily\{date}.json under key "transcripts_purged"
- Never fail silently — raise and alert if DB is inaccessible

---

## MIGRATION RULES

Every schema change = a new migration file. No exceptions.

```
Naming: db\migrations\{YYYYMMDD_HHMMSS}_{description}.sql
Example: db\migrations\20260528_143000_add_priority_to_work_items.sql

Every migration file contains:
  -- UP (apply change)
  ALTER TABLE work_items ADD COLUMN priority TEXT DEFAULT 'ROUTINE';

  -- DOWN (rollback — REQUIRED)
  -- SQLite note: column removal requires table recreation
  -- Document the rollback steps even if they are complex
```

Before writing any migration:
1. Check current schema in db\schema.sql
2. Write migration
3. Test on a copy of sandbox DB (never the live sandbox DB directly)
4. Update db\schema.sql to reflect new state
5. Write a seed update if needed
6. Confirm with Backend Agent which queries need updating
7. Security Agent reviews before applying

---

## QUERY STANDARDS

All queries: parameterised, named, documented.

```python
# CORRECT
cur.execute(
    "SELECT * FROM work_items WHERE practice_id = ? AND status = ?",
    (practice_id, status)
)

# NEVER
cur.execute(f"SELECT * FROM work_items WHERE practice_id = '{practice_id}'")
```

Named queries live in db\queries\ as .sql files.
Backend Agent imports them — never duplicates query logic.

---

## SEED DATA RULES

```
- Fake patients only: generated names, fake NHS numbers (999-prefix)
- Fake call IDs: CALL-TEST-{sequence}
- Practice ID for sandbox: 'churchtown'
- Never copy or derive seed data from real patient records
- Seed script: db\seeds\churchtown_seed.py
- Reset sandbox to seed state: python db\seeds\reset_sandbox.py
```

---

## DAILY HEALTH CHECKS (owned by this agent)

```python
# scripts\daily\db_health.py
# Checks:
# 1. SQLite integrity check: PRAGMA integrity_check
# 2. Transcript purge overdue (any purge_after < now AND purged = 0)
# 3. DB file size (warn if > 500MB — suggest vacuum)
# 4. Check for orphaned work_items (no matching practice_id)
# Writes results to reports\daily\{date}.json
```

---

## WHAT THIS AGENT NEVER DOES

```
✗ Run DROP TABLE, TRUNCATE, or DELETE without WHERE clause
✗ Touch production or live tenant databases
✗ Apply migrations without Security Agent review
✗ Write raw SQL in application code (queries go in db\queries\)
✗ Delete transcript rows — only purge raw_text content
✗ Store real patient data in seed files
✗ Remove the audit_log table or truncate it
✗ Apply a migration without a documented rollback path
```

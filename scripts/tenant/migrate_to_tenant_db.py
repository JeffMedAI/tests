"""
Multi-tenancy step 3: migrate dashboard.sqlite -> churchtown.sqlite.

governance/MULTI_TENANCY_PROPOSAL.md, sequence table row 3:
"Backup, then migrate dashboard.sqlite -> churchtown.sqlite; verify."
Needs Saeed's explicit sign-off on the day (production DB, data is fake).

Run order:
    1. python scripts/backup/backup_db.py        (existing, unchanged)
    2. python scripts/tenant/migrate_to_tenant_db.py

Uses SQLite's built-in backup API (same approach as backup_db.py) so the copy
is safe to run while the dashboard is live and writing to dashboard.sqlite —
it captures a consistent snapshot without locking out the running app.
Refuses to overwrite an existing destination unless force=True, so a second
accidental run can't clobber a tenant database that already has its own data.
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

log = logging.getLogger(__name__)

DEFAULT_SOURCE = Path(r"C:\JeffLocal\dashboard\data\dashboard.sqlite")
DEFAULT_DEST = Path(r"C:\JeffLocal\dashboard\data\churchtown.sqlite")

# Tables to compare row counts for during verification. Kept explicit rather
# than "all tables" so a schema surprise (e.g. a view) can't silently break
# verification — extend this list if the schema gains a new data table.
VERIFY_TABLES = ["cases", "staff_users", "audit_events"]


def migrate_tenant_db(source_db: Path, dest_db: Path, force: bool = False) -> Path:
    """
    Copy source_db to dest_db using SQLite's backup API.

    Raises FileNotFoundError if source_db does not exist.
    Raises ValueError if source_db and dest_db resolve to the same file.
    Raises FileExistsError if dest_db already exists and force is not True.
    Returns the Path to the destination file.
    """
    if not source_db.exists():
        raise FileNotFoundError(f"Source database not found: {source_db}")

    if source_db.resolve() == dest_db.resolve():
        raise ValueError(
            "source and dest must differ — refusing to overwrite the source database"
        )

    if dest_db.exists():
        if not force:
            raise FileExistsError(
                f"Destination already exists: {dest_db} — pass force=True to overwrite"
            )
        # sqlite3's backup API requires the destination to be a fresh/valid
        # SQLite file, not just an empty connection target — remove it first
        # so a stale or non-SQLite file at dest_db can't break the backup.
        dest_db.unlink()

    dest_db.parent.mkdir(parents=True, exist_ok=True)

    src_conn = sqlite3.connect(source_db)
    try:
        dst_conn = sqlite3.connect(dest_db)
        try:
            src_conn.backup(dst_conn)
            log.info("Migrated %s -> %s", source_db, dest_db)
        finally:
            dst_conn.close()
    finally:
        src_conn.close()

    return dest_db


def _integrity_ok(db_path: Path) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        return result == "ok"
    finally:
        conn.close()


def _table_row_count(db_path: Path, table: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def verify_migration(source_db: Path, dest_db: Path, tables: list[str] | None = None) -> dict:
    """
    Compare source and dest: row counts per table, plus an integrity check
    on both files. Returns a report dict; report["match"] is True only if
    every table's row count matches and both databases pass integrity_check.
    """
    tables = tables if tables is not None else VERIFY_TABLES

    table_reports = {}
    all_match = True
    for table in tables:
        source_count = _table_row_count(source_db, table)
        dest_count = _table_row_count(dest_db, table)
        table_match = source_count == dest_count
        all_match = all_match and table_match
        table_reports[table] = {
            "source": source_count,
            "dest": dest_count,
            "match": table_match,
        }

    source_integrity_ok = _integrity_ok(source_db)
    dest_integrity_ok = _integrity_ok(dest_db)

    return {
        "match": all_match and source_integrity_ok and dest_integrity_ok,
        "tables": table_reports,
        "source_integrity_ok": source_integrity_ok,
        "dest_integrity_ok": dest_integrity_ok,
    }


def run_migration(
    source_db: Path = DEFAULT_SOURCE,
    dest_db: Path = DEFAULT_DEST,
    force: bool = False,
    tables: list[str] | None = None,
) -> dict:
    """
    Run migrate + verify as one step. Returns a dict with keys:
    status ("ok" or "error"), dest_file, verify, error.
    """
    try:
        dest_file = migrate_tenant_db(source_db, dest_db, force=force)
    except Exception as exc:
        log.error("Migration failed: %s", exc)
        return {"status": "error", "dest_file": None, "verify": None, "error": str(exc)}

    try:
        verify_report = verify_migration(source_db, dest_file, tables=tables)
    except Exception as exc:
        log.error("Verification failed: %s", exc)
        return {"status": "error", "dest_file": str(dest_file), "verify": None, "error": str(exc)}

    return {
        "status": "ok",
        "dest_file": str(dest_file),
        "verify": verify_report,
        "error": None,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = run_migration()
    if result["status"] == "ok":
        print(f"OK — migrated to {result['dest_file']}")
        print(f"Verify: {result['verify']}")
        if not result["verify"]["match"]:
            print("WARNING — verification did not match. Do not proceed to step 4.")
            raise SystemExit(1)
    else:
        print(f"ERROR — {result['error']}")
        raise SystemExit(1)

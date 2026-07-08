"""
SQLite backup utility for the JeffLocal dashboard database.

Creates a daily timestamped copy of dashboard.sqlite and prunes backups
older than retention_days. Uses SQLite's built-in backup API for a
consistent hot backup — safe to run while the dashboard is live.

Usage:
    python scripts/backup/backup_db.py

Scheduled via Windows Task Scheduler (daily at 02:00).
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import date, timedelta
from pathlib import Path

log = logging.getLogger(__name__)

DEFAULT_SOURCE = Path(r"C:\JeffLocal\dashboard\data\dashboard.sqlite")
DEFAULT_BACKUP_DIR = Path(r"C:\JeffLocal\backups")
DEFAULT_RETENTION_DAYS = 30


def backup_filename_for_date(d: date) -> str:
    """Return the backup filename for a given date: dashboard_YYYY-MM-DD.sqlite"""
    return f"dashboard_{d.isoformat()}.sqlite"


def create_backup(source_db: Path, backup_dir: Path, backup_date: date) -> Path:
    """
    Copy source_db to backup_dir using SQLite's backup API.

    The SQLite backup API is safe to call while the database is open and
    being written to — it captures a consistent snapshot without locking
    out the running application.

    Returns the Path to the backup file.
    Raises FileNotFoundError if source_db does not exist.
    """
    if not source_db.exists():
        raise FileNotFoundError(f"Source database not found: {source_db}")

    backup_dir.mkdir(parents=True, exist_ok=True)
    dest = backup_dir / backup_filename_for_date(backup_date)

    src_conn = sqlite3.connect(source_db)
    try:
        dst_conn = sqlite3.connect(dest)
        try:
            src_conn.backup(dst_conn)
            log.info("Backup created: %s", dest)
        finally:
            dst_conn.close()
    finally:
        src_conn.close()

    return dest


def prune_old_backups(
    backup_dir: Path,
    retention_days: int,
    today: date | None = None,
) -> int:
    """
    Delete backup files older than retention_days.

    Only touches files matching dashboard_YYYY-MM-DD.sqlite — ignores
    everything else in the directory.

    Returns the count of deleted files.
    """
    if today is None:
        today = date.today()

    cutoff = today - timedelta(days=retention_days)
    pruned = 0

    for f in backup_dir.glob("dashboard_*.sqlite"):
        stem = f.stem  # e.g. "dashboard_2026-06-01"
        date_part = stem.replace("dashboard_", "", 1)
        try:
            file_date = date.fromisoformat(date_part)
        except ValueError:
            continue  # not our naming convention, skip

        if file_date < cutoff:
            f.unlink()
            log.info("Pruned old backup: %s", f)
            pruned += 1

    return pruned


def run_backup(
    source_db: Path = DEFAULT_SOURCE,
    backup_dir: Path = DEFAULT_BACKUP_DIR,
    retention_days: int = DEFAULT_RETENTION_DAYS,
) -> dict:
    """
    Run a full backup cycle: create today's backup then prune old ones.

    Returns a dict with keys: status, backup_file, pruned_count, error.
    status is "ok" or "error".
    """
    today = date.today()

    try:
        backup_file = create_backup(source_db, backup_dir, today)
    except Exception as exc:
        log.error("Backup failed: %s", exc)
        return {
            "status": "error",
            "backup_file": None,
            "pruned_count": 0,
            "error": str(exc),
        }

    pruned = prune_old_backups(backup_dir, retention_days, today)

    return {
        "status": "ok",
        "backup_file": str(backup_file),
        "pruned_count": pruned,
        "retention_days": retention_days,
        "error": None,
    }


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    result = run_backup()
    if result["status"] == "ok":
        print(
            f"OK — backed up to {result['backup_file']} "
            f"(pruned {result['pruned_count']} old backups)"
        )
    else:
        print(f"ERROR — {result['error']}")
        raise SystemExit(1)

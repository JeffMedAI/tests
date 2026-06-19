#!/usr/bin/env python3
"""
gdpr_purge.py — GDPR 90-Day Automated Data Purge
JeffLocal / Avamed — Database Agent
Version: 1.0.0
Date: 2026-05-31

PURPOSE
-------
UK GDPR Article 5(1)(e) — Personal data must not be kept longer than necessary.
This script redacts patient-identifiable fields in the production SQLite database records
older than the configured retention period (default: 90 days, minimum: 30 days).

APPROACH
--------
Rows are NOT deleted. PII fields are replaced with '[REDACTED]' or '[PURGED]'.
This preserves the audit trail (call_id, timestamps, pathway stats) while
eliminating personal data. This is the approved pseudonymisation strategy per
database_CLAUDE.md and GDPR Article 4(5).

TABLES AFFECTED
---------------
  1. call_recordings  — DELETE rows (child of cases, recording URLs are PII-linked)
  2. cases            — REDACT PII fields (keep row for audit trail)
  3. alert_events     — REDACT first_patient field

NEVER PURGED
------------
  audit_events        — Permanent audit trail, never modified
  staff_users         — Staff accounts, not patient PII
  sessions / tokens   — Auth infrastructure

USAGE
-----
  python gdpr_purge.py [--db PATH] [--days N] [--dry-run] [--manual]

FLAGS
-----
  --db PATH       Path to SQLite database (default: production DB)
  --days N        Retention period in days (default: 90, minimum: 30)
  --dry-run       Show what WOULD be purged; make no changes
  --manual        Mark purge_trigger as 'manual' instead of 'scheduled'

OUTPUTS
-------
  Logs:   C:\\JeffLocal\\logs\\gdpr\\gdpr_purge.log
  JSONL:  C:\\JeffLocal\\docs\\compliance\\gdpr_purge_log.jsonl

EXIT CODES
----------
  0  — Success (or dry-run completed)
  1  — Argument error (e.g. --days < 30)
  2  — Database error (transaction rolled back)
  3  — I/O error (log or output file not writable)
"""

import argparse
import json
import logging
import os
import sys
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # C:\JeffLocal
LOG_DIR = REPO_ROOT / "logs" / "gdpr"
LOG_FILE = LOG_DIR / "gdpr_purge.log"
JSONL_FILE = REPO_ROOT / "docs" / "compliance" / "gdpr_purge_log.jsonl"

PRODUCTION_DB = REPO_ROOT / "dashboard" / "data" / "dashboard.sqlite"

# Minimum allowed retention period (days). Hard floor — never lower.
MIN_RETENTION_DAYS = 30

# ---------------------------------------------------------------------------
# PII field definitions
# ---------------------------------------------------------------------------

# Fields in `cases` that constitute personal data under GDPR Article 4.
# These are replaced with the redaction marker on purge.
CASES_PII_FIELDS = [
    "patient_name",
    "dob",
    "postcode",
    "callback_number",
    "nhs_number",
    "emis_number",
    "top_candidate_name",
    "matched_patient_ref",
    "transcript",
    "call_summary",
    "open_details",
    "ai_summary",
    "patient_record_note",
]

REDACTED = "[REDACTED - GDPR 90-day retention expired]"
PURGED   = "[PURGED - GDPR 90-day retention expired]"

# Map each PII field to its redaction value
CASES_REDACTION_MAP = {
    # Identifiers — hard redact
    "patient_name":       REDACTED,
    "dob":                REDACTED,
    "postcode":           REDACTED,
    "callback_number":    REDACTED,
    "nhs_number":         REDACTED,
    "emis_number":        REDACTED,
    "top_candidate_name": REDACTED,
    "matched_patient_ref": REDACTED,
    # Content — purged marker
    "transcript":         PURGED,
    "call_summary":       PURGED,
    "open_details":       PURGED,
    "ai_summary":         PURGED,
    "patient_record_note": PURGED,
}

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

def setup_logging(log_file: Path) -> logging.Logger:
    """Configure file + stderr logging. No patient data ever enters log messages."""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("gdpr_purge")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ"
    )

    # File handler (always DEBUG level)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Stderr handler (INFO and above)
    sh = logging.StreamHandler(sys.stderr)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="GDPR 90-day patient data purge for JeffLocal"
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=PRODUCTION_DB,
        help=f"Path to SQLite database (default: {PRODUCTION_DB})"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=90,
        help=f"Retention period in days (default: 90, minimum: {MIN_RETENTION_DAYS})"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be purged without making any changes"
    )
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Mark this run as manually triggered (vs scheduled)"
    )
    return parser.parse_args(argv)


def validate_args(args, logger: logging.Logger) -> bool:
    """Validate arguments. Returns False and logs error if invalid."""
    if args.days < MIN_RETENTION_DAYS:
        logger.error(
            "REJECTED: --days %d is below the minimum allowed retention period of %d days. "
            "UK GDPR does not permit retention periods shorter than %d days for this system.",
            args.days, MIN_RETENTION_DAYS, MIN_RETENTION_DAYS
        )
        return False

    if not args.db.exists():
        logger.error("Database not found: %s", args.db)
        return False

    return True


# ---------------------------------------------------------------------------
# Pre-purge statistics (no PII — counts only)
# ---------------------------------------------------------------------------

def collect_pre_purge_stats(cur: sqlite3.Cursor, cutoff: str) -> dict:
    """
    Collect aggregate counts of records that will be purged.
    Returns a dict of table -> count. NO patient data is retrieved.
    """
    stats = {}

    # cases: count by request_type (pathway) — aggregate only, no names/IDs
    cur.execute(
        """
        SELECT request_type, COUNT(*) as cnt
        FROM cases
        WHERE (created_at < ? OR (created_at IS NULL AND timestamp < ?))
          AND patient_name != ?
          AND patient_name IS NOT NULL
        GROUP BY request_type
        """,
        (cutoff, cutoff, REDACTED)
    )
    pathway_counts = {row[0] or "unknown": row[1] for row in cur.fetchall()}
    stats["cases_by_pathway"] = pathway_counts
    stats["cases_total"] = sum(pathway_counts.values())

    # call_recordings: count rows to delete
    cur.execute(
        """
        SELECT COUNT(*) FROM call_recordings
        WHERE created_at < ?
        """,
        (cutoff,)
    )
    stats["call_recordings_total"] = cur.fetchone()[0]

    # alert_events: count rows with first_patient set (not already redacted)
    cur.execute(
        """
        SELECT COUNT(*) FROM alert_events
        WHERE timestamp < ?
          AND first_patient IS NOT NULL
          AND first_patient != ?
        """,
        (cutoff, REDACTED)
    )
    stats["alert_events_total"] = cur.fetchone()[0]

    return stats


# ---------------------------------------------------------------------------
# Purge operations (inside transaction)
# ---------------------------------------------------------------------------

def purge_call_recordings(cur: sqlite3.Cursor, cutoff: str, dry_run: bool) -> int:
    """Delete call_recordings rows older than cutoff. Returns count."""
    cur.execute(
        "SELECT COUNT(*) FROM call_recordings WHERE created_at < ?",
        (cutoff,)
    )
    count = cur.fetchone()[0]
    if not dry_run and count > 0:
        cur.execute(
            "DELETE FROM call_recordings WHERE created_at < ?",
            (cutoff,)
        )
    return count


def purge_cases_pii(cur: sqlite3.Cursor, cutoff: str, dry_run: bool) -> int:
    """
    Redact PII fields in cases older than cutoff.
    Rows are NOT deleted — audit trail is preserved.
    Returns count of cases affected.
    """
    # Only count cases where PII has NOT already been redacted (idempotent)
    cur.execute(
        """
        SELECT COUNT(*) FROM cases
        WHERE (created_at < ? OR (created_at IS NULL AND timestamp < ?))
          AND patient_name != ?
          AND patient_name IS NOT NULL
        """,
        (cutoff, cutoff, REDACTED)
    )
    count = cur.fetchone()[0]

    if not dry_run and count > 0:
        # Build SET clause dynamically from redaction map
        set_clauses = ", ".join(f"{col} = ?" for col in CASES_REDACTION_MAP)
        values = list(CASES_REDACTION_MAP.values())
        values += [cutoff, cutoff, REDACTED]

        cur.execute(
            f"""
            UPDATE cases
            SET {set_clauses}
            WHERE (created_at < ? OR (created_at IS NULL AND timestamp < ?))
              AND patient_name != ?
              AND patient_name IS NOT NULL
            """,
            values
        )

    return count


def purge_alert_events_pii(cur: sqlite3.Cursor, cutoff: str, dry_run: bool) -> int:
    """
    Redact first_patient field in alert_events older than cutoff.
    Returns count of rows affected.
    """
    cur.execute(
        """
        SELECT COUNT(*) FROM alert_events
        WHERE timestamp < ?
          AND first_patient IS NOT NULL
          AND first_patient != ?
        """,
        (cutoff, REDACTED)
    )
    count = cur.fetchone()[0]

    if not dry_run and count > 0:
        cur.execute(
            """
            UPDATE alert_events
            SET first_patient = ?
            WHERE timestamp < ?
              AND first_patient IS NOT NULL
              AND first_patient != ?
            """,
            (REDACTED, cutoff, REDACTED)
        )

    return count


# ---------------------------------------------------------------------------
# Audit log entry (no PII)
# ---------------------------------------------------------------------------

def write_audit_jsonl(
    jsonl_path: Path,
    run_id: str,
    dry_run: bool,
    purge_trigger: str,
    cutoff_date: str,
    retention_days: int,
    pre_stats: dict,
    results: dict,
    status: str,
    error_msg: str = None,
):
    """
    Append one JSON line to the GDPR purge audit log.
    CRITICAL: No patient data (names, NHS numbers, DOBs etc.) is ever written here.
    Only aggregate counts and metadata are recorded.
    """
    entry = {
        "run_id": run_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "purge_trigger": purge_trigger,
        "retention_days": retention_days,
        "cutoff_date": cutoff_date,
        "status": status,
        "pre_purge_counts": {
            "cases_total": pre_stats.get("cases_total", 0),
            "cases_by_pathway": pre_stats.get("cases_by_pathway", {}),
            "call_recordings_total": pre_stats.get("call_recordings_total", 0),
            "alert_events_total": pre_stats.get("alert_events_total", 0),
        },
        "purged_counts": results,
    }
    if error_msg:
        entry["error"] = error_msg

    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Main purge orchestration
# ---------------------------------------------------------------------------

def run_purge(args, logger: logging.Logger) -> int:
    """
    Execute the full purge workflow.
    Returns exit code: 0=success, 2=db error, 3=io error.
    """
    run_id = datetime.now(timezone.utc).strftime("PURGE-%Y%m%d-%H%M%S")
    purge_trigger = "manual" if args.manual else "scheduled"
    dry_run = args.dry_run

    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=args.days)
    cutoff_str = cutoff_dt.strftime("%Y-%m-%d %H:%M:%S")

    logger.info("=" * 60)
    logger.info("GDPR Purge run started | run_id=%s", run_id)
    logger.info("dry_run=%s | trigger=%s | retention=%d days | cutoff=%s",
                dry_run, purge_trigger, args.days, cutoff_str)
    logger.info("Database: %s", args.db)

    if dry_run:
        logger.info("DRY RUN MODE — no data will be modified")

    pre_stats = {}
    results = {}
    status = "error"
    error_msg = None

    conn = None
    try:
        conn = sqlite3.connect(str(args.db))
        conn.execute("PRAGMA journal_mode=WAL")
        cur = conn.cursor()

        # --- Pre-purge stats (outside transaction — read-only) ---
        pre_stats = collect_pre_purge_stats(cur, cutoff_str)
        logger.info(
            "Pre-purge counts: cases=%d | call_recordings=%d | alert_events=%d",
            pre_stats.get("cases_total", 0),
            pre_stats.get("call_recordings_total", 0),
            pre_stats.get("alert_events_total", 0),
        )

        if dry_run:
            # Dry run: report counts and exit without touching anything
            logger.info("DRY RUN complete. Nothing was modified.")
            results = {
                "cases_would_redact": pre_stats.get("cases_total", 0),
                "call_recordings_would_delete": pre_stats.get("call_recordings_total", 0),
                "alert_events_would_redact": pre_stats.get("alert_events_total", 0),
            }
            status = "dry_run_ok"
        else:
            # --- ATOMIC TRANSACTION ---
            conn.execute("BEGIN EXCLUSIVE")

            try:
                # Step 1: Delete child rows (call_recordings) before touching cases
                rec_count = purge_call_recordings(cur, cutoff_str, dry_run=False)
                logger.info("call_recordings deleted: %d", rec_count)

                # Step 2: Redact PII in cases (row preserved, fields cleared)
                cases_count = purge_cases_pii(cur, cutoff_str, dry_run=False)
                logger.info("cases redacted: %d", cases_count)

                # Step 3: Redact first_patient in alert_events
                alert_count = purge_alert_events_pii(cur, cutoff_str, dry_run=False)
                logger.info("alert_events redacted: %d", alert_count)

                conn.commit()
                logger.info("Transaction committed successfully.")

                results = {
                    "cases_redacted": cases_count,
                    "call_recordings_deleted": rec_count,
                    "alert_events_redacted": alert_count,
                }
                status = "success"

            except Exception as db_err:
                conn.rollback()
                error_msg = str(db_err)
                logger.error(
                    "Transaction ROLLED BACK due to error: %s", error_msg
                )
                raise

            # --- VACUUM (outside transaction — reclaim disk space) ---
            try:
                logger.info("Running VACUUM...")
                conn.execute("VACUUM")
                logger.info("VACUUM complete.")
            except Exception as vac_err:
                # VACUUM failure is non-fatal — log and continue
                logger.warning("VACUUM failed (non-fatal): %s", vac_err)

    except sqlite3.Error as e:
        error_msg = str(e)
        logger.error("Database error: %s", error_msg)
        status = "error"
        return 2

    except OSError as e:
        error_msg = str(e)
        logger.error("I/O error: %s", error_msg)
        status = "error"
        return 3

    finally:
        if conn:
            conn.close()

        # Always write audit JSONL (even on failure — records the attempt)
        try:
            write_audit_jsonl(
                jsonl_path=JSONL_FILE,
                run_id=run_id,
                dry_run=dry_run,
                purge_trigger=purge_trigger,
                cutoff_date=cutoff_str,
                retention_days=args.days,
                pre_stats=pre_stats,
                results=results,
                status=status,
                error_msg=error_msg,
            )
            logger.info("Audit entry written: %s", JSONL_FILE)
        except Exception as log_err:
            logger.error("Failed to write audit JSONL: %s", log_err)

        logger.info("Run complete | status=%s | run_id=%s", status, run_id)
        logger.info("=" * 60)

    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    # Set up logging first (needed even for argument errors)
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"ERROR: Cannot create log directory {LOG_DIR}: {e}", file=sys.stderr)
        return 3

    logger = setup_logging(LOG_FILE)

    args = parse_args(argv)

    if not validate_args(args, logger):
        return 1

    return run_purge(args, logger)


if __name__ == "__main__":
    sys.exit(main())

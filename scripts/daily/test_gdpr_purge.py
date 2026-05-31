#!/usr/bin/env python3
"""
test_gdpr_purge.py — GDPR Purge Script Test Suite
JeffLocal / Avamed — Database Agent / Test Agent
Date: 2026-05-31

Runs against a TEMPORARY in-memory copy of the schema.
Never touches sandbox or production databases.

Test cases:
  T1 — Dry run: no data deleted, correct counts reported
  T2 — 89-day-old record: NOT purged (boundary check)
  T3 — 91-day-old record: IS purged (boundary check)
  T4 — Transaction rollback on DB error: no partial deletion
  T5 — Audit JSONL written correctly, contains no PII
  T6 — --days floor: values < 30 rejected with exit code 1
"""

import json
import os
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

# Add scripts/daily to path so we can import gdpr_purge
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gdpr_purge


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_db(tmp_path: Path) -> Path:
    """Create a minimal test database with the required schema and seed data."""
    db_path = tmp_path / "test.sqlite"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE cases (
            call_id TEXT PRIMARY KEY,
            timestamp TEXT,
            created_at TEXT,
            request_type TEXT,
            patient_name TEXT,
            dob TEXT,
            postcode TEXT,
            callback_number TEXT,
            nhs_number TEXT,
            emis_number TEXT,
            top_candidate_name TEXT,
            matched_patient_ref TEXT,
            transcript TEXT,
            call_summary TEXT,
            open_details TEXT,
            ai_summary TEXT,
            patient_record_note TEXT,
            status TEXT DEFAULT 'PENDING',
            priority TEXT DEFAULT 'ROUTINE'
        );

        CREATE TABLE call_recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT NOT NULL,
            recording_url TEXT,
            recording_local_path TEXT,
            recording_received_at TEXT NOT NULL,
            recording_status TEXT NOT NULL DEFAULT 'available',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE alert_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT NOT NULL UNIQUE,
            timestamp TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            first_patient TEXT,
            dedupe_key TEXT NOT NULL
        );

        CREATE TABLE audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            call_id TEXT NOT NULL,
            action TEXT NOT NULL,
            changed_fields TEXT NOT NULL DEFAULT '{}',
            old_values TEXT NOT NULL DEFAULT '{}',
            new_values TEXT NOT NULL DEFAULT '{}'
        );
    """)
    conn.commit()
    conn.close()
    return db_path


def insert_case(conn, call_id, days_ago, patient_name="Test Patient"):
    """Insert a case record with a timestamp days_ago days in the past."""
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """INSERT INTO cases
           (call_id, timestamp, created_at, request_type, patient_name, dob,
            postcode, callback_number, nhs_number, emis_number,
            top_candidate_name, matched_patient_ref,
            transcript, call_summary, open_details, ai_summary, patient_record_note)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (call_id, ts, ts, "prescription", patient_name, "01/01/1980",
         "PR8 1AA", "07700900001", "999-123-4567", "EMIS-001",
         patient_name, "REF-001",
         "full transcript text", "call summary text", "open details text",
         "ai summary", "patient note")
    )
    conn.commit()


def insert_recording(conn, call_id, days_ago):
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """INSERT INTO call_recordings
           (call_id, recording_url, recording_local_path, recording_received_at,
            created_at, updated_at)
           VALUES (?,?,?,?,?,?)""",
        (call_id, "http://example.com/rec.mp3", "/data/rec.mp3", ts, ts, ts)
    )
    conn.commit()


def insert_alert(conn, alert_id, days_ago, first_patient="Test Patient"):
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT INTO alert_events (alert_id, timestamp, alert_type, first_patient, dedupe_key) VALUES (?,?,?,?,?)",
        (alert_id, ts, "HIGH_PRIORITY", first_patient, f"key-{alert_id}")
    )
    conn.commit()


def run_purge_with_args(argv, db_path, jsonl_path, log_path):
    """Patch paths and run purge. Returns exit code."""
    with patch.object(gdpr_purge, "SANDBOX_DB", db_path), \
         patch.object(gdpr_purge, "JSONL_FILE", jsonl_path), \
         patch.object(gdpr_purge, "LOG_FILE", log_path), \
         patch.object(gdpr_purge, "LOG_DIR", log_path.parent):
        return gdpr_purge.main(argv)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class TestGDPRPurge(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.tmp.name)
        self.db_path = make_db(self.tmp_path)
        self.jsonl_path = self.tmp_path / "gdpr_purge_log.jsonl"
        self.log_path = self.tmp_path / "gdpr_purge.log"

    def tearDown(self):
        self.tmp.cleanup()

    # -----------------------------------------------------------------------
    # T1: Dry run — no data deleted, correct counts reported
    # -----------------------------------------------------------------------
    def test_T1_dry_run_no_changes(self):
        conn = sqlite3.connect(str(self.db_path))
        insert_case(conn, "CALL-DRY-001", days_ago=100)
        insert_recording(conn, "CALL-DRY-001", days_ago=100)
        conn.close()

        exit_code = run_purge_with_args(
            ["--dry-run", "--db", str(self.db_path)],
            self.db_path, self.jsonl_path, self.log_path
        )
        self.assertEqual(exit_code, 0, "Dry run should exit 0")

        # Verify data untouched
        conn = sqlite3.connect(str(self.db_path))
        row = conn.execute("SELECT patient_name FROM cases WHERE call_id='CALL-DRY-001'").fetchone()
        self.assertEqual(row[0], "Test Patient", "Dry run must not modify patient_name")

        rec = conn.execute("SELECT COUNT(*) FROM call_recordings").fetchone()[0]
        self.assertEqual(rec, 1, "Dry run must not delete recordings")
        conn.close()

        # Verify audit JSONL reports the count
        self.assertTrue(self.jsonl_path.exists(), "JSONL audit log must be written on dry run")
        with open(self.jsonl_path) as f:
            entry = json.loads(f.readline())
        self.assertTrue(entry["dry_run"], "JSONL must record dry_run=true")
        self.assertEqual(entry["status"], "dry_run_ok")
        self.assertGreater(entry["pre_purge_counts"]["cases_total"], 0,
                           "Pre-purge count must be > 0")

    # -----------------------------------------------------------------------
    # T2: 89-day-old record — NOT purged
    # -----------------------------------------------------------------------
    def test_T2_89_day_record_not_purged(self):
        conn = sqlite3.connect(str(self.db_path))
        insert_case(conn, "CALL-89D-001", days_ago=89)
        conn.close()

        exit_code = run_purge_with_args(
            ["--db", str(self.db_path), "--days", "90"],
            self.db_path, self.jsonl_path, self.log_path
        )
        self.assertEqual(exit_code, 0)

        conn = sqlite3.connect(str(self.db_path))
        row = conn.execute("SELECT patient_name FROM cases WHERE call_id='CALL-89D-001'").fetchone()
        self.assertEqual(row[0], "Test Patient",
                         "89-day-old record must NOT be redacted with 90-day retention")
        conn.close()

    # -----------------------------------------------------------------------
    # T3: 91-day-old record — IS purged
    # -----------------------------------------------------------------------
    def test_T3_91_day_record_is_purged(self):
        conn = sqlite3.connect(str(self.db_path))
        insert_case(conn, "CALL-91D-001", days_ago=91)
        insert_recording(conn, "CALL-91D-001", days_ago=91)
        insert_alert(conn, "ALERT-91D-001", days_ago=91)
        conn.close()

        exit_code = run_purge_with_args(
            ["--db", str(self.db_path), "--days", "90"],
            self.db_path, self.jsonl_path, self.log_path
        )
        self.assertEqual(exit_code, 0)

        conn = sqlite3.connect(str(self.db_path))

        # Case: row exists but PII fields redacted
        row = conn.execute(
            "SELECT patient_name, nhs_number, transcript FROM cases WHERE call_id='CALL-91D-001'"
        ).fetchone()
        self.assertIsNotNone(row, "Case row must still exist (audit trail preserved)")
        self.assertEqual(row[0], gdpr_purge.REDACTED, "patient_name must be redacted")
        self.assertEqual(row[1], gdpr_purge.REDACTED, "nhs_number must be redacted")
        self.assertEqual(row[2], gdpr_purge.PURGED, "transcript must be purged")

        # call_recordings: row deleted
        rec = conn.execute(
            "SELECT COUNT(*) FROM call_recordings WHERE call_id='CALL-91D-001'"
        ).fetchone()[0]
        self.assertEqual(rec, 0, "call_recordings row must be deleted")

        # alert_events: first_patient redacted
        alert = conn.execute(
            "SELECT first_patient FROM alert_events WHERE alert_id='ALERT-91D-001'"
        ).fetchone()
        self.assertEqual(alert[0], gdpr_purge.REDACTED, "alert first_patient must be redacted")

        conn.close()

    # -----------------------------------------------------------------------
    # T4: Transaction rollback — no partial deletion on DB error
    # -----------------------------------------------------------------------
    def test_T4_transaction_rollback_on_error(self):
        conn = sqlite3.connect(str(self.db_path))
        insert_case(conn, "CALL-ERR-001", days_ago=100)
        insert_recording(conn, "CALL-ERR-001", days_ago=100)
        conn.close()

        # Patch purge_alert_events_pii to raise an exception mid-transaction
        original_alert_fn = gdpr_purge.purge_alert_events_pii

        def exploding_alert_purge(cur, cutoff, dry_run):
            raise sqlite3.OperationalError("Simulated DB error mid-purge")

        with patch.object(gdpr_purge, "purge_alert_events_pii", exploding_alert_purge):
            exit_code = run_purge_with_args(
                ["--db", str(self.db_path), "--days", "90"],
                self.db_path, self.jsonl_path, self.log_path
            )

        self.assertEqual(exit_code, 2, "DB error must return exit code 2")

        # Verify rollback: call_recordings row must still exist
        conn = sqlite3.connect(str(self.db_path))
        rec_count = conn.execute(
            "SELECT COUNT(*) FROM call_recordings WHERE call_id='CALL-ERR-001'"
        ).fetchone()[0]
        self.assertEqual(rec_count, 1,
                         "Rollback: call_recordings must be unchanged after DB error")

        # Verify rollback: case PII must still be intact
        row = conn.execute(
            "SELECT patient_name FROM cases WHERE call_id='CALL-ERR-001'"
        ).fetchone()
        self.assertEqual(row[0], "Test Patient",
                         "Rollback: patient_name must be unchanged after DB error")
        conn.close()

        # Verify error recorded in JSONL
        self.assertTrue(self.jsonl_path.exists())
        with open(self.jsonl_path) as f:
            entry = json.loads(f.readline())
        self.assertEqual(entry["status"], "error")
        self.assertIn("error", entry)

    # -----------------------------------------------------------------------
    # T5: Audit JSONL written correctly — no PII in log
    # -----------------------------------------------------------------------
    def test_T5_audit_log_no_pii(self):
        conn = sqlite3.connect(str(self.db_path))
        insert_case(conn, "CALL-AUDIT-001", days_ago=95, patient_name="Jane Smith")
        conn.close()

        run_purge_with_args(
            ["--db", str(self.db_path), "--days", "90"],
            self.db_path, self.jsonl_path, self.log_path
        )

        self.assertTrue(self.jsonl_path.exists())
        with open(self.jsonl_path) as f:
            entry = json.loads(f.readline())

        # Check required fields exist
        self.assertIn("run_id", entry)
        self.assertIn("timestamp_utc", entry)
        self.assertIn("retention_days", entry)
        self.assertIn("cutoff_date", entry)
        self.assertIn("pre_purge_counts", entry)
        self.assertIn("purged_counts", entry)

        # Verify NO PII in the entire serialised entry
        entry_str = json.dumps(entry)
        pii_strings = [
            "Jane Smith", "01/01/1980", "PR8 1AA", "07700900001",
            "999-123-4567", "EMIS-001", "full transcript text",
            "call summary text", "open details text", "ai summary",
            "patient note", "REF-001"
        ]
        for pii in pii_strings:
            self.assertNotIn(pii, entry_str,
                             f"PII '{pii}' must not appear in audit log")

        # Verify log file also contains no PII
        log_content = self.log_path.read_text(encoding="utf-8")
        for pii in pii_strings:
            self.assertNotIn(pii, log_content,
                             f"PII '{pii}' must not appear in log file")

    # -----------------------------------------------------------------------
    # T6: --days minimum floor — values < 30 rejected
    # -----------------------------------------------------------------------
    def test_T6_days_minimum_floor_rejected(self):
        for bad_days in [0, 1, 15, 29]:
            with self.subTest(days=bad_days):
                exit_code = run_purge_with_args(
                    ["--db", str(self.db_path), "--days", str(bad_days)],
                    self.db_path, self.jsonl_path, self.log_path
                )
                self.assertEqual(exit_code, 1,
                                 f"--days {bad_days} must be rejected with exit code 1")

    # -----------------------------------------------------------------------
    # T7: Idempotency — running twice does not double-redact or error
    # -----------------------------------------------------------------------
    def test_T7_idempotent_second_run(self):
        conn = sqlite3.connect(str(self.db_path))
        insert_case(conn, "CALL-IDEM-001", days_ago=100)
        conn.close()

        for run in range(2):
            exit_code = run_purge_with_args(
                ["--db", str(self.db_path), "--days", "90"],
                self.db_path, self.jsonl_path, self.log_path
            )
            self.assertEqual(exit_code, 0, f"Run {run+1} should succeed")

        # After second run, counts in JSONL for second run should show 0 affected
        with open(self.jsonl_path) as f:
            lines = f.readlines()
        second_entry = json.loads(lines[1])
        self.assertEqual(second_entry["pre_purge_counts"]["cases_total"], 0,
                         "Second run should find 0 records to purge (idempotent)")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestGDPRPurge)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)

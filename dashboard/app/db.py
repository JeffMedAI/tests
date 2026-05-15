from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "dashboard.sqlite"


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cases (
            call_id TEXT PRIMARY KEY,
            open_details TEXT,
            timestamp TEXT,
            call_timestamp_sort REAL,
            request_type TEXT,
            patient_name TEXT,
            dob TEXT,
            postcode TEXT,
            gender TEXT,
            age INTEGER,
            callback_number TEXT,
            verification_status TEXT,
            verification_reason TEXT,
            matched_patient_ref TEXT,
            emis_number TEXT,
            nhs_number TEXT,
            top_candidate_name TEXT,
            priority TEXT,
            safe_to_queue INTEGER,
            task_title TEXT,
            task_body TEXT,
            staff_task_title TEXT,
            staff_task_body TEXT,
            transcript TEXT,
            call_summary TEXT,
            ai_summary TEXT,
            patient_record_note TEXT,
            call_duration_seconds INTEGER,
            caller_sentiment TEXT,
            caller_difficulty TEXT,
            transcript_quality TEXT,
            handoff_confidence TEXT,
            extraction_confidence TEXT,
            staff_review_required INTEGER,
            red_flags_present INTEGER,
            status TEXT,
            assigned_to TEXT,
            action_needed TEXT,
            outcome_notes TEXT,
            staff_action TEXT,
            resolved_at TEXT,
            resolved_by TEXT,
            last_updated TEXT,
            last_edited_at TEXT,
            last_edited_by TEXT,
            turnaround_minutes INTEGER,
            source_path TEXT,
            source_file_mtime TEXT,
            imported_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            call_id TEXT NOT NULL,
            action TEXT NOT NULL,
            edited_by TEXT,
            changed_fields TEXT NOT NULL,
            old_values TEXT NOT NULL,
            new_values TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS alert_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id TEXT NOT NULL UNIQUE,
            timestamp TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT,
            count INTEGER,
            message TEXT,
            first_call_id TEXT,
            first_patient TEXT,
            first_priority TEXT,
            source_workflow TEXT,
            dedupe_key TEXT NOT NULL,
            acknowledged_at TEXT,
            acknowledged_by TEXT,
            acknowledgement_source TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS staff_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL CHECK(role IN ('admin', 'staff', 'readonly')),
            demo_pin_hash TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS staff_invitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'staff', 'readonly')),
            invited_by_staff_id INTEGER,
            token_hash TEXT,
            status TEXT NOT NULL CHECK(status IN ('pending', 'accepted', 'cancelled', 'expired')),
            created_at TEXT NOT NULL,
            expires_at TEXT,
            accepted_at TEXT,
            cancelled_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS call_recordings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id TEXT NOT NULL,
            recording_url TEXT,
            recording_local_path TEXT,
            recording_received_at TEXT NOT NULL,
            recording_duration_seconds INTEGER,
            recording_status TEXT NOT NULL CHECK(recording_status IN ('pending', 'available', 'unavailable', 'failed')),
            recording_metadata_json TEXT,
            attached_by TEXT,
            source TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(cases)").fetchall()
    }
    if "source_file_mtime" not in columns:
        conn.execute("ALTER TABLE cases ADD COLUMN source_file_mtime TEXT")
    if "call_timestamp_sort" not in columns:
        conn.execute("ALTER TABLE cases ADD COLUMN call_timestamp_sort REAL")
    for column, definition in {
        "gender": "TEXT",
        "age": "INTEGER",
        "staff_task_title": "TEXT",
        "staff_task_body": "TEXT",
        "ai_summary": "TEXT",
        "patient_record_note": "TEXT",
    }.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE cases ADD COLUMN {column} {definition}")
    alert_columns = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(alert_events)").fetchall()
    }
    for column in ("acknowledged_at", "acknowledged_by", "acknowledgement_source"):
        if column not in alert_columns:
            conn.execute(f"ALTER TABLE alert_events ADD COLUMN {column} TEXT")
    staff_count = conn.execute("SELECT COUNT(*) FROM staff_users").fetchone()[0]
    if staff_count == 0:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        conn.executemany(
            """
            INSERT INTO staff_users (display_name, email, role, demo_pin_hash, active, created_at, updated_at)
            VALUES (?, ?, ?, ?, 1, ?, ?)
            """,
            [
                ("Admin Demo", None, "admin", None, now, now),
                ("Reception Demo", None, "staff", None, now, now),
                ("GP Demo", None, "readonly", None, now, now),
            ],
        )
    conn.commit()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}

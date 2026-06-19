from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import utc_now_iso


ROOT_DIR = Path(__file__).resolve().parents[2]
AUDIT_DIR = ROOT_DIR / "logs" / "audits"


def write_audit_event(
    conn: sqlite3.Connection,
    call_id: str,
    action: str,
    edited_by: str,
    changed_fields: list[str],
    old_values: dict[str, Any],
    new_values: dict[str, Any],
) -> None:
    timestamp = utc_now_iso()
    payload = {
        "timestamp": timestamp,
        "call_id": call_id,
        "action": action,
        "edited_by": edited_by,
        "changed_fields": changed_fields,
        "old_values": old_values,
        "new_values": new_values,
    }
    conn.execute(
        """
        INSERT INTO audit_events (
            timestamp, call_id, action, edited_by, changed_fields, old_values, new_values
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            timestamp,
            call_id,
            action,
            edited_by,
            json.dumps(changed_fields, sort_keys=True),
            json.dumps(old_values, sort_keys=True),
            json.dumps(new_values, sort_keys=True),
        ),
    )
    conn.commit()

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    jsonl_path = AUDIT_DIR / f"dashboard_audit_{timestamp[:10]}.jsonl"
    with jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")

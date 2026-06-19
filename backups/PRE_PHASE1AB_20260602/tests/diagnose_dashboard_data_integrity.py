from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_ROOT = ROOT / "dashboard"
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from app.db import DB_PATH, connect, init_db

HANDOFF_DIR = ROOT / "outputs" / "handoff_json"
EXPECTED_PATH = ROOT / "tests" / "fixtures" / "expected_raw_intake_mock_outcomes.json"

FIELDS = [
    "request_type",
    "priority",
    "safe_to_queue",
    "staff_review_required",
    "red_flags_present",
    "verification_status",
]


def as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def load_handoff(call_id: str) -> dict:
    path = HANDOFF_DIR / f"{call_id}_handoff.json"
    return json.loads(path.read_text(encoding="utf-8-sig"))


def expected_value(expected: dict, field: str):
    return expected.get(f"expected_{field}")


def comparable(value: object, field: str):
    if field in {"safe_to_queue", "staff_review_required", "red_flags_present"}:
        return as_bool(value)
    return value


def main() -> int:
    expected = json.loads(EXPECTED_PATH.read_text(encoding="utf-8-sig"))
    with connect(DB_PATH) as conn:
        init_db(conn)
        rows = {
            row["call_id"]: row
            for row in conn.execute(
                "SELECT call_id, request_type, priority, safe_to_queue, staff_review_required, red_flags_present, verification_status FROM cases WHERE call_id LIKE 'RAWMOCK-%'"
            ).fetchall()
        }

    mismatches = []
    print("call_id,field,expected,handoff,dashboard")
    for call_id in sorted(expected):
        handoff = load_handoff(call_id)
        dashboard = rows.get(call_id)
        if dashboard is None:
            mismatches.append((call_id, "row", "present", "present", "missing"))
            print(f"{call_id},row,present,present,missing")
            continue
        for field in FIELDS:
            expected_raw = expected_value(expected[call_id], field)
            handoff_raw = handoff.get(field)
            dashboard_raw = dashboard[field]
            expected_cmp = comparable(expected_raw, field)
            handoff_cmp = comparable(handoff_raw, field)
            dashboard_cmp = comparable(dashboard_raw, field)
            print(f"{call_id},{field},{expected_raw},{handoff_raw},{dashboard_raw}")
            if expected_cmp != handoff_cmp or handoff_cmp != dashboard_cmp:
                mismatches.append((call_id, field, expected_raw, handoff_raw, dashboard_raw))

    if mismatches:
        print("\nMISMATCHES")
        for item in mismatches:
            print(item)
        return 1

    print("\nDashboard data integrity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

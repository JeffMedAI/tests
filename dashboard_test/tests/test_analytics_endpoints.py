"""Regression tests for the Clarity analytics endpoints (tech-debt item B1).

Both endpoints queried things that do not exist on the ``cases`` table:
  * ``created_at`` — not a column on ``cases`` (it lives on staff_users/sessions)
  * ``dashboard_imports`` — a table that is never created in the schema

So in production both endpoints raised ``OperationalError`` and returned 500.
These tests pin the corrected behaviour: they must return 200 and count
today's cases.
"""
from datetime import datetime, timezone
from pathlib import Path
import sys

DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from fastapi.testclient import TestClient

import app.audit as audit_module
import app.db as db_module
import app.main as main_module
from app.db import connect, init_db
from app.importer import map_handoff_to_case, upsert_case
from app.main import SESSION_COOKIE, app

# Accepted by the autouse `_bypass_session_lookup` fixture in conftest.py,
# which resolves it to an admin staff user (not a demo fallback).
_TOKEN = "jefflocal-test-bypass-x"


def _today_iso(hour: int = 12, minute: int = 0) -> str:
    return (
        datetime.now(timezone.utc)
        .replace(hour=hour, minute=minute, second=0, microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _make_case(call_id: str, *, red_flags_present: bool = False, priority: str = "routine") -> dict:
    return map_handoff_to_case(
        {
            "call_id": call_id,
            "call_timestamp": _today_iso(),
            "request_type": "admin",
            "normalized_input": {
                "patient_name": f"Patient {call_id}",
                "dob": "1970-01-01",
                "postcode": "PR9 7LT",
                "callback_number": "07111000000",
            },
            "verification_status": "matched",
            "priority": priority,
            "safe_to_queue": True,
            "task_title": f"Task {call_id}",
            "task_body": "Test task",
            "raw_transcript": "Test transcript",
            "call_summary": "Test summary",
            "red_flags_present": red_flags_present,
            "status": "New",
        }
    )


def _setup_db(tmp_path, monkeypatch) -> Path:
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "ALERT_DIR", tmp_path / "alerts")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
    return db_path


def _client() -> TestClient:
    # raise_server_exceptions=False so a 500 surfaces as a response we can
    # assert on, rather than re-raising inside the test.
    return TestClient(app, cookies={SESSION_COOKIE: _TOKEN}, raise_server_exceptions=False)


def test_hourly_volume_counts_todays_cases(tmp_path, monkeypatch):
    db_path = _setup_db(tmp_path, monkeypatch)
    with connect(db_path) as conn:
        upsert_case(conn, _make_case("ANALYTICS-HV-1"))
        upsert_case(conn, _make_case("ANALYTICS-HV-2"))

    resp = _client().get("/api/analytics/hourly-volume")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert len(body["hours"]) == 24
    assert sum(h["count"] for h in body["hours"]) == 2


def test_performance_summary_reports_todays_kpis(tmp_path, monkeypatch):
    db_path = _setup_db(tmp_path, monkeypatch)
    with connect(db_path) as conn:
        upsert_case(conn, _make_case("ANALYTICS-PS-1"))
        upsert_case(conn, _make_case("ANALYTICS-PS-RED", red_flags_present=True, priority="999 Emergency"))

    resp = _client().get("/api/analytics/performance-summary")

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["cases_today"] == 2
    assert body["red_flags_today"] == 1
    assert body["throughput_last_hour"] >= 2

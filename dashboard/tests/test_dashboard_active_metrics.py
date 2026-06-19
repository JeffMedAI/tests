from datetime import datetime, timedelta, timezone
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
from app.main import app


def iso_days_ago(days: int, hour: int = 12, minute: int = 0) -> str:
    value = datetime.now(timezone.utc) - timedelta(days=days)
    value = value.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def make_case(
    call_id: str,
    *,
    status: str = "New",
    priority: str = "routine",
    request_type: str = "admin",
    verification_status: str = "matched",
    staff_review_required: bool = False,
    red_flags_present: bool = False,
    assigned_to: str = "",
    resolved_at: str = "",
    resolved_by: str = "",
) -> dict:
    case = map_handoff_to_case(
        {
            "call_id": call_id,
            "call_timestamp": iso_days_ago(0),
            "request_type": request_type,
            "normalized_input": {
                "patient_name": f"Patient {call_id}",
                "dob": "1970-01-01",
                "postcode": "PR9 7LT",
                "callback_number": "07111000000",
            },
            "verification_status": verification_status,
            "verification_reason": "test",
            "priority": priority,
            "safe_to_queue": True,
            "task_title": f"Task {call_id}",
            "task_body": "Test task",
            "raw_transcript": "Test transcript",
            "call_summary": "Test summary",
            "staff_review_required": staff_review_required,
            "red_flags_present": red_flags_present,
            "status": status,
            "assigned_to": assigned_to,
            "resolved_at": resolved_at,
            "resolved_by": resolved_by,
        }
    )
    case["assigned_to"] = assigned_to
    case["resolved_at"] = resolved_at
    case["resolved_by"] = resolved_by
    return case


def metric_value(cards: list[dict], label: str) -> int:
    return next(card["value"] for card in cards if card["label"] == label)


def setup_db(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "ALERT_DIR", tmp_path / "alerts")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
    return db_path


def test_active_red_flag_metrics_exclude_resolved_red_flags(tmp_path, monkeypatch):
    db_path = setup_db(tmp_path, monkeypatch)
    with connect(db_path) as conn:
        upsert_case(conn, make_case("METRIC-RED-OPEN", priority="999 Emergency", red_flags_present=True))
        upsert_case(
            conn,
            make_case(
                "METRIC-RED-RESOLVED",
                status="Resolved",
                priority="999 Emergency",
                red_flags_present=True,
                resolved_at=now_iso(),
                resolved_by="Admin Demo",
            ),
        )
        kpis = main_module.get_kpi_cards(conn, "all")
        urgent = main_module.get_urgent_attention(conn)

    assert metric_value(kpis, "Red Flags") == 1
    assert urgent["red_flags"] == 1


def test_urgent_attention_ignores_resolved_red_flags_and_linked_alerts(tmp_path, monkeypatch):
    db_path = setup_db(tmp_path, monkeypatch)
    resolved_at = now_iso()
    with connect(db_path) as conn:
        upsert_case(
            conn,
            make_case(
                "METRIC-RED-ONLY-RESOLVED",
                status="Resolved",
                priority="999 Emergency",
                red_flags_present=True,
                resolved_at=resolved_at,
                resolved_by="Admin Demo",
            ),
        )
        conn.execute(
            """
            INSERT INTO alert_events (
                alert_id, timestamp, alert_type, severity, count, message,
                first_call_id, first_patient, first_priority, source_workflow, dedupe_key
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "alert-resolved-red",
                resolved_at,
                "red flag",
                "critical",
                1,
                "Resolved red flag should not keep banner active",
                "METRIC-RED-ONLY-RESOLVED",
                "Patient",
                "999 Emergency",
                "test",
                "resolved-red",
            ),
        )
        conn.commit()
        urgent = main_module.get_urgent_attention(conn)

    assert urgent["red_flags"] == 0
    assert urgent["staff_review"] == 0
    assert urgent["identity_checks"] == 0
    assert urgent["latest"] is None


def test_staff_review_identity_and_processed_today_counts_use_current_state(tmp_path, monkeypatch):
    db_path = setup_db(tmp_path, monkeypatch)
    with connect(db_path) as conn:
        upsert_case(conn, make_case("METRIC-REVIEW-OPEN", staff_review_required=True, status="Needs Review"))
        upsert_case(
            conn,
            make_case(
                "METRIC-REVIEW-RESOLVED",
                staff_review_required=True,
                status="Resolved",
                resolved_at=now_iso(),
                resolved_by="Admin Demo",
            ),
        )
        upsert_case(conn, make_case("METRIC-IDENTITY-OPEN", verification_status="possible_match", status="New"))
        upsert_case(
            conn,
            make_case(
                "METRIC-IDENTITY-RESOLVED",
                verification_status="possible_match",
                status="Resolved",
                resolved_at=now_iso(),
                resolved_by="Admin Demo",
            ),
        )
        kpis = main_module.get_kpi_cards(conn, "all")

    assert metric_value(kpis, "Staff Review") == 1
    assert metric_value(kpis, "Identity Checks") == 1
    assert metric_value(kpis, "Processed Today") == 2


def test_assigned_staff_workload_separates_open_and_resolved(tmp_path, monkeypatch):
    db_path = setup_db(tmp_path, monkeypatch)
    with connect(db_path) as conn:
        upsert_case(conn, make_case("METRIC-ADMIN-OPEN", assigned_to="Admin Demo", status="In Progress"))
        upsert_case(
            conn,
            make_case(
                "METRIC-ADMIN-RESOLVED",
                assigned_to="Admin Demo",
                status="Resolved",
                resolved_at=now_iso(),
                resolved_by="Admin Demo",
            ),
        )
        activity = main_module.get_team_activity(conn, "today")

    admin_row = next(row for row in activity["rows"] if row["staff_name"] == "Admin Demo")
    assert admin_row["assigned_open"] == 1
    assert admin_row["resolved_today"] == 1
    assert activity["team"]["in_progress"] == 1


def test_reopen_moves_case_back_to_active_counts(tmp_path, monkeypatch, authed_client):
    db_path = setup_db(tmp_path, monkeypatch)
    with connect(db_path) as conn:
        upsert_case(
            conn,
            make_case(
                "METRIC-REOPEN",
                status="Resolved",
                resolved_at=now_iso(),
                resolved_by="Admin Demo",
            ),
        )
        assert metric_value(main_module.get_kpi_cards(conn, "all"), "Open Cases") == 0

    with authed_client as client:
        response = client.post(
            "/case/METRIC-REOPEN/quick_action",
            data={"action": "reopen", "return_url": "/"},
            follow_redirects=False,
        )

    assert response.status_code == 303
    with connect(db_path) as conn:
        row = conn.execute("SELECT status, resolved_at, resolved_by FROM cases WHERE call_id = ?", ("METRIC-REOPEN",)).fetchone()
        kpis = main_module.get_kpi_cards(conn, "all")

    assert row["status"] == "Needs Review"
    assert row["resolved_at"] == ""
    assert row["resolved_by"] == ""
    assert metric_value(kpis, "Open Cases") == 1

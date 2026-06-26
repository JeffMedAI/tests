from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys


DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from fastapi.testclient import TestClient

import app.audit as audit_module
import app.db as db_module
from app.db import connect, init_db
from app.importer import map_handoff_to_case, upsert_case
from app.main import app


def _iso(days_ago: int = 0):
    t = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return t.replace(hour=10, minute=0, second=0, microsecond=0).isoformat().replace("+00:00", "Z")


def _make(call_id, priority="routine", verification_status="matched",
          red_flags_present=False, safe_to_queue=True, status="New",
          request_type="prescription"):
    return map_handoff_to_case({
        "call_id": call_id,
        "call_timestamp": _iso(1),
        "request_type": request_type,
        "normalized_input": {
            "patient_name": f"Test Patient",
            "dob": "1980-05-15",
            "postcode": "PR9 7LT",
            "callback_number": "07111000000",
        },
        "verification_status": verification_status,
        "verification_reason": "test fixture",
        "priority": priority,
        "safe_to_queue": safe_to_queue,
        "task_title": f"Task for {call_id}",
        "task_body": "Test task body",
        "raw_transcript": "Patient called about a routine matter. " * 15,
        "call_summary": "Routine test call.",
        "staff_review_required": verification_status != "matched" or red_flags_present,
        "red_flags_present": red_flags_present,
        "status": status,
    })


def _seed(db_path):
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, _make("RAWMOCK-001-REPEAT-EXACT"))
        upsert_case(conn, _make("RAWMOCK-006-URGENT-REDFLAG",
                                priority="999 Emergency",
                                red_flags_present=True,
                                safe_to_queue=False))
        upsert_case(conn, _make("RAWMOCK-011-NO-MATCH",
                                verification_status="no_match",
                                safe_to_queue=False))
        upsert_case(conn, _make("RAWMOCK-009-INSUFFICIENT-ID",
                                verification_status="insufficient_data",
                                safe_to_queue=False))
        upsert_case(conn, _make("RAWMOCK-012-MESSY-MULTI-INTENT",
                                request_type="needs_review",
                                verification_status="matched"))


def test_locked_fields_cannot_be_updated_and_staff_fields_can(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    _seed(db_path)

    with connect(db_path) as conn:
        before = conn.execute(
            "SELECT priority, verification_status, safe_to_queue FROM cases WHERE call_id = ?",
            ("RAWMOCK-001-REPEAT-EXACT",),
        ).fetchone()

    with authed_client as client:
        response = client.post(
            "/case/RAWMOCK-001-REPEAT-EXACT/update",
            data={
                "status": "In Progress",
                "assigned_to": "Test Staff",
                "action_needed": "Review locally",
                "outcome_notes": "Updated by test",
                "staff_action": "Checked",
                "resolved_by": "",
                "last_edited_by": "tester",
                "priority": "999 Emergency",
                "verification_status": "no_match",
                "safe_to_queue": "false",
            },
            follow_redirects=False,
        )

    assert response.status_code == 303
    with connect(db_path) as conn:
        after = conn.execute(
            """
            SELECT priority, verification_status, safe_to_queue, status, assigned_to,
                   action_needed, outcome_notes, staff_action, last_edited_by
            FROM cases WHERE call_id = ?
            """,
            ("RAWMOCK-001-REPEAT-EXACT",),
        ).fetchone()
        audit_count = conn.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]

    assert after["priority"] == before["priority"]
    assert after["verification_status"] == before["verification_status"]
    assert after["safe_to_queue"] == before["safe_to_queue"]
    assert after["status"] == "In Progress"
    assert after["assigned_to"] == "Test Staff"
    assert after["action_needed"] == "Review locally"
    assert after["outcome_notes"] == "Updated by test"
    assert after["staff_action"] == "Checked"
    assert after["last_edited_by"] == "tester"
    assert audit_count == 1


def test_resolved_case_gets_resolved_at_and_turnaround(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    _seed(db_path)

    with authed_client as client:
        response = client.post(
            "/case/RAWMOCK-001-REPEAT-EXACT/update",
            data={
                "status": "New",
                "assigned_to": "Test Staff",
                "action_needed": "Completed",
                "outcome_notes": "Done",
                "staff_action": "Resolved locally",
                "resolved_by": "tester",
                "last_edited_by": "tester",
                "mark_resolved": "yes",
            },
            follow_redirects=False,
        )

    assert response.status_code == 303
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT status, resolved_at, resolved_by, turnaround_minutes FROM cases WHERE call_id = ?",
            ("RAWMOCK-001-REPEAT-EXACT",),
        ).fetchone()

    assert row["status"] == "Resolved"
    assert row["resolved_at"]
    assert row["resolved_by"] == "tester"
    assert row["turnaround_minutes"] is not None


def test_red_flag_case_cannot_resolve_without_outcome_notes(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    _seed(db_path)

    with authed_client as client:
        response = client.post(
            "/case/RAWMOCK-006-URGENT-REDFLAG/quick_action",
            data={
                "action": "resolve",
                "resolved_by": "tester",
            },
            follow_redirects=False,
        )

    assert response.status_code == 400
    assert "Outcome notes are required before resolving a red-flag case." in response.text


def test_identity_issue_cannot_resolve_without_outcome_notes(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    _seed(db_path)

    with authed_client as client:
        no_match_response = client.post(
            "/case/RAWMOCK-011-NO-MATCH/quick_action",
            data={
                "action": "resolve",
                "resolved_by": "tester",
            },
            follow_redirects=False,
        )
        insufficient_response = client.post(
            "/case/RAWMOCK-009-INSUFFICIENT-ID/quick_action",
            data={
                "action": "resolve",
                "resolved_by": "tester",
            },
            follow_redirects=False,
        )

    assert no_match_response.status_code == 400
    assert insufficient_response.status_code == 400
    assert "Outcome notes are required before resolving an identity issue." in no_match_response.text
    assert "Outcome notes are required before resolving an identity issue." in insufficient_response.text


def test_quick_actions_update_only_editable_fields(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    _seed(db_path)

    with connect(db_path) as conn:
        before = conn.execute(
            """
            SELECT priority, verification_status, safe_to_queue, red_flags_present,
                   staff_review_required, task_title, task_body
            FROM cases WHERE call_id = ?
            """,
            ("RAWMOCK-012-MESSY-MULTI-INTENT",),
        ).fetchone()

    with authed_client as client:
        start_response = client.post(
            "/case/RAWMOCK-012-MESSY-MULTI-INTENT/quick_action",
            data={
                "action": "start_review",
                "assigned_to": "Reception A",
                "edited_by": "tester",
                "priority": "999 Emergency",
                "safe_to_queue": "false",
            },
            follow_redirects=False,
        )
        flag_response = client.post(
            "/case/RAWMOCK-012-MESSY-MULTI-INTENT/quick_action",
            data={
                "action": "flag_issue",
                "edited_by": "tester",
            },
            follow_redirects=False,
        )

    assert start_response.status_code == 303
    assert flag_response.status_code == 303

    with connect(db_path) as conn:
        after = conn.execute(
            """
            SELECT priority, verification_status, safe_to_queue, red_flags_present,
                   staff_review_required, task_title, task_body, status, assigned_to,
                   action_needed, last_edited_by
            FROM cases WHERE call_id = ?
            """,
            ("RAWMOCK-012-MESSY-MULTI-INTENT",),
        ).fetchone()

    for field in [
        "priority",
        "verification_status",
        "safe_to_queue",
        "red_flags_present",
        "staff_review_required",
        "task_title",
        "task_body",
    ]:
        assert after[field] == before[field]

    assert after["status"] == "Needs Review"
    assert after["assigned_to"] == "Reception A"
    assert after["action_needed"] == "Issue flagged by staff"
    assert after["last_edited_by"] == "tester"

from pathlib import Path
import sys


DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))
FIXTURE_DIR = DASHBOARD_ROOT.parent / "tests" / "fixtures"
if str(FIXTURE_DIR) not in sys.path:
    sys.path.insert(0, str(FIXTURE_DIR))

from fastapi.testclient import TestClient

import app.audit as audit_module
import app.db as db_module
import app.main as main_module
from app.db import connect, init_db
from app.importer import import_handoffs, map_handoff_to_case, upsert_case
from app.main import app
from n8n_webhook_test_pack import build_test_calls


HANDOFF_DIR = DASHBOARD_ROOT.parent / "outputs" / "handoff_json"


def seed_rawmock_db(db_path):
    with connect(db_path) as conn:
        init_db(conn)
        return import_handoffs(conn, HANDOFF_DIR, pattern="TC-*_handoff.json")


def make_client(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "ALERT_DIR", tmp_path / "alerts")
    seed_rawmock_db(db_path)
    return TestClient(app), db_path


def assert_json_response(response):
    assert response.headers["content-type"].startswith("application/json")
    assert "<html" not in response.text.lower()


def test_api_health_returns_json_case_count(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    with client_context as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert_json_response(response)
    data = response.json()
    assert data["ok"] is True
    assert data["service"] == "JeffLocal"
    assert data["checks"]["database"] is True
    assert data["checks"]["handoff_folder"] is True
    assert data["checks"]["case_count"] >= 12


def test_api_sync_rawmock_only_returns_pattern(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    with client_context as client:
        response = client.post("/api/sync?rawmock_only=true")

    assert response.status_code == 200
    assert_json_response(response)
    data = response.json()
    assert data["ok"] is True
    assert data["pattern"] == "TC-*_handoff.json"
    assert data["imported"] == 12


def test_api_red_flags_includes_rawmock_006(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    with client_context as client:
        response = client.get("/api/red-flags")

    assert response.status_code == 200
    assert_json_response(response)
    data = response.json()
    assert data["ok"] is True
    assert data["count"] >= 1
    case_ids = {case["call_id"] for case in data["cases"]}
    assert "TC-006-URGENT-REDFLAG" in case_ids
    rawmock_006 = next(case for case in data["cases"] if case["call_id"] == "TC-006-URGENT-REDFLAG")
    assert rawmock_006["red_flags_present"] is True
    assert rawmock_006["safe_to_queue"] is False


def test_api_overdue_returns_json(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    with client_context as client:
        response = client.get("/api/overdue?threshold_hours=24")

    assert response.status_code == 200
    assert_json_response(response)
    data = response.json()
    assert data["ok"] is True
    assert data["threshold_hours"] == 24
    assert isinstance(data["cases"], list)
    assert data["count"] == len(data["cases"])


def test_api_daily_summary_returns_request_type_counts(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    with client_context as client:
        response = client.get("/api/daily-summary")

    assert response.status_code == 200
    assert_json_response(response)
    data = response.json()
    assert data["ok"] is True
    assert data["total"] >= 12
    assert "request_type_counts" in data
    assert "prescription" in data["request_type_counts"]
    assert "admin" in data["request_type_counts"]


def test_api_implementation_has_no_external_call_clients():
    source = (DASHBOARD_ROOT / "app" / "main.py").read_text(encoding="utf-8")
    forbidden = ["requests.", "urllib.request", "https://"]
    for term in forbidden:
        assert term not in source


def alert_payload():
    return {
        "alert_type": "JeffLocal Red Flag",
        "severity": "critical",
        "count": 1,
        "message": "Red flag cases require review",
        "first_call_id": "TC-006-URGENT-REDFLAG",
        "first_patient": "Avery Redfield",
        "first_priority": "999 Emergency",
        "source_workflow": "JeffLocal - 03 Red Flag Scan",
    }


def test_api_alert_log_writes_sqlite_and_jsonl(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    with client_context as client:
        response = client.post("/api/alerts/log", json=alert_payload())

    assert response.status_code == 200
    assert_json_response(response)
    data = response.json()
    assert data["ok"] is True
    assert data["logged"] is True
    assert data["alert_id"].startswith("alert-")
    jsonl_files = list((tmp_path / "alerts").glob("alerts_*.jsonl"))
    assert len(jsonl_files) == 1
    assert "JeffLocal Red Flag" in jsonl_files[0].read_text(encoding="utf-8")


def test_api_alert_log_dedupes_recent_duplicate(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    with client_context as client:
        first = client.post("/api/alerts/log", json=alert_payload())
        second = client.post("/api/alerts/log", json=alert_payload())

    assert first.status_code == 200
    assert second.status_code == 200
    data = second.json()
    assert data["ok"] is True
    assert data["logged"] is False
    assert data["deduped"] is True
    assert data["reason"] == "duplicate_recent_alert"


def test_api_alerts_recent_returns_logged_alerts(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    with client_context as client:
        client.post("/api/alerts/log", json=alert_payload())
        response = client.get("/api/alerts/recent?limit=5")

    assert response.status_code == 200
    assert_json_response(response)
    data = response.json()
    assert data["ok"] is True
    assert data["count"] == 1
    assert data["alerts"][0]["alert_type"] == "JeffLocal Red Flag"
    assert data["alerts"][0]["dedupe_key"] == "jefflocal red flag|tc-006-urgent-redflag|jefflocal - 03 red flag scan"


def test_api_alert_logging_does_not_alter_locked_case_fields(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    fields = """
        priority, safe_to_queue, staff_review_required, red_flags_present,
        verification_status, verification_reason, matched_patient_ref,
        emis_number, nhs_number, task_title, task_body
    """
    with connect(db_path) as conn:
        before = dict(
            conn.execute(
                f"SELECT {fields} FROM cases WHERE call_id = ?",
                ("TC-006-URGENT-REDFLAG",),
            ).fetchone()
        )
    with client_context as client:
        response = client.post("/api/alerts/log", json=alert_payload())
    with connect(db_path) as conn:
        after = dict(
            conn.execute(
                f"SELECT {fields} FROM cases WHERE call_id = ?",
                ("TC-006-URGENT-REDFLAG",),
            ).fetchone()
        )

    assert response.status_code == 200
    assert before == after


def n8ntest_payload(calls=None):
    return {
        "test_mode": True,
        "batch_id": "PYTEST-BATCH-001",
        "disable_google_push": True,
        "calls": calls if calls is not None else build_test_calls(),
    }


def test_api_n8n_test_intake_rejects_missing_test_mode(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    payload = n8ntest_payload()
    payload.pop("test_mode")
    with client_context as client:
        response = client.post("/api/n8n/test-intake-batch", json=payload)

    assert response.status_code == 400
    assert "test_mode must be true" in response.text


def test_api_n8n_test_intake_rejects_google_push_enabled(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    payload = n8ntest_payload()
    payload["disable_google_push"] = False
    with client_context as client:
        response = client.post("/api/n8n/test-intake-batch", json=payload)

    assert response.status_code == 400
    assert "disable_google_push must be true" in response.text


def test_api_n8n_test_intake_rejects_more_than_five_calls(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    calls = [{"call_id": f"TC-EXTRA-{index}"} for index in range(6)]
    with client_context as client:
        response = client.post("/api/n8n/test-intake-batch", json=n8ntest_payload(calls))

    assert response.status_code == 400
    assert "1 to 5" in response.text



def test_api_n8n_test_intake_accepts_valid_five_call_batch(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    monkeypatch.setattr(main_module, "archive_n8ntest_artifacts", lambda: {"total_archived": 0, "folders": []})
    monkeypatch.setattr(main_module, "write_n8ntest_envelopes", lambda calls: [call["call_id"] for call in calls])
    monkeypatch.setattr(main_module, "run_encrypted_cycle_disable_google_push", lambda: {"returncode": 0, "stdout": "", "stderr": ""})
    monkeypatch.setattr(main_module, "count_n8ntest_files", lambda folder, pattern="*": 5 if folder in {"queue/processed", "outputs/handoff_json"} else 0)
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn, pattern="*_handoff.json": 5)
    monkeypatch.setattr(
        main_module,
        "n8ntest_dashboard_cases",
        lambda: [
            {
                "call_id": "TC-BATCH-005",
                "priority": "999 Emergency",
                "red_flags_present": True,
                "safe_to_queue": False,
                "staff_review_required": True,
            }
        ],
    )

    with client_context as client:
        response = client.post("/api/n8n/test-intake-batch", json=n8ntest_payload())

    assert response.status_code == 200
    assert_json_response(response)
    data = response.json()
    assert data["ok"] is True
    assert data["received"] == 5
    assert data["processed"] == 5
    assert data["handoffs"] == 5
    assert data["failed"] == 0
    assert data["deadletter"] == 0
    assert data["google_push"] == "disabled_for_test"
    assert data["dashboard_imported"] == 5


def test_api_n8n_test_intake_does_not_disable_production_google_push_config():
    settings = (DASHBOARD_ROOT.parent / "config" / "app_settings.json").read_text(encoding="utf-8")
    assert '"enable_google_sheet_push": false' not in settings.lower()


def insert_alert(conn, alert_id, severity, alert_type="JeffLocal Red Flag"):
    conn.execute(
        """
        INSERT INTO alert_events (
            alert_id, timestamp, alert_type, severity, count, message,
            first_call_id, first_patient, first_priority, source_workflow,
            dedupe_key
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            alert_id,
            "2026-05-12T12:00:00+00:00",
            alert_type,
            severity,
            1,
            "Local alert test message",
            "TC-BATCH-005",
            "Geoffrey Mynne",
            "999 Emergency",
            "JeffLocal - 03 Red Flag Scan",
            f"{alert_type.lower()}|n8ntest-005-redflag|jefflocal - 03 red flag scan",
        ),
    )
    conn.commit()


def test_alerts_page_renders_recent_alert_rows(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    with connect(db_path) as conn:
        insert_alert(conn, "alert-page-1", "critical")

    with client_context as client:
        response = client.get("/alerts")

    assert response.status_code == 200
    assert "Local Alert Log" in response.text
    assert "TC-BATCH-005" in response.text
    assert "JeffLocal - 03 Red Flag Scan" in response.text
    assert "local_secrets" not in response.text
    assert "token" not in response.text.lower()


def test_alerts_page_severity_filter_works(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    with connect(db_path) as conn:
        insert_alert(conn, "alert-page-critical", "critical", "Critical Alert")
        insert_alert(conn, "alert-page-info", "info", "Info Alert")

    with client_context as client:
        response = client.get("/alerts?severity=info")

    assert response.status_code == 200
    assert "Info Alert" in response.text
    assert "Critical Alert" not in response.text


def test_alerts_page_does_not_update_cases(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn, pattern="*_handoff.json": 0)
    with connect(db_path) as conn:
        before = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        insert_alert(conn, "alert-page-no-case-update", "warning")

    with client_context as client:
        response = client.get("/alerts")

    with connect(db_path) as conn:
        after = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]

    assert response.status_code == 200
    assert before == after


def test_api_red_flags_sorts_newer_n8ntest_before_older_rawmock(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    with connect(db_path) as conn:
        upsert_case(
            conn,
            map_handoff_to_case(
                {
                    "call_id": "TC-BATCH-005",
                    "call_timestamp": "2026-05-30T14:00:00Z",
                    "request_type": "appointment_redirect",
                    "normalized_input": {"patient_name": "Geoffrey Mynne", "dob": "1941-02-21"},
                    "verification_status": "matched",
                    "priority": "999 Emergency",
                    "safe_to_queue": False,
                    "staff_review_required": True,
                    "red_flags_present": True,
                    "task_title": "Emergency red flag",
                    "task_body": "Immediate review",
                    "call_summary": "Chest pain and breathlessness",
                    "raw_transcript": "Caller reports chest pain and breathlessness.",
                }
            ),
        )

    with client_context as client:
        response = client.get("/api/red-flags")

    assert response.status_code == 200
    cases = response.json()["cases"]
    ids = [case["call_id"] for case in cases]
    assert "TC-BATCH-005" in ids
    assert "TC-006-URGENT-REDFLAG" in ids
    assert ids.index("TC-BATCH-005") < ids.index("TC-006-URGENT-REDFLAG")


def test_api_services_status_dashboard_online_and_n8n_offline_graceful(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    monkeypatch.setattr(main_module, "check_local_n8n", lambda timeout_seconds=1.5: main_module.service_status("n8n", "offline", "http://localhost:5678", "Localhost check failed: test", main_module.utc_now_iso()))

    with client_context as client:
        response = client.get("/api/services/status")

    assert response.status_code == 200
    data = response.json()
    assert data["services"]["dashboard"]["status"] == "online"
    assert data["services"]["n8n"]["status"] == "offline"
    assert data["services"]["voice_agent"]["status"] in {"not_configured", "test_ready"}


def test_api_services_refresh_check_only_does_not_start_services(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    called = {"start": False}

    def fake_run(*args, **kwargs):
        called["start"] = True
        raise AssertionError("service start should not run")

    monkeypatch.setattr(main_module.subprocess, "run", fake_run)
    monkeypatch.setattr(main_module, "check_local_n8n", lambda timeout_seconds=1.5: main_module.service_status("n8n", "offline", "http://localhost:5678", "Localhost check failed: test", main_module.utc_now_iso()))

    with client_context as client:
        response = client.post("/api/services/refresh", json={"start_missing": False})

    assert response.status_code == 200
    assert called["start"] is False
    assert response.json()["actions"][0]["action"] == "check_only"


def test_dashboard_renders_service_status_panel(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    monkeypatch.setattr(main_module, "check_local_n8n", lambda timeout_seconds=1.5: main_module.service_status("n8n", "offline", "http://localhost:5678", "Localhost check failed: test", main_module.utc_now_iso()))

    with client_context as client:
        response = client.get("/?range=all")

    assert response.status_code == 200
    assert "System Status" in response.text
    assert "Refresh" in response.text
    assert "Voice Agent" in response.text
    assert "Service Status" not in response.text


def test_dashboard_renders_when_service_status_check_fails(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)

    def broken_status():
        raise RuntimeError("service check failure")

    monkeypatch.setattr(main_module, "get_service_statuses", broken_status)

    with client_context as client:
        response = client.get("/?range=all")

    assert response.status_code == 200
    assert "System Status" in response.text
    assert "Degraded" in response.text or "Unknown" in response.text or "Online" in response.text


def staff_id(db_path, display_name):
    with connect(db_path) as conn:
        return conn.execute("SELECT id FROM staff_users WHERE display_name = ?", (display_name,)).fetchone()["id"]


def test_demo_staff_users_seed_and_selector_renders(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    with connect(db_path) as conn:
        names = {row["display_name"]: row["role"] for row in conn.execute("SELECT display_name, role FROM staff_users").fetchall()}

    with client_context as client:
        response = client.get("/?range=all")

    assert names["Admin Demo"] == "admin"
    assert names["Reception Demo"] == "staff"
    assert names["GP Demo"] == "readonly"
    assert response.status_code == 200
    assert "DEMO / TEST DATA MODE" in response.text
    assert "Dashboard" in response.text  # page title includes "Dashboard"


def test_demo_banner_renders_for_test_cases(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    with client_context as client:
        response = client.get("/?range=all")

    assert response.status_code == 200
    assert "DEMO / TEST DATA MODE" in response.text
    assert "No real patient data. Google push disabled for test runs." in response.text


def test_alert_modal_api_and_acknowledgement_flow(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    with connect(db_path) as conn:
        insert_alert(conn, "alert-modal-critical", "critical")
        insert_alert(conn, "alert-modal-info", "info", "Daily Summary")

    with client_context as client:
        response = client.get("/api/alerts/unacknowledged?modal_only=true")
        alert_id = response.json()["alerts"][0]["alert_id"]
        ack = client.post(f"/api/alerts/{alert_id}/acknowledge", json={})
        after = client.get("/api/alerts/unacknowledged?modal_only=true")

    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["alerts"][0]["alert_type"] == "JeffLocal Red Flag"
    assert ack.status_code == 200
    assert ack.json()["acknowledged_by"] == "demo_user"
    assert after.json()["count"] == 0
    with connect(db_path) as conn:
        row = conn.execute("SELECT acknowledged_at, acknowledged_by, acknowledgement_source FROM alert_events WHERE alert_id = ?", (alert_id,)).fetchone()
        audit_count = conn.execute("SELECT COUNT(*) FROM audit_events WHERE action = 'alert_acknowledged'").fetchone()[0]
    assert row["acknowledged_at"]
    assert row["acknowledged_by"] == "demo_user"
    assert row["acknowledgement_source"] == "dashboard_modal"
    assert audit_count == 1


def test_alert_message_leading_equals_cleaned_for_new_and_existing_alerts(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    payload = alert_payload()
    payload["message"] = "=JeffLocal has a red flag alert"
    with client_context as client:
        logged = client.post("/api/alerts/log", json=payload)
        alerts_page = client.get("/alerts")

    assert logged.status_code == 200
    with connect(db_path) as conn:
        message = conn.execute("SELECT message FROM alert_events WHERE alert_id = ?", (logged.json()["alert_id"],)).fetchone()["message"]
    assert message.startswith("JeffLocal")
    assert "=JeffLocal" not in alerts_page.text


def make_batch_case(call_id, red_flags_present=False, request_type="prescription", priority="routine", verification_status="matched", staff_review_required=False, safe_to_queue=True):
    case = map_handoff_to_case(
        {
            "call_id": call_id,
            "call_timestamp": "2026-05-12T09:00:00Z",
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
            "safe_to_queue": safe_to_queue,
            "staff_review_required": staff_review_required,
            "red_flags_present": red_flags_present,
            "task_title": "Routine prescription",
            "task_body": "Routine prescription request",
            "call_summary": "Routine request",
            "raw_transcript": "Routine request",
            "status": "New",
        }
    )
    return case


def test_batch_resolve_valid_cases_and_preserves_locked_fields(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    with connect(db_path) as conn:
        upsert_case(conn, make_batch_case("TC-BATCH-001"))
        upsert_case(conn, make_batch_case("TC-BATCH-002"))
        before = dict(conn.execute("SELECT priority, verification_status, safe_to_queue, red_flags_present FROM cases WHERE call_id = ?", ("TC-BATCH-001",)).fetchone())

    with client_context as client:
        response = client.post(
            "/api/cases/batch-resolve",
            json={"call_ids": ["TC-BATCH-001", "TC-BATCH-002"], "allow_demo_user": True},
        )

    assert response.status_code == 200
    assert response.json()["resolved"] == 2
    with connect(db_path) as conn:
        after = dict(conn.execute("SELECT priority, verification_status, safe_to_queue, red_flags_present, status, resolved_by, last_edited_by FROM cases WHERE call_id = ?", ("TC-BATCH-001",)).fetchone())
        audit_count = conn.execute("SELECT COUNT(*) FROM audit_events WHERE action = 'batch_resolve'").fetchone()[0]
    for field in before:
        assert after[field] == before[field]
    assert after["status"] == "Resolved"
    assert after["resolved_by"] == "demo_user"
    assert after["last_edited_by"] == "demo_user"
    assert audit_count == 2


def test_batch_resolve_rejects_mixed_type_red_flag_and_missing_identity(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    with connect(db_path) as conn:
        upsert_case(conn, make_batch_case("TC-BATCH-A"))
        upsert_case(conn, make_batch_case("TC-BATCH-B", request_type="admin"))
        upsert_case(conn, make_batch_case("TC-BATCH-RED", red_flags_present=True, priority="999 Emergency", safe_to_queue=False, staff_review_required=True))

    with client_context as client:
        missing_identity = client.post("/api/cases/batch-resolve", json={"call_ids": ["TC-BATCH-A"]})
        mixed = client.post("/api/cases/batch-resolve", json={"call_ids": ["TC-BATCH-A", "TC-BATCH-B"], "allow_demo_user": True})
        red_flag = client.post("/api/cases/batch-resolve", json={"call_ids": ["TC-BATCH-RED"], "allow_demo_user": True})

    assert missing_identity.status_code == 400
    assert "Staff identity is required" in missing_identity.text
    assert mixed.status_code == 400
    assert red_flag.status_code == 400
    assert "Batch resolve unavailable" in red_flag.text


def test_readonly_user_cannot_resolve_or_acknowledge(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    readonly_id = staff_id(db_path, "GP Demo")
    with connect(db_path) as conn:
        insert_alert(conn, "alert-readonly", "critical")

    with client_context as client:
        client.cookies.set("jefflocal_staff_id", str(readonly_id))
        resolve = client.post(
            "/case/TC-001-REPEAT-EXACT/quick_action",
            data={"action": "resolve", "outcome_notes": "done"},
            follow_redirects=False,
        )
        ack = client.post("/api/alerts/alert-readonly/acknowledge", json={})

    assert resolve.status_code == 403
    assert ack.status_code == 403


def test_staff_identity_populates_quick_action_fields(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    staff = staff_id(db_path, "Reception Demo")
    with client_context as client:
        client.cookies.set("jefflocal_staff_id", str(staff))
        response = client.post(
            "/case/TC-001-REPEAT-EXACT/quick_action",
            data={"action": "start_review"},
            follow_redirects=False,
        )

    assert response.status_code == 303
    with connect(db_path) as conn:
        row = conn.execute("SELECT assigned_to, last_edited_by FROM cases WHERE call_id = ?", ("TC-001-REPEAT-EXACT",)).fetchone()
    assert row["assigned_to"] == "Reception Demo"
    assert row["last_edited_by"] == "Reception Demo"


def test_staff_performance_and_workload_apis_return_expected_shape(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    monkeypatch.setattr(main_module, "check_local_n8n", lambda timeout_seconds=1.5: main_module.service_status("n8n", "offline", "http://localhost:5678", "Localhost check failed: test", main_module.utc_now_iso()))
    with client_context as client:
        performance = client.get("/api/staff/performance?range=today")
        workload = client.get("/api/system/workload")
        dashboard = client.get("/?range=all")

    assert performance.status_code == 200
    assert {"resolved_today", "in_progress", "average_turnaround", "escalations", "reopened", "alerts_acknowledged"} <= set(performance.json()["team"])
    assert isinstance(performance.json()["rows"], list)
    assert workload.status_code == 200
    assert {"incoming", "encrypted_raw", "processed_today", "failed", "deadletter"} <= set(workload.json()["queue_depth"])
    assert "Staff Workload" in dashboard.text
    assert "Live Workload" in dashboard.text
    assert "Failed Safety Queue" in dashboard.text


def test_n8n_test_intake_response_uses_batch_specific_counts(tmp_path, monkeypatch):
    client_context, _db_path = make_client(tmp_path, monkeypatch)
    calls = [{"call_id": f"TC-PYTEST-BATCH-{index}"} for index in range(5)]
    monkeypatch.setattr(main_module, "archive_n8ntest_artifacts", lambda: {"total_archived": 0, "folders": []})
    monkeypatch.setattr(main_module, "write_n8ntest_envelopes", lambda calls: [call["call_id"] for call in calls])
    monkeypatch.setattr(main_module, "run_encrypted_cycle_disable_google_push", lambda: {"returncode": 0, "stdout": "", "stderr": ""})
    monkeypatch.setattr(main_module, "count_n8ntest_files", lambda folder, pattern="*": 10 if folder in {"queue/processed", "outputs/handoff_json"} else 0)
    monkeypatch.setattr(main_module, "count_batch_files", lambda folder, call_ids, suffix="": 5 if folder in {"queue/processed", "outputs/handoff_json"} else 0)
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn, pattern="*_handoff.json": 10)
    monkeypatch.setattr(main_module, "n8ntest_dashboard_cases", lambda call_ids=None: [{"call_id": call_id} for call_id in (call_ids or [])])

    with client_context as client:
        response = client.post("/api/n8n/test-intake-batch", json=n8ntest_payload(calls))

    assert response.status_code == 200
    data = response.json()
    assert data["received"] == 5
    assert data["batch_processed"] == 5
    assert data["batch_handoffs"] == 5
    assert data["batch_failed"] == 0
    assert data["batch_deadletter"] == 0
    assert data["total_n8ntest_handoffs"] == 10
    assert data["dashboard_imported_batch"] == 5



def test_admin_staff_edit_reactivate_invitation_and_audit(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    admin = staff_id(db_path, "Admin Demo")
    with client_context as client:
        client.cookies.set("jefflocal_staff_id", str(admin))
        create = client.post("/staff/create", data={"display_name": "Demo Temp", "email": "temp@example.test", "role": "staff"}, follow_redirects=False)
        new_id = staff_id(db_path, "Demo Temp")
        edit = client.post(f"/staff/{new_id}/edit", data={"display_name": "Demo Temp Edited", "email": "edited@example.test", "role": "readonly", "active": "yes"}, follow_redirects=False)
        deactivate = client.post(f"/staff/{new_id}/deactivate", follow_redirects=False)
        reactivate = client.post(f"/staff/{new_id}/reactivate", follow_redirects=False)
        invite = client.post("/staff/invitations/create", data={"email": "future@example.test", "role": "staff"}, follow_redirects=False)
        cancel = client.post("/staff/invitations/1/cancel", follow_redirects=False)

    assert create.status_code == 303
    assert edit.status_code == 303
    assert deactivate.status_code == 303
    assert reactivate.status_code == 303
    assert invite.status_code == 303
    assert cancel.status_code == 303
    with connect(db_path) as conn:
        row = conn.execute("SELECT display_name, role, active FROM staff_users WHERE id = ?", (new_id,)).fetchone()
        invitation = conn.execute("SELECT status FROM staff_invitations WHERE email = ?", ("future@example.test",)).fetchone()
        actions = {r["action"] for r in conn.execute("SELECT action FROM audit_events WHERE call_id = 'staff'").fetchall()}
    assert row["display_name"] == "Demo Temp Edited"
    assert row["role"] == "readonly"
    assert row["active"] == 1
    assert invitation["status"] == "cancelled"
    assert {"staff_created", "staff_updated", "staff_deactivated", "staff_reactivated", "staff_invitation_created", "staff_invitation_cancelled"} <= actions


def test_non_admin_staff_management_mutation_forbidden(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    staff = staff_id(db_path, "Reception Demo")
    readonly = staff_id(db_path, "GP Demo")
    with client_context as client:
        client.cookies.set("jefflocal_staff_id", str(staff))
        staff_response = client.post("/staff/create", data={"display_name": "Bad", "role": "staff"})
        client.cookies.set("jefflocal_staff_id", str(readonly))
        readonly_response = client.post("/staff/invitations/create", data={"email": "bad@example.test", "role": "staff"})

    assert staff_response.status_code == 403
    assert readonly_response.status_code == 403


def test_recording_attachment_existing_call_no_overwrite_and_audit(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    staff = staff_id(db_path, "Reception Demo")
    with client_context as client:
        client.cookies.set("jefflocal_staff_id", str(staff))
        first = client.post("/api/calls/TC-001-REPEAT-EXACT/recording", json={"recording_local_path": "C:\\JeffLocal\\recordings\\demo.wav", "duration_seconds": 65, "source": "voice_agent_demo"})
        second = client.post("/api/calls/TC-001-REPEAT-EXACT/recording", json={"recording_local_path": "C:\\JeffLocal\\recordings\\other.wav"})
        missing = client.post("/api/calls/TC-GP-MISSING/recording", json={"recording_local_path": "C:\\JeffLocal\\recordings\\missing.wav"})
        detail = client.get("/case/TC-001-REPEAT-EXACT")

    assert first.status_code == 200
    assert first.json()["recording"]["recording_status"] == "available"
    assert second.status_code == 409
    assert missing.status_code == 404
    assert "Recording" in detail.text
    assert "Available" in detail.text
    with connect(db_path) as conn:
        audit_count = conn.execute("SELECT COUNT(*) FROM audit_events WHERE action = 'recording_attached'").fetchone()[0]
    assert audit_count == 1


def test_bulk_actions_assign_review_and_resolve_skips_unsafe(tmp_path, monkeypatch):
    client_context, db_path = make_client(tmp_path, monkeypatch)
    staff = staff_id(db_path, "Reception Demo")
    with connect(db_path) as conn:
        upsert_case(conn, make_batch_case("TC-BULK-SAFE"))
        upsert_case(conn, make_batch_case("TC-BULK-REVIEW", staff_review_required=True))
        upsert_case(conn, make_batch_case("TC-BULK-RED", red_flags_present=True, priority="999 Emergency", safe_to_queue=False, staff_review_required=True))
    with client_context as client:
        client.cookies.set("jefflocal_staff_id", str(staff))
        assign = client.post("/api/cases/bulk-action", json={"call_ids": ["TC-BULK-REVIEW"], "action": "assign_to_me"})
        review = client.post("/api/cases/bulk-action", json={"call_ids": ["TC-BULK-RED"], "action": "start_review"})
        resolve = client.post("/api/cases/bulk-action", json={"call_ids": ["TC-BULK-SAFE", "TC-BULK-REVIEW", "TC-BULK-RED"], "action": "resolve_eligible_only"})

    assert assign.status_code == 200
    assert review.status_code == 200
    assert resolve.status_code == 200
    data = resolve.json()
    assert len(data["updated"]) == 1
    assert {item["reason"] for item in data["skipped"]} >= {"requires_individual_review", "red_flag"}


# ── HMAC verification tests (IR-01) ──────────────────────────────────────────

import hashlib
import hmac
import json
import os


def _hmac_header(secret: str, body: bytes) -> str:
    """Compute X-Hub-Signature-256 value for a given body."""
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_hmac_missing_header_returns_401_when_secret_set(tmp_path, monkeypatch):
    """Missing X-Hub-Signature-256 → 401 when JEFF_WEBHOOK_SECRET is configured."""
    client_context, _ = make_client(tmp_path, monkeypatch)
    monkeypatch.setenv("JEFF_WEBHOOK_SECRET", "test-secret-abc123")
    with client_context as client:
        response = client.post("/api/n8n/test-intake-batch", json=n8ntest_payload())
    assert response.status_code == 401


def test_hmac_wrong_secret_returns_401(tmp_path, monkeypatch):
    """Correct header format but wrong secret value → 401."""
    client_context, _ = make_client(tmp_path, monkeypatch)
    monkeypatch.setenv("JEFF_WEBHOOK_SECRET", "correct-secret")
    body = json.dumps(n8ntest_payload()).encode()
    bad_sig = _hmac_header("wrong-secret", body)
    with client_context as client:
        response = client.post(
            "/api/n8n/test-intake-batch",
            content=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": bad_sig},
        )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_hmac_tampered_body_returns_401(tmp_path, monkeypatch):
    """Valid HMAC header for original body, but body is then modified → 401."""
    client_context, _ = make_client(tmp_path, monkeypatch)
    secret = "tamper-test-secret"
    monkeypatch.setenv("JEFF_WEBHOOK_SECRET", secret)
    original_body = json.dumps(n8ntest_payload()).encode()
    valid_sig = _hmac_header(secret, original_body)
    # Tamper: append a space — signature no longer matches
    tampered_body = original_body + b" "
    with client_context as client:
        response = client.post(
            "/api/n8n/test-intake-batch",
            content=tampered_body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": valid_sig},
        )
    assert response.status_code == 401


def _inject_live_lookup_stub():
    """Stub live_lookup_test_payloads so HMAC-passing requests don't crash on missing module."""
    import sys, types
    if "live_lookup_test_payloads" not in sys.modules:
        stub = types.ModuleType("live_lookup_test_payloads")
        stub.encrypt_envelope = lambda call: call  # type: ignore[attr-defined]
        sys.modules["live_lookup_test_payloads"] = stub


def test_hmac_valid_signature_passes(tmp_path, monkeypatch):
    """Correct HMAC header → request proceeds (not a 401)."""
    _inject_live_lookup_stub()
    client_context, _ = make_client(tmp_path, monkeypatch)
    secret = "valid-test-secret"
    monkeypatch.setenv("JEFF_WEBHOOK_SECRET", secret)
    body = json.dumps(n8ntest_payload()).encode()
    sig = _hmac_header(secret, body)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/n8n/test-intake-batch",
            content=body,
            headers={"Content-Type": "application/json", "X-Hub-Signature-256": sig},
        )
    # 401 must NOT be returned — any other status is acceptable here
    assert response.status_code != 401


def test_hmac_skipped_when_secret_not_set(tmp_path, monkeypatch):
    """When JEFF_WEBHOOK_SECRET is not set, HMAC check is skipped — existing tests unaffected."""
    _inject_live_lookup_stub()
    monkeypatch.delenv("JEFF_WEBHOOK_SECRET", raising=False)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/n8n/test-intake-batch", json=n8ntest_payload())
    # Must not be a 401 (HMAC not enforced)
    assert response.status_code != 401

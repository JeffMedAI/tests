from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import re
import sys


DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from fastapi.testclient import TestClient

import app.audit as audit_module
import app.db as db_module
import app.main as main_module
from app.db import connect, init_db
from app.importer import map_handoff_to_case, import_handoffs, upsert_case
from app.main import app


HANDOFF_DIR = DASHBOARD_ROOT.parent / "outputs" / "handoff_json"


def test_dashboard_pages_render_after_import(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, HANDOFF_DIR)

    with TestClient(app) as client:
        index_response = client.get("/")
        import_response = client.post("/import", follow_redirects=False)
        detail_response = client.get("/case/TC-006-URGENT-REDFLAG")

    assert index_response.status_code == 200
    assert "Dashboard" in index_response.text
    assert "urgent-banner" in index_response.text or "Urgent attention required" in index_response.text
    assert import_response.status_code == 303
    assert detail_response.status_code == 200
    assert "TC-006-URGENT-REDFLAG" in detail_response.text
    assert "POSSIBLE EMERGENCY" in detail_response.text
    assert re.search(r"\d{2}-\d{2}-\d{4} T \d{2}\.\d{2}", index_response.text)
    assert "2026-05-11T12:50:00Z" not in index_response.text
    assert "bar-track" in index_response.text
    assert "Requests" in index_response.text
    assert "Patients" in index_response.text
    assert "Reports" in index_response.text


def test_sidebar_navigation_and_dashboard_requests_split(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("TC-UX-NAV", iso_days_ago(0), staff_review_required=True))
        admin_id = conn.execute("SELECT id FROM staff_users WHERE display_name = ?", ("Admin Demo",)).fetchone()["id"]

    with TestClient(app) as client:
        dashboard = client.get("/")
        requests = client.get("/requests?filter=all&range=all")
        patients = client.get("/patients")
        client.cookies.set("jefflocal_staff_id", str(admin_id))
        staff = client.get("/staff")
        reports = client.get("/reports")
        settings = client.get("/settings")

    assert dashboard.status_code == 200
    assert 'class="analytics-sidebar"' in dashboard.text
    assert 'href="/requests"' in dashboard.text
    assert "urgent-banner" in dashboard.text or "/requests?filter=urgent_red_flags" in dashboard.text
    assert "TC-UX-NAV" not in dashboard.text
    assert 'class="search-sort-form filter-bar"' not in dashboard.text
    assert requests.status_code == 200
    assert "TC-UX-NAV" in requests.text
    assert 'class="search-sort-form filter-bar"' in requests.text
    assert patients.status_code == 200
    assert staff.status_code == 200
    assert reports.status_code == 200
    assert settings.status_code == 200
    assert "/requests?filter=urgent_red_flags" in dashboard.text


def test_sidebar_shell_renders_on_primary_pages_and_top_nav_is_removed(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        admin_id = conn.execute("SELECT id FROM staff_users WHERE display_name = ?", ("Admin Demo",)).fetchone()["id"]

    pages = ["/", "/requests", "/patients", "/staff", "/reports", "/settings"]
    with TestClient(app) as client:
        client.cookies.set("jefflocal_staff_id", str(admin_id))
        responses = {page: client.get(page) for page in pages}

    for page, response in responses.items():
        assert response.status_code == 200, page
        assert 'class="analytics-sidebar"' in response.text
        assert 'class="main-topbar-nav"' in response.text or 'topbar-nav' in response.text
        assert 'class="topbar"' not in response.text
        assert 'class="topnav"' not in response.text
        assert "JeffLocal Reception Dashboard</a>" not in response.text


def test_dashboard_and_requests_content_are_separated(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("TC-UX-SPLIT", iso_days_ago(0), staff_review_required=True))

    with TestClient(app) as client:
        dashboard = client.get("/")
        requests = client.get("/requests?filter=all&range=all")

    assert dashboard.status_code == 200
    assert 'class="search-sort-form filter-bar"' not in dashboard.text
    assert "TC-UX-SPLIT" not in dashboard.text
    assert "Request Mix" in dashboard.text
    assert "Staff Workload" in dashboard.text
    assert "Live Workload" in dashboard.text
    assert "System Status" in dashboard.text

    assert requests.status_code == 200
    assert "TC-UX-SPLIT" in requests.text
    assert 'class="search-sort-form filter-bar"' in requests.text
    assert "Request Mix" not in requests.text
    assert "Staff Workload" in requests.text
    assert "Live Workload" not in requests.text
    assert "System Status" not in requests.text


def test_default_date_range_selects_today(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, HANDOFF_DIR)

    with TestClient(app) as client:
        response = client.get("/requests")

    assert response.status_code == 200
    assert 'name="range"' in response.text
    assert ('option value="today" selected' in response.text) or ('option value="all" selected' in response.text)


def make_case(call_id, timestamp, priority="routine", status="New", request_type="admin", verification_status="matched", staff_review_required=True, red_flags_present=False):
    return map_handoff_to_case(
        {
            "call_id": call_id,
            "call_timestamp": timestamp,
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
        }
    )


def iso_days_ago(days: int, hour: int = 12, minute: int = 0):
    value = datetime.now(timezone.utc) - timedelta(days=days)
    value = value.replace(hour=hour, minute=minute, second=0, microsecond=0)
    return value.isoformat().replace("+00:00", "Z")


def seed_sort_cases(db_path):
    with connect(db_path) as conn:
        init_db(conn)
        for case in [
            make_case("TC-SORT-OLD", iso_days_ago(4, 12, 22), priority="routine"),
            make_case("TC-SORT-NEW", iso_days_ago(0, 12, 50), priority="routine"),
            make_case("TC-SORT-EMERGENCY", iso_days_ago(3, 12, 0), priority="999 Emergency", red_flags_present=True),
            make_case("TC-SORT-RESOLVED", iso_days_ago(0, 13, 0), priority="routine", status="Resolved"),
            make_case(
                "TC-SORT-IDENTITY",
                iso_days_ago(2, 12, 0),
                priority="review_required",
                request_type="prescription",
                verification_status="possible_match",
            ),
        ]:
            upsert_case(conn, case)


def assert_before(text, first, second):
    assert text.find(first) != -1
    assert text.find(second) != -1
    assert text.find(first) < text.find(second)


def test_worklist_default_sort_newest_first(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with TestClient(app) as client:
        response = client.get("/?filter=all&range=all")

    assert response.status_code == 200
    assert_before(response.text, "TC-SORT-EMERGENCY", "TC-SORT-RESOLVED")
    assert 'option value="newest" selected' in response.text


def test_worklist_explicit_newest_first(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with TestClient(app) as client:
        response = client.get("/?filter=all&sort=newest&range=all")

    assert response.status_code == 200
    assert_before(response.text, "TC-SORT-RESOLVED", "TC-SORT-NEW")
    assert_before(response.text, "TC-SORT-NEW", "TC-SORT-IDENTITY")


def test_worklist_sort_oldest_first(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with TestClient(app) as client:
        response = client.get("/?filter=all&sort=oldest&range=all")

    assert response.status_code == 200
    assert_before(response.text, "TC-SORT-OLD", "TC-SORT-EMERGENCY")
    assert_before(response.text, "TC-SORT-NEW", "TC-SORT-RESOLVED")


def test_worklist_sort_priority(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with TestClient(app) as client:
        response = client.get("/?filter=all&sort=priority&range=all")

    assert response.status_code == 200
    assert_before(response.text, "TC-SORT-EMERGENCY", "TC-SORT-NEW")
    assert_before(response.text, "TC-SORT-IDENTITY", "TC-SORT-NEW")


def test_worklist_sort_unresolved_first(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with TestClient(app) as client:
        response = client.get("/?filter=all&sort=unresolved&range=all")

    assert response.status_code == 200
    assert_before(response.text, "TC-SORT-EMERGENCY", "TC-SORT-RESOLVED")
    assert_before(response.text, "TC-SORT-NEW", "TC-SORT-RESOLVED")


def test_sorting_works_with_identity_filter_search_and_request_type(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with TestClient(app) as client:
        response = client.get("/?filter=identity_issues&sort=newest&q=IDENTITY&request_type=prescription&range=all")

    assert response.status_code == 200
    assert "TC-SORT-IDENTITY" in response.text
    assert "TC-SORT-NEW" not in response.text


def test_rawmock_cards_show_friendly_locked_values(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, HANDOFF_DIR)

    with TestClient(app) as client:
        response = client.get("/?filter=all&sort=newest&q=TC-012&range=all")

    assert response.status_code == 200
    assert "TC-012-MESSY-MULTI-INTENT" in response.text
    assert "routine" in response.text
    assert "card-received" in response.text  # timestamp element is rendered
    assert "Admin" in response.text
    assert "data-patient" in response.text  # patient name is embedded in card
    assert "Action" in response.text
    assert 'class="request-card' in response.text
    assert response.text.count('class="badge') >= 4
    assert "Summary" in response.text
    assert 'card-badges' in response.text  # chip row container
    assert "Review Required" in response.text  # staff review chip for TC-012
    assert "Safe To Queue" in response.text  # safe_to_queue chip for TC-012


def test_rawmock_006_emergency_marker(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        resolved_red = make_case(
            "TC-STATUS-RED-RESOLVED",
            iso_days_ago(0),
            status="Resolved",
            priority="999 Emergency",
            red_flags_present=True,
            staff_review_required=True,
        )
        resolved_red["safe_to_queue"] = False
        upsert_case(conn, resolved_red)

    with TestClient(app) as client:
        response = client.get("/?filter=resolved&sort=newest&q=TC-STATUS-RED-RESOLVED&range=all")

    assert response.status_code == 200
    assert "TC-STATUS-RED-RESOLVED" in response.text
    row = response.text.split('id="case-TC-STATUS-RED-RESOLVED"')[1].split('</article>')[0]
    # Footer-left holds the single primary status badge
    footer_section = row.split('class="card-footer-left"')[1].split('</div>', 1)[0]
    assert footer_section.count('class="badge') == 1
    assert "RESOLVED" in footer_section
    assert "EMERGENCY / RED FLAG" not in footer_section
    assert "POSSIBLE EMERGENCY" not in footer_section
    assert "999 Emergency" not in footer_section
    # Red Flag chip IS shown in card-badges for resolved emergency (audit visibility)
    assert "Red Flag" in row


def test_search_matches_patient_call_id_emis_nhs_callback(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, HANDOFF_DIR)

    searches = ["Marcus Mosey", "TC-012", "1521", "4729356187", "07111001012"]
    with TestClient(app) as client:
        for query in searches:
            response = client.get(f"/?filter=all&sort=newest&q={query}&range=all")
            assert response.status_code == 200
            assert "TC-012-MESSY-MULTI-INTENT" in response.text


def test_request_type_chips_admin_and_prescription(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, HANDOFF_DIR)

    with TestClient(app) as client:
        admin_response = client.get("/?filter=all&sort=newest&request_type=admin&range=all")
        prescription_response = client.get("/?filter=all&sort=newest&request_type=prescription&range=all")

    assert admin_response.status_code == 200
    assert "TC-012-MESSY-MULTI-INTENT" in admin_response.text
    assert "TC-001-REPEAT-EXACT" not in admin_response.text
    assert prescription_response.status_code == 200
    assert "TC-001-REPEAT-EXACT" in prescription_response.text


def test_identity_filter_includes_expected_cases(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, HANDOFF_DIR)

    with TestClient(app) as client:
        response = client.get("/?filter=identity_issues&sort=newest&range=all")

    assert response.status_code == 200
    assert "TC-008-THIRD-PARTY-POSSIBLE" in response.text
    assert "TC-009-INSUFFICIENT-ID" in response.text
    assert "TC-011-NO-MATCH" in response.text


def test_copy_buttons_disabled_when_values_missing(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    case = make_case("TC-SORT-MISSING", "2026-05-11T12:50:00Z")
    case["callback_number"] = ""
    case["emis_number"] = ""
    case["matched_patient_ref"] = ""
    case["call_summary"] = ""
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, case)

    with TestClient(app) as client:
        response = client.get("/?filter=all&q=TC-SORT-MISSING&range=all")
        detail = client.get("/case/TC-SORT-MISSING")

    assert response.status_code == 200
    assert detail.text.count('data-copy-button') >= 3
    assert 'Copied' in detail.text
    assert detail.text.count("disabled") >= 1


def test_recent_audit_history_renders_without_old_new_values(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, HANDOFF_DIR)

    with TestClient(app) as client:
        update = client.post(
            "/case/TC-012-MESSY-MULTI-INTENT/quick_action",
            data={
                "action": "start_review",
                "edited_by": "tester",
            },
            follow_redirects=False,
        )
        response = client.get("/?filter=all&q=TC-012&range=all")
        detail = client.get("/case/TC-012-MESSY-MULTI-INTENT")

    assert update.status_code == 303
    assert response.status_code == 200

    assert "Audit" in detail.text
    assert ("updated the case" in detail.text) or ("assigned the case" in detail.text) or ("updated case status" in detail.text)
    assert "cd-audit-tech" in detail.text
    assert "staff_update" in detail.text
    assert "tester" in detail.text
    assert "old_values" not in detail.text
    assert "new_values" not in detail.text


def test_date_range_filters_affect_call_list_and_counts(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with TestClient(app) as client:
        today_response = client.get("/?filter=all&range=today")
        all_response = client.get("/?filter=all&range=all")

    assert today_response.status_code == 200
    assert all_response.status_code == 200
    assert "TC-SORT-OLD" not in today_response.text
    assert "TC-SORT-NEW" in today_response.text
    # "Processed Today" now in sidebar on all pages
    assert "Request Mix" not in today_response.text
    assert "TC-SORT-OLD" in all_response.text


def test_dashboard_renders_compact_case_row_hooks_and_expanded_copy_buttons(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, HANDOFF_DIR)

    with TestClient(app) as client:
        response = client.get("/?filter=all&sort=newest&q=TC-001&range=all")
        detail = client.get("/case/TC-001-REPEAT-EXACT")

    assert response.status_code == 200
    assert "data-case-row" in response.text
    assert "data-batch-resolve-button" in response.text
    assert "request-card" in response.text
    assert "class=\"badge" in response.text
    assert "data-patient" in response.text  # patient name embedded in card
    assert "Summary" in response.text
    assert detail.status_code == 200
    assert "Copy patient record note" in detail.text or "copied_patient_record_note" in detail.text
    assert "copied_staff_task" in detail.text
    assert "Copy EMIS number" in detail.text or "cd-copy-icon" in detail.text
    assert "Staff Task" in detail.text
    assert "Conversation" in detail.text
    assert "Recording" in detail.text


def test_call_column_does_not_render_workflow_status_pill(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, HANDOFF_DIR)

    with TestClient(app) as client:
        response = client.get("/?filter=all&sort=newest&q=TC-001&range=all")

    assert response.status_code == 200
    assert 'data-case-row' in response.text
    assert "Call" in response.text
    # call-cell column was removed in the redesign — verify the class is gone
    assert 'class="call-cell"' not in response.text
    assert 'class="workflow-status-pill"' not in response.text


def test_red_flag_case_row_remains_visually_marked_and_batch_checkbox_present(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        open_red = make_case(
            "TC-STATUS-RED-OPEN",
            iso_days_ago(0),
            status="New",
            priority="999 Emergency",
            red_flags_present=True,
            staff_review_required=True,
        )
        open_red["safe_to_queue"] = False
        upsert_case(conn, open_red)

    with TestClient(app) as client:
        response = client.get("/?filter=urgent_red_flags&sort=newest&q=TC-STATUS-RED-OPEN&range=all")

    assert response.status_code == 200
    assert 'class="request-card' in response.text and 'emergency' in response.text
    assert 'class="case-select"' in response.text
    assert 'data-red-flag="true"' in response.text
    row = response.text.split('id="case-TC-STATUS-RED-OPEN"')[1].split('</article>')[0]
    # card-footer-left contains the single primary status badge
    footer_section = row.split('class="card-footer-left"')[1].split('</div>', 1)[0]
    assert footer_section.count('class="badge') == 1
    assert "OPEN" in footer_section
    assert "EMERGENCY / RED FLAG" not in footer_section
    assert "POSSIBLE EMERGENCY" not in footer_section
    # Summary chips and attention badge for open emergency appear in card-badges
    assert "999 Emergency" in row
    assert "Red Flag" in row
    assert "CALL NOW" in row  # attention badge for active emergency


def test_batch_resolve_frontend_messages_and_disabled_button_state_render(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, HANDOFF_DIR)

    with TestClient(app) as client:
        response = client.get("/requests?range=all")

    assert response.status_code == 200
    assert 'id="batch-resolve-button"' in response.text
    assert "data-batch-resolve-button" in response.text
    assert 'data-bulk-action="resolve_eligible_only"' in response.text
    assert "data-bulk-action-button" in response.text
    assert "Assign to me" in response.text
    assert "Start review" in response.text
    assert "Resolve eligible only" in response.text
    assert "Resolve eligible only will skip unsafe cases" in response.text


def test_dashboard_demo_polish_top_layout(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, HANDOFF_DIR)

    with TestClient(app) as client:
        response = client.get("/?range=all")

    assert response.status_code == 200
    assert "Service Status" not in response.text
    assert "Connect / Refresh All Services" not in response.text
    assert "System Status" in response.text
    assert "Request Mix" in response.text
    assert "Staff Workload" in response.text
    assert "Live Workload" in response.text
    assert "Failed Safety Queue" in response.text
    assert "Deadletter" not in response.text
    assert "Encrypted Raw" not in response.text
    assert "Active Processing" in response.text
    assert "Not tracked" in response.text


def test_secondary_pages_have_dashboard_navigation(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        admin_id = conn.execute("SELECT id FROM staff_users WHERE display_name = ?", ("Admin Demo",)).fetchone()["id"]
        upsert_case(conn, make_case("TC-NAV-001", iso_days_ago(0), staff_review_required=False))

    with TestClient(app) as client:
        alerts = client.get("/alerts")
        client.cookies.set("jefflocal_staff_id", str(admin_id))
        staff = client.get("/staff")
        detail = client.get("/case/TC-NAV-001")

    assert alerts.status_code == 200
    assert staff.status_code == 200
    assert detail.status_code == 200
    assert "Back to Dashboard" in alerts.text
    assert "Team operations" in staff.text
    assert "Back to Requests" in detail.text
    assert "Staff" in staff.text


def test_dashboard_warns_when_processed_task_or_summary_missing(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    case = make_case("TC-MISSING-PROCESSED", iso_days_ago(0), staff_review_required=True)
    case["task_title"] = ""
    case["task_body"] = ""
    case["call_summary"] = ""
    case["staff_task_title"] = ""
    case["staff_task_body"] = ""
    case["ai_summary"] = ""
    case["patient_record_note"] = ""
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, case)

    with TestClient(app) as client:
        response = client.get("/?filter=all&q=TC-MISSING-PROCESSED&range=all")

    assert response.status_code == 200
    assert "Processing output missing - staff review required." in response.text
    assert "staff review required" in response.text


def test_copyable_dashboard_payloads_exclude_displayed_patient_name(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    case = make_case("TC-COPY-SAFE", iso_days_ago(0), request_type="prescription", staff_review_required=False)
    case["patient_name"] = "Copy Safety"
    case["task_title"] = "Prescription request for Copy Safety"
    case["task_body"] = "Copy Safety asked for repeat medication."
    case["call_summary"] = "Copy Safety requested a routine prescription."
    case["staff_task_title"] = case["task_title"]
    case["staff_task_body"] = case["task_body"]
    case["ai_summary"] = case["call_summary"]
    case["patient_record_note"] = "EMIS: EMIS-COPY. The caller requested a routine prescription. Callback number provided: 07111000000."
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, case)

    with TestClient(app) as client:
        response = client.get("/?filter=all&q=TC-COPY-SAFE&range=all")
        detail = client.get("/case/TC-COPY-SAFE")

    assert response.status_code == 200
    assert detail.status_code == 200
    assert "Copy Safety" in response.text
    copy_payloads = re.findall(r'data-copy-text="([^"]*)"', detail.text)
    assert copy_payloads
    assert all("Copy Safety" not in payload for payload in copy_payloads)
    assert "EMIS:" in detail.text
    assert "NHS:" in detail.text


def test_status_column_renders_single_primary_status_only(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("TC-STATUS-OPEN", iso_days_ago(0), staff_review_required=False))
        upsert_case(conn, make_case("TC-STATUS-RESOLVED", iso_days_ago(0), status="Resolved", staff_review_required=False))
        upsert_case(conn, make_case("TC-STATUS-REVIEW", iso_days_ago(0), request_type="admin", status="Needs Review", staff_review_required=True))
        upsert_case(conn, make_case("TC-STATUS-IDENTITY", iso_days_ago(0), request_type="prescription", verification_status="possible_match", priority="review_required", staff_review_required=True))
        red_case = make_case("TC-STATUS-RED", iso_days_ago(0), priority="999 Emergency", red_flags_present=True, staff_review_required=True)
        red_case["safe_to_queue"] = False
        upsert_case(conn, red_case)

    with TestClient(app) as client:
        routine = client.get("/?filter=all&sort=newest&q=TC-STATUS-OPEN&range=all")
        resolved = client.get("/?filter=resolved&sort=newest&q=TC-STATUS-RESOLVED&range=all")
        review = client.get("/?filter=needs_review&sort=newest&q=TC-STATUS-REVIEW&range=all")
        identity = client.get("/?filter=identity_issues&sort=newest&q=TC-STATUS-IDENTITY&range=all")
        red_flag = client.get("/?filter=urgent_red_flags&sort=newest&q=TC-STATUS-RED&range=all")

    assert routine.status_code == 200
    assert resolved.status_code == 200
    assert review.status_code == 200
    assert identity.status_code == 200
    assert red_flag.status_code == 200

    routine_row = routine.text.split('id="case-TC-STATUS-OPEN"')[1].split('</article>')[0]
    resolved_row = resolved.text.split('id="case-TC-STATUS-RESOLVED"')[1].split('</article>')[0]
    review_row = review.text.split('id="case-TC-STATUS-REVIEW"')[1].split('</article>')[0]
    identity_row = identity.text.split('id="case-TC-STATUS-IDENTITY"')[1].split('</article>')[0]
    red_row = red_flag.text.split('id="case-TC-STATUS-RED"')[1].split('</article>')[0]

    # card-footer-left contains the single primary status badge
    assert routine_row.split('class="card-footer-left"')[1].count('class="badge') == 1
    assert "OPEN" in routine_row.split('class="card-footer-left"')[1]

    assert resolved_row.split('class="card-footer-left"')[1].count('class="badge') == 1
    assert "RESOLVED" in resolved_row.split('class="card-footer-left"')[1]

    assert review_row.split('class="card-footer-left"')[1].count('class="badge') == 1
    assert "OPEN" in review_row.split('class="card-footer-left"')[1]

    assert identity_row.split('class="card-footer-left"')[1].count('class="badge') == 1
    assert "OPEN" in identity_row.split('class="card-footer-left"')[1]

    assert red_row.split('class="card-footer-left"')[1].count('class="badge') == 1
    assert "OPEN" in red_row.split('class="card-footer-left"')[1]
    assert "EMERGENCY / RED FLAG" not in red_row.split('class="card-footer-left"')[1]
    assert "POSSIBLE EMERGENCY" not in red_row.split('class="card-footer-left"')[1]
    assert "999 Emergency" in red_row
    assert "Red Flag" in red_row
    assert "Not Safe To Queue" in red_row
    assert "CALL NOW" in red_row  # attention badge for active emergency


def test_workflow_and_risk_filters_keep_resolved_red_flags_out_of_open(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        resolved_red = make_case(
            "TC-FILTER-RED-RESOLVED",
            iso_days_ago(0),
            status="Resolved",
            priority="999 Emergency",
            red_flags_present=True,
            staff_review_required=True,
        )
        open_red = make_case(
            "TC-FILTER-RED-OPEN",
            iso_days_ago(0),
            status="New",
            priority="999 Emergency",
            red_flags_present=True,
            staff_review_required=True,
        )
        resolved_red["safe_to_queue"] = False
        open_red["safe_to_queue"] = False
        upsert_case(conn, resolved_red)
        upsert_case(conn, open_red)

    with TestClient(app) as client:
        resolved = client.get("/?filter=resolved&sort=newest&q=TC-FILTER-RED&range=all")
        open_cases = client.get("/?filter=open&sort=newest&q=TC-FILTER-RED&range=all")
        urgent = client.get("/?filter=urgent_red_flags&sort=newest&q=TC-FILTER-RED&range=all")

    assert resolved.status_code == 200
    assert open_cases.status_code == 200
    assert urgent.status_code == 200
    assert "TC-FILTER-RED-RESOLVED" in resolved.text
    assert "TC-FILTER-RED-RESOLVED" not in open_cases.text
    assert "TC-FILTER-RED-OPEN" in urgent.text


def test_display_helpers_do_not_mutate_case_risk_fields(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        case = make_case(
            "TC-DISPLAY-NO-MUTATE",
            iso_days_ago(0),
            status="Resolved",
            priority="999 Emergency",
            red_flags_present=True,
            staff_review_required=True,
        )
        case["safe_to_queue"] = False
        upsert_case(conn, case)
        before = conn.execute(
            "SELECT status, priority, red_flags_present, safe_to_queue, verification_status FROM cases WHERE call_id = ?",
            ("TC-DISPLAY-NO-MUTATE",),
        ).fetchone()

    with TestClient(app) as client:
        response = client.get("/?filter=all&sort=newest&q=TC-DISPLAY-NO-MUTATE&range=all")

    assert response.status_code == 200
    with connect(db_path) as conn:
        after = conn.execute(
            "SELECT status, priority, red_flags_present, safe_to_queue, verification_status FROM cases WHERE call_id = ?",
            ("TC-DISPLAY-NO-MUTATE",),
        ).fetchone()

    assert before == after


def test_default_dashboard_paginates_latest_twenty(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        for index in range(25):
            upsert_case(conn, make_case(f"TC-PAGE-{index:03d}", iso_days_ago(0, 10, index % 60), staff_review_required=False))

    with TestClient(app) as client:
        first = client.get("/?filter=all&range=all")
        second = client.get("/?filter=all&range=all&page=2")
        search = client.get("/?filter=all&range=all&q=TC-PAGE-024")

    assert first.status_code == 200
    assert first.text.count("data-case-row") == 20
    assert "Showing 1–20 of 25" in first.text  # template uses en-dash –
    assert "Page 1 of 2" in first.text
    assert second.status_code == 200
    assert "Page 2 of 2" in second.text
    assert search.status_code == 200
    assert "TC-PAGE-024" in search.text


def test_dashboard_selection_controls_and_filter_bar_render(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("TC-UX-SELECT-001", iso_days_ago(0), staff_review_required=False))
        upsert_case(conn, make_case("TC-UX-SELECT-002", iso_days_ago(0), staff_review_required=False))

    with TestClient(app) as client:
        response = client.get("/?filter=all&sort=newest&range=all")

    assert response.status_code == 200
    assert 'http-equiv="refresh"' not in response.text
    assert 'class="search-sort-form filter-bar"' in response.text
    assert 'name="filter"' in response.text
    assert "Active filters" in response.text
    assert "Select all visible" in response.text
    assert "Clear selection" in response.text
    assert "data-case-checkbox" in response.text
    assert "data-call-id" in response.text
    assert "data-selected-count" in response.text
    assert "data-select-all-visible" in response.text
    assert "data-clear-selection" in response.text
    assert "data-bulk-action-button" in response.text
    assert "var selectedCallIds = new Set()" in response.text
    assert "visibleSelectedCallIds()" in response.text
    assert "Selection cleared because filters changed." in response.text
    assert "Bulk actions apply to selected cases on this page only." in response.text


def test_invalid_filter_defaults_to_all_and_quick_action_preserves_return_url(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        staff_id = conn.execute("SELECT id FROM staff_users WHERE display_name = ?", ("Reception Demo",)).fetchone()["id"]
        upsert_case(conn, make_case("TC-UX-RETURN", iso_days_ago(0), staff_review_required=False))

    return_url = "/?filter=open&sort=newest&range=all"
    with TestClient(app) as client:
        invalid = client.get("/?filter=bad-filter&sort=newest&range=all")
        client.cookies.set("jefflocal_staff_id", str(staff_id))
        action = client.post(
            "/case/TC-UX-RETURN/quick_action",
            data={"action": "start_review", "return_url": return_url},
            follow_redirects=False,
        )

    assert invalid.status_code == 200
    assert '<option value="all" selected>All</option>' in invalid.text
    assert action.status_code == 303
    assert action.headers["location"] == return_url + "&notice=review_started"


def test_detail_back_link_uses_safe_return_url_and_fallback(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("TC-UX-BACK", iso_days_ago(0), staff_review_required=False))

    with TestClient(app) as client:
        from_list = client.get("/?filter=all&sort=priority&range=all&q=TC-UX-BACK")
        invalid = client.get("/case/TC-UX-BACK?return_url=https%3A%2F%2Fevil.example%2F")
        missing = client.get("/case/TC-UX-BACK")

    assert from_list.status_code == 200
    assert "return_url=/requests%3Ffilter%3Dall%26sort%3Dpriority%26range%3Dall%26q%3DTC-UX-BACK" in from_list.text
    assert invalid.status_code == 200
    assert 'href="/requests?filter=all&amp;sort=newest&amp;range=today&amp;page_size=20"' in invalid.text
    assert missing.status_code == 200
    assert 'href="/requests?filter=all&amp;sort=newest&amp;range=today&amp;page_size=20"' in missing.text


def test_readonly_staff_cannot_select_bulk_rows(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        readonly_id = conn.execute("SELECT id FROM staff_users WHERE display_name = ?", ("GP Demo",)).fetchone()["id"]
        upsert_case(conn, make_case("TC-UX-READONLY", iso_days_ago(0), staff_review_required=False))

    with TestClient(app) as client:
        client.cookies.set("jefflocal_staff_id", str(readonly_id))
        response = client.get("/?filter=all&range=all")

    assert response.status_code == 200
    row = response.text.split('id="case-TC-UX-READONLY"')[1].split("</article>")[0]
    assert "Read-only staff cannot update cases." in row
    assert "disabled" in row.split('class="case-select"')[1].split(">")[0]


def test_detail_mark_resolved_requires_confirmation_and_preserves_return_url(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        staff_id = conn.execute("SELECT id FROM staff_users WHERE display_name = ?", ("Reception Demo",)).fetchone()["id"]
        upsert_case(conn, make_case("TC-UX-DETAIL", iso_days_ago(0), staff_review_required=False))

    return_url = "/?filter=open&sort=newest&range=all"
    with TestClient(app) as client:
        client.cookies.set("jefflocal_staff_id", str(staff_id))
        detail = client.get("/case/TC-UX-DETAIL?return_url=%2F%3Ffilter%3Dopen%26sort%3Dnewest%26range%3Dall")
        missing_tick = client.post(
            "/case/TC-UX-DETAIL/update",
            data={
                "intent": "resolve",
                "return_url": return_url,
                "status": "New",
                "assigned_to": "Reception Demo",
                "action_needed": "Review and process according to local workflow.",
                "outcome_notes": "Processed according to JeffLocal workflow.",
                "staff_action": "",
                "resolved_by": "Reception Demo",
                "last_edited_by": "Reception Demo",
            },
            follow_redirects=True,
        )
        resolved = client.post(
            "/case/TC-UX-DETAIL/update",
            data={
                "intent": "resolve",
                "return_url": return_url,
                "status": "New",
                "assigned_to": "Reception Demo",
                "action_needed": "Review and process according to local workflow.",
                "outcome_notes": "Processed according to JeffLocal workflow.",
                "staff_action": "",
                "resolved_by": "Reception Demo",
                "last_edited_by": "Reception Demo",
                "mark_resolved": "yes",
            },
            follow_redirects=False,
        )

    assert detail.status_code == 200
    assert "Mark as Resolved" in detail.text
    assert "Save Staff Update" not in detail.text
    assert "Back to Requests" in detail.text
    assert "/?filter=open&amp;sort=newest&amp;range=all" in detail.text
    assert missing_tick.status_code == 200
    assert "Tick the confirmation box before marking this request as resolved." in missing_tick.text
    with connect(db_path) as conn:
        row = conn.execute("SELECT status FROM cases WHERE call_id = ?", ("TC-UX-DETAIL",)).fetchone()
        audit_count = conn.execute("SELECT COUNT(*) FROM audit_events WHERE call_id = ? AND action = 'staff_update'", ("TC-UX-DETAIL",)).fetchone()[0]
    assert row["status"] == "Resolved"
    assert audit_count >= 1
    assert resolved.status_code == 303
    assert resolved.headers["location"] == return_url + "&notice=case_resolved"


def test_staff_workflow_is_simplified_with_advanced_fields_collapsed_and_save_progress_only(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        staff_id = conn.execute("SELECT id FROM staff_users WHERE display_name = ?", ("Reception Demo",)).fetchone()["id"]
        upsert_case(conn, make_case("TC-UX-WORKFLOW", iso_days_ago(0), staff_review_required=False))
        resolved_case = make_case("TC-UX-WORKFLOW-RESOLVED", iso_days_ago(0), status="Resolved", staff_review_required=False)
        upsert_case(conn, resolved_case)

    with TestClient(app) as client:
        client.cookies.set("jefflocal_staff_id", str(staff_id))
        detail = client.get("/case/TC-UX-WORKFLOW")
        save = client.post(
            "/case/TC-UX-WORKFLOW/update",
            data={
                "intent": "save_progress",
                "status": "New",
                "assigned_to": "Reception Demo",
                "action_needed": "Review and process according to local workflow.",
                "outcome_notes": "Notes saved only",
                "staff_action": "Checked progress",
                "resolved_by": "Reception Demo",
                "last_edited_by": "Reception Demo",
                "mark_resolved": "yes",
            },
            follow_redirects=False,
        )
        resolved_detail = client.get("/case/TC-UX-WORKFLOW-RESOLVED")

    assert detail.status_code == 200
    # Locate staff workflow section via its card header div
    workflow_section = detail.text.split('<div class="cd-card-hd">Staff Workflow</div>')[1].split("</form>")[0]
    before_advanced = workflow_section.split("Advanced staff fields")[0]
    assert "Outcome note" in before_advanced
    assert "I confirm staff review is complete" in before_advanced
    assert "Save progress" in before_advanced
    assert "Assigned To" not in before_advanced
    assert 'class="advanced-staff-fields"' in workflow_section
    assert "Advanced staff fields" in workflow_section
    assert "Mark as Resolved" in workflow_section
    assert "Reception Demo" in workflow_section
    assert save.status_code == 303
    with connect(db_path) as conn:
        row = conn.execute("SELECT status, outcome_notes FROM cases WHERE call_id = ?", ("TC-UX-WORKFLOW",)).fetchone()
    assert row["status"] == "New"
    assert row["outcome_notes"] == "Notes saved only"
    assert resolved_detail.status_code == 200
    assert "Reopen" in resolved_detail.text


def test_action_needed_layout_groups_copy_buttons(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("TC-UX-COPY-LAYOUT", iso_days_ago(0), staff_review_required=False))

    with TestClient(app) as client:
        response = client.get("/case/TC-UX-COPY-LAYOUT")

    assert response.status_code == 200
    assert 'data-copy-button' in response.text
    assert "copied_patient_record_note" in response.text
    assert "copied_staff_task" in response.text
    assert "cd-copy-icon" in response.text
    assert "Staff Task" in response.text
    assert "Patient Record Note" in response.text


def test_transcript_splits_inline_speaker_labels_and_raw_transcript_is_collapsed(tmp_path, monkeypatch):
    lines = main_module.transcript_conversation_lines("Jeff: Hello. Caller: Yes. Agent: Any symptoms? Patient: No.")
    assert [line["role"] for line in lines] == ["agent", "caller", "agent", "caller"]
    assert lines[0]["speaker"] == "Jeff"
    assert lines[1]["speaker"] == "Caller"

    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        case = make_case("TC-UX-TRANSCRIPT", iso_days_ago(0), staff_review_required=False)
        case["transcript"] = "Jeff: Hello. Caller: Yes. Jeff: Are you calling about yourself? Caller: Myself."
        upsert_case(conn, case)

    with TestClient(app) as client:
        response = client.get("/case/TC-UX-TRANSCRIPT")

    assert response.status_code == 200
    assert 'conversation-line agent' in response.text
    assert 'conversation-line caller' in response.text
    assert 'class="raw-transcript"' in response.text  # may have inline style attr
    assert "Show raw transcript" in response.text
    fallback = main_module.transcript_conversation_lines("No speaker labels in this transcript.")
    assert fallback == [{"speaker": "Transcript", "role": "system", "text": "No speaker labels in this transcript."}]


def test_pathway_question_responses_render_without_raw_json(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    monkeypatch.setattr(main_module, "ROOT_DIR", tmp_path)
    payload = {
        "call_id": "TC-UX-PATHWAY",
        "request_type": "prescription",
        "normalized_input": {"caller_for": "self", "medications_requested": ["atorvastatin 20mg"], "pharmacy": "Demo Pharmacy"},
        "pathway_responses": {
            "caller_for": "self",
            "prescription": {"prescription_type": "repeat", "medications_requested": ["atorvastatin 20mg"], "pharmacy": "Demo Pharmacy", "run_out_status": "two tablets left"},
            "identity": {"callback_confirmed": True},
            "urgency_assessment": {"urgency_level": "routine", "red_flags_mentioned": [], "emergency_advice_given": False},
        },
    }
    source = tmp_path / "pathway_handoff.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    with connect(db_path) as conn:
        init_db(conn)
        case = make_case("TC-UX-PATHWAY", iso_days_ago(0), request_type="prescription", staff_review_required=False)
        case["source_path"] = str(source)
        upsert_case(conn, case)

    with TestClient(app) as client:
        response = client.get("/case/TC-UX-PATHWAY")

    assert response.status_code == 200
    assert "Pathway Questions &amp; Responses" in response.text
    assert "Prescription type" in response.text
    assert "Medication requested" in response.text
    assert "atorvastatin 20mg" in response.text
    assert "Run-out status" in response.text
    assert "Red flags mentioned" in response.text
    assert "pathway_responses" not in response.text


def test_duplicate_staff_review_text_is_deduped_for_display(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        case = make_case("TC-UX-DEDUPE", iso_days_ago(0), verification_status="possible_match", priority="review_required", staff_review_required=True)
        case["staff_task_body"] = "Patient verification: possible_match. Staff review required. Staff review required."
        case["task_body"] = case["staff_task_body"]
        case["action_needed"] = "Staff review required"
        upsert_case(conn, case)

    with TestClient(app) as client:
        response = client.get("/case/TC-UX-DEDUPE")

    assert response.status_code == 200
    assert "Staff review required. Staff review required." not in response.text
    # Internal codes are sanitized to human-readable in display text
    assert "possible_match" not in response.text or "Possible Match" in response.text
    assert "Staff review required." in response.text
    with connect(db_path) as conn:
        row = conn.execute("SELECT staff_review_required, action_needed FROM cases WHERE call_id = ?", ("TC-UX-DEDUPE",)).fetchone()
    assert row["staff_review_required"] == 1
    assert row["action_needed"] == "Staff review required"


def test_red_border_only_applies_to_true_red_flag_rows(tmp_path, monkeypatch):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("TC-UX-ROUTINE", iso_days_ago(0), staff_review_required=False))
        upsert_case(conn, make_case("TC-UX-REVIEW", iso_days_ago(0), staff_review_required=True))
        upsert_case(conn, make_case("TC-UX-IDENTITY", iso_days_ago(0), verification_status="possible_match", priority="review_required", staff_review_required=True))
        red_case = make_case("TC-UX-RED", iso_days_ago(0), priority="999 Emergency", red_flags_present=True, staff_review_required=True)
        red_case["safe_to_queue"] = False
        upsert_case(conn, red_case)

    with TestClient(app) as client:
        response = client.get("/?filter=all&sort=newest&range=all")

    assert response.status_code == 200
    routine_row = response.text.split('id="case-TC-UX-ROUTINE"')[0].split("<article")[-1]
    review_row = response.text.split('id="case-TC-UX-REVIEW"')[0].split("<article")[-1]
    identity_row = response.text.split('id="case-TC-UX-IDENTITY"')[0].split("<article")[-1]
    red_row = response.text.split('id="case-TC-UX-RED"')[0].split("<article")[-1]
    assert "emergency" not in routine_row
    assert "review-row" in review_row and "emergency" not in review_row
    assert "identity-row" in identity_row and "emergency" not in identity_row
    assert "emergency" in red_row


def test_reset_and_sender_scripts_are_confirmation_gated():
    root = DASHBOARD_ROOT.parent
    reset_script = (root / "tests" / "reset_demo_test_data.ps1").read_text(encoding="utf-8")
    sender_script = (root / "tests" / "send_gp_demo_n8n_webhook_calls.py").read_text(encoding="utf-8")

    assert "ConfirmReset" in reset_script
    assert "backup\\test_data_archives" in reset_script
    assert "Remove-Item" in reset_script
    assert "TC-GP-" in sender_script
    assert "--confirm-send" in sender_script
    assert "disable_google_push" in sender_script

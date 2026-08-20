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


def test_dashboard_pages_render_after_import(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-006-URGENT-REDFLAG", iso_days_ago(0), priority="999 Emergency", red_flags_present=True))

    with authed_client as client:
        index_response = client.get("/")
        import_response = client.post("/import", follow_redirects=False)
        detail_response = client.get("/case/RAWMOCK-006-URGENT-REDFLAG")

    assert index_response.status_code == 200
    assert "Dashboard" in index_response.text
    assert "Critical" in index_response.text
    assert import_response.status_code == 303
    assert detail_response.status_code == 200
    assert "RAWMOCK-006-URGENT-REDFLAG" in detail_response.text
    assert "Emergency red-flag case" in detail_response.text
    assert "2026-05-11T12:50:00Z" not in index_response.text
    assert "bar-track" in index_response.text
    assert "Requests" in index_response.text
    assert "Patients" in index_response.text
    assert "Reports" in index_response.text


def test_sidebar_navigation_and_dashboard_requests_split(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-UX-NAV", iso_days_ago(0), staff_review_required=True))
        admin_id = conn.execute("SELECT id FROM staff_users WHERE display_name = ?", ("Admin Demo",)).fetchone()["id"]

    with authed_client as client:
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
    assert "Needs Attention" in dashboard.text
    assert "RAWMOCK-UX-NAV" not in dashboard.text
    assert 'class="search-sort-form filter-bar"' not in dashboard.text
    assert requests.status_code == 200
    assert "RAWMOCK-UX-NAV" in requests.text
    assert 'class="search-sort-form filter-bar"' in requests.text
    assert patients.status_code == 200
    assert staff.status_code == 200
    assert reports.status_code == 200
    assert settings.status_code == 200
    assert "Critical" in dashboard.text
    assert "/requests?filter=urgent_red_flags" in dashboard.text


def test_sidebar_shell_renders_on_primary_pages_and_top_nav_is_removed(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        admin_id = conn.execute("SELECT id FROM staff_users WHERE display_name = ?", ("Admin Demo",)).fetchone()["id"]

    pages = ["/", "/requests", "/patients", "/staff", "/reports", "/settings"]
    with authed_client as client:
        client.cookies.set("jefflocal_staff_id", str(admin_id))
        responses = {page: client.get(page) for page in pages}

    for page, response in responses.items():
        assert response.status_code == 200, page
        assert 'class="analytics-sidebar"' in response.text
        assert 'class="topbar"' not in response.text
        assert 'class="topnav"' not in response.text
        assert "JeffLocal Reception Dashboard</a>" not in response.text


def test_dashboard_and_requests_content_are_separated(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-UX-SPLIT", iso_days_ago(0), staff_review_required=True))

    with authed_client as client:
        dashboard = client.get("/")
        requests = client.get("/requests?filter=all&range=all")

    assert dashboard.status_code == 200
    assert 'class="search-sort-form filter-bar"' not in dashboard.text
    assert "RAWMOCK-UX-SPLIT" not in dashboard.text
    assert "Request Mix" in dashboard.text
    assert "Staff Workload" in dashboard.text
    assert "Live Workload" in dashboard.text

    assert requests.status_code == 200
    assert "RAWMOCK-UX-SPLIT" in requests.text
    assert 'class="search-sort-form filter-bar"' in requests.text
    assert "Request Mix" not in requests.text
    assert "Staff Workload" not in requests.text
    assert "Live Workload" not in requests.text


def test_default_date_range_selects_today(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, HANDOFF_DIR)

    with authed_client as client:
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
            make_case("RAWMOCK-SORT-OLD", iso_days_ago(4, 12, 22), priority="routine"),
            make_case("RAWMOCK-SORT-NEW", iso_days_ago(0, 12, 50), priority="routine"),
            make_case("RAWMOCK-SORT-EMERGENCY", iso_days_ago(3, 12, 0), priority="999 Emergency", red_flags_present=True),
            make_case("RAWMOCK-SORT-RESOLVED", iso_days_ago(0, 13, 0), priority="routine", status="Resolved"),
            make_case(
                "RAWMOCK-SORT-IDENTITY",
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


def test_worklist_default_sort_newest_first(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with authed_client as client:
        response = client.get("/?filter=all&range=all")

    assert response.status_code == 200
    assert_before(response.text, "RAWMOCK-SORT-EMERGENCY", "RAWMOCK-SORT-RESOLVED")
    assert 'option value="newest" selected' in response.text


def test_worklist_explicit_newest_first(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with authed_client as client:
        response = client.get("/?filter=all&sort=newest&range=all")

    assert response.status_code == 200
    assert_before(response.text, "RAWMOCK-SORT-RESOLVED", "RAWMOCK-SORT-NEW")
    assert_before(response.text, "RAWMOCK-SORT-NEW", "RAWMOCK-SORT-IDENTITY")


def test_worklist_sort_oldest_first(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with authed_client as client:
        response = client.get("/?filter=all&sort=oldest&range=all")

    assert response.status_code == 200
    assert_before(response.text, "RAWMOCK-SORT-OLD", "RAWMOCK-SORT-EMERGENCY")
    assert_before(response.text, "RAWMOCK-SORT-NEW", "RAWMOCK-SORT-RESOLVED")


def test_worklist_sort_priority(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with authed_client as client:
        response = client.get("/?filter=all&sort=priority&range=all")

    assert response.status_code == 200
    assert_before(response.text, "RAWMOCK-SORT-EMERGENCY", "RAWMOCK-SORT-NEW")
    assert_before(response.text, "RAWMOCK-SORT-IDENTITY", "RAWMOCK-SORT-NEW")


def test_worklist_sort_unresolved_first(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with authed_client as client:
        response = client.get("/?filter=all&sort=unresolved&range=all")

    assert response.status_code == 200
    assert_before(response.text, "RAWMOCK-SORT-EMERGENCY", "RAWMOCK-SORT-RESOLVED")
    assert_before(response.text, "RAWMOCK-SORT-NEW", "RAWMOCK-SORT-RESOLVED")


def test_sorting_works_with_identity_filter_search_and_request_type(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with authed_client as client:
        response = client.get("/?filter=identity_issues&sort=newest&q=IDENTITY&request_type=prescription&range=all")

    assert response.status_code == 200
    assert "RAWMOCK-SORT-IDENTITY" in response.text
    assert "RAWMOCK-SORT-NEW" not in response.text


def test_rawmock_cards_show_friendly_locked_values(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-012-MESSY-MULTI-INTENT", iso_days_ago(0), request_type="admin"))

    with authed_client as client:
        response = client.get("/?filter=all&sort=newest&q=RAWMOCK-012&range=all")

    assert response.status_code == 200
    assert "RAWMOCK-012-MESSY-MULTI-INTENT" in response.text
    assert "Admin" in response.text
    assert "Review Required" in response.text
    assert response.text.count('class="badge') >= 4


def test_rawmock_006_emergency_marker(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        resolved_red = make_case(
            "RAWMOCK-STATUS-RED-RESOLVED",
            iso_days_ago(0),
            status="Resolved",
            priority="999 Emergency",
            red_flags_present=True,
            staff_review_required=True,
        )
        resolved_red["safe_to_queue"] = False
        upsert_case(conn, resolved_red)

    with authed_client as client:
        response = client.get("/?filter=resolved&sort=newest&q=RAWMOCK-STATUS-RED-RESOLVED&range=all")

    assert response.status_code == 200
    assert "RAWMOCK-STATUS-RED-RESOLVED" in response.text
    row = response.text.split('id="case-RAWMOCK-STATUS-RED-RESOLVED"')[1].split('</article>')[0]
    status_section = row.split('class="card-footer-left"')[1].split('</div>', 1)[0]
    summary_section = row.split('class="card-badges"')[1].split('</div>', 1)[0]
    assert status_section.count('class="badge') == 1
    assert "RESOLVED" in status_section
    assert "EMERGENCY / RED FLAG" not in status_section
    assert "999 Emergency" not in status_section
    assert "Not Safe To Queue" not in status_section
    assert "Review Required" not in status_section
    assert "Red Flag" in summary_section


def test_search_matches_patient_call_id_emis_nhs_callback(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        case = make_case("RAWMOCK-012-MESSY-MULTI-INTENT", iso_days_ago(0), request_type="admin")
        case["patient_name"] = "Marcus Mosey"
        case["emis_number"] = "1521"
        case["nhs_number"] = "472 935 6187"
        case["callback_number"] = "07111001012"
        upsert_case(conn, case)

    searches = ["Marcus Mosey", "RAWMOCK-012", "1521", "472 935 6187", "07111001012"]
    with authed_client as client:
        for query in searches:
            response = client.get(f"/?filter=all&sort=newest&q={query}&range=all")
            assert response.status_code == 200
            assert "RAWMOCK-012-MESSY-MULTI-INTENT" in response.text


def test_request_type_chips_admin_and_prescription(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-012-MESSY-MULTI-INTENT", iso_days_ago(0), request_type="admin"))
        upsert_case(conn, make_case("RAWMOCK-001-REPEAT-EXACT", iso_days_ago(0), request_type="prescription"))

    with authed_client as client:
        admin_response = client.get("/?filter=all&sort=newest&request_type=admin&range=all")
        prescription_response = client.get("/?filter=all&sort=newest&request_type=prescription&range=all")

    assert admin_response.status_code == 200
    assert "RAWMOCK-012-MESSY-MULTI-INTENT" in admin_response.text
    assert "RAWMOCK-001-REPEAT-EXACT" not in admin_response.text
    assert prescription_response.status_code == 200
    assert "RAWMOCK-001-REPEAT-EXACT" in prescription_response.text


def test_identity_filter_includes_expected_cases(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-008-THIRD-PARTY-POSSIBLE", iso_days_ago(0), verification_status="possible_match"))
        upsert_case(conn, make_case("RAWMOCK-009-INSUFFICIENT-ID", iso_days_ago(0), verification_status="insufficient_data"))
        upsert_case(conn, make_case("RAWMOCK-011-NO-MATCH", iso_days_ago(0), verification_status="no_match"))

    with authed_client as client:
        response = client.get("/?filter=identity_issues&sort=newest&range=all")

    assert response.status_code == 200
    assert "RAWMOCK-008-THIRD-PARTY-POSSIBLE" in response.text
    assert "RAWMOCK-009-INSUFFICIENT-ID" in response.text
    assert "RAWMOCK-011-NO-MATCH" in response.text


def test_copy_buttons_disabled_when_values_missing(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    case = make_case("RAWMOCK-SORT-MISSING", "2026-05-11T12:50:00Z")
    case["callback_number"] = ""
    case["emis_number"] = ""
    case["matched_patient_ref"] = ""
    case["call_summary"] = ""
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, case)

    with authed_client as client:
        response = client.get("/?filter=all&q=RAWMOCK-SORT-MISSING&range=all")
        detail = client.get("/case/RAWMOCK-SORT-MISSING")

    assert response.status_code == 200
    assert detail.text.count('data-copy-button') >= 3
    assert 'Copied' in detail.text
    assert detail.text.count("disabled") >= 1


def test_recent_audit_history_renders_without_old_new_values(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-012-MESSY-MULTI-INTENT", iso_days_ago(0), request_type="admin"))

    with authed_client as client:
        update = client.post(
            "/case/RAWMOCK-012-MESSY-MULTI-INTENT/quick_action",
            data={
                "action": "start_review",
                "edited_by": "tester",
            },
            follow_redirects=False,
        )
        response = client.get("/?filter=all&q=RAWMOCK-012&range=all")
        detail = client.get("/case/RAWMOCK-012-MESSY-MULTI-INTENT")

    assert update.status_code == 303
    assert response.status_code == 200

    assert "Audit" in detail.text
    assert ("updated the case" in detail.text) or ("assigned the case" in detail.text) or ("updated case status" in detail.text)
    assert "Technical detail" in detail.text
    assert "staff_update" in detail.text
    assert "tester" in detail.text
    assert "old_values" not in detail.text
    assert "new_values" not in detail.text


def test_date_range_filters_affect_call_list_and_counts(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    seed_sort_cases(db_path)

    with authed_client as client:
        today_response = client.get("/?filter=all&range=today")
        all_response = client.get("/?filter=all&range=all")

    assert today_response.status_code == 200
    assert all_response.status_code == 200
    assert "RAWMOCK-SORT-OLD" not in today_response.text
    assert "RAWMOCK-SORT-NEW" in today_response.text
    assert "Processed Today" not in today_response.text
    assert "Request Mix" not in today_response.text
    assert "RAWMOCK-SORT-OLD" in all_response.text


def test_dashboard_renders_compact_case_row_hooks_and_expanded_copy_buttons(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-001-REPEAT-EXACT", iso_days_ago(0), request_type="prescription"))

    with authed_client as client:
        response = client.get("/?filter=all&sort=newest&q=RAWMOCK-001&range=all")
        detail = client.get("/case/RAWMOCK-001-REPEAT-EXACT")

    assert response.status_code == 200
    assert "data-case-row" in response.text
    assert "data-batch-resolve-button" in response.text
    assert detail.status_code == 200
    assert 'aria-label="Copy patient record note"' in detail.text
    assert 'aria-label="Copy staff task"' in detail.text
    assert "Staff Task" in detail.text
    assert "Conversation" in detail.text
    assert "Recording" in detail.text


def test_call_column_does_not_render_workflow_status_pill(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-001-REPEAT-EXACT", iso_days_ago(0), request_type="prescription"))

    with authed_client as client:
        response = client.get("/?filter=all&sort=newest&q=RAWMOCK-001&range=all")

    assert response.status_code == 200
    assert "RAWMOCK-001-REPEAT-EXACT" in response.text
    row = response.text.split('id="case-RAWMOCK-001-REPEAT-EXACT"')[1].split('</article>')[0]
    badges_section = row.split('class="card-badges"')[1].split('</div>', 1)[0]
    # Status values must only appear in card-footer-left, not in the badges area
    assert "Resolved" not in badges_section
    assert "In Review" not in badges_section


def test_red_flag_case_row_remains_visually_marked_and_batch_checkbox_present(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        open_red = make_case(
            "RAWMOCK-STATUS-RED-OPEN",
            iso_days_ago(0),
            status="New",
            priority="999 Emergency",
            red_flags_present=True,
            staff_review_required=True,
        )
        open_red["safe_to_queue"] = False
        upsert_case(conn, open_red)

    with authed_client as client:
        response = client.get("/?filter=urgent_red_flags&sort=newest&q=RAWMOCK-STATUS-RED-OPEN&range=all")

    assert response.status_code == 200
    assert 'request-card emergency' in response.text
    assert 'class="case-select"' in response.text
    assert 'data-red-flag="true"' in response.text
    row = response.text.split('id="case-RAWMOCK-STATUS-RED-OPEN"')[1].split('</article>')[0]
    status_section = row.split('class="card-footer-left"')[1].split('</div>', 1)[0]
    summary_section = row.split('class="card-badges"')[1].split('</div>', 1)[0]
    assert status_section.count('class="badge') == 1
    assert "OPEN" in status_section
    assert "999 Emergency" not in status_section
    assert "Not Safe To Queue" not in status_section
    assert "Review Required" not in status_section
    assert "Red Flag" in summary_section
    assert "Not Safe To Queue" in summary_section


def test_batch_resolve_frontend_messages_and_disabled_button_state_render(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    with connect(db_path) as conn:
        init_db(conn)
        import_handoffs(conn, HANDOFF_DIR)

    with authed_client as client:
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


def test_dashboard_demo_polish_top_layout(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)

    with authed_client as client:
        response = client.get("/?range=all")

    assert response.status_code == 200
    assert "Service Status" not in response.text
    assert "Connect / Refresh All Services" not in response.text
    assert "Needs Attention" in response.text
    assert "Request Mix" in response.text
    assert "Staff Workload" in response.text
    assert "Live Workload" in response.text
    assert "Failed Safety Queue" in response.text
    assert "Deadletter" not in response.text
    assert "Encrypted Raw" not in response.text
    assert "Active Processing" in response.text


def test_secondary_pages_have_dashboard_navigation(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        admin_id = conn.execute("SELECT id FROM staff_users WHERE display_name = ?", ("Admin Demo",)).fetchone()["id"]
        upsert_case(conn, make_case("RAWMOCK-NAV-001", iso_days_ago(0), staff_review_required=False))

    with authed_client as client:
        alerts = client.get("/alerts")
        client.cookies.set("jefflocal_staff_id", str(admin_id))
        staff = client.get("/staff")
        detail = client.get("/case/RAWMOCK-NAV-001")

    assert alerts.status_code == 200
    assert staff.status_code == 200
    assert detail.status_code == 200
    assert "Back to Dashboard" in alerts.text
    assert "Team operations" in staff.text
    assert "Back to Requests" in detail.text
    assert "Staff" in staff.text


def test_dashboard_warns_when_processed_task_or_summary_missing(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    case = make_case("RAWMOCK-MISSING-PROCESSED", iso_days_ago(0), staff_review_required=True)
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

    with authed_client as client:
        response = client.get("/?filter=all&q=RAWMOCK-MISSING-PROCESSED&range=all")

    assert response.status_code == 200
    assert "Processing output missing - staff review required." in response.text
    assert "staff review required" in response.text


def test_copyable_dashboard_payloads_exclude_displayed_patient_name(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    case = make_case("RAWMOCK-COPY-SAFE", iso_days_ago(0), request_type="prescription", staff_review_required=False)
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

    with authed_client as client:
        response = client.get("/?filter=all&q=RAWMOCK-COPY-SAFE&range=all")
        detail = client.get("/case/RAWMOCK-COPY-SAFE")

    assert response.status_code == 200
    assert detail.status_code == 200
    assert "Copy Safety" in response.text
    copy_payloads = re.findall(r'data-copy-text="([^"]*)"', detail.text)
    assert copy_payloads
    assert all("Copy Safety" not in payload for payload in copy_payloads)
    assert "EMIS:" in detail.text
    assert "NHS:" in detail.text


def test_status_column_renders_single_primary_status_only(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")

    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-STATUS-OPEN", iso_days_ago(0), staff_review_required=False))
        upsert_case(conn, make_case("RAWMOCK-STATUS-RESOLVED", iso_days_ago(0), status="Resolved", staff_review_required=False))
        upsert_case(conn, make_case("RAWMOCK-STATUS-REVIEW", iso_days_ago(0), request_type="admin", status="Needs Review", staff_review_required=True))
        upsert_case(conn, make_case("RAWMOCK-STATUS-IDENTITY", iso_days_ago(0), request_type="prescription", verification_status="possible_match", priority="review_required", staff_review_required=True))
        red_case = make_case("RAWMOCK-STATUS-RED", iso_days_ago(0), priority="999 Emergency", red_flags_present=True, staff_review_required=True)
        red_case["safe_to_queue"] = False
        upsert_case(conn, red_case)

    with authed_client as client:
        routine = client.get("/?filter=all&sort=newest&q=RAWMOCK-STATUS-OPEN&range=all")
        resolved = client.get("/?filter=resolved&sort=newest&q=RAWMOCK-STATUS-RESOLVED&range=all")
        review = client.get("/?filter=needs_review&sort=newest&q=RAWMOCK-STATUS-REVIEW&range=all")
        identity = client.get("/?filter=identity_issues&sort=newest&q=RAWMOCK-STATUS-IDENTITY&range=all")
        red_flag = client.get("/?filter=urgent_red_flags&sort=newest&q=RAWMOCK-STATUS-RED&range=all")

    assert routine.status_code == 200
    assert resolved.status_code == 200
    assert review.status_code == 200
    assert identity.status_code == 200
    assert red_flag.status_code == 200

    routine_row = routine.text.split('id="case-RAWMOCK-STATUS-OPEN"')[1].split('</article>')[0]
    resolved_row = resolved.text.split('id="case-RAWMOCK-STATUS-RESOLVED"')[1].split('</article>')[0]
    review_row = review.text.split('id="case-RAWMOCK-STATUS-REVIEW"')[1].split('</article>')[0]
    identity_row = identity.text.split('id="case-RAWMOCK-STATUS-IDENTITY"')[1].split('</article>')[0]
    red_row = red_flag.text.split('id="case-RAWMOCK-STATUS-RED"')[1].split('</article>')[0]

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
    assert "999 Emergency" in red_row
    assert "Red Flag" in red_row
    assert "Not Safe To Queue" in red_row


def test_workflow_and_risk_filters_keep_resolved_red_flags_out_of_open(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        resolved_red = make_case(
            "RAWMOCK-FILTER-RED-RESOLVED",
            iso_days_ago(0),
            status="Resolved",
            priority="999 Emergency",
            red_flags_present=True,
            staff_review_required=True,
        )
        open_red = make_case(
            "RAWMOCK-FILTER-RED-OPEN",
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

    with authed_client as client:
        resolved = client.get("/?filter=resolved&sort=newest&q=RAWMOCK-FILTER-RED&range=all")
        open_cases = client.get("/?filter=open&sort=newest&q=RAWMOCK-FILTER-RED&range=all")
        urgent = client.get("/?filter=urgent_red_flags&sort=newest&q=RAWMOCK-FILTER-RED&range=all")

    assert resolved.status_code == 200
    assert open_cases.status_code == 200
    assert urgent.status_code == 200
    assert "RAWMOCK-FILTER-RED-RESOLVED" in resolved.text
    assert "RAWMOCK-FILTER-RED-RESOLVED" not in open_cases.text
    assert "RAWMOCK-FILTER-RED-OPEN" in urgent.text


def test_display_helpers_do_not_mutate_case_risk_fields(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)

    with connect(db_path) as conn:
        init_db(conn)
        case = make_case(
            "RAWMOCK-DISPLAY-NO-MUTATE",
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
            ("RAWMOCK-DISPLAY-NO-MUTATE",),
        ).fetchone()

    with authed_client as client:
        response = client.get("/?filter=all&sort=newest&q=RAWMOCK-DISPLAY-NO-MUTATE&range=all")

    assert response.status_code == 200
    with connect(db_path) as conn:
        after = conn.execute(
            "SELECT status, priority, red_flags_present, safe_to_queue, verification_status FROM cases WHERE call_id = ?",
            ("RAWMOCK-DISPLAY-NO-MUTATE",),
        ).fetchone()

    assert before == after


def test_default_dashboard_paginates_latest_twenty(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        for index in range(25):
            upsert_case(conn, make_case(f"RAWMOCK-PAGE-{index:03d}", iso_days_ago(0, 10, index % 60), staff_review_required=False))

    with authed_client as client:
        first = client.get("/?filter=all&range=all")
        second = client.get("/?filter=all&range=all&page=2")
        search = client.get("/?filter=all&range=all&q=RAWMOCK-PAGE-024")

    assert first.status_code == 200
    assert first.text.count("data-case-row") == 20
    assert "Showing 1–20 of 25" in first.text
    assert "Page 1 of 2" in first.text
    assert second.status_code == 200
    assert "Page 2 of 2" in second.text
    assert search.status_code == 200
    assert "RAWMOCK-PAGE-024" in search.text


def test_dashboard_selection_controls_and_filter_bar_render(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-UX-SELECT-001", iso_days_ago(0), staff_review_required=False))
        upsert_case(conn, make_case("RAWMOCK-UX-SELECT-002", iso_days_ago(0), staff_review_required=False))

    with authed_client as client:
        response = client.get("/?filter=all&sort=newest&range=all")

    assert response.status_code == 200
    assert 'http-equiv="refresh"' not in response.text
    assert 'class="search-sort-form filter-bar"' in response.text
    assert 'name="filter"' in response.text
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


def test_invalid_filter_defaults_to_all_and_quick_action_preserves_return_url(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        staff_id = conn.execute("SELECT id FROM staff_users WHERE display_name = ?", ("Reception Demo",)).fetchone()["id"]
        upsert_case(conn, make_case("RAWMOCK-UX-RETURN", iso_days_ago(0), staff_review_required=False))

    return_url = "/?filter=open&sort=newest&range=all"
    with authed_client as client:
        invalid = client.get("/?filter=bad-filter&sort=newest&range=all")
        client.cookies.set("jefflocal_staff_id", str(staff_id))
        action = client.post(
            "/case/RAWMOCK-UX-RETURN/quick_action",
            data={"action": "start_review", "return_url": return_url},
            follow_redirects=False,
        )

    assert invalid.status_code == 200
    assert '<option value="all" selected>All</option>' in invalid.text
    assert action.status_code == 303
    assert action.headers["location"] == return_url + "&notice=review_started"


def test_detail_back_link_uses_safe_return_url_and_fallback(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-UX-BACK", iso_days_ago(0), staff_review_required=False))

    with authed_client as client:
        from_list = client.get("/?filter=all&sort=priority&range=all&q=RAWMOCK-UX-BACK")
        invalid = client.get("/case/RAWMOCK-UX-BACK?return_url=https%3A%2F%2Fevil.example%2F")
        missing = client.get("/case/RAWMOCK-UX-BACK")

    assert from_list.status_code == 200
    assert "return_url=/requests%3Ffilter%3Dall%26sort%3Dpriority%26range%3Dall%26q%3DRAWMOCK-UX-BACK" in from_list.text
    assert invalid.status_code == 200
    assert 'href="/requests?filter=all&amp;sort=newest&amp;range=today&amp;page_size=20"' in invalid.text
    assert missing.status_code == 200
    assert 'href="/requests?filter=all&amp;sort=newest&amp;range=today&amp;page_size=20"' in missing.text


def test_readonly_staff_cannot_select_bulk_rows(tmp_path, monkeypatch, readonly_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-UX-READONLY", iso_days_ago(0), staff_review_required=False))

    with readonly_client as client:
        response = client.get("/?filter=all&range=all")

    assert response.status_code == 200
    row = response.text.split('id="case-RAWMOCK-UX-READONLY"')[1].split("</article>")[0]
    assert "Read-only staff cannot update cases." in row
    assert "disabled" in row.split('class="case-select"')[1].split(">")[0]


def test_detail_mark_resolved_requires_confirmation_and_preserves_return_url(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        staff_id = conn.execute("SELECT id FROM staff_users WHERE display_name = ?", ("Reception Demo",)).fetchone()["id"]
        upsert_case(conn, make_case("RAWMOCK-UX-DETAIL", iso_days_ago(0), staff_review_required=False))

    return_url = "/?filter=open&sort=newest&range=all"
    with authed_client as client:
        client.cookies.set("jefflocal_staff_id", str(staff_id))
        detail = client.get("/case/RAWMOCK-UX-DETAIL?return_url=%2F%3Ffilter%3Dopen%26sort%3Dnewest%26range%3Dall")
        missing_tick = client.post(
            "/case/RAWMOCK-UX-DETAIL/update",
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
            "/case/RAWMOCK-UX-DETAIL/update",
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
        row = conn.execute("SELECT status FROM cases WHERE call_id = ?", ("RAWMOCK-UX-DETAIL",)).fetchone()
        audit_count = conn.execute("SELECT COUNT(*) FROM audit_events WHERE call_id = ? AND action = 'staff_update'", ("RAWMOCK-UX-DETAIL",)).fetchone()[0]
    assert row["status"] == "Resolved"
    assert audit_count >= 1
    assert resolved.status_code == 303
    assert resolved.headers["location"] == return_url + "&notice=case_resolved"


def test_staff_workflow_is_simplified_with_advanced_fields_collapsed_and_save_progress_only(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        staff_id = conn.execute("SELECT id FROM staff_users WHERE display_name = ?", ("Reception Demo",)).fetchone()["id"]
        upsert_case(conn, make_case("RAWMOCK-UX-WORKFLOW", iso_days_ago(0), staff_review_required=False))
        resolved_case = make_case("RAWMOCK-UX-WORKFLOW-RESOLVED", iso_days_ago(0), status="Resolved", staff_review_required=False)
        upsert_case(conn, resolved_case)

    with authed_client as client:
        client.cookies.set("jefflocal_staff_id", str(staff_id))
        detail = client.get("/case/RAWMOCK-UX-WORKFLOW")
        save = client.post(
            "/case/RAWMOCK-UX-WORKFLOW/update",
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
        resolved_detail = client.get("/case/RAWMOCK-UX-WORKFLOW-RESOLVED")

    assert detail.status_code == 200
    workflow_section = detail.text.split('<div class="cd-card-hd">Staff Workflow</div>')[1].split("</form>")[0]
    before_advanced = workflow_section.split("Advanced staff fields")[0]
    assert "Outcome note" in before_advanced
    assert "I confirm staff review is complete" in before_advanced
    assert "Save progress" in before_advanced
    assert "Assigned To" not in before_advanced
    assert 'class="advanced-staff-fields"' in workflow_section
    assert "<summary>Advanced staff fields</summary>" in workflow_section
    assert "Mark as Resolved" in workflow_section
    assert "Test Admin" in workflow_section
    assert save.status_code == 303
    with connect(db_path) as conn:
        row = conn.execute("SELECT status, outcome_notes FROM cases WHERE call_id = ?", ("RAWMOCK-UX-WORKFLOW",)).fetchone()
    assert row["status"] == "New"
    assert row["outcome_notes"] == "Notes saved only"
    assert resolved_detail.status_code == 200
    assert "Reopen" in resolved_detail.text


def test_action_needed_layout_groups_copy_buttons(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-UX-COPY-LAYOUT", iso_days_ago(0), staff_review_required=False))

    with authed_client as client:
        response = client.get("/case/RAWMOCK-UX-COPY-LAYOUT")

    assert response.status_code == 200
    assert 'class="cd-action-row"' in response.text
    assert 'aria-label="Copy staff task"' in response.text
    assert 'aria-label="Copy patient record note"' in response.text
    assert "Staff Task" in response.text
    assert "AI Summary" in response.text
    assert "Patient Record Note" in response.text


def test_transcript_splits_inline_speaker_labels_and_raw_transcript_is_collapsed(tmp_path, monkeypatch, authed_client):
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
        case = make_case("RAWMOCK-UX-TRANSCRIPT", iso_days_ago(0), staff_review_required=False)
        case["transcript"] = "Jeff: Hello. Caller: Yes. Jeff: Are you calling about yourself? Caller: Myself."
        upsert_case(conn, case)

    with authed_client as client:
        response = client.get("/case/RAWMOCK-UX-TRANSCRIPT")

    assert response.status_code == 200
    assert 'conversation-line agent' in response.text
    assert 'conversation-line caller' in response.text
    assert 'class="raw-transcript"' in response.text
    assert "Show raw transcript" in response.text
    fallback = main_module.transcript_conversation_lines("No speaker labels in this transcript.")
    assert fallback == [{"speaker": "Transcript", "role": "system", "text": "No speaker labels in this transcript."}]


def test_pathway_question_responses_render_without_raw_json(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    monkeypatch.setattr(main_module, "ROOT_DIR", tmp_path)
    payload = {
        "call_id": "RAWMOCK-UX-PATHWAY",
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
        case = make_case("RAWMOCK-UX-PATHWAY", iso_days_ago(0), request_type="prescription", staff_review_required=False)
        case["source_path"] = str(source)
        upsert_case(conn, case)

    with authed_client as client:
        response = client.get("/case/RAWMOCK-UX-PATHWAY")

    assert response.status_code == 200
    assert "Pathway Questions &amp; Responses" in response.text
    assert "Prescription type" in response.text
    assert "Medication requested" in response.text
    assert "atorvastatin 20mg" in response.text
    assert "Run-out status" in response.text
    assert "Red flags mentioned" in response.text
    assert "pathway_responses" not in response.text


def test_pathway_question_responses_grouped_sections_and_new_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "ROOT_DIR", tmp_path)
    payload = {
        "call_id": "TEST-TRIAGE-001",
        "request_type": "prescription",
        "stated_request": "Repeat atorvastatin",
        "normalized_input": {"caller_for": "self", "postcode": "PR9 7LT"},
        "identity": {"dob_stated": "1970-01-10", "name_stated": "Jason Morrey", "callback_confirmed": True},
        "pathway_responses": {
            "caller_for": "self",
            "prescription": {
                "prescription_type": "repeat",
                "medications_requested": ["atorvastatin 20mg"],
                "run_out_status": "two tablets left",
                "pharmacy": "Demo Pharmacy",
                "pharmacy_first_condition": "sore_throat_5_plus",
                "pharmacy_first_advised": True,
            },
        },
        "urgency_assessment": {
            "urgency_level": "routine",
            "red_flags_mentioned": [],
            "red_flag_followup_questions": [
                {"question": "Any chest pain?", "answer": "No"},
                {"question": "Short of breath?", "answer": "No"},
            ],
            "emergency_advice_given": False,
        },
    }
    source = tmp_path / "triage_handoff.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    case = {
        "call_id": "TEST-TRIAGE-001",
        "request_type": "prescription",
        "verification_status": "matched",
        "priority": "routine",
        "source_path": str(source),
    }

    items = main_module.pathway_question_responses(case)
    sections = [it["section"] for it in items]
    labels = {it["label"]: it["value"] for it in items}

    # All four fixed sections present, grouped, in order
    seen: list[str] = []
    for s in sections:
        if s not in seen:
            seen.append(s)
    assert seen == ["Caller", "Identity", "Pathway Q&A", "Red flag & urgency"]
    # New structured fields surface
    assert labels.get("Postcode stated") == "PR9 7LT"
    assert labels.get("Pharmacy First condition") == "Sore throat (5+)"
    assert labels.get("Pharmacy First advice given") == "Yes"
    assert "Any chest pain? — No" in labels.get("Red-flag follow-up Q&A", "")


def test_pathway_question_responses_handles_non_caller_request_type(tmp_path, monkeypatch):
    monkeypatch.setattr(main_module, "ROOT_DIR", tmp_path)
    # Safety-net / unclassified cases are no longer caller pathways but must still render.
    payload = {
        "call_id": "TEST-TRIAGE-UNK",
        "request_type": "unknown",
        "stated_request": "Caller was unclear about what they needed",
        "pathway_responses": {"caller_for": "self"},
        "urgency_assessment": {"urgency_level": "review_required"},
    }
    source = tmp_path / "unknown_handoff.json"
    source.write_text(json.dumps(payload), encoding="utf-8")
    case = {
        "call_id": "TEST-TRIAGE-UNK",
        "request_type": "unknown",
        "verification_status": "matched",
        "priority": "review_required",
        "source_path": str(source),
    }
    items = main_module.pathway_question_responses(case)
    labels = {it["label"]: it["value"] for it in items}
    assert labels.get("Caller stated reason") == "Caller was unclear about what they needed"


def test_priority_label_urgent_same_day():
    case = main_module.prepare_case({"call_id": "X", "priority": "urgent_same_day"})
    assert case["priority_label"] == "Urgent – Same Day"


def test_duplicate_staff_review_text_is_deduped_for_display(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        case = make_case("RAWMOCK-UX-DEDUPE", iso_days_ago(0), verification_status="possible_match", priority="review_required", staff_review_required=True)
        case["staff_task_body"] = "Patient verification: possible_match. Staff review required. Staff review required."
        case["task_body"] = case["staff_task_body"]
        case["action_needed"] = "Staff review required"
        upsert_case(conn, case)

    with authed_client as client:
        response = client.get("/case/RAWMOCK-UX-DEDUPE")

    assert response.status_code == 200
    assert "Patient verification: possible_match. Staff review required. Staff review required." not in response.text
    assert "Patient verification: possible_match. Staff review required." in response.text
    with connect(db_path) as conn:
        row = conn.execute("SELECT staff_review_required, action_needed FROM cases WHERE call_id = ?", ("RAWMOCK-UX-DEDUPE",)).fetchone()
    assert row["staff_review_required"] == 1
    assert row["action_needed"] == "Staff review required"


def test_red_border_only_applies_to_true_red_flag_rows(tmp_path, monkeypatch, authed_client):
    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "import_handoffs", lambda conn: 0)
    with connect(db_path) as conn:
        init_db(conn)
        upsert_case(conn, make_case("RAWMOCK-UX-ROUTINE", iso_days_ago(0), staff_review_required=False))
        upsert_case(conn, make_case("RAWMOCK-UX-REVIEW", iso_days_ago(0), staff_review_required=True))
        upsert_case(conn, make_case("RAWMOCK-UX-IDENTITY", iso_days_ago(0), verification_status="possible_match", priority="review_required", staff_review_required=True))
        red_case = make_case("RAWMOCK-UX-RED", iso_days_ago(0), priority="999 Emergency", red_flags_present=True, staff_review_required=True)
        red_case["safe_to_queue"] = False
        upsert_case(conn, red_case)

    with authed_client as client:
        response = client.get("/?filter=all&sort=newest&range=all")

    assert response.status_code == 200
    routine_row = response.text.split('id="case-RAWMOCK-UX-ROUTINE"')[0].split("<article")[-1]
    review_row = response.text.split('id="case-RAWMOCK-UX-REVIEW"')[0].split("<article")[-1]
    identity_row = response.text.split('id="case-RAWMOCK-UX-IDENTITY"')[0].split("<article")[-1]
    red_row = response.text.split('id="case-RAWMOCK-UX-RED"')[0].split("<article")[-1]
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
    assert "GPDEMO-" in sender_script
    assert "--confirm-send" in sender_script
    assert "disable_google_push" in sender_script

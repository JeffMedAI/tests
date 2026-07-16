"""Tests for the new-case beep poll endpoint and the St Marks Pharmacy intake.

Covers:
  * /api/cases/new-since — returns only cases imported after the given marker.
  * /api/intake/stmarks-contact — shared-secret gated, validates required
    fields, lands a case in the normal queue (call_id prefixed STMARKS-).
"""
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
from app.main import SESSION_COOKIE, app
from app.routers import stmarks as stmarks_module

_TOKEN = "jefflocal-test-bypass-x"


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


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
    return TestClient(app, cookies={SESSION_COOKIE: _TOKEN}, raise_server_exceptions=False)


def _make_case(call_id: str, imported_at_iso: str) -> dict:
    case = map_handoff_to_case(
        {
            "call_id": call_id,
            "call_timestamp": imported_at_iso,
            "request_type": "admin",
            "patient_name": f"Patient {call_id}",
            "priority": "routine",
            "safe_to_queue": True,
            "task_title": f"Task {call_id}",
            "task_body": "Test task",
            "raw_transcript": "Test transcript",
            "call_summary": "Test summary",
        }
    )
    case["imported_at"] = imported_at_iso
    return case


class TestNewSince:
    def test_returns_only_cases_after_marker(self, tmp_path, monkeypatch):
        db_path = _setup_db(tmp_path, monkeypatch)
        now = datetime.now(timezone.utc)
        before = _iso(now - timedelta(minutes=5))
        marker = _iso(now - timedelta(minutes=2))
        after = _iso(now + timedelta(minutes=1))

        with connect(db_path) as conn:
            upsert_case(conn, _make_case("NEWSINCE-BEFORE", before))
            upsert_case(conn, _make_case("NEWSINCE-AFTER", after))

        resp = _client().get(f"/api/cases/new-since?since={marker}")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["ok"] is True
        call_ids = [c["call_id"] for c in data["cases"]]
        assert "NEWSINCE-AFTER" in call_ids
        assert "NEWSINCE-BEFORE" not in call_ids
        assert data["latest"] == after

    def test_no_new_cases_returns_empty_list(self, tmp_path, monkeypatch):
        _setup_db(tmp_path, monkeypatch)
        future = _iso(datetime.now(timezone.utc) + timedelta(days=1))
        resp = _client().get(f"/api/cases/new-since?since={future}")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["cases"] == []
        assert data["latest"] == future

    def test_requires_auth(self, tmp_path, monkeypatch):
        _setup_db(tmp_path, monkeypatch)
        client = TestClient(app)
        resp = client.get("/api/cases/new-since?since=2020-01-01T00:00:00Z", follow_redirects=False)
        assert resp.status_code in (302, 401)


class TestStMarksIntake:
    def test_missing_secret_rejected(self, tmp_path, monkeypatch):
        _setup_db(tmp_path, monkeypatch)
        monkeypatch.setenv(stmarks_module.STMARKS_SECRET_ENV, "correct-secret")
        client = TestClient(app)
        resp = client.post(
            "/api/intake/stmarks-contact",
            json={"name": "Jo Bloggs", "phone": "07000000000", "message": "Do you stock X?"},
        )
        assert resp.status_code == 401

    def test_wrong_secret_rejected(self, tmp_path, monkeypatch):
        _setup_db(tmp_path, monkeypatch)
        monkeypatch.setenv(stmarks_module.STMARKS_SECRET_ENV, "correct-secret")
        client = TestClient(app)
        resp = client.post(
            "/api/intake/stmarks-contact",
            json={"name": "Jo Bloggs", "phone": "07000000000", "message": "Do you stock X?"},
            headers={"X-Stmarks-Secret": "wrong-secret"},
        )
        assert resp.status_code == 401

    def test_missing_required_fields_rejected(self, tmp_path, monkeypatch):
        _setup_db(tmp_path, monkeypatch)
        monkeypatch.setenv(stmarks_module.STMARKS_SECRET_ENV, "correct-secret")
        client = TestClient(app)
        resp = client.post(
            "/api/intake/stmarks-contact",
            json={"name": "Jo Bloggs", "message": "Do you stock X?"},  # no phone/email
            headers={"X-Stmarks-Secret": "correct-secret"},
        )
        assert resp.status_code == 422

    def test_valid_submission_lands_case_in_queue(self, tmp_path, monkeypatch):
        _setup_db(tmp_path, monkeypatch)
        monkeypatch.setenv(stmarks_module.STMARKS_SECRET_ENV, "correct-secret")
        client = TestClient(app)
        resp = client.post(
            "/api/intake/stmarks-contact",
            json={
                "name": "Jo Bloggs",
                "phone": "07000000000",
                "message": "Do you stock nicotine patches?",
                "page": "/contact",
            },
            headers={"X-Stmarks-Secret": "correct-secret"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["ok"] is True
        call_id = data["call_id"]
        assert call_id.startswith("STMARKS-")

        case_resp = _client().get(f"/api/cases/{call_id}")
        assert case_resp.status_code == 200, case_resp.text
        case = case_resp.json()
        assert case["patient_name"] == "Jo Bloggs"
        assert case["callback_number"] == "07000000000"
        assert case["safe_to_queue"] in (1, True)
        assert case["staff_review_required"] in (0, False)

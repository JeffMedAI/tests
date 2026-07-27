import pytest
import app.helpers as helpers_module
import app.importer as importer_module
import app.main as main_module
from app.main import SESSION_COOKIE, app
from fastapi.testclient import TestClient

_TEST_SESSION_TOKEN = "jefflocal-test-bypass-x"
_TEST_STAFF_USER = {"id": 1, "display_name": "Test Admin", "role": "admin", "active": 1}

_TEST_READONLY_TOKEN = "jefflocal-test-bypass-readonly"
_TEST_READONLY_USER = {"id": 2, "display_name": "Test Readonly", "role": "readonly", "active": 1}

_TEST_STAFF_TOKEN = "jefflocal-test-bypass-staff"
_TEST_STAFF_USER_ROLE = {"id": 3, "display_name": "Test Staff", "role": "staff", "active": 1}

_TEST_SUPER_ADMIN_TOKEN = "jefflocal-test-bypass-super-admin"
_TEST_SUPER_ADMIN_USER = {"id": 4, "display_name": "Test Avamed Super Admin", "role": "avamed-super-admin", "active": 1}


@pytest.fixture(autouse=True)
def _isolate_handoff_dir_from_production(tmp_path, monkeypatch):
    """Point the importer at a temp inbox for EVERY test. Non-negotiable.

    C:\\JeffLocal IS the production directory, and running the suite here is a
    routine release check. main.py's startup hook calls import_handoffs(conn)
    with no directory argument, so it defaults to the module-level HANDOFF_DIR —
    the REAL outputs/handoff_json. FastAPI's TestClient fires that startup hook,
    so merely constructing a TestClient reaches into production's inbox.

    That used to be harmless: tests read the real files into a temp DB and left
    them alone, so production's own 60s importer still picked them up. Since the
    importer started RETIRING imported files to processed/, it stopped being
    harmless — a test run now MOVES a pending handoff out of the inbox while
    importing it only into the test's throwaway DB. Production's importer never
    sees the file again and the case is silently lost.

    Proven on 2026-07-17: a canary file placed in the production inbox was moved
    to processed/ by a single unrelated health-check test, and its case landed in
    the temp DB, not production's.

    Tests that want a real inbox pass handoff_dir explicitly (see
    test_importer.py) and are unaffected by this fixture.
    """
    monkeypatch.setattr(importer_module, "HANDOFF_DIR", tmp_path / "handoff_json_isolated")


@pytest.fixture(autouse=True)
def _bypass_session_lookup(monkeypatch):
    """Accept hardcoded test tokens without a real DB session lookup."""
    real_lookup = main_module.get_session_user

    def _patched(conn, token):
        if token == _TEST_SESSION_TOKEN:
            return _TEST_STAFF_USER
        if token == _TEST_READONLY_TOKEN:
            return _TEST_READONLY_USER
        if token == _TEST_STAFF_TOKEN:
            return _TEST_STAFF_USER_ROLE
        if token == _TEST_SUPER_ADMIN_TOKEN:
            return _TEST_SUPER_ADMIN_USER
        return real_lookup(conn, token)

    # Patch in both main and helpers — helpers has its own import reference
    monkeypatch.setattr(main_module, "get_session_user", _patched)
    monkeypatch.setattr(helpers_module, "get_session_user", _patched)


@pytest.fixture
def authed_client():
    """TestClient pre-loaded with an admin session cookie."""
    return TestClient(app, cookies={SESSION_COOKIE: _TEST_SESSION_TOKEN})


@pytest.fixture
def readonly_client():
    """TestClient pre-loaded with a readonly session cookie."""
    return TestClient(app, cookies={SESSION_COOKIE: _TEST_READONLY_TOKEN})


@pytest.fixture
def staff_role_client():
    """TestClient pre-loaded with a plain 'staff' (non-admin) session cookie."""
    return TestClient(app, cookies={SESSION_COOKIE: _TEST_STAFF_TOKEN})


@pytest.fixture
def super_admin_client():
    """TestClient pre-loaded with an avamed-super-admin session cookie."""
    return TestClient(app, cookies={SESSION_COOKIE: _TEST_SUPER_ADMIN_TOKEN})

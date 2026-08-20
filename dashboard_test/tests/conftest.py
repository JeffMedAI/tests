import pytest
import app.helpers as helpers_module
import app.main as main_module
from app.main import SESSION_COOKIE, app
from fastapi.testclient import TestClient

_TEST_SESSION_TOKEN = "jefflocal-test-bypass-x"
_TEST_STAFF_USER = {"id": 1, "display_name": "Test Admin", "role": "admin", "active": 1}

_TEST_READONLY_TOKEN = "jefflocal-test-bypass-readonly"
_TEST_READONLY_USER = {"id": 2, "display_name": "Test Readonly", "role": "readonly", "active": 1}


@pytest.fixture(autouse=True)
def _bypass_session_lookup(monkeypatch):
    """Accept hardcoded test tokens without a real DB session lookup."""
    real_lookup = main_module.get_session_user

    def _patched(conn, token):
        if token == _TEST_SESSION_TOKEN:
            return _TEST_STAFF_USER
        if token == _TEST_READONLY_TOKEN:
            return _TEST_READONLY_USER
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

"""
conftest.py — shared pytest fixtures for sandbox/dashboard/tests/

Auth fixture: bypass_auth (autouse=True, function-scoped)
─────────────────────────────────────────────────────────
The sandbox dashboard uses an HTTP middleware (enforce_auth in app/main.py)
that checks every request for a valid session cookie. Without a real session
cookie, all non-public routes redirect to /login (HTTP 302) which would cause
every integration and render test to fail with a redirect instead of the
expected 200.

bypass_auth solves this by monkeypatching app.main._is_public_path to always
return True. The middleware calls _is_public_path(request.url.path) at runtime
via the module-level name, so replacing the attribute on the module object
causes the middleware to treat every path as public and call_next immediately
without a session check.

Mechanism:
  - monkeypatch.setattr is used (not direct assignment) so pytest automatically
    restores the original function after each test — no teardown code required
    and no state bleeds between tests.
  - autouse=True ensures every test in this directory gets the fixture without
    needing to declare it explicitly.
  - Auth-specific tests (test_auth_middleware.py) should override this fixture
    locally if they need to test the real authentication flow.

Security note:
  - This bypass is test-only. It cannot reach production because:
    a) it patches an in-process module attribute (not a config value)
    b) it is scoped to the pytest process lifetime only
    c) the sandbox app runs on port 5000; production (port 8765) is a
       separate process that this patch never touches.
"""
import sys
from pathlib import Path

# Ensure sandbox/dashboard/ is on sys.path so `import app.*` works
# whether tests are run from sandbox/dashboard/ or any other directory.
_DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
if str(_DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(_DASHBOARD_ROOT))

import pytest


@pytest.fixture(autouse=True)
def bypass_auth(monkeypatch):
    """
    Bypass enforce_auth middleware for all tests in this directory.

    Patches app.main._is_public_path to return True unconditionally so the
    HTTP auth middleware passes every request through without requiring a
    session cookie. Monkeypatch restores the original after each test.

    Tests that exercise the real auth flow should override this fixture.
    """
    import app.main as main_module
    monkeypatch.setattr(main_module, "_is_public_path", lambda path: True)


@pytest.fixture(autouse=True)
def no_archive_artifacts(monkeypatch):
    """
    Prevent archive_n8ntest_artifacts() from moving real files during tests.

    Any test calling POST /api/n8n/test-intake-batch triggers archiving of
    outputs/handoff_json/ (and other folders) to a backup directory. This
    silently deletes the TC-* rawmock fixture files that other tests rely on,
    causing downstream 'import returns 0' failures in a seemingly unrelated
    order-dependent way.

    This fixture patches archive_n8ntest_artifacts to return a harmless no-op
    result so test ordering never affects the on-disk fixture state.
    """
    import app.main as main_module
    monkeypatch.setattr(
        main_module,
        "archive_n8ntest_artifacts",
        lambda: {"archive_root": "", "total_archived": 0, "folders": []},
    )

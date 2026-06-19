"""
Shared fixtures for JeffLocal Playwright E2E tests.

Prerequisites:
    pip install playwright pytest-playwright
    playwright install chromium

Run tests with:
    pytest tests/e2e/

Environment variables (override defaults for non-test environments):
    JEFF_BASE_URL   — base URL of the running dashboard (default: http://127.0.0.1:8765)
    JEFF_TEST_USER  — test staff username (default: test_user)
    JEFF_TEST_PASS  — test staff password (default: test_pass)

IMPORTANT: Never use real patient names, NHS numbers, or production credentials
in these fixtures or any test file.
"""

import os
import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page


# ---------------------------------------------------------------------------
# Config — pulled from environment so CI can override without touching code
# ---------------------------------------------------------------------------

BASE_URL: str = os.environ.get("JEFF_BASE_URL", "http://127.0.0.1:8765")
TEST_USER: str = os.environ.get("JEFF_TEST_USER", "test_user")
TEST_PASS: str = os.environ.get("JEFF_TEST_PASS", "test_pass")

# Session cookie name (must match SESSION_COOKIE in main.py)
SESSION_COOKIE = "jefflocal_session"


# ---------------------------------------------------------------------------
# Session-scoped browser — launched once per pytest session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def playwright_instance():
    with sync_playwright() as pw:
        yield pw


@pytest.fixture(scope="session")
def browser(playwright_instance) -> Browser:
    """Launch Chromium in headless mode for the full test session."""
    browser = playwright_instance.chromium.launch(headless=True)
    yield browser
    browser.close()


# ---------------------------------------------------------------------------
# Function-scoped context — fresh browser context (isolated cookies) per test
# ---------------------------------------------------------------------------

@pytest.fixture()
def context(browser: Browser) -> BrowserContext:
    """
    Fresh browser context per test.  Ignores HTTPS certificate errors so tests
    can run against localhost without a valid TLS cert (the app sets secure=True
    on cookies but Playwright accepts them over HTTP in tests).
    """
    ctx = browser.new_context(
        base_url=BASE_URL,
        ignore_https_errors=True,
    )
    yield ctx
    ctx.close()


@pytest.fixture()
def page(context: BrowserContext) -> Page:
    """Fresh page inside a fresh context — no session cookie at start."""
    return context.new_page()


# ---------------------------------------------------------------------------
# Authenticated page — logs in with test credentials before yielding
# ---------------------------------------------------------------------------

@pytest.fixture()
def auth_page(context: BrowserContext) -> Page:
    """
    Returns a Page that is already logged in with TEST_USER / TEST_PASS.

    The fixture posts credentials to /login and asserts the redirect to a
    protected page succeeds before handing the page to the test.
    """
    pg = context.new_page()
    pg.goto(f"{BASE_URL}/login")

    pg.fill('input[name="username"]', TEST_USER)
    pg.fill('input[name="password"]', TEST_PASS)
    pg.click('button[type="submit"]')

    # After a successful login the app redirects away from /login
    pg.wait_for_url(lambda url: "/login" not in url, timeout=10_000)
    return pg


# ---------------------------------------------------------------------------
# Convenience helpers exported for tests
# ---------------------------------------------------------------------------

def login_url() -> str:
    return f"{BASE_URL}/login"


def dashboard_url() -> str:
    return f"{BASE_URL}/requests"


def health_url() -> str:
    return f"{BASE_URL}/api/health"

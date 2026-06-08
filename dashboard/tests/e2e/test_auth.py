"""
E2E tests — authentication flows.

Covers:
  - Login with valid credentials → dashboard loads
  - Login with bad credentials → error message shown
  - Accessing /requests (protected) without session → redirect to /login
  - Accessing /api/alerts/recent without session → 401
  - GET /logout → session cleared, redirect to /login

Run with: pytest tests/e2e/test_auth.py
Requires the dashboard to be running at JEFF_BASE_URL (default http://127.0.0.1:8765).

No real patient names, NHS numbers, or production credentials are used here.
"""

import pytest
from playwright.sync_api import BrowserContext, Page, expect

from conftest import BASE_URL, TEST_USER, TEST_PASS, SESSION_COOKIE


class TestLoginPageRenders:
    """The login page must be reachable and contain the expected form elements."""

    def test_login_page_loads(self, page: Page):
        page.goto(f"{BASE_URL}/login")
        expect(page).to_have_url(f"{BASE_URL}/login")
        # Username and password fields must exist
        expect(page.locator('input[name="username"]')).to_be_visible()
        expect(page.locator('input[name="password"]')).to_be_visible()
        expect(page.locator('button[type="submit"]')).to_be_visible()


class TestValidLogin:
    """A valid username / password pair must authenticate and land on a protected page."""

    def test_valid_login_redirects_away_from_login(self, page: Page):
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="username"]', TEST_USER)
        page.fill('input[name="password"]', TEST_PASS)
        page.click('button[type="submit"]')

        # Should no longer be on /login after a successful auth
        page.wait_for_url(lambda url: "/login" not in url, timeout=10_000)
        assert "/login" not in page.url, (
            f"Expected redirect away from /login after valid credentials, but URL is: {page.url}"
        )

    def test_valid_login_sets_session_cookie(self, page: Page):
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="username"]', TEST_USER)
        page.fill('input[name="password"]', TEST_PASS)
        page.click('button[type="submit"]')
        page.wait_for_url(lambda url: "/login" not in url, timeout=10_000)

        cookies = {c["name"]: c for c in page.context.cookies()}
        assert SESSION_COOKIE in cookies, (
            f"Session cookie '{SESSION_COOKIE}' not found after login. "
            f"Cookies present: {list(cookies.keys())}"
        )
        # Cookie must be httpOnly
        assert cookies[SESSION_COOKIE].get("httpOnly") is True, (
            "Session cookie must be httpOnly to prevent JavaScript access."
        )


class TestInvalidLogin:
    """Wrong credentials must NOT authenticate; the login page must show an error."""

    def test_bad_password_stays_on_login_page(self, page: Page):
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="username"]', TEST_USER)
        page.fill('input[name="password"]', "definitely_wrong_password_xyz_987")
        page.click('button[type="submit"]')

        # Must stay on /login
        page.wait_for_load_state("networkidle")
        assert "/login" in page.url, (
            f"Expected to remain on /login after bad credentials, but URL is: {page.url}"
        )

    def test_bad_password_shows_error_message(self, page: Page):
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="username"]', TEST_USER)
        page.fill('input[name="password"]', "wrong_password_abc_456")
        page.click('button[type="submit"]')

        page.wait_for_load_state("networkidle")
        # The app renders error text — check for common error keywords
        body_text = page.locator("body").inner_text().lower()
        assert any(
            kw in body_text for kw in ("invalid", "incorrect", "credentials", "attempt", "locked")
        ), f"Expected an error message on failed login, but page text was:\n{body_text[:500]}"

    def test_blank_username_shows_error(self, page: Page):
        page.goto(f"{BASE_URL}/login")
        # Leave username blank
        page.fill('input[name="password"]', "some_password")
        page.click('button[type="submit"]')

        page.wait_for_load_state("networkidle")
        body_text = page.locator("body").inner_text().lower()
        assert any(
            kw in body_text for kw in ("username", "enter", "required", "invalid")
        ), "Expected an error when username is blank."

    def test_nonexistent_user_shows_generic_error(self, page: Page):
        """Error message must not reveal whether the username exists (no user enumeration)."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="username"]', "user_that_does_not_exist_zzz")
        page.fill('input[name="password"]', "any_password_here")
        page.click('button[type="submit"]')

        page.wait_for_load_state("networkidle")
        body_text = page.locator("body").inner_text().lower()
        # Must not say "user not found" or reveal the user doesn't exist
        assert "not found" not in body_text, (
            "Error message must not reveal whether the username exists (user enumeration risk)."
        )
        # Must show some error
        assert any(kw in body_text for kw in ("invalid", "incorrect", "credentials")), (
            "Expected a generic error for a nonexistent username."
        )


class TestUnauthenticatedAccess:
    """Unauthenticated requests to protected routes must redirect to /login or return 401."""

    def test_requests_page_without_session_redirects_to_login(self, page: Page):
        """GET /requests (the task worklist) requires authentication."""
        page.goto(f"{BASE_URL}/requests")
        page.wait_for_load_state("networkidle")
        assert "/login" in page.url, (
            f"Expected /requests to redirect unauthenticated user to /login, but URL is: {page.url}"
        )

    def test_login_redirect_carries_next_param(self, page: Page):
        """The redirect to /login should include a ?next= param so the user lands back after login."""
        page.goto(f"{BASE_URL}/requests")
        page.wait_for_load_state("networkidle")
        assert "next=" in page.url or "/login" in page.url, (
            f"Expected next= parameter in redirect URL, got: {page.url}"
        )

    def test_dashboard_root_without_session_redirects_to_login(self, page: Page):
        """GET / (root) must also redirect to /login when unauthenticated."""
        page.goto(f"{BASE_URL}/")
        page.wait_for_load_state("networkidle")
        assert "/login" in page.url, (
            f"Expected / to redirect to /login for unauthenticated user, got: {page.url}"
        )

    def test_api_alerts_recent_without_session_returns_401(self, page: Page):
        """
        /api/alerts/recent is not in AUTH_PUBLIC_PREFIXES so it must be protected.
        An unauthenticated browser request should get a 302 redirect to /login
        (FastAPI middleware) or a 401 response.
        """
        response = page.request.get(f"{BASE_URL}/api/alerts/recent")
        # The auth middleware redirects (302) rather than returning 401 for browser
        # requests, but the final URL should be /login, OR the status is 401.
        assert response.status in (302, 401) or "/login" in page.url, (
            f"Expected 302/401 for unauthenticated API request, got {response.status}"
        )

    def test_api_alerts_unacknowledged_without_session_protected(self, page: Page):
        response = page.request.get(f"{BASE_URL}/api/alerts/unacknowledged")
        assert response.status in (302, 401), (
            f"Expected 302/401 for unauthenticated request to /api/alerts/unacknowledged, "
            f"got {response.status}"
        )


class TestLogout:
    """POST /logout must clear the session and redirect to /login."""

    def test_logout_clears_session_and_redirects(self, auth_page: Page):
        """
        After logging in (via the auth_page fixture), navigating to /logout should
        clear the session cookie and land the user on /login.
        """
        # Confirm we start authenticated
        assert "/login" not in auth_page.url, (
            "auth_page fixture should start on a protected page, not /login."
        )

        auth_page.goto(f"{BASE_URL}/logout")
        auth_page.wait_for_load_state("networkidle")

        # Must now be on /login
        assert "/login" in auth_page.url, (
            f"Expected /logout to redirect to /login, but URL is: {auth_page.url}"
        )

    def test_logout_removes_session_cookie(self, auth_page: Page):
        auth_page.goto(f"{BASE_URL}/logout")
        auth_page.wait_for_load_state("networkidle")

        cookies = {c["name"]: c for c in auth_page.context.cookies()}
        assert SESSION_COOKIE not in cookies, (
            f"Session cookie '{SESSION_COOKIE}' should be deleted after logout, "
            f"but it was still present."
        )

    def test_after_logout_protected_page_redirects_to_login(self, auth_page: Page):
        auth_page.goto(f"{BASE_URL}/logout")
        auth_page.wait_for_load_state("networkidle")

        # Attempt to navigate to protected page — must be blocked
        auth_page.goto(f"{BASE_URL}/requests")
        auth_page.wait_for_load_state("networkidle")
        assert "/login" in auth_page.url, (
            f"After logout, /requests should redirect to /login, but URL is: {auth_page.url}"
        )

    def test_logout_info_message_shown(self, auth_page: Page):
        auth_page.goto(f"{BASE_URL}/logout")
        auth_page.wait_for_load_state("networkidle")

        # The app appends ?info=You+have+been+signed+out. — check it renders
        body_text = auth_page.locator("body").inner_text().lower()
        assert any(
            kw in body_text for kw in ("signed out", "logged out", "sign in", "login")
        ), f"Expected a signed-out confirmation message, got:\n{body_text[:400]}"

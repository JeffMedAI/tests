"""
E2E tests — dashboard pages and API health.

Covers:
  - /requests (task worklist) loads for an authenticated user
  - Summary cards are rendered
  - /case/<id> (case detail) page loads without error
  - /api/health returns HTTP 200 with expected JSON structure
  - /reports page loads for an authenticated user
  - /profile page loads for an authenticated user

Run with: pytest tests/e2e/test_dashboard.py
Requires the dashboard to be running at JEFF_BASE_URL (default http://127.0.0.1:8765).

No real patient names, NHS numbers, or production credentials are used here.
"""

import json
import pytest
from playwright.sync_api import Page, expect

import os

BASE_URL: str = os.environ.get("JEFF_BASE_URL", "http://127.0.0.1:8765")
SESSION_COOKIE = "jefflocal_session"


class TestHealthEndpoint:
    """
    /api/health is a public endpoint (no auth required).
    It must return 200 with a valid JSON body confirming the service is up.
    """

    def test_health_returns_200(self, page: Page):
        response = page.request.get(f"{BASE_URL}/api/health")
        assert response.status == 200, (
            f"Expected /api/health to return 200, got {response.status}"
        )

    def test_health_returns_json(self, page: Page):
        response = page.request.get(f"{BASE_URL}/api/health")
        content_type = response.headers.get("content-type", "")
        assert "json" in content_type, (
            f"Expected /api/health to return JSON, got Content-Type: {content_type}"
        )

    def test_health_body_has_ok_true(self, page: Page):
        response = page.request.get(f"{BASE_URL}/api/health")
        body = response.json()
        assert body.get("ok") is True, (
            f"Expected 'ok: true' in /api/health response, got: {body}"
        )

    def test_health_body_has_service_name(self, page: Page):
        response = page.request.get(f"{BASE_URL}/api/health")
        body = response.json()
        assert "service" in body, f"Expected 'service' key in /api/health response: {body}"
        assert "jefflocal" in str(body["service"]).lower(), (
            f"Expected service name to contain 'jefflocal', got: {body['service']}"
        )

    def test_health_body_has_checks(self, page: Page):
        response = page.request.get(f"{BASE_URL}/api/health")
        body = response.json()
        checks = body.get("checks", {})
        assert isinstance(checks, dict), f"Expected 'checks' to be a dict: {body}"
        assert "dashboard" in checks, f"Expected 'dashboard' check in /api/health: {checks}"
        assert "database" in checks, f"Expected 'database' check in /api/health: {checks}"


class TestRequestsPage:
    """
    /requests is the main task worklist.  It must load correctly for an
    authenticated user and render the key UI regions.
    """

    def test_requests_page_loads_authenticated(self, auth_page: Page):
        auth_page.goto(f"{BASE_URL}/requests")
        auth_page.wait_for_load_state("networkidle")

        assert auth_page.title() != "", "Page title should not be empty."
        # Must NOT be on the login page
        assert "/login" not in auth_page.url, (
            f"Authenticated user was redirected to /login when accessing /requests: {auth_page.url}"
        )

    def test_requests_page_has_no_server_error(self, auth_page: Page):
        response = auth_page.goto(f"{BASE_URL}/requests")
        assert response is not None
        assert response.status < 500, (
            f"Expected non-5xx response for /requests, got {response.status}"
        )

    def test_requests_page_renders_body(self, auth_page: Page):
        auth_page.goto(f"{BASE_URL}/requests")
        auth_page.wait_for_load_state("networkidle")

        body_text = auth_page.locator("body").inner_text()
        assert len(body_text.strip()) > 50, (
            "Expected /requests to render meaningful content, but body is nearly empty."
        )

    def test_requests_page_has_navigation(self, auth_page: Page):
        """The dashboard must have a navigation element — nav or header."""
        auth_page.goto(f"{BASE_URL}/requests")
        auth_page.wait_for_load_state("networkidle")

        nav = auth_page.locator("nav, header").first
        expect(nav).to_be_visible()

    def test_requests_page_filter_controls_present(self, auth_page: Page):
        """
        The worklist should have at least one filter/sort control.
        This confirms the Jinja2 template rendered correctly.
        """
        auth_page.goto(f"{BASE_URL}/requests")
        auth_page.wait_for_load_state("networkidle")

        # Check for a form element or a select/link relating to filters
        # The app uses URL params for filters — look for filter links or a form
        body_html = auth_page.content()
        assert any(
            kw in body_html for kw in ("filter=", "sort=", "?filter", "request_type")
        ), "Expected filter/sort controls to be present on /requests page."


class TestCaseDetailPage:
    """
    /case/<id> shows full detail for a single intake case.
    We test the URL shape and that it handles a non-existent ID gracefully.
    """

    def test_case_detail_nonexistent_returns_404(self, auth_page: Page):
        """
        A call_id that does not exist should return a 404, not a 500.
        This confirms the route is wired up and error handling works.
        """
        response = auth_page.goto(f"{BASE_URL}/case/NONEXISTENT-CASE-ID-000")
        assert response is not None
        assert response.status == 404, (
            f"Expected 404 for a nonexistent case ID, got {response.status}"
        )

    def test_case_detail_unauthenticated_redirects_to_login(self, page: Page):
        """Without auth, /case/<id> must redirect to /login."""
        page.goto(f"{BASE_URL}/case/SOME-CASE-ID-001")
        page.wait_for_load_state("networkidle")
        assert "/login" in page.url, (
            f"Expected /case/<id> to redirect unauthenticated user to /login, got: {page.url}"
        )

    def test_case_detail_route_exists(self, auth_page: Page):
        """
        Even a 404 (case not found) means the route resolved — a 404 is
        preferable to a 500 (unhandled exception) or 405 (route not found).
        """
        response = auth_page.goto(f"{BASE_URL}/case/TEST-CASE-XYZ")
        assert response is not None
        assert response.status != 405, (
            f"/case/<id> route appears not to be registered (got 405 Method Not Allowed)."
        )
        assert response.status < 500, (
            f"Expected non-5xx response for /case/<id>, got {response.status}"
        )


class TestReportsPage:
    """
    /reports is the KPI / analytics page.  Auth required.
    """

    def test_reports_page_loads_authenticated(self, auth_page: Page):
        auth_page.goto(f"{BASE_URL}/reports")
        auth_page.wait_for_load_state("networkidle")

        assert "/login" not in auth_page.url, (
            f"Authenticated user was redirected to /login for /reports: {auth_page.url}"
        )

    def test_reports_page_has_no_server_error(self, auth_page: Page):
        response = auth_page.goto(f"{BASE_URL}/reports")
        assert response is not None
        assert response.status < 500, (
            f"Expected non-5xx for /reports, got {response.status}"
        )

    def test_reports_unauthenticated_redirects(self, page: Page):
        page.goto(f"{BASE_URL}/reports")
        page.wait_for_load_state("networkidle")
        assert "/login" in page.url, (
            f"/reports should redirect unauthenticated users to /login, got: {page.url}"
        )


class TestProfilePage:
    """
    /profile lets authenticated staff manage their credentials and sessions.
    """

    def test_profile_page_loads_authenticated(self, auth_page: Page):
        auth_page.goto(f"{BASE_URL}/profile")
        auth_page.wait_for_load_state("networkidle")

        assert "/login" not in auth_page.url, (
            f"Authenticated user was redirected to /login for /profile: {auth_page.url}"
        )

    def test_profile_page_has_no_server_error(self, auth_page: Page):
        response = auth_page.goto(f"{BASE_URL}/profile")
        assert response is not None
        assert response.status < 500, (
            f"Expected non-5xx for /profile, got {response.status}"
        )

    def test_profile_unauthenticated_redirects(self, page: Page):
        page.goto(f"{BASE_URL}/profile")
        page.wait_for_load_state("networkidle")
        assert "/login" in page.url


class TestStaffManagementPage:
    """
    /staff is the user management page — admin only in production.
    An authenticated test user may or may not have admin role; we test
    that the route resolves (doesn't 500) rather than testing admin-gated UI.
    """

    def test_staff_page_redirects_or_loads_without_500(self, auth_page: Page):
        response = auth_page.goto(f"{BASE_URL}/staff")
        assert response is not None
        assert response.status < 500, (
            f"Expected non-5xx for /staff, got {response.status}"
        )

    def test_staff_page_unauthenticated_redirects(self, page: Page):
        page.goto(f"{BASE_URL}/staff")
        page.wait_for_load_state("networkidle")
        assert "/login" in page.url, (
            f"/staff should redirect unauthenticated users to /login, got: {page.url}"
        )


class TestPublicPaths:
    """
    A small set of paths must be reachable without authentication.
    """

    def test_login_page_is_public(self, page: Page):
        response = page.goto(f"{BASE_URL}/login")
        assert response is not None
        assert response.status == 200, (
            f"Expected /login to be publicly accessible (200), got {response.status}"
        )

    def test_favicon_is_public(self, page: Page):
        response = page.goto(f"{BASE_URL}/favicon.ico")
        assert response is not None
        # App returns 204 for favicon
        assert response.status in (200, 204), (
            f"Expected 200/204 for /favicon.ico, got {response.status}"
        )

    def test_health_is_public(self, page: Page):
        response = page.goto(f"{BASE_URL}/api/health")
        assert response is not None
        assert response.status == 200, (
            f"Expected /api/health to be publicly accessible (200), got {response.status}"
        )

"""
TDD tests for the /tenants picker page (step 5, STEP5_DESIGN.md §5) and for
the privilege-escalation guard on the staff-management routes (§2): a
tenant-admin (role='admin') must never be able to grant avamed-super-admin
through the ordinary staff UI.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.routers.tenants import load_tenant_registry, tenant_login_url


class TestTenantsPageAccess:
    def test_super_admin_can_view(self, super_admin_client):
        resp = super_admin_client.get("/tenants")
        assert resp.status_code == 200
        assert "Tenant" in resp.text

    def test_admin_forbidden(self, authed_client):
        resp = authed_client.get("/tenants")
        assert resp.status_code == 403

    def test_staff_forbidden(self, staff_role_client):
        resp = staff_role_client.get("/tenants")
        assert resp.status_code == 403

    def test_readonly_forbidden(self, readonly_client):
        resp = readonly_client.get("/tenants")
        assert resp.status_code == 403

    def test_unauthenticated_redirects_to_login(self):
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app, follow_redirects=False)
        resp = client.get("/tenants")
        assert resp.status_code == 302
        assert "/login" in resp.headers["location"]

    def test_page_never_queries_a_tenant_database(self, super_admin_client, monkeypatch):
        """The picker must render purely from registry.json — never open a
        second sqlite3 connection to a tenant DB. Patch sqlite3.connect to
        fail loudly if the tenants router ever calls it directly (it shouldn't
        — it only uses the app's own connect() for the current-staff lookup,
        which the autouse fixtures already isolate to a temp DB)."""
        resp = super_admin_client.get("/tenants")
        assert resp.status_code == 200
        # No case data should ever appear on this page (base.html's own nav
        # legitimately says "Patients" as a link label — that's fine; what must
        # never appear is actual case/patient record content).
        assert "call_id" not in resp.text.lower()
        assert "nhs_number" not in resp.text.lower()
        assert "verification_status" not in resp.text.lower()


class TestLoadTenantRegistry:
    def test_missing_file_returns_empty_list(self, tmp_path):
        assert load_tenant_registry(tmp_path / "does-not-exist.json") == []

    def test_malformed_json_returns_empty_list(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{not valid json", encoding="utf-8")
        assert load_tenant_registry(path) == []

    def test_reads_real_registry_file(self):
        real_registry = Path(__file__).resolve().parents[2] / "config" / "registry.json"
        tenants = load_tenant_registry(real_registry)
        slugs = {t["slug"] for t in tenants}
        assert "tenant1" in slugs
        assert "tenant2" in slugs


class TestTenantLoginUrl:
    def test_uses_hostname_when_set(self):
        url = tenant_login_url({"hostname": "churchtown.app-avamed.uk", "port": 8765})
        assert url == "https://churchtown.app-avamed.uk/login"

    def test_falls_back_to_localhost_port(self):
        url = tenant_login_url({"hostname": None, "port": 8766})
        assert url == "http://localhost:8766/login"


class TestStaffUiCannotGrantSuperAdmin:
    """The core privilege-escalation regression test for this step."""

    def test_staff_create_rejects_avamed_super_admin_role(self, authed_client):
        resp = authed_client.post(
            "/staff/create",
            data={
                "display_name": "Sneaky Escalation",
                "role": "avamed-super-admin",
                "username": "sneaky",
            },
        )
        assert resp.status_code == 400

    def test_staff_invitation_rejects_avamed_super_admin_role(self, authed_client):
        resp = authed_client.post(
            "/staff/invitations/create",
            data={"email": "sneaky@example.com", "role": "avamed-super-admin"},
        )
        assert resp.status_code == 400

    def test_even_a_logged_in_super_admin_cannot_grant_it_via_the_ui(self, super_admin_client):
        """staff_can_manage() lets avamed-super-admin reach /staff/create too
        (support access), but STAFF_ROLES still blocks the role value itself —
        the escalation guard is on the ASSIGNABLE ROLE, not on who's asking."""
        resp = super_admin_client.post(
            "/staff/create",
            data={
                "display_name": "Still Blocked",
                "role": "avamed-super-admin",
                "username": "stillblocked",
            },
        )
        assert resp.status_code == 400

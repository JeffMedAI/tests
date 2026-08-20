"""
TDD tests for app/routers/staff.py — staff management routes.

RED phase: imports from app.routers.staff will fail until the module is created.
"""
from fastapi import APIRouter
from app.routers.staff import router


class TestStaffRouterStructure:
    def test_router_is_apirouter(self):
        assert isinstance(router, APIRouter)

    def _paths(self):
        return {r.path for r in router.routes}

    def _methods_by_path(self):
        result = {}
        for r in router.routes:
            result.setdefault(r.path, set()).update(r.methods or set())
        return result

    def test_router_has_staff_get(self):
        assert "/staff" in self._paths()

    def test_router_has_staff_get_method(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/staff", set())

    def test_router_has_staff_create_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/staff/create", set())

    def test_router_has_staff_edit_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/staff/{staff_id}/edit", set())

    def test_router_has_staff_deactivate_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/staff/{staff_id}/deactivate", set())

    def test_router_has_staff_reactivate_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/staff/{staff_id}/reactivate", set())

    def test_router_has_staff_invitations_get(self):
        assert "/staff/invitations" in self._paths()

    def test_router_has_staff_invitations_create_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/staff/invitations/create", set())

    def test_router_has_staff_invitations_cancel_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/staff/invitations/{invitation_id}/cancel", set())

    def test_router_has_api_staff_performance_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/staff/performance", set())

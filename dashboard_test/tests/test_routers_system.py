"""
TDD tests for app/routers/system.py — health, services, and workload routes.

RED phase: imports from app.routers.system will fail until the module is created.
"""
from fastapi import APIRouter
from app.routers.system import router


class TestSystemRouterStructure:
    def _paths(self):
        return {r.path for r in router.routes}

    def _methods_by_path(self):
        result = {}
        for r in router.routes:
            result.setdefault(r.path, set()).update(r.methods or set())
        return result

    def test_router_is_apirouter(self):
        assert isinstance(router, APIRouter)

    def test_router_has_favicon(self):
        assert "/favicon.ico" in self._paths()

    def test_router_has_health_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/health", set())

    def test_router_has_staff_workload_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/staff-workload", set())

    def test_router_has_services_status_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/services/status", set())

    def test_router_has_services_refresh_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/api/services/refresh", set())

    def test_router_has_system_workload_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/system/workload", set())

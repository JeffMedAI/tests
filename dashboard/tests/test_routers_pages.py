"""
TDD tests for app/routers/pages.py — dashboard page-rendering routes.

RED phase: imports from app.routers.pages will fail until the module is created.
"""
from fastapi import APIRouter
from app.routers.pages import router


class TestPagesRouterStructure:
    def _paths(self):
        return {r.path for r in router.routes}

    def _methods_by_path(self):
        result = {}
        for r in router.routes:
            result.setdefault(r.path, set()).update(r.methods or set())
        return result

    def test_router_is_apirouter(self):
        assert isinstance(router, APIRouter)

    def test_router_has_index_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/", set())

    def test_router_has_requests_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/requests", set())

    def test_router_has_patients_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/patients", set())

    def test_router_has_reports_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/reports", set())

    def test_router_has_settings_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/settings", set())

    def test_router_has_import_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/import", set())

    def test_router_has_api_import_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/api/import", set())

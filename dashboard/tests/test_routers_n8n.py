"""
TDD tests for app/routers/n8n.py — n8n workflow integration routes.

RED phase: imports from app.routers.n8n will fail until the module is created.
"""
from fastapi import APIRouter
from app.routers.n8n import router


class TestN8nRouterStructure:
    def _paths(self):
        return {r.path for r in router.routes}

    def _methods_by_path(self):
        result = {}
        for r in router.routes:
            result.setdefault(r.path, set()).update(r.methods or set())
        return result

    def test_router_is_apirouter(self):
        assert isinstance(router, APIRouter)

    def test_router_has_sync_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/api/n8n/sync", set())

    def test_router_has_red_flags_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/n8n/red-flags", set())

    def test_router_has_overdue_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/n8n/overdue", set())

    def test_router_has_daily_summary_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/n8n/daily-summary", set())

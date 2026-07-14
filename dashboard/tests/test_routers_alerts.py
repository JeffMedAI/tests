"""
TDD tests for app/routers/alerts.py — alert management routes.

RED phase: imports from app.routers.alerts will fail until the module is created.
"""
from fastapi import APIRouter
from app.routers.alerts import router


class TestAlertsRouterStructure:
    def _paths(self):
        return {r.path for r in router.routes}

    def _methods_by_path(self):
        result = {}
        for r in router.routes:
            result.setdefault(r.path, set()).update(r.methods or set())
        return result

    def test_router_is_apirouter(self):
        assert isinstance(router, APIRouter)

    def test_router_has_alerts_page(self):
        assert "/alerts" in self._paths()

    def test_router_has_api_alert_log_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/api/n8n/alerts/log", set())

    def test_router_has_api_alerts_recent_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/alerts/recent", set())

    def test_router_has_api_alerts_unacknowledged_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/alerts/unacknowledged", set())

    def test_router_has_api_alert_acknowledge_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/api/alerts/{alert_id}/acknowledge", set())

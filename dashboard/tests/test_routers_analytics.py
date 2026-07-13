"""
TDD tests for app/routers/analytics.py — analytics and search routes.

RED phase: imports from app.routers.analytics will fail until the module is created.
"""
from fastapi import APIRouter
from app.routers.analytics import router


class TestAnalyticsRouterStructure:
    def _paths(self):
        return {r.path for r in router.routes}

    def _methods_by_path(self):
        result = {}
        for r in router.routes:
            result.setdefault(r.path, set()).update(r.methods or set())
        return result

    def test_router_is_apirouter(self):
        assert isinstance(router, APIRouter)

    def test_router_has_hourly_volume_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/analytics/hourly-volume", set())

    def test_router_has_performance_summary_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/analytics/performance-summary", set())

    def test_router_has_patient_card_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/patient-card", set())

    def test_router_has_search_get(self):
        mbp = self._methods_by_path()
        assert "GET" in mbp.get("/api/search", set())

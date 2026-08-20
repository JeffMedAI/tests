"""
TDD tests for app/routers/cases.py — case management routes.

RED phase: imports from app.routers.cases will fail until the module is created.
"""
from fastapi import APIRouter
from app.routers.cases import router


class TestCasesRouterStructure:
    def _paths(self):
        return {r.path for r in router.routes}

    def _methods_by_path(self):
        result = {}
        for r in router.routes:
            result.setdefault(r.path, set()).update(r.methods or set())
        return result

    def test_router_is_apirouter(self):
        assert isinstance(router, APIRouter)

    def test_router_has_case_detail_get(self):
        assert "/case/{call_id}" in self._paths()

    def test_router_has_case_update_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/case/{call_id}/update", set())

    def test_router_has_case_quick_action_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/case/{call_id}/quick_action", set())

    def test_router_has_api_case_get(self):
        assert "/api/cases/{call_id}" in self._paths()

    def test_router_has_api_case_action_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/api/cases/{call_id}/action", set())

    def test_router_has_api_case_enrich_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/api/cases/{call_id}/enrich", set())

    def test_router_has_api_case_copy_audit_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/api/cases/{call_id}/copy-audit", set())

    def test_router_has_api_cases_batch_resolve_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/api/cases/batch-resolve", set())

    def test_router_has_api_cases_bulk_action_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/api/cases/bulk-action", set())

    def test_router_has_api_call_recording_post(self):
        mbp = self._methods_by_path()
        assert "POST" in mbp.get("/api/calls/{call_id}/recording", set())

"""
TDD tests for app/routers/auth.py — auth and profile routes.

RED phase: imports from app.routers.auth will fail until the module is created.
"""
from fastapi import APIRouter
from app.routers.auth import router


class TestAuthRouterStructure:
    def test_router_is_apirouter(self):
        assert isinstance(router, APIRouter)

    def test_router_has_login_get(self):
        paths = {r.path for r in router.routes}
        assert "/login" in paths

    def test_router_has_login_post(self):
        methods_by_path = {}
        for r in router.routes:
            methods_by_path.setdefault(r.path, set()).update(r.methods or set())
        assert "POST" in methods_by_path.get("/login", set())

    def test_router_has_logout(self):
        paths = {r.path for r in router.routes}
        assert "/logout" in paths

    def test_router_has_forgot_get(self):
        paths = {r.path for r in router.routes}
        assert "/forgot" in paths

    def test_router_has_forgot_post(self):
        methods_by_path = {}
        for r in router.routes:
            methods_by_path.setdefault(r.path, set()).update(r.methods or set())
        assert "POST" in methods_by_path.get("/forgot", set())

    def test_router_has_reset_get(self):
        paths = {r.path for r in router.routes}
        assert "/reset" in paths

    def test_router_has_reset_post(self):
        methods_by_path = {}
        for r in router.routes:
            methods_by_path.setdefault(r.path, set()).update(r.methods or set())
        assert "POST" in methods_by_path.get("/reset", set())

    def test_router_has_profile(self):
        paths = {r.path for r in router.routes}
        assert "/profile" in paths

    def test_router_has_change_password(self):
        paths = {r.path for r in router.routes}
        assert "/profile/change-password" in paths

    def test_router_has_change_pin(self):
        paths = {r.path for r in router.routes}
        assert "/profile/change-pin" in paths

    def test_router_has_sign_out_all(self):
        paths = {r.path for r in router.routes}
        assert "/profile/sign-out-all" in paths

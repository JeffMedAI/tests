"""
TDD tests for app/helpers.py — shared helper functions extracted from main.py.

RED phase: imports from app.helpers will fail until the module is created.
"""
from unittest.mock import MagicMock, patch

from app.helpers import (
    current_staff_from_request,
    ensure_ready,
    normalize_staff_name,
    require_staff_edit,
    staff_can_edit,
    staff_can_manage,
    staff_display,
)


class TestNormalizeStaffName:
    def test_returns_string(self):
        assert isinstance(normalize_staff_name("Alice"), str)

    def test_strips_whitespace(self):
        assert normalize_staff_name("  Alice  ") == "Alice"

    def test_none_returns_demo_user(self):
        assert normalize_staff_name(None) == "demo_user"

    def test_empty_string_returns_demo_user(self):
        assert normalize_staff_name("") == "demo_user"

    def test_whitespace_only_returns_demo_user(self):
        assert normalize_staff_name("   ") == "demo_user"

    def test_returns_value_as_string(self):
        assert normalize_staff_name("Dr Smith") == "Dr Smith"


class TestStaffCanEdit:
    def test_admin_can_edit(self):
        assert staff_can_edit({"role": "admin"}) is True

    def test_staff_can_edit(self):
        assert staff_can_edit({"role": "staff"}) is True

    def test_readonly_cannot_edit(self):
        assert staff_can_edit({"role": "readonly"}) is False

    def test_missing_role_cannot_edit(self):
        assert staff_can_edit({}) is False

    def test_unknown_role_cannot_edit(self):
        assert staff_can_edit({"role": "unknown"}) is False


class TestStaffCanManage:
    def test_admin_can_manage(self):
        assert staff_can_manage({"role": "admin"}) is True

    def test_staff_cannot_manage(self):
        assert staff_can_manage({"role": "staff"}) is False

    def test_readonly_cannot_manage(self):
        assert staff_can_manage({"role": "readonly"}) is False


class TestStaffDisplay:
    def test_returns_display_name(self):
        result = staff_display({"display_name": "Dr Jones"})
        assert result == "Dr Jones"

    def test_none_staff_returns_demo_user(self):
        assert staff_display(None) == "demo_user"

    def test_missing_display_name_returns_demo_user(self):
        assert staff_display({}) == "demo_user"


class TestRequireStaffEdit:
    def test_admin_passes(self):
        require_staff_edit({"role": "admin"})  # should not raise

    def test_staff_passes(self):
        require_staff_edit({"role": "staff"})  # should not raise

    def test_readonly_raises_403(self):
        from fastapi import HTTPException
        try:
            require_staff_edit({"role": "readonly"})
            assert False, "Should have raised HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 403


class TestCurrentStaffFromRequest:
    def test_returns_dict(self):
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        mock_conn = MagicMock()
        result = current_staff_from_request(mock_request, mock_conn)
        assert isinstance(result, dict)

    def test_no_cookie_returns_demo_fallback(self):
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = None
        mock_conn = MagicMock()
        result = current_staff_from_request(mock_request, mock_conn)
        assert result.get("demo_fallback") is True

    def test_none_request_returns_demo_fallback(self):
        mock_conn = MagicMock()
        result = current_staff_from_request(None, mock_conn)
        assert result.get("demo_fallback") is True

    def test_valid_token_returns_user_data(self):
        mock_request = MagicMock()
        mock_request.cookies.get.return_value = "valid_token"
        mock_conn = MagicMock()
        with patch("app.helpers.get_session_user") as mock_gsu:
            mock_gsu.return_value = {
                "id": 1, "display_name": "Alice", "email": "a@x.com",
                "role": "staff", "username": "alice",
            }
            result = current_staff_from_request(mock_request, mock_conn)
        assert result["id"] == 1
        assert result["display_name"] == "Alice"
        assert result.get("demo_fallback") is not True


class TestEnsureReady:
    def test_ensure_ready_callable(self):
        assert callable(ensure_ready)

    def test_ensure_ready_runs_without_error(self):
        with patch("app.helpers.connect") as mock_connect, \
             patch("app.helpers.init_db") as mock_init_db:
            mock_conn = MagicMock()
            mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
            mock_connect.return_value.__exit__ = MagicMock(return_value=False)
            ensure_ready()
            mock_init_db.assert_called_once_with(mock_conn)

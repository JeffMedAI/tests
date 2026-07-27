"""
TDD tests for step 5's role model (governance/STEP5_DESIGN.md §1/§2):
- admin == tenant-admin (no new role value, no behaviour change)
- avamed-super-admin is a new role with full in-tenant access
- avamed-super-admin must NEVER be assignable via the ordinary staff-management
  HTTP routes (the privilege-escalation guard this step's whole design turns on)
"""
from __future__ import annotations

import pytest

from app.consts import ALL_VALID_ROLES, AVAMED_SUPER_ADMIN_ROLE, STAFF_ROLES
from app.helpers import (
    is_avamed_super_admin,
    require_avamed_super_admin,
    require_staff_admin,
    require_staff_edit,
    staff_can_edit,
    staff_can_manage,
)
from fastapi import HTTPException


class TestRoleConstants:
    def test_staff_roles_unchanged_by_step5(self):
        """STAFF_ROLES is the assignable-via-UI set. Step 5 must not widen it —
        see STEP5_DESIGN.md section 2 for why."""
        assert STAFF_ROLES == {"admin", "staff", "readonly"}

    def test_avamed_super_admin_not_in_staff_roles(self):
        assert AVAMED_SUPER_ADMIN_ROLE not in STAFF_ROLES

    def test_all_valid_roles_is_staff_roles_plus_super_admin(self):
        assert ALL_VALID_ROLES == STAFF_ROLES | {AVAMED_SUPER_ADMIN_ROLE}


class TestStaffCanEdit:
    @pytest.mark.parametrize("role", ["admin", "staff", "avamed-super-admin"])
    def test_can_edit_roles(self, role):
        assert staff_can_edit({"role": role}) is True

    @pytest.mark.parametrize("role", ["readonly", "", "bogus"])
    def test_cannot_edit_roles(self, role):
        assert staff_can_edit({"role": role}) is False


class TestStaffCanManage:
    @pytest.mark.parametrize("role", ["admin", "avamed-super-admin"])
    def test_can_manage_roles(self, role):
        assert staff_can_manage({"role": role}) is True

    @pytest.mark.parametrize("role", ["staff", "readonly", "", "bogus"])
    def test_cannot_manage_roles(self, role):
        assert staff_can_manage({"role": role}) is False


class TestIsAvamedSuperAdmin:
    def test_true_for_super_admin(self):
        assert is_avamed_super_admin({"role": "avamed-super-admin"}) is True

    @pytest.mark.parametrize("role", ["admin", "staff", "readonly"])
    def test_false_for_everyone_else(self, role):
        assert is_avamed_super_admin({"role": role}) is False


class TestRequireGuards:
    def test_require_staff_edit_blocks_readonly(self):
        with pytest.raises(HTTPException) as exc:
            require_staff_edit({"role": "readonly"})
        assert exc.value.status_code == 403

    def test_require_staff_edit_allows_super_admin(self):
        require_staff_edit({"role": "avamed-super-admin"})  # must not raise

    def test_require_staff_admin_blocks_staff(self):
        with pytest.raises(HTTPException) as exc:
            require_staff_admin({"role": "staff"})
        assert exc.value.status_code == 403

    def test_require_staff_admin_allows_super_admin(self):
        require_staff_admin({"role": "avamed-super-admin"})  # must not raise

    def test_require_avamed_super_admin_blocks_admin(self):
        """admin (tenant-admin) must NOT reach the tenant picker — Avamed-only."""
        with pytest.raises(HTTPException) as exc:
            require_avamed_super_admin({"role": "admin"})
        assert exc.value.status_code == 403

    def test_require_avamed_super_admin_blocks_staff_and_readonly(self):
        for role in ("staff", "readonly"):
            with pytest.raises(HTTPException):
                require_avamed_super_admin({"role": role})

    def test_require_avamed_super_admin_allows_super_admin(self):
        require_avamed_super_admin({"role": "avamed-super-admin"})  # must not raise

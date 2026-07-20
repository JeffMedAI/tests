"""
TDD tests for create_tenant_db.py — written BEFORE the implementation.
Run: python -m pytest scripts/tenant/test_create_tenant_db.py -v

Multi-tenancy step 4 (governance/MULTI_TENANCY_PROPOSAL.md sequence table, row 4):
"Stand up the stmarks tenant instance + hostname + its staff accounts" — this
script is the "its staff accounts" half, for a brand-new tenant with no existing
data (unlike migrate_to_tenant_db.py, which copies an already-populated database).
"""
import sqlite3
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from create_tenant_db import create_tenant_db  # noqa: E402

_DASHBOARD_DIR = Path(__file__).resolve().parents[2] / "dashboard"
sys.path.insert(0, str(_DASHBOARD_DIR))
import app.auth as auth_module  # noqa: E402


class TestCreateTenantDb:
    def test_dest_file_exists_after_create(self, tmp_path):
        db_path = tmp_path / "tenant2.sqlite"
        result_path, _ = create_tenant_db(db_path, "Tenant 2", "Tenant 2 Admin", "Tenant 2 Staff")
        assert result_path.exists()

    def test_seeds_exactly_two_staff_rows(self, tmp_path):
        db_path = tmp_path / "tenant2.sqlite"
        create_tenant_db(db_path, "Tenant 2", "Tenant 2 Admin", "Tenant 2 Staff")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM staff_users ORDER BY role").fetchall()
        conn.close()

        assert len(rows) == 2
        roles = {row["role"] for row in rows}
        assert roles == {"admin", "staff"}

    def test_no_demo_rows_and_no_null_password_hashes(self, tmp_path):
        db_path = tmp_path / "tenant2.sqlite"
        create_tenant_db(db_path, "Tenant 2", "Tenant 2 Admin", "Tenant 2 Staff")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM staff_users").fetchall()
        conn.close()

        display_names = {row["display_name"] for row in rows}
        assert "Admin Demo" not in display_names
        for row in rows:
            assert row["password_hash"] is not None
            assert row["password_hash"].count(":") == 4  # 5-part pbkdf2 format

    def test_both_placeholders_force_password_change(self, tmp_path):
        db_path = tmp_path / "tenant2.sqlite"
        create_tenant_db(db_path, "Tenant 2", "Tenant 2 Admin", "Tenant 2 Staff")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT must_change_password FROM staff_users").fetchall()
        conn.close()

        assert all(row["must_change_password"] == 1 for row in rows)

    def test_returned_passwords_verify_against_stored_hashes(self, tmp_path):
        db_path = tmp_path / "tenant2.sqlite"
        _, passwords = create_tenant_db(db_path, "Tenant 2", "Tenant 2 Admin", "Tenant 2 Staff")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = {row["role"]: row for row in conn.execute("SELECT * FROM staff_users").fetchall()}
        conn.close()

        assert auth_module.verify_password(passwords["admin"], rows["admin"]["password_hash"])
        assert auth_module.verify_password(passwords["staff"], rows["staff"]["password_hash"])

    def test_placeholder_emails_are_distinct_and_obviously_fake(self, tmp_path):
        db_path = tmp_path / "tenant2.sqlite"
        create_tenant_db(db_path, "Tenant 2", "Tenant 2 Admin", "Tenant 2 Staff")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = {row["role"]: row for row in conn.execute("SELECT * FROM staff_users").fetchall()}
        conn.close()

        assert rows["admin"]["email"] != rows["staff"]["email"]
        assert rows["admin"]["email"].endswith(".placeholder")
        assert rows["staff"]["email"].endswith(".placeholder")

    def test_refuses_existing_file_without_force(self, tmp_path):
        db_path = tmp_path / "tenant2.sqlite"
        create_tenant_db(db_path, "Tenant 2", "Tenant 2 Admin", "Tenant 2 Staff")

        with pytest.raises(FileExistsError):
            create_tenant_db(db_path, "Tenant 2", "Tenant 2 Admin", "Tenant 2 Staff")

    def test_force_true_twice_does_not_duplicate_rows(self, tmp_path):
        db_path = tmp_path / "tenant2.sqlite"
        create_tenant_db(db_path, "Tenant 2", "Tenant 2 Admin", "Tenant 2 Staff")
        create_tenant_db(db_path, "Tenant 2", "Tenant 2 Admin", "Tenant 2 Staff", force=True)

        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM staff_users").fetchone()[0]
        conn.close()
        assert count == 2

    def test_pin_hash_is_null_not_a_fake_pin(self, tmp_path):
        """No real PIN is generated for a placeholder account — pin_hash stays
        NULL (a valid, fail-closed state) rather than seeding an unusable,
        non-numeric PIN that could never match auth.verify_pin()'s digit check."""
        db_path = tmp_path / "tenant2.sqlite"
        create_tenant_db(db_path, "Tenant 2", "Tenant 2 Admin", "Tenant 2 Staff")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT pin_hash FROM staff_users").fetchall()
        conn.close()

        assert all(row["pin_hash"] is None for row in rows)

    def test_writes_staff_created_audit_events(self, tmp_path):
        db_path = tmp_path / "tenant2.sqlite"
        create_tenant_db(db_path, "Tenant 2", "Tenant 2 Admin", "Tenant 2 Staff")

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM audit_events WHERE action = 'staff_created'"
        ).fetchall()
        conn.close()

        assert len(rows) == 2
        assert all(row["edited_by"] == "tenant_provisioning_script" for row in rows)

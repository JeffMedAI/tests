"""
TDD tests for seed_super_admin.py — written before/alongside the implementation.
Run: python -m pytest scripts/tenant/test_seed_super_admin.py -v

Multi-tenancy step 5 (governance/STEP5_DESIGN.md §4): one avamed-super-admin
identity, replicated as a row in each of several tenant DBs.
"""
import sqlite3
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from create_tenant_db import create_tenant_db  # noqa: E402
from seed_super_admin import seed_super_admin  # noqa: E402

_DASHBOARD_DIR = Path(__file__).resolve().parents[2] / "dashboard"
sys.path.insert(0, str(_DASHBOARD_DIR))
import app.auth as auth_module  # noqa: E402


def _two_tenant_dbs(tmp_path):
    db1 = tmp_path / "tenant1.sqlite"
    db2 = tmp_path / "tenant2.sqlite"
    create_tenant_db(db1, "Tenant 1", "T1 Admin", "T1 Staff")
    create_tenant_db(db2, "Tenant 2", "T2 Admin", "T2 Staff")
    return db1, db2


class TestSeedSuperAdmin:
    def test_refuses_missing_db_path(self, tmp_path):
        missing = tmp_path / "does-not-exist.sqlite"
        with pytest.raises(FileNotFoundError):
            seed_super_admin([missing], "Saeed", "avamed-saeed", "saeed@example.invalid")

    def test_creates_one_row_in_each_target_db(self, tmp_path):
        db1, db2 = _two_tenant_dbs(tmp_path)
        results = seed_super_admin(
            [db1, db2], "Saeed (Avamed)", "avamed-saeed", "saeed@example.invalid"
        )
        assert results[str(db1)]["outcome"] == "created"
        assert results[str(db2)]["outcome"] == "created"

        for db_path in (db1, db2):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM staff_users WHERE username='avamed-saeed'"
            ).fetchone()
            conn.close()
            assert row is not None
            assert row["role"] == "avamed-super-admin"
            assert row["display_name"] == "Saeed (Avamed)"
            assert row["email"] == "saeed@example.invalid"
            assert row["must_change_password"] == 1

    def test_each_tenant_gets_a_distinct_password(self, tmp_path):
        """Saeed's decision 2026-07-27 (matching Security's recommendation):
        per-tenant one-time passwords, not one shared across every tenant DB —
        a leaked password then only ever exposes one tenant's row."""
        db1, db2 = _two_tenant_dbs(tmp_path)
        results = seed_super_admin(
            [db1, db2], "Saeed (Avamed)", "avamed-saeed", "saeed@example.invalid"
        )
        password1 = results[str(db1)]["password"]
        password2 = results[str(db2)]["password"]
        assert password1 != password2

        for db_path, password in ((db1, password1), (db2, password2)):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT password_hash FROM staff_users WHERE username='avamed-saeed'"
            ).fetchone()
            conn.close()
            # each tenant's own password verifies against that tenant's own hash...
            assert auth_module.verify_password(password, row["password_hash"])

        # ...and NEITHER password works against the OTHER tenant's hash.
        conn1 = sqlite3.connect(db1)
        conn1.row_factory = sqlite3.Row
        hash1 = conn1.execute("SELECT password_hash FROM staff_users WHERE username='avamed-saeed'").fetchone()["password_hash"]
        conn1.close()
        assert not auth_module.verify_password(password2, hash1)

    def test_does_not_touch_tenant_own_placeholder_accounts(self, tmp_path):
        db1, db2 = _two_tenant_dbs(tmp_path)
        seed_super_admin([db1, db2], "Saeed (Avamed)", "avamed-saeed", "saeed@example.invalid")

        conn = sqlite3.connect(db1)
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT username, role FROM staff_users").fetchall()
        conn.close()
        usernames = {row["username"] for row in rows}
        # the two placeholders from create_tenant_db.py plus the new super-admin
        assert "admin-tenant1" in usernames
        assert "staff-tenant1" in usernames
        assert "avamed-saeed" in usernames
        assert len(rows) == 3

    def test_duplicate_username_without_force_raises(self, tmp_path):
        db1, db2 = _two_tenant_dbs(tmp_path)
        seed_super_admin([db1, db2], "Saeed (Avamed)", "avamed-saeed", "saeed@example.invalid")
        with pytest.raises(ValueError):
            seed_super_admin([db1], "Saeed (Avamed)", "avamed-saeed", "saeed@example.invalid")

    def test_force_updates_existing_row_without_duplicating(self, tmp_path):
        db1, db2 = _two_tenant_dbs(tmp_path)
        seed_super_admin([db1, db2], "Saeed (Avamed)", "avamed-saeed", "saeed@example.invalid")
        seed_super_admin(
            [db1, db2], "Saeed (Avamed)", "avamed-saeed", "saeed@example.invalid", force=True
        )
        conn = sqlite3.connect(db1)
        count = conn.execute(
            "SELECT COUNT(*) FROM staff_users WHERE username='avamed-saeed'"
        ).fetchone()[0]
        conn.close()
        assert count == 1

    def test_writes_audit_event_with_provisioning_marker(self, tmp_path):
        db1, db2 = _two_tenant_dbs(tmp_path)
        seed_super_admin([db1, db2], "Saeed (Avamed)", "avamed-saeed", "saeed@example.invalid")

        conn = sqlite3.connect(db1)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM audit_events WHERE edited_by='super_admin_provisioning_script'"
        ).fetchall()
        conn.close()
        assert len(rows) == 1
        assert rows[0]["action"] == "staff_created"

    def test_pin_hash_stays_null(self, tmp_path):
        db1, db2 = _two_tenant_dbs(tmp_path)
        seed_super_admin([db1, db2], "Saeed (Avamed)", "avamed-saeed", "saeed@example.invalid")
        conn = sqlite3.connect(db1)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT pin_hash FROM staff_users WHERE username='avamed-saeed'").fetchone()
        conn.close()
        assert row["pin_hash"] is None

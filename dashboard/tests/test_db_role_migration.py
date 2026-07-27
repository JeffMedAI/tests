"""
TDD tests for db.py's role-CHECK-constraint migration (STEP5_DESIGN.md §3).

SQLite has no ALTER TABLE for CHECK constraints, and CREATE TABLE IF NOT EXISTS
never touches an existing table, so a tenant DB created before
'avamed-super-admin' existed must be migrated in place before it can accept
that role. Build a DB under the OLD schema by hand (simulating churchtown.sqlite/
tenant2.sqlite as they exist today), then prove init_db() fixes it without
losing data.
"""
from __future__ import annotations

import sqlite3

import pytest

import app.db as db_module


def _make_old_schema_db(path):
    """Create a DB with the pre-step-5 staff_users/staff_invitations schema —
    CHECK(role IN ('admin', 'staff', 'readonly')), no avamed-super-admin."""
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE staff_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL CHECK(role IN ('admin', 'staff', 'readonly')),
            demo_pin_hash TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            username TEXT,
            password_hash TEXT,
            pin_hash TEXT,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TEXT,
            last_login_at TEXT,
            must_change_password INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE staff_invitations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'staff', 'readonly')),
            invited_by_staff_id INTEGER,
            token_hash TEXT,
            status TEXT NOT NULL CHECK(status IN ('pending', 'accepted', 'cancelled', 'expired')),
            created_at TEXT NOT NULL,
            expires_at TEXT,
            accepted_at TEXT,
            cancelled_at TEXT
        )
        """
    )
    conn.execute(
        "INSERT INTO staff_users (display_name, email, role, active, created_at, updated_at) "
        "VALUES ('Existing Admin', 'admin@example.placeholder', 'admin', 1, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO staff_invitations (email, role, status, created_at) "
        "VALUES ('invite@example.placeholder', 'staff', 'pending', '2026-01-01T00:00:00Z')"
    )
    conn.commit()
    conn.close()


class TestRoleCheckMigration:
    def test_old_schema_rejects_new_role_before_migration(self, tmp_path):
        """Sanity check the test fixture actually reproduces the bug."""
        db_path = tmp_path / "old.sqlite"
        _make_old_schema_db(db_path)
        conn = sqlite3.connect(db_path)
        try:
            with pytest.raises(sqlite3.IntegrityError):
                conn.execute(
                    "INSERT INTO staff_users (display_name, role, active, created_at, updated_at) "
                    "VALUES ('X', 'avamed-super-admin', 1, '2026-01-01', '2026-01-01')"
                )
        finally:
            conn.close()

    def test_init_db_widens_check_and_preserves_existing_rows(self, tmp_path):
        db_path = tmp_path / "old.sqlite"
        _make_old_schema_db(db_path)

        conn = db_module.connect(db_path)
        try:
            db_module.init_db(conn)

            # Existing row survived, with its original id/data intact.
            row = conn.execute(
                "SELECT id, display_name, email, role FROM staff_users WHERE display_name='Existing Admin'"
            ).fetchone()
            assert row is not None
            assert row["id"] == 1
            assert row["role"] == "admin"
            assert row["email"] == "admin@example.placeholder"

            invite_row = conn.execute(
                "SELECT email, role, status FROM staff_invitations WHERE email='invite@example.placeholder'"
            ).fetchone()
            assert invite_row is not None
            assert invite_row["status"] == "pending"

            # New role now accepted.
            conn.execute(
                "INSERT INTO staff_users (display_name, role, active, created_at, updated_at) "
                "VALUES ('Avamed Support', 'avamed-super-admin', 1, '2026-01-01', '2026-01-01')"
            )
            conn.execute(
                "INSERT INTO staff_invitations (email, role, status, created_at) "
                "VALUES ('super@example.placeholder', 'avamed-super-admin', 'pending', '2026-01-01')"
            )
            conn.commit()

            count = conn.execute(
                "SELECT COUNT(*) FROM staff_users WHERE role='avamed-super-admin'"
            ).fetchone()[0]
            assert count == 1
        finally:
            conn.close()

    def test_migration_is_idempotent(self, tmp_path):
        """Calling init_db() twice on an already-migrated DB must not error or duplicate rows."""
        db_path = tmp_path / "old.sqlite"
        _make_old_schema_db(db_path)

        conn = db_module.connect(db_path)
        try:
            db_module.init_db(conn)
            db_module.init_db(conn)  # second call — must be a no-op for the migration
            count = conn.execute("SELECT COUNT(*) FROM staff_users").fetchone()[0]
            assert count == 1
        finally:
            conn.close()

    def test_sessions_fk_still_resolves_after_migration(self, tmp_path):
        """The staff_users table gets renamed/recreated in place — sessions.user_id
        must still resolve to the same row (same id) afterwards.

        This originally only checked a JOIN returns a row, which passes even
        with a CORRUPTED foreign key definition — sqlite3 does not enforce FKs
        by default, so a plain JOIN can't tell a real FK from a dangling one.
        Hardened per Security review 2026-07-22 (which reproduced the FK
        corruption bug this test was supposed to catch, and didn't): assert
        under PRAGMA foreign_keys=ON that (a) the insert actually succeeds
        (it would raise IntegrityError if the FK pointed at a dropped table),
        (b) PRAGMA foreign_key_check reports zero violations, and (c) the
        sessions/auth_reset_tokens table DDL itself still references plain
        'staff_users', not a temporary migration table name."""
        db_path = tmp_path / "old.sqlite"
        _make_old_schema_db(db_path)

        conn = db_module.connect(db_path)
        try:
            db_module.init_db(conn)
            conn.execute("PRAGMA foreign_keys=ON")

            # (a) insert under FK enforcement must succeed — it would raise
            # IntegrityError here if sessions.user_id's FK were repointed at
            # a table that no longer exists (the exact bug Security found).
            conn.execute(
                "INSERT INTO sessions (token, user_id, created_at, last_active_at, expires_at) "
                "VALUES ('tok', 1, '2026-01-01', '2026-01-01', '2099-01-01')"
            )
            conn.execute(
                "INSERT INTO auth_reset_tokens (user_id, token, created_at, expires_at) "
                "VALUES (1, 'reset-tok', '2026-01-01', '2099-01-01')"
            )
            conn.commit()

            # (b) no dangling/broken FK anywhere in the database.
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            assert violations == []

            # (c) the DDL text itself references 'staff_users', not a
            # __pre_role_migration temp name (the actual failure mode: RENAME
            # rewriting dependents' FK definitions to point at the temp table).
            for dependent_table in ("sessions", "auth_reset_tokens"):
                ddl = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                    (dependent_table,),
                ).fetchone()["sql"]
                assert "REFERENCES staff_users" in ddl
                assert "pre_role_migration" not in ddl

            row = conn.execute(
                "SELECT staff_users.display_name FROM sessions "
                "JOIN staff_users ON staff_users.id = sessions.user_id WHERE sessions.token='tok'"
            ).fetchone()
            assert row is not None
            assert row["display_name"] == "Existing Admin"
        finally:
            conn.close()

    def test_fresh_db_gets_new_check_directly_no_migration_needed(self, tmp_path):
        """A brand-new DB (no pre-existing table) should get the widened CHECK
        straight from the CREATE TABLE statement — migration path never triggers."""
        db_path = tmp_path / "fresh.sqlite"
        conn = db_module.connect(db_path)
        try:
            db_module.init_db(conn)
            conn.execute(
                "INSERT INTO staff_users (display_name, role, active, created_at, updated_at) "
                "VALUES ('Fresh Super Admin', 'avamed-super-admin', 1, '2026-01-01', '2026-01-01')"
            )
            conn.commit()
            count = conn.execute(
                "SELECT COUNT(*) FROM staff_users WHERE role='avamed-super-admin'"
            ).fetchone()[0]
            assert count == 1
        finally:
            conn.close()

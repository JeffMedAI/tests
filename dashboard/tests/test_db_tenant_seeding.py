"""init_db()'s demo-row auto-seed must only fire for the default, no-tenant instance.

Regression coverage for a bug found while building multi-tenancy step 4: a brand-new
empty tenant database used to get 3 demo staff_users rows seeded automatically,
including an "Admin Demo" row with password_hash=NULL — unusable, since
auth.verify_password() raises ValueError on a malformed hash. Tenant onboarding must
seed its own real (even if placeholder) accounts instead.
"""
import sqlite3

from app.db import init_db


def _connect_memory() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


def _staff_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM staff_users").fetchone()[0]


def test_init_db_seeds_demo_rows_when_no_tenant_name(monkeypatch):
    """Today's default, no-tenant instance must keep its existing demo-seed behaviour."""
    monkeypatch.delenv("JEFFLOCAL_TENANT_NAME", raising=False)
    conn = _connect_memory()
    init_db(conn)
    assert _staff_count(conn) == 3


def test_init_db_skips_demo_rows_when_tenant_name_set(monkeypatch):
    """A tenant-mode instance (JEFFLOCAL_TENANT_NAME set) must start with zero staff rows."""
    monkeypatch.setenv("JEFFLOCAL_TENANT_NAME", "Tenant 2")
    conn = _connect_memory()
    init_db(conn)
    assert _staff_count(conn) == 0

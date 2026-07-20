"""
Multi-tenancy step 4: create a brand-new, empty tenant database — schema
initialised, two PLACEHOLDER staff logins seeded (one admin, one staff).

This is the fresh-database counterpart to migrate_to_tenant_db.py, which only
copies an already-populated database (e.g. dashboard.sqlite -> churchtown.sqlite).
A genuinely new tenant has no existing data to copy, so this script initialises
schema directly via dashboard/app/db.py and seeds real (even if placeholder)
credentials via dashboard/app/auth.py — reusing both rather than reimplementing.

Seeded accounts are PLACEHOLDERS: obviously-fake names/emails
(admin@<tenant-slug>.placeholder / staff@<tenant-slug>.placeholder), both forced
to change password on first login (must_change_password=1). Replace them with
real named people and real emails before that tenant goes live — see
governance/MULTI_TENANCY_PROPOSAL.md.

One-time generated passwords are printed to stdout ONCE by this script's CLI
entry point and never logged or committed anywhere.
"""
from __future__ import annotations

import argparse
import os
import secrets
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

_DASHBOARD_DIR = Path(__file__).resolve().parents[2] / "dashboard"
sys.path.insert(0, str(_DASHBOARD_DIR))

import app.auth as auth_module  # noqa: E402
import app.audit as audit_module  # noqa: E402
import app.db as db_module  # noqa: E402


def _generate_temp_password() -> str:
    return secrets.token_urlsafe(12)


def _slug(tenant_name: str) -> str:
    return tenant_name.lower().replace(" ", "")


def create_tenant_db(
    db_path: Path,
    tenant_name: str,
    admin_display_name: str,
    staff_display_name: str,
    force: bool = False,
) -> tuple[Path, dict[str, str]]:
    """
    Create a fresh, empty tenant SQLite database with schema initialised and
    two placeholder staff_users rows seeded (one admin, one staff).

    Raises FileExistsError if db_path already exists and force is not True.
    Returns (db_path, {"admin": one_time_password, "staff": one_time_password}).
    """
    if db_path.exists():
        if not force:
            raise FileExistsError(
                f"Tenant database already exists: {db_path} — pass force=True to overwrite"
            )
        db_path.unlink()

    db_path.parent.mkdir(parents=True, exist_ok=True)

    # db.py's init_db() only skips its demo-seed block when JEFFLOCAL_TENANT_NAME
    # is set — set it for the duration of this call so a fresh tenant DB never
    # gets the unusable ("Admin Demo", password_hash=NULL) rows.
    previous_tenant_name = os.environ.get("JEFFLOCAL_TENANT_NAME")
    os.environ["JEFFLOCAL_TENANT_NAME"] = tenant_name
    try:
        conn: sqlite3.Connection = db_module.connect(db_path)
        try:
            db_module.init_db(conn)

            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            slug = _slug(tenant_name)
            passwords: dict[str, str] = {}
            for role, display_name in (
                ("admin", admin_display_name),
                ("staff", staff_display_name),
            ):
                password = _generate_temp_password()
                passwords[role] = password
                username = f"{role}-{slug}"
                email = f"{role}@{slug}.placeholder"
                # pin_hash stays NULL — no real PIN is generated for a placeholder
                # account. auth.py's PIN-login path checks `bool(stored)` before
                # attempting verification, so NULL fails closed rather than
                # seeding an unusable/non-numeric PIN.
                conn.execute(
                    """
                    INSERT INTO staff_users
                        (display_name, username, email, role, password_hash, pin_hash,
                         failed_attempts, must_change_password, active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, NULL, 0, 1, 1, ?, ?)
                    """,
                    (
                        display_name,
                        username,
                        email,
                        role,
                        auth_module.hash_password(password),
                        now,
                        now,
                    ),
                )
                audit_module.write_audit_event(
                    conn,
                    call_id="staff",
                    action="staff_created",
                    edited_by="tenant_provisioning_script",
                    changed_fields=["display_name", "username", "email", "role", "active"],
                    old_values={},
                    new_values={
                        "display_name": display_name,
                        "username": username,
                        "email": email,
                        "role": role,
                        "active": True,
                    },
                )
            conn.commit()
        finally:
            conn.close()
    finally:
        if previous_tenant_name is None:
            os.environ.pop("JEFFLOCAL_TENANT_NAME", None)
        else:
            os.environ["JEFFLOCAL_TENANT_NAME"] = previous_tenant_name

    return db_path, passwords


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", required=True, type=Path)
    parser.add_argument("--tenant-name", required=True)
    parser.add_argument("--admin-name", required=True)
    parser.add_argument("--staff-name", required=True)
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    path, passwords = create_tenant_db(
        args.db_path,
        args.tenant_name,
        args.admin_name,
        args.staff_name,
        force=args.force,
    )
    print(f"OK — created {path}")
    print(f"Admin one-time password: {passwords['admin']}")
    print(f"Staff one-time password: {passwords['staff']}")
    print("Both accounts are forced to change password on first login.")
    print("These are placeholder accounts — replace with real named staff before go-live.")

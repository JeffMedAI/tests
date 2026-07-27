"""
Multi-tenancy step 5: seed ONE avamed-super-admin identity as a row inside each
of several tenant databases.

governance/MULTI_TENANCY_PROPOSAL.md §6/§6b: Avamed has a standing admin
account inside every tenant DB, reached via the /tenants picker, one tenant at
a time. There is no shared cross-tenant table — staff_users is per-tenant, so
"one account" for one real person means "one row per tenant DB, same identity,
replicated". See governance/STEP5_DESIGN.md §4 for the full reasoning,
including why display_name/username/email are required CLI args rather than
hardcoded (this script is committed to git). Each tenant gets its OWN one-time
password (Saeed's decision, 2026-07-27, matching Security's recommendation) —
a leaked password only ever exposes one tenant's row, never every tenant at
once. The identity (display_name/username/email) is still shared across
tenants; only the credential is per-tenant.

Deliberately does NOT touch STAFF_ROLES/the ordinary staff-management HTTP
routes — this is the ONLY sanctioned way to create an avamed-super-admin
account (see consts.AVAMED_SUPER_ADMIN_ROLE's docstring and STEP5_DESIGN.md §2).

Run order example (two tenants):
    python scripts/tenant/seed_super_admin.py \\
        --display-name "Saeed (Avamed)" --username avamed-saeed --email saeed@example.invalid \\
        --db-path C:\\JeffLocal\\dashboard\\data\\churchtown.sqlite \\
        --db-path C:\\JeffLocal\\dashboard\\data\\tenants\\tenant2.sqlite
"""
from __future__ import annotations

import argparse
import secrets
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

_DASHBOARD_DIR = Path(__file__).resolve().parents[2] / "dashboard"
sys.path.insert(0, str(_DASHBOARD_DIR))

import app.auth as auth_module  # noqa: E402
import app.audit as audit_module  # noqa: E402
import app.consts as consts_module  # noqa: E402
import app.db as db_module  # noqa: E402

PROVISIONING_MARKER = "super_admin_provisioning_script"


def _generate_temp_password() -> str:
    return secrets.token_urlsafe(12)


def seed_super_admin(
    db_paths: list[Path],
    display_name: str,
    username: str,
    email: str,
    force: bool = False,
) -> dict[str, dict[str, str]]:
    """
    Insert one avamed-super-admin row into every DB in db_paths, all sharing
    the same identity (display_name/username/email) but each getting its OWN
    freshly generated one-time password.

    Per-tenant passwords, not a shared one (Saeed's decision, 2026-07-27,
    matching Security's recommendation): a leaked or intercepted password then
    only ever exposes ONE tenant's row, not every tenant Avamed has access to
    at once. Generated fresh inside the loop, one secrets.token_urlsafe(12)
    call per tenant — see STEP5_DESIGN.md §4.

    Raises FileNotFoundError if any db_path does not exist.
    Raises ValueError if the username already exists in a target DB and force
    is not True (force updates that row's password/role in place instead of
    inserting a duplicate).
    Returns {str(db_path): {"outcome": "created"|"updated", "password": <that DB's own one-time password>}}.
    """
    for db_path in db_paths:
        if not db_path.exists():
            raise FileNotFoundError(f"Tenant database not found: {db_path}")

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    role = consts_module.AVAMED_SUPER_ADMIN_ROLE

    results: dict[str, dict[str, str]] = {}
    for db_path in db_paths:
        password = _generate_temp_password()  # fresh per tenant — never reused across DBs
        password_hash = auth_module.hash_password(password)
        conn = db_module.connect(db_path)
        try:
            db_module.init_db(conn)  # idempotent — also runs the role-CHECK migration

            existing = conn.execute(
                "SELECT id FROM staff_users WHERE username = ?", (username,)
            ).fetchone()
            if existing is not None:
                if not force:
                    raise ValueError(
                        f"username '{username}' already exists in {db_path} — pass force=True to update it"
                    )
                old = dict(existing)
                conn.execute(
                    """
                    UPDATE staff_users
                    SET display_name = ?, email = ?, role = ?, password_hash = ?,
                        must_change_password = 1, active = 1, updated_at = ?
                    WHERE username = ?
                    """,
                    (display_name, email, role, password_hash, now, username),
                )
                audit_module.write_audit_event(
                    conn,
                    call_id="staff",
                    action="staff_updated",
                    edited_by=PROVISIONING_MARKER,
                    changed_fields=["display_name", "email", "role", "password_hash"],
                    old_values={"id": old.get("id")},
                    new_values={"display_name": display_name, "email": email, "role": role},
                )
                results[str(db_path)] = {"outcome": "updated", "password": password}
            else:
                conn.execute(
                    """
                    INSERT INTO staff_users
                        (display_name, username, email, role, password_hash, pin_hash,
                         failed_attempts, must_change_password, active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, NULL, 0, 1, 1, ?, ?)
                    """,
                    (display_name, username, email, role, password_hash, now, now),
                )
                audit_module.write_audit_event(
                    conn,
                    call_id="staff",
                    action="staff_created",
                    edited_by=PROVISIONING_MARKER,
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
                results[str(db_path)] = {"outcome": "created", "password": password}
            conn.commit()
        finally:
            conn.close()

    return results


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--display-name", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--db-path", required=True, type=Path, action="append", dest="db_paths")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    results = seed_super_admin(
        args.db_paths, args.display_name, args.username, args.email, force=args.force
    )
    print("Each tenant below has its OWN one-time password — do not reuse one across tenants.")
    for db_path, info in results.items():
        slug = Path(db_path).stem  # e.g. "tenant2.sqlite" -> "tenant2" — label only, not a registry lookup
        print(f"OK — {info['outcome']}: [{slug}] {db_path}")
        print(f"    one-time password: {info['password']}")
    print("Forced to change password on first login, per tenant, separately.")

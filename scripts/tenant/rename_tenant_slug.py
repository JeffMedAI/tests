"""
Multi-tenancy step 5: apply the tenant1 naming convention to Churchtown.

governance/TENANT_REGISTRY.md (decided by Saeed 2026-07-21): slug = stable
`tenant1`, display name = "Churchtown Medical Centre". Today's churchtown.sqlite
is an unused step-3 migrated copy (verified 78 cases/5 staff_users/1251
audit_events/integrity OK) — this script copies it to a tenant1-named database
and writes config/tenants/tenant1.env in the same format as tenant2.env. See
governance/STEP5_DESIGN.md §7 for the full scope and what this script
deliberately does NOT do (it does not touch dashboard.sqlite, does not restart
or repoint the live 8765 process — that cutover is a separate, deliberate ops
step for DevOps/Saeed to run, same as step 4's apply_tenant2_ops.ps1).

Reuses migrate_to_tenant_db.py's copy + verify logic rather than reimplementing
it — same sqlite3.Connection.backup() approach, safe against a live writer, and
the same VERIFY_TABLES row-count + integrity_check comparison.

Takes source/dest paths as parameters (never hardcodes a single "the real
production path" as the only option) so it can be proven against throwaway
copies in tests, per this step's brief. --dry-run reports what would happen
without writing anything.

Usage (dry run, safe to run anytime):
    python scripts/tenant/rename_tenant_slug.py --dry-run

Usage (apply, against real paths — NOT run by this build):
    python scripts/tenant/rename_tenant_slug.py \\
        --source C:\\JeffLocal\\dashboard\\data\\churchtown.sqlite \\
        --dest   C:\\JeffLocal\\dashboard\\data\\tenant1.sqlite \\
        --env-path C:\\JeffLocal\\config\\tenants\\tenant1.env
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migrate_to_tenant_db import migrate_tenant_db, verify_migration  # noqa: E402

DEFAULT_SOURCE = Path(r"C:\JeffLocal\dashboard\data\churchtown.sqlite")
DEFAULT_DEST = Path(r"C:\JeffLocal\dashboard\data\tenant1.sqlite")
DEFAULT_ENV_PATH = Path(r"C:\JeffLocal\config\tenants\tenant1.env")

SLUG = "tenant1"
DISPLAY_NAME = "Churchtown Medical Centre"
PORT = 8765

ENV_TEMPLATE = """# TENANT - {display_name}. See governance/TENANT_REGISTRY.md.
# Slug is stable forever: {slug}. Display name may change freely; slug never does.
#
# No patient data, no secrets - see _template.env.example for the format rules.

JEFFLOCAL_TENANT_NAME={display_name}
JEFFLOCAL_DB_PATH={db_path}
JEFFLOCAL_PORT={port}
"""


def render_env_file(display_name: str, db_path: Path, port: int, slug: str = SLUG) -> str:
    return ENV_TEMPLATE.format(display_name=display_name, db_path=db_path, port=port, slug=slug)


def plan(source_db: Path, dest_db: Path, env_path: Path) -> dict:
    """Describe what an apply run would do, without doing it."""
    return {
        "source_db": str(source_db),
        "source_exists": source_db.exists(),
        "dest_db": str(dest_db),
        "dest_exists": dest_db.exists(),
        "env_path": str(env_path),
        "env_exists": env_path.exists(),
        "slug": SLUG,
        "display_name": DISPLAY_NAME,
        "port": PORT,
    }


def apply_rename(
    source_db: Path = DEFAULT_SOURCE,
    dest_db: Path = DEFAULT_DEST,
    env_path: Path = DEFAULT_ENV_PATH,
    force: bool = False,
) -> dict:
    """
    Copy source_db -> dest_db (via migrate_tenant_db), verify, then write the
    tenant1 .env file. Does NOT touch source_db. Does NOT restart any service.

    Returns a report dict: status ("ok"/"error"), dest_file, env_path, verify, error.
    """
    try:
        dest_file = migrate_tenant_db(source_db, dest_db, force=force)
    except Exception as exc:
        return {"status": "error", "dest_file": None, "env_path": None, "verify": None, "error": str(exc)}

    try:
        verify_report = verify_migration(source_db, dest_file)
    except Exception as exc:
        return {"status": "error", "dest_file": str(dest_file), "env_path": None, "verify": None, "error": str(exc)}

    if not verify_report["match"]:
        return {
            "status": "error",
            "dest_file": str(dest_file),
            "env_path": None,
            "verify": verify_report,
            "error": "verification did not match — env file NOT written",
        }

    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(render_env_file(DISPLAY_NAME, dest_file, PORT), encoding="ascii")

    return {
        "status": "ok",
        "dest_file": str(dest_file),
        "env_path": str(env_path),
        "verify": verify_report,
        "error": None,
    }


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--env-path", type=Path, default=DEFAULT_ENV_PATH)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    if args.dry_run:
        report = plan(args.source, args.dest, args.env_path)
        print("DRY RUN — nothing written.")
        for key, value in report.items():
            print(f"  {key}: {value}")
        raise SystemExit(0)

    result = apply_rename(args.source, args.dest, args.env_path, force=args.force)
    if result["status"] == "ok":
        print(f"OK — copied to {result['dest_file']}")
        print(f"Wrote {result['env_path']}")
        print(f"Verify: {result['verify']}")
    else:
        print(f"ERROR — {result['error']}")
        raise SystemExit(1)

"""
TDD tests for backup_db.py's multi-tenant loop — written BEFORE the change.
Run: python -m pytest scripts/backup/test_backup_multi_tenant.py -v

Multi-tenancy step 4: backup_db.py must back up every known tenant database,
not just the single hardcoded dashboard.sqlite, per
governance/MULTI_TENANCY_PROPOSAL.md section 4 ("Backups... loop over tenant
databases"). A tenant whose database doesn't exist yet (not provisioned on this
machine) must be skipped without failing the whole scheduled run.
"""
import sqlite3
from datetime import date
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from backup_db import (  # noqa: E402
    backup_filename_for_date,
    create_backup,
    prune_old_backups,
    run_all_backups,
)


def _make_source_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE cases (id INTEGER)")
    conn.commit()
    conn.close()


class TestPrefixParam:
    def test_filename_uses_custom_prefix(self):
        name = backup_filename_for_date(date(2026, 7, 8), prefix="tenant2")
        assert name == "tenant2_2026-07-08.sqlite"

    def test_filename_defaults_to_dashboard_prefix(self):
        # Existing behaviour (test_backup.py) must not change.
        name = backup_filename_for_date(date(2026, 7, 8))
        assert name == "dashboard_2026-07-08.sqlite"

    def test_create_backup_respects_prefix(self, tmp_path):
        source = tmp_path / "tenant2.sqlite"
        _make_source_db(source)
        result = create_backup(source, tmp_path / "backups", date(2026, 7, 8), prefix="tenant2")
        assert result.name == "tenant2_2026-07-08.sqlite"

    def test_prune_only_touches_matching_prefix(self, tmp_path):
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        (backup_dir / "dashboard_2020-01-01.sqlite").touch()
        (backup_dir / "tenant2_2020-01-01.sqlite").touch()

        pruned = prune_old_backups(backup_dir, retention_days=30, today=date(2026, 7, 8), prefix="tenant2")

        assert pruned == 1
        assert (backup_dir / "dashboard_2020-01-01.sqlite").exists()  # untouched
        assert not (backup_dir / "tenant2_2020-01-01.sqlite").exists()


class TestRunAllBackups:
    def test_backs_up_every_database_in_the_list(self, tmp_path):
        db_a = tmp_path / "dashboard.sqlite"
        db_b = tmp_path / "tenant2.sqlite"
        _make_source_db(db_a)
        _make_source_db(db_b)
        databases = [
            {"prefix": "dashboard", "source": db_a},
            {"prefix": "tenant2", "source": db_b},
        ]

        results = run_all_backups(databases=databases, backup_dir=tmp_path / "backups", retention_days=30)

        assert len(results) == 2
        assert all(r["status"] == "ok" for r in results)

    def test_missing_tenant_database_is_skipped_not_a_failure(self, tmp_path):
        db_a = tmp_path / "dashboard.sqlite"
        _make_source_db(db_a)
        missing = tmp_path / "not_provisioned_yet.sqlite"
        databases = [
            {"prefix": "dashboard", "source": db_a},
            {"prefix": "tenant2", "source": missing},
        ]

        results = run_all_backups(databases=databases, backup_dir=tmp_path / "backups", retention_days=30)

        by_prefix = {r["prefix"]: r for r in results}
        assert by_prefix["dashboard"]["status"] == "ok"
        assert by_prefix["tenant2"]["status"] == "skipped"

    def test_one_real_failure_does_not_block_other_tenants(self, tmp_path, monkeypatch):
        db_a = tmp_path / "dashboard.sqlite"
        db_b = tmp_path / "tenant2.sqlite"
        _make_source_db(db_a)
        _make_source_db(db_b)
        databases = [
            {"prefix": "dashboard", "source": db_a},
            {"prefix": "tenant2", "source": db_b},
        ]

        import backup_db as backup_db_module

        real_create_backup = backup_db_module.create_backup

        def _boom(source_db, backup_dir, backup_date, prefix="dashboard"):
            if prefix == "dashboard":
                raise RuntimeError("simulated disk failure")
            return real_create_backup(source_db, backup_dir, backup_date, prefix=prefix)

        monkeypatch.setattr(backup_db_module, "create_backup", _boom)

        results = run_all_backups(databases=databases, backup_dir=tmp_path / "backups", retention_days=30)
        by_prefix = {r["prefix"]: r for r in results}

        assert by_prefix["dashboard"]["status"] == "error"
        assert by_prefix["tenant2"]["status"] == "ok"

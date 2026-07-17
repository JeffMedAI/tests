"""
TDD tests for migrate_to_tenant_db.py — written BEFORE the implementation.
Run: python -m pytest scripts/tenant/test_migrate_to_tenant_db.py -v

Multi-tenancy step 3 (governance/MULTI_TENANCY_PROPOSAL.md sequence table, row 3):
"Backup, then migrate dashboard.sqlite -> churchtown.sqlite; verify."
This script does the migrate + verify half. The backup half is the existing,
already-tested scripts/backup/backup_db.py — this script does not re-back-up.
"""
import sqlite3
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from migrate_to_tenant_db import migrate_tenant_db, verify_migration, run_migration


def _make_source_db(path: Path, cases=1, staff=1, audit=1) -> None:
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE cases (id INTEGER PRIMARY KEY, name TEXT)")
    conn.execute("CREATE TABLE staff (id INTEGER PRIMARY KEY, username TEXT)")
    conn.execute("CREATE TABLE audit_log (id INTEGER PRIMARY KEY, event TEXT)")
    for i in range(cases):
        conn.execute("INSERT INTO cases (name) VALUES (?)", (f"case_{i}",))
    for i in range(staff):
        conn.execute("INSERT INTO staff (username) VALUES (?)", (f"staff_{i}",))
    for i in range(audit):
        conn.execute("INSERT INTO audit_log (event) VALUES (?)", (f"event_{i}",))
    conn.commit()
    conn.close()


# ── migrate_tenant_db ──────────────────────────────────────────────────────────

class TestMigrateTenantDb:
    def test_dest_file_exists_after_migrate(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        _make_source_db(source)
        result = migrate_tenant_db(source, tmp_path / "churchtown.sqlite")
        assert result.exists()

    def test_dest_has_same_data_as_source(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        _make_source_db(source, cases=3, staff=2)
        dest = migrate_tenant_db(source, tmp_path / "churchtown.sqlite")

        conn = sqlite3.connect(dest)
        case_count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        staff_count = conn.execute("SELECT COUNT(*) FROM staff").fetchone()[0]
        conn.close()
        assert case_count == 3
        assert staff_count == 2

    def test_raises_if_source_missing(self, tmp_path):
        source = tmp_path / "does_not_exist.sqlite"
        with pytest.raises(FileNotFoundError, match="Source database not found"):
            migrate_tenant_db(source, tmp_path / "churchtown.sqlite")

    def test_refuses_same_path_for_source_and_dest(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        _make_source_db(source)
        with pytest.raises(ValueError, match="source and dest must differ"):
            migrate_tenant_db(source, source, force=True)

    def test_refuses_to_overwrite_existing_dest_without_force(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        _make_source_db(source)
        dest = tmp_path / "churchtown.sqlite"
        dest.write_text("pretend existing tenant db")

        with pytest.raises(FileExistsError, match="already exists"):
            migrate_tenant_db(source, dest)

    def test_force_true_allows_overwrite(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        _make_source_db(source, cases=1)
        dest = tmp_path / "churchtown.sqlite"
        dest.write_text("pretend existing tenant db")

        result = migrate_tenant_db(source, dest, force=True)
        conn = sqlite3.connect(result)
        count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        conn.close()
        assert count == 1

    def test_source_untouched_after_migrate(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        _make_source_db(source, cases=5, staff=1)

        migrate_tenant_db(source, tmp_path / "churchtown.sqlite")

        conn = sqlite3.connect(source)
        case_count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        conn.close()
        assert case_count == 5  # nothing deleted from the source

    def test_returns_path_to_dest(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        _make_source_db(source)
        result = migrate_tenant_db(source, tmp_path / "churchtown.sqlite")
        assert isinstance(result, Path)
        assert result.is_file()


# ── verify_migration ───────────────────────────────────────────────────────────

class TestVerifyMigration:
    def test_reports_match_true_when_row_counts_equal(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        _make_source_db(source, cases=4, staff=2)
        dest = migrate_tenant_db(source, tmp_path / "churchtown.sqlite")

        report = verify_migration(source, dest)
        assert report["match"] is True
        assert report["tables"]["cases"]["source"] == 4
        assert report["tables"]["cases"]["dest"] == 4
        assert report["tables"]["staff"]["source"] == 2
        assert report["tables"]["staff"]["dest"] == 2

    def test_reports_match_false_when_row_counts_differ(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        _make_source_db(source, cases=4)
        dest = tmp_path / "churchtown.sqlite"
        _make_source_db(dest, cases=2)  # deliberately different

        report = verify_migration(source, dest)
        assert report["match"] is False
        assert report["tables"]["cases"]["match"] is False

    def test_reports_integrity_ok_for_valid_databases(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        _make_source_db(source)
        dest = migrate_tenant_db(source, tmp_path / "churchtown.sqlite")

        report = verify_migration(source, dest)
        assert report["source_integrity_ok"] is True
        assert report["dest_integrity_ok"] is True


# ── run_migration (integration) ────────────────────────────────────────────────

class TestRunMigration:
    def test_status_ok_on_success(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        _make_source_db(source, cases=2)
        result = run_migration(source_db=source, dest_db=tmp_path / "churchtown.sqlite")
        assert result["status"] == "ok"

    def test_reports_dest_file_and_verify_report(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        _make_source_db(source, cases=2)
        result = run_migration(source_db=source, dest_db=tmp_path / "churchtown.sqlite")
        assert Path(result["dest_file"]).exists()
        assert result["verify"]["match"] is True

    def test_error_status_if_source_missing(self, tmp_path):
        result = run_migration(
            source_db=tmp_path / "nope.sqlite",
            dest_db=tmp_path / "churchtown.sqlite",
        )
        assert result["status"] == "error"
        assert result["dest_file"] is None

    def test_error_status_if_dest_exists_and_no_force(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        _make_source_db(source)
        dest = tmp_path / "churchtown.sqlite"
        dest.write_text("existing")

        result = run_migration(source_db=source, dest_db=dest)
        assert result["status"] == "error"
        assert "already exists" in result["error"]

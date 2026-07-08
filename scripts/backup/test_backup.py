"""
TDD tests for backup_db.py — written BEFORE the implementation.
Run: python -m pytest scripts/backup/test_backup.py -v
"""
import sqlite3
from datetime import date, timedelta
from pathlib import Path
import sys

import pytest

# Import the module we are about to build (will fail until implemented)
sys.path.insert(0, str(Path(__file__).parent))
from backup_db import backup_filename_for_date, create_backup, prune_old_backups, run_backup


# ── Filename convention ────────────────────────────────────────────────────────

class TestBackupFilename:
    def test_filename_includes_iso_date(self):
        name = backup_filename_for_date(date(2026, 7, 8))
        assert "2026-07-08" in name

    def test_filename_has_sqlite_extension(self):
        name = backup_filename_for_date(date(2026, 7, 8))
        assert name.endswith(".sqlite")

    def test_filename_has_dashboard_prefix(self):
        name = backup_filename_for_date(date(2026, 7, 8))
        assert name.startswith("dashboard_")

    def test_full_filename_format(self):
        name = backup_filename_for_date(date(2026, 7, 8))
        assert name == "dashboard_2026-07-08.sqlite"


# ── create_backup ─────────────────────────────────────────────────────────────

class TestCreateBackup:
    def _make_source_db(self, path: Path) -> None:
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE cases (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO cases VALUES (1, 'test_patient')")
        conn.commit()
        conn.close()

    def test_backup_file_exists_after_create(self, tmp_path):
        source = tmp_path / "source.sqlite"
        self._make_source_db(source)
        result = create_backup(source, tmp_path / "backups", date(2026, 7, 8))
        assert result.exists()

    def test_backup_is_valid_sqlite_with_correct_data(self, tmp_path):
        source = tmp_path / "source.sqlite"
        self._make_source_db(source)
        result = create_backup(source, tmp_path / "backups", date(2026, 7, 8))

        conn = sqlite3.connect(result)
        row = conn.execute("SELECT name FROM cases WHERE id=1").fetchone()
        conn.close()
        assert row[0] == "test_patient"

    def test_backup_filename_matches_convention(self, tmp_path):
        source = tmp_path / "source.sqlite"
        self._make_source_db(source)
        result = create_backup(source, tmp_path / "backups", date(2026, 7, 8))
        assert result.name == "dashboard_2026-07-08.sqlite"

    def test_backup_creates_directory_if_missing(self, tmp_path):
        source = tmp_path / "source.sqlite"
        self._make_source_db(source)
        backup_dir = tmp_path / "backups" / "nested"
        assert not backup_dir.exists()
        create_backup(source, backup_dir, date(2026, 7, 8))
        assert backup_dir.exists()

    def test_backup_raises_if_source_missing(self, tmp_path):
        source = tmp_path / "nonexistent.sqlite"
        with pytest.raises(FileNotFoundError, match="Source database not found"):
            create_backup(source, tmp_path / "backups", date(2026, 7, 8))

    def test_backup_returns_path_to_backup_file(self, tmp_path):
        source = tmp_path / "source.sqlite"
        self._make_source_db(source)
        result = create_backup(source, tmp_path / "backups", date(2026, 7, 8))
        assert isinstance(result, Path)
        assert result.is_file()


# ── prune_old_backups ─────────────────────────────────────────────────────────

class TestPruneOldBackups:
    def _make_dummy_backup(self, backup_dir: Path, d: date) -> Path:
        path = backup_dir / f"dashboard_{d.isoformat()}.sqlite"
        path.touch()
        return path

    def test_prune_deletes_file_older_than_retention(self, tmp_path):
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        today = date(2026, 7, 8)

        old = self._make_dummy_backup(backup_dir, today - timedelta(days=31))
        recent = self._make_dummy_backup(backup_dir, today - timedelta(days=5))

        prune_old_backups(backup_dir, retention_days=30, today=today)

        assert not old.exists()
        assert recent.exists()

    def test_prune_keeps_files_at_retention_boundary(self, tmp_path):
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        today = date(2026, 7, 8)

        # Exactly 30 days ago — should be kept
        boundary = self._make_dummy_backup(backup_dir, today - timedelta(days=30))
        prune_old_backups(backup_dir, retention_days=30, today=today)
        assert boundary.exists()

    def test_prune_removes_file_at_31_days(self, tmp_path):
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        today = date(2026, 7, 8)

        too_old = self._make_dummy_backup(backup_dir, today - timedelta(days=31))
        prune_old_backups(backup_dir, retention_days=30, today=today)
        assert not too_old.exists()

    def test_prune_keeps_all_files_within_30_days(self, tmp_path):
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        today = date(2026, 7, 8)

        for days_ago in [1, 10, 20, 29, 30]:
            self._make_dummy_backup(backup_dir, today - timedelta(days=days_ago))

        prune_old_backups(backup_dir, retention_days=30, today=today)

        remaining = list(backup_dir.glob("dashboard_*.sqlite"))
        assert len(remaining) == 5

    def test_prune_ignores_non_backup_files(self, tmp_path):
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        today = date(2026, 7, 8)

        non_backup = backup_dir / "readme.txt"
        non_backup.write_text("do not delete")

        prune_old_backups(backup_dir, retention_days=30, today=today)
        assert non_backup.exists()

    def test_prune_handles_empty_directory(self, tmp_path):
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        # Should not raise
        count = prune_old_backups(backup_dir, retention_days=30, today=date(2026, 7, 8))
        assert count == 0

    def test_prune_returns_count_of_deleted_files(self, tmp_path):
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        today = date(2026, 7, 8)

        for days_ago in [31, 45, 60]:
            self._make_dummy_backup(backup_dir, today - timedelta(days=days_ago))

        count = prune_old_backups(backup_dir, retention_days=30, today=today)
        assert count == 3

    def test_prune_uses_today_by_default(self, tmp_path):
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        # recent backup — should survive
        recent = self._make_dummy_backup(backup_dir, date.today() - timedelta(days=1))
        prune_old_backups(backup_dir, retention_days=30)
        assert recent.exists()


# ── run_backup (integration) ──────────────────────────────────────────────────

class TestRunBackup:
    def _make_source_db(self, path: Path) -> None:
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE cases (id INTEGER)")
        conn.execute("INSERT INTO cases VALUES (42)")
        conn.commit()
        conn.close()

    def test_run_backup_returns_ok_status(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        self._make_source_db(source)
        result = run_backup(source_db=source, backup_dir=tmp_path / "backups", retention_days=30)
        assert result["status"] == "ok"

    def test_run_backup_reports_backup_file_path(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        self._make_source_db(source)
        result = run_backup(source_db=source, backup_dir=tmp_path / "backups", retention_days=30)
        assert result["backup_file"] is not None
        assert Path(result["backup_file"]).exists()

    def test_run_backup_reports_pruned_count(self, tmp_path):
        source = tmp_path / "dashboard.sqlite"
        self._make_source_db(source)
        result = run_backup(source_db=source, backup_dir=tmp_path / "backups", retention_days=30)
        assert "pruned_count" in result
        assert result["pruned_count"] >= 0

    def test_run_backup_returns_error_status_if_source_missing(self, tmp_path):
        source = tmp_path / "does_not_exist.sqlite"
        result = run_backup(source_db=source, backup_dir=tmp_path / "backups", retention_days=30)
        assert result["status"] == "error"
        assert result["backup_file"] is None
        assert "error" in result

"""
TDD tests for rename_tenant_slug.py (churchtown -> tenant1), written before/
alongside the implementation. Every test operates on tmp_path throwaway
copies — never on the real C:\\JeffLocal\\dashboard\\data\\churchtown.sqlite or
dashboard.sqlite. See governance/STEP5_DESIGN.md §7.
"""
import sqlite3
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from rename_tenant_slug import apply_rename, plan, render_env_file  # noqa: E402


def _make_fake_churchtown_db(path: Path) -> Path:
    """A tiny stand-in for the real churchtown.sqlite — just enough tables/rows
    for migrate_to_tenant_db.verify_migration's VERIFY_TABLES to compare."""
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE cases (call_id TEXT PRIMARY KEY)")
    conn.execute("CREATE TABLE staff_users (id INTEGER PRIMARY KEY, role TEXT)")
    conn.execute("CREATE TABLE audit_events (id INTEGER PRIMARY KEY, action TEXT)")
    conn.execute("INSERT INTO cases VALUES ('AVA-TEST-001')")
    conn.execute("INSERT INTO cases VALUES ('AVA-TEST-002')")
    conn.execute("INSERT INTO staff_users VALUES (1, 'admin')")
    conn.execute("INSERT INTO audit_events VALUES (1, 'staff_created')")
    conn.commit()
    conn.close()
    return path


class TestPlanDryRun:
    def test_dry_run_touches_nothing(self, tmp_path):
        source = _make_fake_churchtown_db(tmp_path / "churchtown.sqlite")
        dest = tmp_path / "tenant1.sqlite"
        env_path = tmp_path / "tenant1.env"

        report = plan(source, dest, env_path)

        assert report["source_exists"] is True
        assert report["dest_exists"] is False
        assert report["env_exists"] is False
        assert report["slug"] == "tenant1"
        assert report["display_name"] == "Churchtown Medical Centre"
        assert not dest.exists()
        assert not env_path.exists()


class TestApplyRename:
    def test_copies_db_and_writes_env_file(self, tmp_path):
        source = _make_fake_churchtown_db(tmp_path / "churchtown.sqlite")
        dest = tmp_path / "tenant1.sqlite"
        env_path = tmp_path / "tenant1.env"

        result = apply_rename(source, dest, env_path)

        assert result["status"] == "ok"
        assert dest.exists()
        assert env_path.exists()
        assert result["verify"]["match"] is True

    def test_source_file_untouched(self, tmp_path):
        source = _make_fake_churchtown_db(tmp_path / "churchtown.sqlite")
        dest = tmp_path / "tenant1.sqlite"
        env_path = tmp_path / "tenant1.env"

        original_bytes = source.read_bytes()
        apply_rename(source, dest, env_path)
        assert source.read_bytes() == original_bytes

    def test_env_file_content_matches_convention(self, tmp_path):
        source = _make_fake_churchtown_db(tmp_path / "churchtown.sqlite")
        dest = tmp_path / "tenant1.sqlite"
        env_path = tmp_path / "tenant1.env"

        apply_rename(source, dest, env_path)
        content = env_path.read_text(encoding="ascii")
        assert "JEFFLOCAL_TENANT_NAME=Churchtown Medical Centre" in content
        assert f"JEFFLOCAL_DB_PATH={dest}" in content
        assert "JEFFLOCAL_PORT=8765" in content

    def test_refuses_existing_dest_without_force(self, tmp_path):
        source = _make_fake_churchtown_db(tmp_path / "churchtown.sqlite")
        dest = tmp_path / "tenant1.sqlite"
        env_path = tmp_path / "tenant1.env"

        apply_rename(source, dest, env_path)
        result = apply_rename(source, dest, env_path)
        assert result["status"] == "error"

    def test_force_allows_overwrite(self, tmp_path):
        source = _make_fake_churchtown_db(tmp_path / "churchtown.sqlite")
        dest = tmp_path / "tenant1.sqlite"
        env_path = tmp_path / "tenant1.env"

        apply_rename(source, dest, env_path)
        result = apply_rename(source, dest, env_path, force=True)
        assert result["status"] == "ok"

    def test_missing_source_returns_error_not_exception(self, tmp_path):
        source = tmp_path / "does-not-exist.sqlite"
        dest = tmp_path / "tenant1.sqlite"
        env_path = tmp_path / "tenant1.env"

        result = apply_rename(source, dest, env_path)
        assert result["status"] == "error"
        assert not dest.exists()
        assert not env_path.exists()

    def test_env_not_written_if_verification_fails(self, tmp_path, monkeypatch):
        source = _make_fake_churchtown_db(tmp_path / "churchtown.sqlite")
        dest = tmp_path / "tenant1.sqlite"
        env_path = tmp_path / "tenant1.env"

        import rename_tenant_slug as module

        def _fake_verify(*a, **kw):
            return {"match": False, "tables": {}, "source_integrity_ok": True, "dest_integrity_ok": True}

        monkeypatch.setattr(module, "verify_migration", _fake_verify)
        result = apply_rename(source, dest, env_path)
        assert result["status"] == "error"
        assert not env_path.exists()


class TestRenderEnvFile:
    def test_is_plain_ascii(self):
        content = render_env_file("Churchtown Medical Centre", Path(r"C:\x\tenant1.sqlite"), 8765)
        content.encode("ascii")  # raises UnicodeEncodeError if not — known gotcha from step 4

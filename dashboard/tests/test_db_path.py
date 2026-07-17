from pathlib import Path

from app.db import _resolve_db_path


def test_resolve_db_path_uses_env_var_when_set():
    env = {"JEFFLOCAL_DB_PATH": "C:\\tenants\\churchtown\\churchtown.sqlite"}
    result = _resolve_db_path(env, base_dir=Path("C:\\JeffLocal\\dashboard"))
    assert result == Path("C:\\tenants\\churchtown\\churchtown.sqlite")


def test_resolve_db_path_falls_back_to_default_when_unset():
    env = {}
    result = _resolve_db_path(env, base_dir=Path("C:\\JeffLocal\\dashboard"))
    assert result == Path("C:\\JeffLocal\\dashboard") / "data" / "dashboard.sqlite"

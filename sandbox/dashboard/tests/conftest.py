"""
conftest.py — shared pytest fixtures for sandbox/dashboard/tests/

Key fixture: bypass_auth (autouse)
  Patches _is_public_path to return True for every path so that the
  enforce_auth HTTP middleware lets all test requests through without
  a real session cookie. Auth logic itself is tested separately via
  the auth unit tests; all other tests should not be gated by it.
"""
import pytest


@pytest.fixture(autouse=True)
def bypass_auth(monkeypatch):
    """Allow all test requests through the auth middleware."""
    import app.main as main_module
    monkeypatch.setattr(main_module, "_is_public_path", lambda path: True)

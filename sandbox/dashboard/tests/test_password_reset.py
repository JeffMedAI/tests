"""
test_password_reset.py — Comprehensive tests for the secure password reset flow.

Tests cover:
  1. Token generation: plaintext token never stored in DB (only SHA-256 hash)
  2. Token expiry: expired tokens are rejected
  3. Single-use: a used token is rejected on second attempt
  4. Password update: password is correctly updated after reset
  5. Rate limiting: >3 requests per hour per user raises ValueError
  6. Invalid token: bad token returns None (no enumeration)
  7. End-to-end HTTP flow: /forgot → /reset round-trip

All tests run against an in-memory SQLite DB; no disk state is touched.
"""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

# ---------------------------------------------------------------------------
# Minimal in-memory DB helpers
# ---------------------------------------------------------------------------

def make_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE staff_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT NOT NULL,
            email TEXT,
            role TEXT NOT NULL DEFAULT 'staff',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            username TEXT,
            password_hash TEXT,
            pin_hash TEXT,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked_until TEXT,
            last_login_at TEXT,
            must_change_password INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE auth_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            token TEXT NOT NULL UNIQUE,
            token_type TEXT NOT NULL DEFAULT 'password',
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT NOT NULL UNIQUE,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            last_active_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT
        )
        """
    )
    conn.commit()
    return conn


def insert_user(conn: sqlite3.Connection, username: str = "testuser") -> int:
    from app.auth import hash_password
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO staff_users (display_name, username, role, active, password_hash, created_at, updated_at) "
        "VALUES (?, ?, 'staff', 1, ?, ?, ?)",
        ("Test User", username, hash_password("oldpassword"), now, now),
    )
    conn.commit()
    return cur.lastrowid


# ---------------------------------------------------------------------------
# 1. Token storage — plaintext NEVER in DB
# ---------------------------------------------------------------------------

class TestTokenStorage:
    def test_token_hash_stored_not_plaintext(self):
        """The DB must contain the SHA-256 hash of the token, not the token itself."""
        from app.auth import create_reset_token
        conn = make_conn()
        uid = insert_user(conn)
        plaintext = create_reset_token(conn, uid, "password")

        row = conn.execute("SELECT token FROM auth_reset_tokens WHERE user_id=?", (uid,)).fetchone()
        stored = row["token"]

        # Stored value must NOT equal the plaintext token
        assert stored != plaintext, "Plaintext token must never be stored in the database"

        # Stored value must equal SHA-256(plaintext)
        expected_hash = hashlib.sha256(plaintext.encode("utf-8")).hexdigest()
        assert stored == expected_hash, f"Expected SHA-256 hash in DB, got: {stored}"

    def test_plaintext_token_is_url_safe_and_long_enough(self):
        """Token must be secrets.token_urlsafe(32) — at least 43 chars of base64url."""
        from app.auth import create_reset_token
        conn = make_conn()
        uid = insert_user(conn)
        token = create_reset_token(conn, uid, "password")
        # token_urlsafe(32) produces 43-char base64url string
        assert len(token) >= 43, f"Token too short: {len(token)} chars"
        # Only URL-safe base64 characters
        import re
        assert re.match(r"^[A-Za-z0-9_\-]+$", token), "Token contains non-URL-safe characters"

    def test_two_tokens_are_unique(self):
        """Each call must produce a distinct token (collision resistance)."""
        from app.auth import create_reset_token
        conn = make_conn()
        uid = insert_user(conn)
        t1 = create_reset_token(conn, uid, "password")
        t2 = create_reset_token(conn, uid, "password")
        assert t1 != t2, "Two tokens generated for same user must be distinct"


# ---------------------------------------------------------------------------
# 2. Token expiry
# ---------------------------------------------------------------------------

class TestTokenExpiry:
    def test_valid_token_within_expiry_is_accepted(self):
        from app.auth import create_reset_token, consume_reset_token
        conn = make_conn()
        uid = insert_user(conn)
        token = create_reset_token(conn, uid, "password")
        result = consume_reset_token(conn, token, "password")
        assert result == uid, "Valid, unexpired token must return the user_id"

    def test_expired_token_is_rejected(self):
        """Backdate the expiry to the past and confirm the token is rejected."""
        from app.auth import create_reset_token, consume_reset_token
        conn = make_conn()
        uid = insert_user(conn)
        create_reset_token(conn, uid, "password")
        # Force the token to be already expired
        past = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        conn.execute("UPDATE auth_reset_tokens SET expires_at=? WHERE user_id=?", (past, uid))
        conn.commit()

        # Re-fetch the plaintext token by recreating a known hash — we need the
        # plaintext. Work around by inserting a known token directly.
        known_pt = "known_plaintext_token_for_expiry_test_aabbccdd"
        known_hash = hashlib.sha256(known_pt.encode()).hexdigest()
        now = datetime.now(timezone.utc).isoformat()
        expired = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        conn.execute(
            "INSERT INTO auth_reset_tokens (user_id, token, token_type, created_at, expires_at, used) "
            "VALUES (?, ?, 'password', ?, ?, 0)",
            (uid, known_hash, now, expired),
        )
        conn.commit()
        result = consume_reset_token(conn, known_pt, "password")
        assert result is None, "Expired token must be rejected"

    def test_expiry_is_one_hour(self):
        """Token expiry must be approximately 60 minutes from creation time."""
        from app.auth import create_reset_token, RESET_TOKEN_EXPIRY_MINUTES
        conn = make_conn()
        uid = insert_user(conn)
        before = datetime.now(timezone.utc)
        create_reset_token(conn, uid, "password")
        row = conn.execute("SELECT expires_at FROM auth_reset_tokens WHERE user_id=?", (uid,)).fetchone()
        expires = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
        delta_minutes = (expires - before).total_seconds() / 60
        assert 59 <= delta_minutes <= 61, (
            f"Token expiry should be ~60 minutes, got {delta_minutes:.1f}"
        )
        assert RESET_TOKEN_EXPIRY_MINUTES == 60, "RESET_TOKEN_EXPIRY_MINUTES constant must be 60"


# ---------------------------------------------------------------------------
# 3. Single-use enforcement
# ---------------------------------------------------------------------------

class TestSingleUse:
    def _make_known_token(self, conn: sqlite3.Connection, user_id: int, used: int = 0) -> str:
        """Insert a known plaintext token (hashed) for predictable testing."""
        pt = "singleuse_test_token_aabbccddeeff0011"
        h = hashlib.sha256(pt.encode()).hexdigest()
        now = datetime.now(timezone.utc).isoformat()
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        conn.execute(
            "INSERT INTO auth_reset_tokens (user_id, token, token_type, created_at, expires_at, used) "
            "VALUES (?, ?, 'password', ?, ?, ?)",
            (user_id, h, now, future, used),
        )
        conn.commit()
        return pt

    def test_token_is_marked_used_after_consumption(self):
        from app.auth import consume_reset_token
        conn = make_conn()
        uid = insert_user(conn)
        pt = self._make_known_token(conn, uid, used=0)
        consume_reset_token(conn, pt, "password")
        row = conn.execute("SELECT used FROM auth_reset_tokens WHERE user_id=?", (uid,)).fetchone()
        assert row["used"] == 1, "Token must be marked used=1 after consumption"

    def test_used_token_rejected_on_second_attempt(self):
        from app.auth import consume_reset_token
        conn = make_conn()
        uid = insert_user(conn)
        pt = self._make_known_token(conn, uid, used=0)
        first = consume_reset_token(conn, pt, "password")
        second = consume_reset_token(conn, pt, "password")
        assert first == uid, "First use must succeed"
        assert second is None, "Second use of same token must be rejected"

    def test_pre_used_token_rejected(self):
        from app.auth import consume_reset_token
        conn = make_conn()
        uid = insert_user(conn)
        pt = self._make_known_token(conn, uid, used=1)
        result = consume_reset_token(conn, pt, "password")
        assert result is None, "Token with used=1 must be rejected immediately"


# ---------------------------------------------------------------------------
# 4. Password update correctness
# ---------------------------------------------------------------------------

class TestPasswordUpdate:
    def test_password_updated_after_reset(self):
        from app.auth import create_reset_token, consume_reset_token, set_new_password, verify_password
        conn = make_conn()
        uid = insert_user(conn)
        token = create_reset_token(conn, uid, "password")
        user_id = consume_reset_token(conn, token, "password")
        assert user_id == uid
        set_new_password(conn, uid, "NewSecurePass123!")
        row = conn.execute("SELECT password_hash FROM staff_users WHERE id=?", (uid,)).fetchone()
        assert verify_password("NewSecurePass123!", row["password_hash"]), (
            "New password must verify correctly after reset"
        )

    def test_old_password_rejected_after_reset(self):
        from app.auth import create_reset_token, consume_reset_token, set_new_password, verify_password
        conn = make_conn()
        uid = insert_user(conn)
        token = create_reset_token(conn, uid, "password")
        consume_reset_token(conn, token, "password")
        set_new_password(conn, uid, "NewSecurePass123!")
        row = conn.execute("SELECT password_hash FROM staff_users WHERE id=?", (uid,)).fetchone()
        assert not verify_password("oldpassword", row["password_hash"]), (
            "Old password must be rejected after reset"
        )

    def test_password_hash_uses_pbkdf2(self):
        """Password must be stored as PBKDF2 hash, not plaintext."""
        from app.auth import set_new_password
        conn = make_conn()
        uid = insert_user(conn)
        set_new_password(conn, uid, "SomePassword99!")
        row = conn.execute("SELECT password_hash FROM staff_users WHERE id=?", (uid,)).fetchone()
        h = row["password_hash"]
        assert h != "SomePassword99!", "Password must never be stored in plaintext"
        assert h.startswith("pbkdf2:"), f"Expected PBKDF2 hash prefix, got: {h[:20]}"

    def test_sessions_invalidated_after_reset(self):
        """All existing sessions for the user must be wiped when password is reset."""
        from app.auth import create_session, set_new_password
        conn = make_conn()
        uid = insert_user(conn)
        create_session(conn, uid, "127.0.0.1", "test-agent")
        count_before = conn.execute("SELECT COUNT(*) FROM sessions WHERE user_id=?", (uid,)).fetchone()[0]
        assert count_before == 1
        set_new_password(conn, uid, "NewPass99!")
        count_after = conn.execute("SELECT COUNT(*) FROM sessions WHERE user_id=?", (uid,)).fetchone()[0]
        assert count_after == 0, "All sessions must be invalidated after password reset"


# ---------------------------------------------------------------------------
# 5. Rate limiting
# ---------------------------------------------------------------------------

class TestRateLimiting:
    def test_three_requests_succeed(self):
        from app.auth import create_reset_token, RESET_RATE_LIMIT_PER_HOUR
        assert RESET_RATE_LIMIT_PER_HOUR == 3, "Rate limit must be 3 per hour"
        conn = make_conn()
        uid = insert_user(conn)
        for i in range(3):
            t = create_reset_token(conn, uid, "password")
            assert t is not None, f"Request {i+1} should succeed within rate limit"

    def test_fourth_request_raises(self):
        from app.auth import create_reset_token
        conn = make_conn()
        uid = insert_user(conn)
        for _ in range(3):
            create_reset_token(conn, uid, "password")
        with pytest.raises(ValueError, match="rate_limit_exceeded"):
            create_reset_token(conn, uid, "password")

    def test_rate_limit_is_per_type(self):
        """Password and PIN rate limits are tracked separately."""
        from app.auth import create_reset_token
        conn = make_conn()
        uid = insert_user(conn)
        for _ in range(3):
            create_reset_token(conn, uid, "password")
        # PIN requests should still be allowed (separate counter)
        t = create_reset_token(conn, uid, "pin")
        assert t is not None, "PIN reset should have its own independent rate limit counter"

    def test_rate_limit_expires_after_an_hour(self):
        """Requests older than 1 hour should not count toward the rate limit."""
        from app.auth import create_reset_token
        conn = make_conn()
        uid = insert_user(conn)
        # Insert 3 tokens backdated to > 1 hour ago
        old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        for i in range(3):
            h = hashlib.sha256(f"old_token_{i}".encode()).hexdigest()
            conn.execute(
                "INSERT INTO auth_reset_tokens (user_id, token, token_type, created_at, expires_at, used) "
                "VALUES (?, ?, 'password', ?, ?, 0)",
                (uid, h, old_time, future),
            )
        conn.commit()
        # A fresh request should still succeed since the old ones are outside the window
        t = create_reset_token(conn, uid, "password")
        assert t is not None, "Old (>1hr) requests must not count toward the hourly rate limit"


# ---------------------------------------------------------------------------
# 6. Invalid token — no user enumeration
# ---------------------------------------------------------------------------

class TestInvalidToken:
    def test_completely_invalid_token_returns_none(self):
        from app.auth import consume_reset_token
        conn = make_conn()
        result = consume_reset_token(conn, "this_is_not_a_valid_token", "password")
        assert result is None

    def test_wrong_type_returns_none(self):
        """A valid token for 'password' type must not work for 'pin' type."""
        from app.auth import create_reset_token, consume_reset_token
        conn = make_conn()
        uid = insert_user(conn)
        token = create_reset_token(conn, uid, "password")
        result = consume_reset_token(conn, token, "pin")
        assert result is None, "Token for 'password' type must be rejected when consumed as 'pin'"

    def test_token_from_different_user_returns_correct_user(self):
        """Each token is bound to its user; consuming must return the correct user_id."""
        from app.auth import create_reset_token, consume_reset_token
        conn = make_conn()
        uid_a = insert_user(conn, "usera")
        uid_b = insert_user(conn, "userb")
        token_b = create_reset_token(conn, uid_b, "password")
        result = consume_reset_token(conn, token_b, "password")
        assert result == uid_b, "Token must be bound to the specific user who requested it"
        assert result != uid_a


# ---------------------------------------------------------------------------
# 7. HTTP end-to-end flow  (/forgot → /reset)
# ---------------------------------------------------------------------------

@pytest.fixture
def test_app():
    """Create a TestClient for the FastAPI app with a temporary in-memory DB."""
    import tempfile, os
    from fastapi.testclient import TestClient
    from app.db import init_db, connect
    from app.auth import hash_password

    # Point the app at a temp file DB so tests are isolated
    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = f.name

    import app.db as db_module
    from pathlib import Path
    original_path = db_module.DB_PATH
    db_module.DB_PATH = Path(db_path)

    # Initialise and seed a test user
    with connect(Path(db_path)) as conn:
        init_db(conn)
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO staff_users (display_name, username, role, active, password_hash, created_at, updated_at) "
            "VALUES ('HTTP Test User', 'httpuser', 'staff', 1, ?, ?, ?)",
            (hash_password("oldpass123"), now, now),
        )
        conn.commit()

    from app.main import app as fastapi_app
    client = TestClient(fastapi_app, raise_server_exceptions=True)

    yield client, db_path

    db_module.DB_PATH = original_path
    os.unlink(db_path)


class TestHTTPFlow:
    def test_forgot_page_loads(self, test_app):
        client, _ = test_app
        resp = client.get("/forgot")
        assert resp.status_code == 200
        assert "Reset credentials" in resp.text

    def test_forgot_post_unknown_user_shows_generic_success(self, test_app):
        """Non-existent username must show the same success text as a real one."""
        client, _ = test_app
        resp = client.post("/forgot", data={"username": "doesnotexist", "reset_type": "password"})
        assert resp.status_code == 200
        # Must show generic success — not "Username not found"
        assert "Username not found" not in resp.text
        assert "registered" in resp.text.lower() or "reset link" in resp.text.lower()
        # No reset link rendered for unknown user
        assert "/reset?token=" not in resp.text

    def test_forgot_post_known_user_returns_link(self, test_app):
        client, _ = test_app
        resp = client.post("/forgot", data={"username": "httpuser", "reset_type": "password"})
        assert resp.status_code == 200
        assert "/reset?token=" in resp.text, "Reset link must appear for a valid user"

    def test_reset_page_with_valid_token(self, test_app):
        client, db_path = test_app
        # Generate a token via the API
        resp = client.post("/forgot", data={"username": "httpuser", "reset_type": "password"})
        # Extract the token from the link in the response
        import re
        match = re.search(r'token=([A-Za-z0-9_\-]{10,})', resp.text)
        assert match, "Could not extract token from /forgot response"
        token = match.group(1)

        reset_resp = client.get(f"/reset?token={token}&type=password")
        assert reset_resp.status_code == 200
        assert "Set new password" in reset_resp.text

    def test_reset_post_updates_password(self, test_app):
        client, db_path = test_app
        import re
        resp = client.post("/forgot", data={"username": "httpuser", "reset_type": "password"})
        match = re.search(r'token=([A-Za-z0-9_\-]{10,})', resp.text)
        assert match
        token = match.group(1)

        reset_resp = client.post("/reset", data={
            "token": token,
            "reset_type": "password",
            "new_value": "NewPass999!",
            "confirm_value": "NewPass999!",
        })
        assert reset_resp.status_code == 200
        assert "updated" in reset_resp.text.lower() or "sign in" in reset_resp.text.lower()

    def test_reset_post_with_used_token_rejected(self, test_app):
        client, _ = test_app
        import re
        resp = client.post("/forgot", data={"username": "httpuser", "reset_type": "password"})
        match = re.search(r'token=([A-Za-z0-9_\-]{10,})', resp.text)
        assert match
        token = match.group(1)
        # Use the token once
        client.post("/reset", data={
            "token": token, "reset_type": "password",
            "new_value": "NewPass999!", "confirm_value": "NewPass999!",
        })
        # Second attempt must be rejected
        second = client.post("/reset", data={
            "token": token, "reset_type": "password",
            "new_value": "AnotherPass!", "confirm_value": "AnotherPass!",
        })
        assert second.status_code == 200
        assert "invalid or has expired" in second.text.lower(), (
            "Used token must produce an error on second attempt"
        )

    def test_mismatched_passwords_rejected(self, test_app):
        client, _ = test_app
        import re
        resp = client.post("/forgot", data={"username": "httpuser", "reset_type": "password"})
        match = re.search(r'token=([A-Za-z0-9_\-]{10,})', resp.text)
        assert match
        token = match.group(1)
        reset_resp = client.post("/reset", data={
            "token": token, "reset_type": "password",
            "new_value": "NewPass999!", "confirm_value": "WrongConfirm!",
        })
        assert reset_resp.status_code == 200
        assert "do not match" in reset_resp.text.lower()

    def test_short_password_rejected(self, test_app):
        client, _ = test_app
        import re
        resp = client.post("/forgot", data={"username": "httpuser", "reset_type": "password"})
        match = re.search(r'token=([A-Za-z0-9_\-]{10,})', resp.text)
        assert match
        token = match.group(1)
        reset_resp = client.post("/reset", data={
            "token": token, "reset_type": "password",
            "new_value": "short", "confirm_value": "short",
        })
        assert reset_resp.status_code == 200
        assert "8 character" in reset_resp.text.lower() or "at least" in reset_resp.text.lower()

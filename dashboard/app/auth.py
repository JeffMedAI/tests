"""
JeffLocal dashboard authentication module.
Handles password/PIN verification, session tokens, and lockout policy.
All hashing uses PBKDF2-HMAC-SHA256 (stdlib only — no bcrypt dependency).

Hash format: pbkdf2:sha256:<iterations>:<salt_hex>:<dk_hex>  (5 parts, per-user random salt)
"""
import hashlib
import secrets
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional

SESSION_TIMEOUT_MINUTES = 60
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
TOKEN_BYTES = 32
PBKDF2_ITERATIONS = 100_000
RESET_TOKEN_EXPIRY_MINUTES = 60        # 1-hour window per task spec
RESET_RATE_LIMIT_PER_HOUR = 3          # max reset requests per user per hour


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_expires(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


# ── Hashing helpers ────────────────────────────────────────────────────────────

def _pbkdf2_hash_with_salt(value: str, salt: bytes) -> str:
    """Return a 5-part hash string with the salt embedded:
    pbkdf2:sha256:<iterations>:<salt_hex>:<dk_hex>
    """
    dk = hashlib.pbkdf2_hmac("sha256", value.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2:sha256:{PBKDF2_ITERATIONS}:{salt.hex()}:{dk.hex()}"


def _verify_new_format(value: str, stored: str) -> bool:
    """Verify a 5-part hash that embeds its own random salt."""
    try:
        parts = stored.split(":", 4)
        if len(parts) != 5 or parts[0] != "pbkdf2":
            return False
        iterations = int(parts[2])
        salt = bytes.fromhex(parts[3])
        dk = hashlib.pbkdf2_hmac("sha256", value.encode(), salt, iterations)
        expected = f"pbkdf2:{parts[1]}:{iterations}:{parts[3]}:{dk.hex()}"
        return secrets.compare_digest(expected, stored)
    except Exception:
        return False


def hash_password(password: str) -> str:
    """Generate a new password hash with a per-user random 16-byte salt."""
    salt = secrets.token_bytes(16)
    return _pbkdf2_hash_with_salt(password, salt)


def hash_pin(pin: str) -> str:
    """Generate a new PIN hash with a per-user random 16-byte salt."""
    salt = secrets.token_bytes(16)
    return _pbkdf2_hash_with_salt(pin, salt)


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify a password against a stored 5-part hash (pbkdf2:sha256:<iter>:<salt_hex>:<dk_hex>).

    Returns True only on a confirmed match. Raises ValueError if the hash format
    is not recognised (i.e. not a 5-part pbkdf2 string).
    """
    parts = stored_hash.split(":", 4)
    if len(parts) != 5 or parts[0] != "pbkdf2":
        raise ValueError(f"Unrecognised password hash format: expected 5-part pbkdf2 string")
    return _verify_new_format(password, stored_hash)


def verify_pin(pin: str, stored_hash: str) -> bool:
    """Verify a PIN against a stored 5-part hash (pbkdf2:sha256:<iter>:<salt_hex>:<dk_hex>).

    Returns True only on a confirmed match. Raises ValueError if the hash format
    is not recognised.
    """
    parts = stored_hash.split(":", 4)
    if len(parts) != 5 or parts[0] != "pbkdf2":
        raise ValueError(f"Unrecognised PIN hash format: expected 5-part pbkdf2 string")
    return _verify_new_format(pin, stored_hash)


def generate_token() -> str:
    return secrets.token_urlsafe(TOKEN_BYTES)


def _hash_reset_token(token: str) -> str:
    """SHA-256 hash of a plaintext reset token — this is what is stored in the DB.
    The plaintext token travels only in the reset URL; it is never persisted.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _hash_session_token(token: str) -> str:
    """SHA-256 hash of a plaintext session token — this is what is stored in sessions.token.
    The plaintext token travels only in the cookie; it is never persisted.
    Identical pre-image barrier to the reset-token pattern.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ── Session management ─────────────────────────────────────────────────────────

def create_session(conn: sqlite3.Connection, user_id: int, ip: str = "", ua: str = "") -> str:
    """Create a new session. Stores the SHA-256 hash of the token in the DB;
    returns the plaintext token to the caller for placement in the session cookie only.

    Migration note: existing rows that hold plaintext tokens will no longer match
    the hashed lookups in get_session_user / invalidate_session after this change
    is deployed. All active sessions will be invalidated on first deploy — users
    will need to log in again. This is the expected and acceptable behaviour.
    """
    token = generate_token()                        # plaintext — returned to caller for cookie
    token_hash = _hash_session_token(token)         # hash — stored in DB
    now = _utc_now()
    expires = _utc_expires(SESSION_TIMEOUT_MINUTES)
    conn.execute(
        "INSERT INTO sessions (token, user_id, created_at, last_active_at, expires_at, ip_address, user_agent) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (token_hash, user_id, now, now, expires, ip, ua),
    )
    conn.execute("UPDATE staff_users SET last_login_at=? WHERE id=?", (now, user_id))
    conn.commit()
    return token  # plaintext — NEVER stored, only returned here for the cookie


def get_session_user(conn: sqlite3.Connection, token: str) -> Optional[dict]:
    """Return the user dict if the session is valid and not expired; also slides the expiry.

    The incoming plaintext token (from the cookie) is hashed before the DB lookup —
    the database only ever holds the SHA-256 hash, not the plaintext.
    """
    if not token:
        return None
    token_hash = _hash_session_token(token)         # hash the incoming cookie value before lookup
    now_dt = datetime.now(timezone.utc)
    row = conn.execute(
        "SELECT s.id as sid, s.user_id, s.expires_at, "
        "u.id, u.display_name, u.username, u.role, u.active, u.must_change_password "
        "FROM sessions s JOIN staff_users u ON s.user_id=u.id "
        "WHERE s.token=?",
        (token_hash,),
    ).fetchone()
    if row is None:
        return None
    expires_at = row["expires_at"] if isinstance(row, dict) else row[2]
    try:
        exp_dt = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
        if now_dt > exp_dt:
            return None
    except Exception:
        return None
    # Slide expiry on activity
    new_expires = _utc_expires(SESSION_TIMEOUT_MINUTES)
    now_str = _utc_now()
    conn.execute(
        "UPDATE sessions SET last_active_at=?, expires_at=? WHERE token=?",
        (now_str, new_expires, token_hash),
    )
    conn.commit()
    if isinstance(row, sqlite3.Row):
        d = dict(row)
    else:
        d = {
            "user_id": row[1], "expires_at": row[2],
            "id": row[3], "display_name": row[4], "username": row[5],
            "role": row[6], "active": row[7], "must_change_password": row[8],
        }
    d["active"] = bool(d.get("active", 1))
    if not d["active"]:
        return None
    return d


def invalidate_session(conn: sqlite3.Connection, token: str) -> None:
    """Delete a session by its plaintext token. Hashes before the DB lookup."""
    token_hash = _hash_session_token(token)
    conn.execute("DELETE FROM sessions WHERE token=?", (token_hash,))
    conn.commit()


def invalidate_all_user_sessions(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    conn.commit()


def purge_expired_sessions(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM sessions WHERE expires_at < ?", (_utc_now(),))
    conn.commit()


# ── Login flow ─────────────────────────────────────────────────────────────────

def lookup_user_by_username(conn: sqlite3.Connection, username: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT id, display_name, username, role, active, password_hash, pin_hash, "
        "failed_attempts, locked_until, must_change_password "
        "FROM staff_users WHERE username=?",
        (username.strip().lower(),),
    ).fetchone()
    if row is None:
        return None
    return dict(row) if isinstance(row, sqlite3.Row) else {
        "id": row[0], "display_name": row[1], "username": row[2], "role": row[3],
        "active": row[4], "password_hash": row[5], "pin_hash": row[6],
        "failed_attempts": row[7], "locked_until": row[8], "must_change_password": row[9],
    }


def is_account_locked(user: dict) -> bool:
    locked_until = user.get("locked_until")
    if not locked_until:
        return False
    try:
        lock_dt = datetime.fromisoformat(str(locked_until).replace("Z", "+00:00"))
        return datetime.now(timezone.utc) < lock_dt
    except Exception:
        return False


def record_failed_attempt(conn: sqlite3.Connection, user_id: int) -> int:
    conn.execute(
        "UPDATE staff_users SET failed_attempts = failed_attempts + 1 WHERE id=?",
        (user_id,),
    )
    row = conn.execute("SELECT failed_attempts FROM staff_users WHERE id=?", (user_id,)).fetchone()
    attempts = row[0] if row else 0
    if attempts >= MAX_FAILED_ATTEMPTS:
        locked_until = _utc_expires(LOCKOUT_MINUTES)
        conn.execute(
            "UPDATE staff_users SET locked_until=? WHERE id=?", (locked_until, user_id)
        )
    conn.commit()
    return attempts


def clear_failed_attempts(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute(
        "UPDATE staff_users SET failed_attempts=0, locked_until=NULL WHERE id=?", (user_id,)
    )
    conn.commit()


# ── Password / PIN reset ───────────────────────────────────────────────────────

def create_reset_token(conn: sqlite3.Connection, user_id: int, token_type: str = "password") -> str:
    """Generate a cryptographically random reset token.

    Security model:
    - The plaintext token (returned) is placed in the reset URL only.
    - Only the SHA-256 hash of the token is stored in the database.
    - If the database is ever read by an attacker, the plaintext tokens
      cannot be recovered and therefore cannot be used.

    Raises ValueError("rate_limit_exceeded") if the user has already made
    RESET_RATE_LIMIT_PER_HOUR requests in the last hour.
    """
    one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    recent_count = conn.execute(
        "SELECT COUNT(*) FROM auth_reset_tokens "
        "WHERE user_id=? AND token_type=? AND created_at >= ?",
        (user_id, token_type, one_hour_ago),
    ).fetchone()[0]
    if recent_count >= RESET_RATE_LIMIT_PER_HOUR:
        raise ValueError("rate_limit_exceeded")

    token = generate_token()                   # plaintext — returned to caller
    token_hash = _hash_reset_token(token)      # hash — stored in DB
    now = _utc_now()
    expires = _utc_expires(RESET_TOKEN_EXPIRY_MINUTES)
    conn.execute(
        "INSERT INTO auth_reset_tokens (user_id, token, token_type, created_at, expires_at, used) "
        "VALUES (?, ?, ?, ?, ?, 0)",
        (user_id, token_hash, token_type, now, expires),
    )
    conn.commit()
    return token   # plaintext — NEVER stored, only returned here


def consume_reset_token(conn: sqlite3.Connection, token: str, token_type: str) -> Optional[int]:
    """Return user_id if token is valid, unused, and not expired. Marks it used.

    Security: the incoming plaintext token is hashed before the DB lookup so
    that (a) the DB never contains plaintext tokens and (b) the comparison is
    performed by the database engine on the hash, which is a fixed-length
    deterministic value — there is no timing side-channel on the hash itself.
    The secrets.compare_digest call in _verify_new_format guards password/PIN paths;
    for reset tokens the SHA-256 pre-image is the security barrier.
    """
    token_hash = _hash_reset_token(token)
    row = conn.execute(
        "SELECT id, user_id, expires_at, used FROM auth_reset_tokens "
        "WHERE token=? AND token_type=?",
        (token_hash, token_type),
    ).fetchone()
    if row is None:
        return None
    rid, user_id, expires_at, used = row[0], row[1], row[2], row[3]
    if used:
        return None
    try:
        exp_dt = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > exp_dt:
            return None
    except Exception:
        return None
    # Mark single-use: token cannot be replayed after this point
    conn.execute("UPDATE auth_reset_tokens SET used=1 WHERE id=?", (rid,))
    conn.commit()
    return user_id


def set_new_password(conn: sqlite3.Connection, user_id: int, new_password: str) -> None:
    conn.execute(
        "UPDATE staff_users SET password_hash=?, must_change_password=0, "
        "failed_attempts=0, locked_until=NULL WHERE id=?",
        (hash_password(new_password), user_id),
    )
    conn.commit()
    invalidate_all_user_sessions(conn, user_id)


def set_new_pin(conn: sqlite3.Connection, user_id: int, new_pin: str) -> None:
    conn.execute(
        "UPDATE staff_users SET pin_hash=?, must_change_password=0, "
        "failed_attempts=0, locked_until=NULL WHERE id=?",
        (hash_pin(new_pin), user_id),
    )
    conn.commit()
    invalidate_all_user_sessions(conn, user_id)

"""
whatsapp_state.py — JeffLocal WhatsApp Conversation State Manager

Tracks each patient's WhatsApp conversation stage in SQLite.
Phone numbers are never stored in plain text — always SHA-256 hashed.

Tables managed here:
  whatsapp_sessions   — active/complete conversation sessions
  whatsapp_consents   — patient opt-in consent records (3-year retention)
"""

import hashlib
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Conversation stages
STAGE_OPT_IN       = 0   # Waiting for consent YES
STAGE_GREETING     = 1   # Waiting for name + DOB
STAGE_REASON       = 2   # Waiting for reason/symptom
STAGE_CLARIFY      = 3   # Waiting for duration/detail
STAGE_EXTRAS       = 4   # Asking for anything else
STAGE_COMPLETE     = 5   # Intake done, handoff written
STAGE_ESCALATED    = 6   # Emergency — escalated to staff

SESSION_STATUS_ACTIVE     = "active"
SESSION_STATUS_COMPLETE   = "complete"
SESSION_STATUS_ABANDONED  = "abandoned"
SESSION_STATUS_ESCALATED  = "escalated"
SESSION_STATUS_STOPPED    = "stopped"

CONSENT_EXPIRY_DAYS = 365  # Re-confirm consent after 12 months


def _hash_phone(phone: str) -> str:
    """SHA-256 hash of phone number — never store plain text."""
    return hashlib.sha256(phone.strip().encode("utf-8")).hexdigest()


def init_whatsapp_tables(conn: sqlite3.Connection):
    """Create WhatsApp tables if they don't exist. Call on app startup."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS whatsapp_sessions (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_hash        TEXT NOT NULL,
            wa_message_id     TEXT,
            stage             INTEGER DEFAULT 0,
            collected_data    TEXT DEFAULT '{}',
            opted_in          INTEGER DEFAULT 0,
            opt_in_timestamp  TEXT,
            created_at        TEXT DEFAULT (datetime('now')),
            last_activity     TEXT DEFAULT (datetime('now')),
            status            TEXT DEFAULT 'active'
        );

        CREATE INDEX IF NOT EXISTS idx_wa_sessions_phone_hash
            ON whatsapp_sessions (phone_hash, status);

        CREATE TABLE IF NOT EXISTS whatsapp_consents (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_hash      TEXT NOT NULL UNIQUE,
            consent_given   INTEGER DEFAULT 0,
            consent_version TEXT DEFAULT 'v1',
            consented_at    TEXT,
            revoked_at      TEXT,
            revoked         INTEGER DEFAULT 0,
            created_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_wa_consents_phone_hash
            ON whatsapp_consents (phone_hash);
    """)
    conn.commit()
    logger.info("WhatsApp tables initialised.")


# ─── Consent ────────────────────────────────────────────────────────────────

def has_valid_consent(conn: sqlite3.Connection, phone: str) -> bool:
    """Return True if patient has given consent within the last CONSENT_EXPIRY_DAYS."""
    phone_hash = _hash_phone(phone)
    expiry_date = (datetime.utcnow() - timedelta(days=CONSENT_EXPIRY_DAYS)).isoformat()
    row = conn.execute(
        """SELECT consent_given, revoked, consented_at
           FROM whatsapp_consents
           WHERE phone_hash = ? AND revoked = 0 AND consent_given = 1
             AND consented_at > ?""",
        (phone_hash, expiry_date)
    ).fetchone()
    return row is not None


def record_consent(conn: sqlite3.Connection, phone: str, version: str = "v1"):
    """Record patient opt-in consent."""
    phone_hash = _hash_phone(phone)
    now = datetime.utcnow().isoformat()
    conn.execute(
        """INSERT INTO whatsapp_consents (phone_hash, consent_given, consent_version, consented_at)
           VALUES (?, 1, ?, ?)
           ON CONFLICT(phone_hash) DO UPDATE SET
               consent_given = 1,
               consent_version = excluded.consent_version,
               consented_at = excluded.consented_at,
               revoked = 0,
               revoked_at = NULL""",
        (phone_hash, version, now)
    )
    conn.commit()
    logger.info(f"Consent recorded for phone_hash={phone_hash[:8]}...")


def revoke_consent(conn: sqlite3.Connection, phone: str):
    """Revoke consent when patient sends STOP."""
    phone_hash = _hash_phone(phone)
    now = datetime.utcnow().isoformat()
    conn.execute(
        """UPDATE whatsapp_consents
           SET revoked = 1, revoked_at = ?
           WHERE phone_hash = ?""",
        (now, phone_hash)
    )
    conn.commit()
    logger.info(f"Consent revoked for phone_hash={phone_hash[:8]}...")


# ─── Sessions ────────────────────────────────────────────────────────────────

def get_active_session(conn: sqlite3.Connection, phone: str) -> Optional[dict]:
    """Get the active session for a phone number, or None."""
    phone_hash = _hash_phone(phone)
    row = conn.execute(
        """SELECT id, stage, collected_data, opted_in, opt_in_timestamp,
                  created_at, last_activity, status, wa_message_id
           FROM whatsapp_sessions
           WHERE phone_hash = ? AND status = ?
           ORDER BY created_at DESC LIMIT 1""",
        (phone_hash, SESSION_STATUS_ACTIVE)
    ).fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "stage": row[1],
        "collected_data": json.loads(row[2] or "{}"),
        "opted_in": bool(row[3]),
        "opt_in_timestamp": row[4],
        "created_at": row[5],
        "last_activity": row[6],
        "status": row[7],
        "wa_message_id": row[8],
    }


def create_session(conn: sqlite3.Connection, phone: str, wa_message_id: str = None) -> dict:
    """Create a new active session for a phone number."""
    phone_hash = _hash_phone(phone)
    now = datetime.utcnow().isoformat()
    cursor = conn.execute(
        """INSERT INTO whatsapp_sessions
               (phone_hash, wa_message_id, stage, collected_data, opted_in,
                created_at, last_activity, status)
           VALUES (?, ?, 0, '{}', 0, ?, ?, 'active')""",
        (phone_hash, wa_message_id, now, now)
    )
    conn.commit()
    session_id = cursor.lastrowid
    logger.info(f"Session created: id={session_id} phone_hash={phone_hash[:8]}...")
    return {"id": session_id, "stage": 0, "collected_data": {}, "opted_in": False, "status": SESSION_STATUS_ACTIVE}


def update_session(conn: sqlite3.Connection, session_id: int,
                   stage: int = None, collected_data: dict = None,
                   opted_in: bool = None, status: str = None,
                   wa_message_id: str = None):
    """Update fields on an existing session."""
    now = datetime.utcnow().isoformat()
    updates = ["last_activity = ?"]
    params = [now]

    if stage is not None:
        updates.append("stage = ?")
        params.append(stage)
    if collected_data is not None:
        updates.append("collected_data = ?")
        params.append(json.dumps(collected_data))
    if opted_in is not None:
        updates.append("opted_in = ?")
        params.append(1 if opted_in else 0)
        if opted_in:
            updates.append("opt_in_timestamp = ?")
            params.append(now)
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if wa_message_id is not None:
        updates.append("wa_message_id = ?")
        params.append(wa_message_id)

    params.append(session_id)
    conn.execute(
        f"UPDATE whatsapp_sessions SET {', '.join(updates)} WHERE id = ?",
        params
    )
    conn.commit()


def close_session(conn: sqlite3.Connection, session_id: int, status: str = SESSION_STATUS_COMPLETE):
    """Mark a session as complete/abandoned/escalated."""
    update_session(conn, session_id, status=status)
    logger.info(f"Session {session_id} closed with status={status}")


def abandon_stale_sessions(conn: sqlite3.Connection, timeout_minutes: int = 30):
    """Mark sessions with no activity in timeout_minutes as abandoned."""
    cutoff = (datetime.utcnow() - timedelta(minutes=timeout_minutes)).isoformat()
    conn.execute(
        """UPDATE whatsapp_sessions
           SET status = 'abandoned'
           WHERE status = 'active' AND last_activity < ?""",
        (cutoff,)
    )
    conn.commit()

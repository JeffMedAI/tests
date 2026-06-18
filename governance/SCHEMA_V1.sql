-- SCHEMA V1 — JeffLocal (Avamed) Dashboard SQLite Database
-- Generated: 2026-06-18
-- Source: dashboard/app/db.py init_db()
-- This file is documentation. The authoritative schema is in db.py.
-- PRAGMA settings applied at connection time (see db.connect()):
--   journal_mode=WAL, synchronous=NORMAL, cache_size=-8000, temp_store=MEMORY

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: cases
-- Primary record for each patient call processed through the pipeline.
-- Fields labelled LOCKED are set by deterministic code only — never LLM output.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS cases (
    call_id                 TEXT    PRIMARY KEY,  -- Unique call identifier (e.g. JEFF-20260618-120000-001)
    open_details            TEXT,                 -- JSON blob of full pipeline output (read-only reference)
    timestamp               TEXT,                 -- ISO8601 timestamp of the call
    call_timestamp_sort     REAL,                 -- Unix epoch for sorting (derived from timestamp)
    request_type            TEXT,                 -- Pathway type: prescription|referral|sick_note|test_result|admin|unknown|needs_review
    patient_name            TEXT,                 -- Caller-supplied name (GDPR: purge after 90 days)
    dob                     TEXT,                 -- Date of birth YYYY-MM-DD (LOCKED — deterministic only; GDPR)
    postcode                TEXT,                 -- Patient postcode (GDPR)
    gender                  TEXT,
    age                     INTEGER,
    callback_number         TEXT,                 -- Caller-supplied callback number (GDPR)
    -- Patient matching (all LOCKED — deterministic patient_matcher.py only)
    verification_status     TEXT,                 -- LOCKED: matched|possible_match|no_match|insufficient_id
    verification_reason     TEXT,                 -- LOCKED: explanation of matching decision
    matched_patient_ref     TEXT,                 -- LOCKED: EMIS patient reference
    emis_number             TEXT,                 -- LOCKED: EMIS patient number (GDPR)
    nhs_number              TEXT,                 -- LOCKED: NHS number (GDPR)
    top_candidate_name      TEXT,                 -- LOCKED: best-match name from EMIS reference data
    -- Safety fields (all LOCKED — deterministic safety rules only)
    priority                TEXT,                 -- LOCKED: 999 Emergency|urgent_same_day|routine|review_required
    safe_to_queue           INTEGER,              -- LOCKED: 0=false, 1=true
    -- LLM-produced display fields (Ollama/Gemma — display only, never used for decisions)
    task_title              TEXT,
    task_body               TEXT,
    staff_task_title        TEXT,
    staff_task_body         TEXT,
    transcript              TEXT,                 -- Full voice transcript (GDPR: purge after 90 days)
    call_summary            TEXT,
    ai_summary              TEXT,
    patient_record_note     TEXT,
    -- Call metadata
    call_duration_seconds   INTEGER,
    caller_sentiment        TEXT,
    caller_difficulty       TEXT,
    transcript_quality      TEXT,
    handoff_confidence      TEXT,
    extraction_confidence   TEXT,
    -- Safety flags (LOCKED — deterministic only)
    staff_review_required   INTEGER,              -- LOCKED: 0|1
    red_flags_present       INTEGER,              -- LOCKED: 0|1
    -- Staff workflow fields (set by reception staff on dashboard)
    status                  TEXT,                 -- New|Needs Review|Resolved
    assigned_to             TEXT,
    action_needed           TEXT,
    outcome_notes           TEXT,
    staff_action            TEXT,
    resolved_at             TEXT,
    resolved_by             TEXT,
    last_updated            TEXT,
    last_edited_at          TEXT,
    last_edited_by          TEXT,
    turnaround_minutes      INTEGER,
    -- Import metadata
    source_path             TEXT,
    source_file_mtime       TEXT,
    imported_at             TEXT
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: audit_events
-- Immutable log of all staff actions on cases. Never deleted (GDPR compliance).
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       TEXT    NOT NULL,
    call_id         TEXT    NOT NULL,
    action          TEXT    NOT NULL,   -- e.g. "update", "quick_action:start_review"
    edited_by       TEXT,
    changed_fields  TEXT    NOT NULL,   -- JSON array of field names changed
    old_values      TEXT    NOT NULL,   -- JSON object of before-values
    new_values      TEXT    NOT NULL    -- JSON object of after-values
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: alert_events
-- System alerts raised by the pipeline (e.g. red flag, unacknowledged emergency)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS alert_events (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id                TEXT    NOT NULL UNIQUE,
    timestamp               TEXT    NOT NULL,
    alert_type              TEXT    NOT NULL,
    severity                TEXT,
    count                   INTEGER,
    message                 TEXT,
    first_call_id           TEXT,
    first_patient           TEXT,
    first_priority          TEXT,
    source_workflow         TEXT,
    dedupe_key              TEXT    NOT NULL,
    acknowledged_at         TEXT,
    acknowledged_by         TEXT,
    acknowledgement_source  TEXT
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: staff_users
-- Reception staff and admin accounts. Roles: admin|staff|readonly.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS staff_users (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    display_name            TEXT    NOT NULL,
    email                   TEXT,
    role                    TEXT    NOT NULL CHECK(role IN ('admin', 'staff', 'readonly')),
    demo_pin_hash           TEXT,
    active                  INTEGER NOT NULL DEFAULT 1,
    created_at              TEXT    NOT NULL,
    updated_at              TEXT    NOT NULL,
    username                TEXT,
    password_hash           TEXT,
    pin_hash                TEXT,
    failed_attempts         INTEGER NOT NULL DEFAULT 0,
    locked_until            TEXT,
    last_login_at           TEXT,
    must_change_password    INTEGER NOT NULL DEFAULT 0
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: sessions
-- Active login sessions. Expires after inactivity.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS sessions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    token           TEXT    NOT NULL UNIQUE,
    user_id         INTEGER NOT NULL,
    created_at      TEXT    NOT NULL,
    last_active_at  TEXT    NOT NULL,
    expires_at      TEXT    NOT NULL,
    ip_address      TEXT,
    user_agent      TEXT,
    FOREIGN KEY (user_id) REFERENCES staff_users(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: auth_reset_tokens
-- Password or PIN reset tokens (single use, short TTL).
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS auth_reset_tokens (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    token       TEXT    NOT NULL UNIQUE,
    token_type  TEXT    NOT NULL DEFAULT 'password',
    created_at  TEXT    NOT NULL,
    expires_at  TEXT    NOT NULL,
    used        INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES staff_users(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: staff_invitations
-- Pending email invitations for new staff accounts.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS staff_invitations (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    email               TEXT    NOT NULL,
    role                TEXT    NOT NULL CHECK(role IN ('admin', 'staff', 'readonly')),
    invited_by_staff_id INTEGER,
    token_hash          TEXT,
    status              TEXT    NOT NULL CHECK(status IN ('pending', 'accepted', 'cancelled', 'expired')),
    created_at          TEXT    NOT NULL,
    expires_at          TEXT,
    accepted_at         TEXT,
    cancelled_at        TEXT
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TABLE: call_recordings
-- Metadata for voice recordings from Hostcomm UK.
-- Phase 1: recording_status = unavailable (recordings not yet wired in).
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS call_recordings (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id                     TEXT    NOT NULL,
    recording_url               TEXT,
    recording_local_path        TEXT,
    recording_received_at       TEXT    NOT NULL,
    recording_duration_seconds  INTEGER,
    recording_status            TEXT    NOT NULL CHECK(recording_status IN ('pending','available','unavailable','failed')),
    recording_metadata_json     TEXT,
    attached_by                 TEXT,
    source                      TEXT,
    created_at                  TEXT    NOT NULL,
    updated_at                  TEXT    NOT NULL
);

-- ─────────────────────────────────────────────────────────────────────────────
-- GDPR PURGE POLICY
-- Fields containing patient PII in the cases table are purged after 90 days.
-- audit_events rows are retained indefinitely (no PII in the audit log).
-- Purge is executed by the scheduled GDPR purge task.
-- ─────────────────────────────────────────────────────────────────────────────
-- Fields purged (set to NULL after 90 days):
--   patient_name, dob, postcode, callback_number, nhs_number, emis_number,
--   transcript, call_summary, ai_summary, patient_record_note, open_details

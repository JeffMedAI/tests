-- Migration: add_created_at_20260531.sql
-- Purpose:   Add created_at column to cases table for GDPR 90-day purge
-- Author:    Database Agent
-- Date:      2026-05-31
-- Reviewed:  Security Agent (see docs/compliance/security_review_gdpr_purge_2026-05-30.md)
--
-- SQLite does not support DROP COLUMN before version 3.35.
-- DOWN path: recreate table without column (documented below, not executable here).
--
-- SAFE for existing rows: DEFAULT copies value from existing timestamp column.
-- Run against SANDBOX only until Security Agent + Saeed approved for production.

-- ============================================================
-- UP
-- ============================================================

-- Add created_at to cases, back-filling from the existing timestamp column.
-- Existing rows get timestamp value; new rows get CURRENT_TIMESTAMP via app.
ALTER TABLE cases ADD COLUMN created_at TEXT;

UPDATE cases
SET created_at = timestamp
WHERE created_at IS NULL;

-- Index to make 90-day purge queries fast
CREATE INDEX IF NOT EXISTS idx_cases_created_at ON cases(created_at);

-- Index on assigned_to. Present on tenant1 and the main DB but absent from this
-- file, so a tenant rebuilt from it came out with a different schema. Added
-- 2026-09-04 after the Security Agent spotted the drift during the tenant2 fix.
CREATE INDEX IF NOT EXISTS idx_cases_assigned_to ON cases(assigned_to);

-- Also index alert_events.timestamp for purge scans
CREATE INDEX IF NOT EXISTS idx_alert_events_timestamp ON alert_events(timestamp);

-- ============================================================
-- DOWN (manual steps — SQLite cannot DROP COLUMN < 3.35)
-- ============================================================
-- 1. CREATE TABLE cases_backup AS SELECT <all cols except created_at> FROM cases;
-- 2. DROP TABLE cases;
-- 3. ALTER TABLE cases_backup RENAME TO cases;
-- 4. Recreate original indexes.
-- Note: Run only if rollback is required. Requires Saeed approval.

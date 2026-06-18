# RELEASE GATE CRITERIA — JeffLocal (Avamed)
**Version:** 1.0  
**Date:** 2026-06-18  
**Owner:** Lead Agent + Saeed  
**Purpose:** Defines what must be true before any code is merged to the main branch or deployed to production.

---

## Gate 1 — Tests Pass

All of the following must be true:

1. `pytest` (run from `C:\JeffLocal\dashboard\`) exits with 0 failures.
2. `test_render_pages.py` — all 46 tests pass. This covers dashboard page rendering, filter logic, staff actions, locked fields, and copy-safe payloads.
3. `test_api_endpoints.py` — all endpoint tests pass (auth, CRUD, locked fields, audit logging).
4. `test_importer.py` — importer tests pass (upsert, dedup, field mapping).
5. No new test is added that is marked `skip` or `xfail` without a documented reason.

**Shortcut not allowed:** Tests must run against the real application code with real SQLite (not mocks). Monkeypatching is allowed only for the session-auth bypass (`conftest.py`) and DB path redirect (`tmp_path`).

---

## Gate 2 — Safety Invariant Holds

The **CORE SAFETY INVARIANT** must be asserted on every release:

- `verification_status` — set by deterministic patient matching only.
- `safe_to_queue` — set by deterministic safety rules only.
- `priority` — set by deterministic safety rules only.
- `matched_patient_name`, `emis_number`, `nhs_number`, `dob` — set by deterministic code only.
- The LLM (Ollama/Gemma) may contribute to `task_title`, `task_body`, `ai_summary`, `patient_record_note`, `call_summary` — these are display fields, not decision fields.

**How to verify:** Run `tests/send_gp_demo_n8n_webhook_calls.py` with a red-flag case and a third-party caller case. Assert that `priority` and `verification_status` match the expected deterministic output, not the LLM's wording.

---

## Gate 3 — No Critical Bugs Open

Before any production deploy:

- No open bugs with severity `P1` (system down, patient safety impact, data loss, auth bypass).
- Any `P2` bugs (wrong data displayed, dashboard incorrect, broken workflow) documented and scheduled.
- `CHANGELOG.md` updated with the change and test result.

---

## Gate 4 — Security Agent Sign-Off

Any change touching the following **must** be reviewed and approved by the Security Agent before Lead Agent approves:

- `auth.py`, `enforce_auth.py` — authentication logic
- `patient_matcher.py` — patient identity matching
- Any endpoint that reads or writes `verification_status`, `priority`, `safe_to_queue`, or patient identity fields
- Any change to the JEIE-1 encryption/decryption path
- Any new external dependency or API call

Security Agent approval is independent. Saeed's approval does not substitute for Security Agent sign-off on safety-sensitive changes.

---

## Gate 5 — Smoke Test Passes

After every deploy, run `C:\JeffLocal\devops\deployment\smoke_test.ps1`. All checks must pass:
- Dashboard `:8765/health` → 200
- n8n `:5678/healthz` → 200
- Ollama `:11434` → 200
- `dashboard.sqlite` exists and is non-empty
- All 4 config files present

---

## P1 Bug Definition (immediate stop)

Any of the following is a P1 bug — halt the deploy and notify Saeed:

- LLM output overrides a deterministic field (`verification_status`, `priority`, `safe_to_queue`, any identity field)
- Auth bypass: a page or endpoint accessible without a valid session
- Patient data written to git history, logs, or any file outside `dashboard/data/`
- Dashboard crashes on startup or under normal use
- Dead-letter queue accumulates > 5 items in < 1 hour
- Red-flag case fails to reach `priority = 999 Emergency`

---

**Maintained by:** Test Agent + Lead Agent  
**Review:** Before every release. Updated when new test categories or safety rules are added.

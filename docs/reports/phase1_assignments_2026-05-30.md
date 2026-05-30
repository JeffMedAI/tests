# Phase 1 Task Assignment Briefs — JeffLocal
**Date:** 2026-05-30  
**Prepared by:** Lead Agent  
**Status:** Awaiting Saeed go-ahead before agent dispatch

---

## Priority Order & Rationale

```
RANK  TASK                              AGENT      WHY THIS ORDER
────────────────────────────────────────────────────────────────────────────────
  1   Auth fixture (conftest.py)        Test       Unblocks 78 unit tests. Nothing
                                                   else in the test suite can be
                                                   confirmed reliable until this lands.

  2   E2E Stage 3 re-run                Test       Fix is already applied. This is a
                                                   verification step, not new work.
                                                   Blocks declaring the call flow
                                                   pipeline "tested and stable."

  3   HMAC payload verification (n8n)   Backend    Security requirement (IR-01).
                                                   Must land before pilot staff
                                                   accounts are active — any live
                                                   webhook traffic before HMAC is
                                                   in place is an unverified intake
                                                   risk.

  4   Password reset end-to-end         Backend    Needed for real staff accounts
                                                   once Saeed provides them (Saeed
                                                   action #1). Backend work can be
                                                   built and tested against sandbox
                                                   accounts while we wait.

  5   GDPR 90-day automated purge       Database   GDPR compliance requirement
                                                   before go-live. Does not block
                                                   other technical tasks but must
                                                   be complete before Pilot 1.

SAEED ACTIONS (not agent tasks — document as pending Saeed decisions):
  A   Real staff accounts               Saeed      Unblocks password reset testing
                                                   with real credentials and pilot
                                                   go-live.

  B   Dedicated pilot URL               Saeed      Required before governance gate
                                                   review and external-facing comms.

  C   Governance gates 1–7              Saeed      Go-live is blocked until all
                                                   gates are signed off. Cannot be
                                                   delegated to agents.
```

---

## TASK 1 — Auth Fixture (conftest.py)

**Assigned to:** Test Agent  
**Priority:** HIGH — IMMEDIATE  
**Depends on:** Nothing (self-contained)  
**Security Agent review required:** No (test infrastructure, no production code)

### Context
78 unit tests are currently blocked because the pytest `conftest.py` does not include a working auth fixture compatible with the session-based authentication in the sandbox Flask app. Until this fixture exists, any test that touches a route behind `@enforce_auth` will fail at setup, making the results meaningless.

### What to do

1. Open `sandbox\conftest.py` and `sandbox\tests\fixtures\conftest.py` (check both locations — confirm which is active).
2. Add an `auth_client` fixture that:
   - Creates a test Flask app via `create_app(testing=True)`
   - Logs in programmatically via the `/login` endpoint with test credentials (`test-staff` / `test-password` or whatever sandbox credentials exist — check `sandbox\dashboard\app\main.py` or `.env.test`)
   - Returns a `test_client()` with the session cookie already attached
   - Tears down cleanly after the test
3. Add a `no_auth_client` fixture that provides an unauthenticated client (for testing redirect behaviour).
4. Run `pytest sandbox\tests\unit\ -v` and confirm the 78 previously-blocked tests now either pass or fail on actual logic (not setup errors).

### Acceptance criteria

- [ ] `pytest sandbox\tests\unit\ -v` runs with zero `fixture not found` or `401 at setup` errors
- [ ] `auth_client` fixture documented with a one-line docstring
- [ ] `no_auth_client` fixture present and used in at least one redirect test
- [ ] Count of tests that now pass vs. now fail (on logic, not setup) reported to Lead Agent
- [ ] No real credentials, NHS numbers, or patient data appear in any fixture

### Deliverable
Report to Lead Agent: "Auth fixture complete. X/78 tests now passing, Y failing on logic. Fixture at `sandbox/conftest.py`. Ready for Backend Agent to action failing tests."

---

## TASK 2 — E2E Stage 3 Re-run (Verification)

**Assigned to:** Test Agent  
**Priority:** HIGH — run immediately after Task 1 (can be parallelised if Test Agent has bandwidth)  
**Depends on:** Stage 3 fix already applied (SQLite direct query) — confirmed in PROJECT_MEMORY.md  
**Security Agent review required:** No (test run, no code change)

### Context
The 10-case E2E call flow test runner covers all 8 pathways across 5 stages. Stages 1, 2, and 4 are passing. Stage 3 (case verification — the step that confirms patient identity against SQLite) had a bug that was fixed in the last session. That fix has not yet been confirmed passing under a clean re-run.

### What to do

1. Locate the E2E runner (likely `sandbox\tests\e2e\` or `sandbox\scripts\` — check git log for the Stage 3 fix commit to find the exact file).
2. Run the full 5-stage E2E suite: all 10 cases, all 8 pathways.
3. Record per-stage, per-case results.
4. If Stage 3 passes all 10 cases: done — report results.
5. If Stage 3 still fails on any case: do NOT attempt to fix the application code. Document the failure with the exact assertion and case ID, then report to Lead Agent for Backend Agent assignment.

### Acceptance criteria

- [ ] All 5 stages run (do not stop at first failure)
- [ ] Results table produced: Stage × Case (pass/fail)
- [ ] Stage 3: all 10 cases PASS (this is the success criterion for this task)
- [ ] If any case fails: failure output captured (not just "it failed") and escalated
- [ ] No Playwright tests run against production (port 8765) — sandbox only (port 5000)

### Deliverable
Report to Lead Agent: "E2E re-run complete. Stage 3: 10/10 PASS [or: X/10 fail — details attached]. Full results matrix attached."

---

## TASK 3 — HMAC Payload Verification on n8n Webhook

**Assigned to:** Backend Agent  
**Priority:** HIGH (security requirement IR-01)  
**Depends on:** Task 1 (auth fixture) — needed so integration tests for this feature can run  
**Security Agent review required:** YES — mandatory before merge

### Context
The n8n webhook at `/api/ingest` (or the current active webhook path `jefflocal-test-intake`) currently accepts payloads from n8n without verifying that the payload actually came from the trusted local n8n instance. An attacker with network access to localhost:5000 could POST fabricated call data. HMAC verification adds a shared-secret signature check that ensures only the configured n8n instance can write to the intake endpoint.

This maps to **IR-01** in the governance framework (PipeWorks / Backend joint ownership — Backend Agent handles the Flask side).

### What to do

1. **Read first:** `sandbox\backend\main.py` (or wherever `/api/ingest` lives) and `sandbox\voice\` to understand the current payload handling.

2. **Agree the secret:** Add `WEBHOOK_HMAC_SECRET` to `.env.test` (test value) and document that the production value must be set in the server environment by Saeed. Never hardcode.

3. **Implement HMAC verification middleware:**
   ```python
   import hmac, hashlib, os

   def verify_hmac(request) -> bool:
       """
       Verify X-Hub-Signature-256 header against request body.
       Returns True if valid, False if missing or invalid.
       """
       secret = os.environ.get('WEBHOOK_HMAC_SECRET', '').encode()
       sig_header = request.headers.get('X-Hub-Signature-256', '')
       if not sig_header.startswith('sha256='):
           return False
       expected = 'sha256=' + hmac.new(secret, request.get_data(), hashlib.sha256).hexdigest()
       return hmac.compare_digest(expected, sig_header)
   ```

4. **Apply to the ingest route:** If HMAC check fails → return 401, log a warning (no payload content in log), do not process.

5. **n8n configuration note:** Document in `sandbox\docs\` (or a code comment) that n8n must be configured to send `X-Hub-Signature-256` using the same `WEBHOOK_HMAC_SECRET`. This is a Saeed / DevOps action for production — the Backend Agent documents it but does not configure n8n directly.

6. **Ask Test Agent to write integration tests first** (per Backend Agent workflow rules):
   - Valid HMAC → 201 (or whatever current success code is)
   - Missing header → 401
   - Wrong secret → 401
   - Tampered body (valid header but body modified) → 401

### Acceptance criteria

- [ ] `WEBHOOK_HMAC_SECRET` read from environment — never hardcoded
- [ ] Missing or invalid HMAC → 401 with no payload content in response body or logs
- [ ] Valid HMAC → request proceeds as normal
- [ ] `hmac.compare_digest` used (not `==`) to prevent timing attacks
- [ ] Test Agent integration tests all passing before Security Agent review
- [ ] Security Agent has reviewed and approved before merge
- [ ] n8n configuration requirement documented (for Saeed / DevOps to action in production)
- [ ] No raw transcript content logged at any point in the new code path

### Deliverable
Report to Lead Agent: "HMAC verification complete. Tests passing. Awaiting Security Agent review."  
Security Agent then reviews and either approves or blocks.

---

## TASK 4 — Password Reset End-to-End

**Assigned to:** Backend Agent  
**Priority:** MEDIUM (needed before pilot go-live; can start now, test with sandbox accounts)  
**Depends on:** Task 1 (auth fixture for test coverage); real staff accounts from Saeed (Saeed action A) for final acceptance testing  
**Security Agent review required:** YES — password handling touches auth

### Context
There is currently no self-service password reset flow. When real staff accounts are created (pending Saeed action A), staff will need a way to reset their passwords without Saeed manually editing the database. Build and test the full flow now using sandbox accounts; final acceptance with real accounts once Saeed provides them.

This flow must not send emails externally (no patient data leaves the building). Reset must be admin-initiated (not email link) for Phase 1 — a GP practice admin resets a staff password from the admin panel.

### What to do

1. **Clarify the flow with Lead Agent before starting** if there is any ambiguity. The assumed Phase 1 flow is:
   - Admin user logs in → navigates to Staff Management
   - Selects a staff account → clicks "Reset Password"
   - System generates a one-time temporary password (or prompts admin to set a new one)
   - Staff member logs in with temporary password → forced to change on first use
   - No email sent (on-premises only)

2. **Backend changes (sandbox only):**
   - Add route `POST /admin/staff/<staff_id>/reset-password` behind `@enforce_auth` with admin role check
   - Generate a temporary password (minimum 12 chars, random, using `secrets` module)
   - Hash with bcrypt (or whatever current password hashing method is in use — check `main.py`)
   - Store hashed temp password + `password_reset_required = True` flag in staff table
   - On next login: detect flag → redirect to `/change-password` before allowing dashboard access
   - Add `POST /change-password` route: validates old temp password, sets new password, clears flag

3. **Database change:** If `password_reset_required` column does not exist in the `staff` table, coordinate with Database Agent to add a migration. Do not add the column directly.

4. **Ask Test Agent to write tests first:**
   - Admin can reset a staff password → 200, temp password set
   - Non-admin cannot access reset route → 403
   - Staff with `password_reset_required=True` → redirected to change-password before dashboard
   - Staff sets new password → flag cleared, normal login resumes
   - Temp password cannot be reused after change

### Acceptance criteria

- [ ] Reset route only accessible to users with admin role
- [ ] Temp password generated via `secrets.token_urlsafe()` or equivalent — never predictable
- [ ] Password hashed before storage — plaintext never stored or logged
- [ ] `password_reset_required` flag enforced on every login (not just the first request after reset)
- [ ] Change-password flow requires both old (temp) and new password — prevents replay
- [ ] No email sending, no external calls
- [ ] All Test Agent tests passing before Security Agent review
- [ ] Security Agent approved before merge
- [ ] Tested end-to-end in sandbox with a sandbox staff account before marking done

### Deliverable
Report to Lead Agent: "Password reset built and tested in sandbox. Tests passing. Awaiting Security Agent review. Note: final acceptance test with real staff accounts requires Saeed action A."

---

## TASK 5 — GDPR 90-Day Automated Data Purge

**Assigned to:** Database Agent  
**Priority:** MEDIUM (compliance requirement before go-live; does not block other tasks)  
**Depends on:** Nothing — can start any time  
**Security Agent review required:** YES — GDPR data handling change

### Context
UK GDPR (Article 5(1)(e)) requires that personal data not be kept longer than necessary. For JeffLocal, raw call transcripts are personal data. The retention policy is 90 days. After 90 days, the raw transcript text must be purged (replaced with a tombstone string), while the row itself is retained for audit continuity.

The Database Agent CLAUDE.md already contains the target implementation pattern. The task is to implement it as a runnable script, register it with the Task Scheduler, and prove it works.

### What to do

1. **Create the script** at `sandbox\scripts\daily\purge_transcripts.py` using the pattern already defined in the Database Agent CLAUDE.md:
   - Query `transcripts` table for rows where `purged = 0` AND `purge_after <= datetime('now')`
   - `UPDATE` matching rows: set `raw_text = '[PURGED - 90 day retention expired]'`, set `purged = 1`
   - Log count of rows purged (count only — no content)
   - Write result to `reports\daily\{date}.json` under key `"transcripts_purged"`
   - If DB is inaccessible: raise an exception and write error to the daily JSON — never fail silently
   - Do NOT `DELETE` rows — the row (call_id, timestamps, purged=1) must be retained

2. **Verify `purge_after` is being set correctly:** Check that when a transcript is inserted, `purge_after` is set to `created_at + 90 days`. If it is not being set, flag this to Backend Agent as a separate issue before proceeding.

3. **Write a dry-run mode:** `purge_transcripts.py --dry-run` should report how many rows would be purged without actually purging. Useful for auditing.

4. **Write tests** (coordinate with Test Agent):
   - Row with `purge_after` in the past → purged (raw_text replaced, purged=1)
   - Row with `purge_after` in the future → untouched
   - Row already purged (purged=1) → untouched (idempotent)
   - DB inaccessible → exception raised, not silent failure
   - Dry-run mode → count reported, no rows changed

5. **Task Scheduler registration:** Document the registration command for DevOps Agent to add to `scripts\register_scheduled_tasks.ps1`. The purge runs at 02:00 daily. Do not register it yourself — hand the registration command to DevOps Agent or Saeed.

6. **Security Agent review:** Before the script is registered to run automatically, Security Agent must review it. The review specifically checks:
   - Correct tombstone string (no original content leaked)
   - `purged = 1` flag correctly set
   - No row deletion
   - Audit log entry written for each purge batch

### Acceptance criteria

- [ ] Script runs without error against sandbox DB (with test data seeded)
- [ ] Rows past `purge_after` have `raw_text = '[PURGED - 90 day retention expired]'` and `purged = 1`
- [ ] Rows not yet expired: untouched
- [ ] Idempotent: running script twice does not double-purge or error
- [ ] `--dry-run` flag works and reports correct count without modifying data
- [ ] Count logged to `reports\daily\{date}.json["transcripts_purged"]`
- [ ] Exception raised (not swallowed) if DB unreachable
- [ ] All Test Agent tests passing
- [ ] Security Agent reviewed and approved
- [ ] Task Scheduler registration command documented (for DevOps Agent / Saeed to execute)

### Deliverable
Report to Lead Agent: "GDPR purge script complete. Tests passing. Awaiting Security Agent review. Task Scheduler registration command ready for DevOps Agent."

---

## SAEED ACTIONS REQUIRED (not agent tasks)

These items cannot be delegated to agents. They are decisions or information only Saeed can provide.

---

### SAEED ACTION A — Real Staff Accounts

**What is needed:** Full name, role (receptionist / admin / GP), and email address for each Churchtown Medical Centre staff member who will have a dashboard login during the pilot.

**Format requested:**
```
Name          | Role          | Email
Firstname L.  | receptionist  | firstname@churchtown.nhs.uk  (or whatever domain)
```

**Why this unblocks:**
- Password reset (Task 4) can be fully acceptance-tested only with real accounts
- Pilot go-live requires staff to be able to log in
- Staff onboarding runbook (ConfigMaster task) requires real role list

**Note:** Accounts will be created in the sandbox first for testing, then migrated to production with Saeed's approval.

---

### SAEED ACTION B — Dedicated Pilot URL Confirmation

**What is needed:** Confirmation of the URL that Churchtown staff will use to access the dashboard during Pilot 1.

Options to confirm:
1. Continue using `dashboard.app-avamed.uk` (current Cloudflare tunnel)
2. New subdomain (e.g. `churchtown.app-avamed.uk`)
3. Other

**Why this unblocks:**
- Governance gate documentation requires a confirmed URL
- Marketing/onboarding materials reference the URL
- Cloudflare tunnel may need reconfiguring (DevOps Agent task, pending this decision)

---

### SAEED ACTION C — Governance Gates 1–7 Sign-off

**What is needed:** Saeed to work through the governance gate checklist (document at `governance\GOVERNANCE_FRAMEWORK.md`) and confirm each gate is satisfied or identify what is outstanding.

**Why this blocks go-live:** No agent has authority to sign off governance gates. These are risk-acceptance decisions that must come from Saeed as Executive Sponsor.

**Suggested approach:** Lead Agent can produce a gate-by-gate status summary for Saeed to review if that would help move this faster. Just ask.

---

## Summary Table

```
#  TASK                        AGENT      PRIORITY  DEPENDS ON   SEC REVIEW?
─────────────────────────────────────────────────────────────────────────────
1  Auth fixture (conftest.py)  Test       HIGH      —            No
2  E2E Stage 3 re-run          Test       HIGH      —            No
3  HMAC webhook verification   Backend    HIGH      Task 1       YES
4  Password reset E2E          Backend    MEDIUM    Task 1       YES
5  GDPR 90-day purge           Database   MEDIUM    —            YES

A  Real staff accounts         SAEED      —         —            —
B  Pilot URL confirmation      SAEED      —         —            —
C  Governance gates 1–7        SAEED      —         —            —
```

---

*Document prepared by Lead Agent. All agent tasks require Saeed's session go-ahead before dispatch. Saeed actions (A, B, C) are decisions only Saeed can make.*

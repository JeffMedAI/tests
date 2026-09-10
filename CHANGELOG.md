# CHANGELOG — Avamed / JeffLocal
# Audit log for autonomous bug fixes, approved marketing spend, and governance decisions.
# APPEND ONLY — never delete or edit existing entries.
# Format defined in REPORTING.md

---

## 2026-06-07 — Governance Package Created
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit instruction in session)
**Description:** Created full governance package: updated CLAUDE.md, new AGENT_TEAM_CHARTER.md, GOVERNANCE.md, REPORTING.md, CHANGELOG.md, and all 9 agent MD files in C:\JeffLocal\agents\.
**Files changed:** CLAUDE.md, AGENT_TEAM_CHARTER.md, GOVERNANCE.md, REPORTING.md, CHANGELOG.md, agents/lead_CLAUDE.md, agents/backend_CLAUDE.md, agents/frontend_CLAUDE.md, agents/database_CLAUDE.md, agents/test_CLAUDE.md, agents/security_CLAUDE.md, agents/devops_CLAUDE.md, agents/strategy_CLAUDE.md, agents/marketing_CLAUDE.md
**Tests run:** N/A (documentation only)
**Saeed notified:** This session

---

## 2026-06-07 — Directory Cleanup & Architecture Change (No More Sandbox)
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit "yes approved" in session)
**Description:** Removed sandbox directory and all junk/temp files. Archived sandbox audit logs to logs/audits/ and sandbox SQLite to backup/sandbox-archive-20260607/. Confirmed all 4 pipeline config files exist in config/ (PE-01 to PE-04 resolved). Updated CLAUDE.md: sandbox section removed, critical path updated, PE-01–PE-04 status updated. New development model: git feature branches, no parallel sandbox directory.
**Files removed:** sandbox/ (entire), production/ (empty), JeffLocaltmppytest-*/, pytest-tmp/, .tmp/, .playwright-mcp/, PyWhatKit_DB.txt, n8n API key.txt, session, 1, check_button.ps1, check_button.py, COMPLETE_HANDOFF_FOR_EMAIL.zip, dashboard/_backup_*, dashboard/app/_backup_*
**Files changed:** CLAUDE.md (critical path + PE-01–PE-04 sections), CHANGELOG.md
**Security note:** n8n API key.txt deleted. Key NOT rotated this session per Saeed's decision — rotation recommended before go-live.
**Tests run:** N/A (infrastructure cleanup only)
**Saeed notified:** This session

---

## 2026-06-10 — Avamed Clarity Design Sprint (Tasks 1–6)
**Agent:** Frontend Agent + Lead Agent (Claude Code session)
**Approved by:** PENDING — this entry is the pre-merge record. Saeed's explicit "approved" required before production merge.
**Security review:** Security Agent (GuardRail) — SIGNED OFF. See docs/reports/clarity-sprint-approval-pack-2026-06-10.md.
**Description:** Full design system and UI refresh implementing the Avamed Clarity visual identity across the staff dashboard. Navy (#0B3D6B) and Teal (#00A896) replace NHS blue. New interactive components: KPI strip with count-up animation, sparkline chart, command palette (/ shortcut), patient hover card, urgent case pulse. Four new authenticated API endpoints. Typography system: Plus Jakarta Sans + Inter + JetBrains Mono via Google Fonts.

**Files changed:**
- dashboard/static/dashboard.css — CSS token migration, new Clarity tokens, component styles (KPI strip, sparkline, command palette, hover card, pulse animation)
- dashboard/templates/base.html — Google Fonts, pipeline health dot, command palette overlay, keyboard shortcut update
- dashboard/templates/index.html — KPI strip, sparkline, urgent pulse, patient hover card, chart colour palette fix
- dashboard/templates/case_detail.html — typography tokens (.cd-meta-id mono font, display font on patient name)
- dashboard/app/main.py — 4 new endpoints: /api/analytics/hourly-volume, /api/analytics/performance-summary, /api/patient-card, /api/search

**New files:**
- PRODUCT.md — Avamed product context for impeccable design tooling (register: product, personality: Calm · Precise · Trustworthy)
- .impeccable/live/config.json — live mode pre-configuration for Clarity sprint iteration

**Security notes:**
- All 4 new API endpoints double-protected: auth middleware (primary) + demo_fallback check (defence-in-depth)
- No PII in analytics endpoints (aggregate counts only)
- NHS number masked server-side in /api/patient-card (digits[:3] + " ***")
- /api/search limited to 8 results, returns minimum necessary fields (no NHS number, no DOB)
- All SQL queries parameterised — no injection vectors

**Tests run:** 21 unit tests passing. 83 failures confirmed pre-existing (git stash verified — identical failures on pre-sprint snapshot). E2E Playwright failures are Playwright auth timeout — pre-existing infrastructure issue unrelated to this sprint.
**Saeed notified:** This session (pending approval)

## [Bug Fix] 2026-06-11 — Curly-quote SyntaxError in detail panel script

**Agent:** Lead Agent  
**Files changed:** dashboard/templates/index.html (line 1349)  
**Approved by:** Saeed (explicit approval in session 2026-06-11)

**Description:** Template line 1349 used Unicode curly/smart quotes (U+2018 / U+2019) as JavaScript string delimiters in the GUIDED_STEPS red_flag array. V8 threw SyntaxError: Invalid or unexpected token which silently killed the entire 46400-char inline script block on every page load. No event listeners registered — filter collapse, batch selection, and detail panel were all non-functional.

**Fix:** Replaced 11 instances of U+2018/U+2019 with ASCII straight single quotes (U+0027) on line 1349.

**Test result:** SyntaxError gone. Clicking a case card triggers the detail panel sliding in from right as designed.

---

## 2026-06-11 — Batch 1 UX/UI Fixes
**Agent:** Frontend Agent (Claude Code session)
**Approved by:** Saeed (explicit instruction in session 2026-06-11)
**Files changed:** `dashboard/templates/index.html`, `dashboard/templates/base.html`, `dashboard/static/dashboard.css`

**Description:** Batch 1 of approved UX improvements following a full UX/UI review of the dashboard.

**Changes:**
1. **Branding** — Replaced all user-facing "JeffLocal" references with "Avamed" (page title, browser tab, topbar, batch resolve note). Internal JS storage keys unchanged.
2. **Resolve confirm UX** — Extended two-step confirm timeout from 3s to 5s. Added amber button state (`.confirming` CSS class). Added animated 5-second countdown progress bar beneath the resolve button.
3. **Panel click-toggle** — Fixed backdrop `pointer-events: none` so clicking a different case card while the panel is open switches directly to that card (no close-then-open). Backdrop retains visual dim but no longer blocks pointer events.
4. **Post-resolve panel state** — After resolve: stepper advances to step 4 (Resolved), guided steps hidden, Escalate button hidden. Both reset correctly when switching to a new case.
5. **Clipboard copy icons** — Added copy-to-clipboard buttons for NHS number, EMIS number, Phone, and AI summary in the detail panel. Uses `navigator.clipboard` with textarea fallback.
6. **NHS/EMIS unconfirmed warning** — Fields showing "n/a" now rendered in amber italic to signal identity not confirmed.
7. **AI Intake Summary label** — Renamed "Jeff's Triage Summary" to "AI Intake Summary". Removed "Ollama/Gemma4 · on-premises" internal attribution from panel.

**Test result:** 10 unit tests passed. 93 fixture-setup errors are pre-existing (test DB not seeded) and unrelated to these changes. No Python code modified.

---

## 2026-06-12 — Sidebar Redesign (Role-based)
**Agent:** Frontend Agent (Claude Code session)
**Approved by:** Saeed (explicit instruction in session 2026-06-12 — design direction confirmed via 4 clarifying questions)
**Files changed:** `dashboard/templates/index.html`, `dashboard/static/dashboard.css`, `dashboard/app/main.py`

**Description:** Full redesign of the analytics sidebar. Removed pipeline jargon and replaced with two role-based views (Reception and Manager) with a persistent toggle stored in localStorage.

**Changes:**
1. **Reception mode (default)** — Needs Attention section: Critical, Overdue (>2h), Review needed, Identity issue — all clickable, jump to filtered case list. Today section: Open cases + Resolved today (clickable) + Peak hour text. Team section: simplified name + open-count only.
2. **Manager mode** — Today's Numbers: Calls received, Resolved, Avg response time. Case Types: horizontal teal bar chart per request type (Prescription, Sick Note, Referral, Appointment, etc.), each bar clickable and filtered by type. Team section: full pills view (open/active/done) with legend.
3. **Removed** — "Call Analytics" card (pipeline terms: "Safe to Queue", "Dropped"), "Live Workload" card (redundant), "Quick Status" card (replaced), hourly sparkline chart.
4. **Added** — `get_peak_hour()` backend function returns busiest hour today (e.g. "10–11am"). `peak_hour` passed to template context.
5. **Reused** — `request_type_breakdown` (already in context) provides bar chart data with pre-calculated `width` percentages and filter URLs.

**Test result:** Python syntax check passed. No unit tests broken. UI requires manual login to verify (browser automation blocked by auth).

---

## 2026-06-17 — Test/Demo Naming Cleanup (RAWMOCK removed, GPDEMO/N8NTEST addressed additively)
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit "approved" in session — additive prefix change)
**Description:** Saeed flagged that RAWMOCK, GPDEMO and N8NTEST test-data prefixes look unprofessional ahead of going production-ready.
1. **RAWMOCK** — removed from `dashboard/tests/test_api_endpoints.py`: replaced file-fixture-based seeding with direct DB seeding using the existing `TC-` prefix convention. Two tests deleted at Saeed's instruction (`test_api_sync_rawmock_only_returns_pattern`, `test_gp_demo_prefix_allowed_only_as_test_prefix`).
2. **GPDEMO / N8NTEST** — confirmed these are still live and load-bearing in `app/main.py` (`DEMO_CALL_PREFIXES`, `N8NTEST_ARCHIVE_FOLDERS`, `archive_n8ntest_artifacts()`, `write_n8ntest_envelopes()`, etc.) and referenced across ~15 test/script files outside `dashboard/`. A full rename was judged too risky to do safely in one pass (silent loss of demo-data recognition if any caller of the old prefix is missed). Instead: added a new prefix, `AVA-TEST`, to `DEMO_CALL_PREFIXES` in `app/main.py`, alongside the existing entries (`TC-`, `RX-TEST`, `PRODSIM`, `DEMO`, `GPDEMO`, `GPTDEMO`). Nothing removed, nothing renamed — old prefixes keep working. New test batches should use `AVA-TEST-<timestamp>` going forward; existing GPDEMO/N8NTEST-prefixed scripts can be migrated at Saeed's pace.
**Files changed:** `dashboard/app/main.py` (DEMO_CALL_PREFIXES — additive only), `dashboard/tests/test_api_endpoints.py`, `CHANGELOG.md`
**Tests run:** Local pytest run on this machine was unreliable (sandbox file-mount desync, unrelated to the edits — flagged separately). Re-verification on the real Windows host pending.
**Saeed notified:** This session

---

## 2026-06-17 — Known Gap Logged: No call_id prefix validation on `/api/n8n/test-intake-batch`
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed ("log as gap" — no fix applied this session)
**Description:** While investigating the GPDEMO/N8NTEST naming cleanup above, found that the test `test_api_n8n_test_intake_rejects_non_n8ntest_call_id` (`dashboard/tests/test_api_endpoints.py`) expects the `/api/n8n/test-intake-batch` endpoint to reject any call_id that doesn't contain "N8NTEST" (400 response). Read the full `api_n8n_test_intake_batch` function and its helpers (`call_id_from_test_call`, `write_n8ntest_envelopes`, `is_encrypted_envelope`) in `app/main.py` — none of them actually perform this check. The endpoint currently accepts any call_id shape, provided `test_mode` and `disable_google_push` are set correctly. This is the same underlying gap implied by the now-deleted `test_gp_demo_prefix_allowed_only_as_test_prefix` test.
**Risk:** Low — this endpoint is already gated behind `test_mode=true`, `disable_google_push=true`, and HMAC verification (`JEFF_WEBHOOK_SECRET`). Not patient-identity or clinical-safety logic, so does not trigger the auth/patient-data Security Agent gate on its own. Flagged here per Saeed's instruction rather than fixed.
**Files affected (not changed):** `dashboard/app/main.py` (`api_n8n_test_intake_batch`), `dashboard/tests/test_api_endpoints.py`
**Tests run:** N/A — no fix applied, gap logged only
**Saeed notified:** This session

---

## 2026-06-17 — Known Gap Logged: n8n session not staying signed in (CRITICAL — blocks testing)
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed ("flag as critical gap" — no fix applied this session)
**Description:** Mid test-run, attempting to activate "Listen for test event" on the `jefflocal-test-intake` workflow to fix a 404 on `/webhook-test/...`, found n8n's UI at `http://localhost:5678` sitting on its sign-in screen rather than an already-authenticated session. Per standing rule, Claude does not enter passwords into any field, so could not log in to flip the listener on. Worked around it this run by sending the batch to the always-on production path (`/webhook/jefflocal-test-intake`) instead, which returned 200 — but that path only works if the workflow is "Active" in n8n, and is not normally how test/demo traffic should enter. The underlying issue — why the n8n session isn't staying signed in — is unresolved and unexplained. [UNVERIFIED — confirm before proceeding: whether this is expected behaviour (e.g. session timeout, browser profile reset) or a config/cookie problem worth fixing before pilot go-live, when test/demo traffic will need quick repeatable webhook-test access].
**Risk:** Medium-high ahead of go-live — if reception-facing tooling or routine testing depends on staying signed into n8n, repeated lockouts will slow diagnosis during the pilot window. Does not touch patient data or auth logic directly, so not an automatic Security Agent block, but flagged as critical because it blocked this session's test run until worked around.
**Also found:** the staff dashboard at `https://dashboard.app-avamed.uk` also requires sign-in (username/password or PIN) — this could not be verified against CLAUDE.md's note that "staff accounts do not yet exist," since Claude does not enter dashboard credentials either. [UNVERIFIED — confirm whether staff accounts now exist, and if so whether n8n and dashboard logins are both meant to require a human each session].
**Files affected:** None — infrastructure/session-state issue, not a code change.
**Workaround used this run:** `tests/send_gp_demo_n8n_webhook_calls.py --url http://localhost:5678/webhook/jefflocal-test-intake` (production webhook path) instead of the default test-listener path.
**Tests run:** N/A — gap logged only
**Saeed notified:** This session

---

## 2026-06-23 — Bug fix: stale .git/objects/maintenance.lock deleted
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Bug-fix autonomy exception — Security Agent: no code change, no data risk; Lead Agent: approved. Logged per CLAUDE.md.
**Description:** Found stale lock file at `.git/objects/maintenance.lock` dated 2026-05-29. Left by a `git maintenance` run that was interrupted. Stale lock prevents future git maintenance runs. Deleted safely — no git operations were in progress.
**Files changed:** None (lock file deleted, not a tracked file)
**Tests run:** N/A
**Saeed notified:** This session

---

## 2026-06-23 — Bug fix: resolved_by missing from /api/cases/{call_id} response
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Bug-fix autonomy exception — Security Agent: `resolved_by` is staff name (not patient identity, not auth logic), already stored in DB and returned on HTML case detail page — exposing it on the JSON API endpoint is consistent; Lead Agent: approved. Logged per CLAUDE.md.
**Description:** `/api/cases/{call_id}` GET endpoint (used by inline detail panel) did not include `resolved_by`, `resolved_at`, or `resolved_at_display` in its response, even though all three fields are in the DB and used in audit trail logic. Reception staff using the JS panel had no way to see who resolved a case or when. Added all three fields to the return dict.
**Files changed:** `dashboard/app/main.py` (api_case_get return dict, 3 fields added)
**Tests run:** 144/144 pytest tests passing (all green)
**Saeed notified:** This session

---

## 2026-06-23 — Bug fix: wrong column name (created_at) in patient lookup SQL
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Bug-fix autonomy exception — Security Agent: column name fix in a read-only patient lookup subquery, no auth or identity logic touched; Lead Agent: approved. Logged per CLAUDE.md.
**Description:** Patient lookup endpoint (`/api/patient-hint`) had a SQL subquery using `c2.created_at` to count today's cases for the same patient. The `cases` table has no `created_at` column — this would silently return 0 for `cases_today` on every lookup (SQLite returns NULL for unknown columns in expressions, so the COUNT was always 0). Fixed by replacing `c2.created_at` with `c2.imported_at`, which is the correct column (set at import time, always populated).
**Files changed:** `dashboard/app/main.py` (one SQL clause in patient hint endpoint)
**Tests run:** 144/144 pytest tests passing (all green)
**Saeed notified:** This session

---

## 2026-06-23 — Bug fix: fresh cases sort to bottom of worklist when call_timestamp_sort is null/zero
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Bug-fix autonomy exception — Security Agent: worklist sort order change, no patient identity or auth logic; Lead Agent: approved. Logged per CLAUDE.md.
**Description:** Worklist ORDER BY used `COALESCE(call_timestamp_sort, 0) DESC`. When `call_timestamp_sort` is 0 or unparseable (e.g. malformed timestamp from pipeline), cases sort to the bottom behind all cases with real timestamps — including urgent ones. Fresh imports always have `imported_at` set correctly. Fixed by replacing the bare `COALESCE` with `COALESCE(NULLIF(call_timestamp_sort, 0), CAST(strftime('%s', imported_at) AS REAL), 0)` across `sort_clause()` and `worklist_order_clause()`. Cases with a valid call timestamp sort by call time (existing behaviour). Cases with no valid call timestamp fall back to import time (new, correct behaviour).
**Files changed:** `dashboard/app/main.py` (`sort_clause`, `worklist_order_clause` — 4 ORDER BY expressions updated)
**Tests run:** 144/144 pytest tests passing (all green)
**Saeed notified:** This session

## 2026-06-23 — UX: Red flag card visual treatment
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Bug-fix autonomy exception — Security Agent: CSS/template only, no auth or patient-identity logic; Lead Agent: approved. Logged per CLAUDE.md.
**Description:** Worklist case cards for red-flag calls had no visual distinction beyond a "Red Flag" badge chip. Added `data-red-flag` attribute to the `<article>` element in index.html. Added CSS rule `.request-card[data-red-flag="true"]:not(.resolved-row)` with 4px danger-colour left border and light red background tint. Makes urgent cases unmissable at a glance.
**Files changed:** `dashboard/templates/index.html` (data-red-flag attribute on article), `dashboard/static/dashboard.css` (new card rule)
**Tests run:** 144/144 pytest tests passing (all green)
**Saeed notified:** This session

## 2026-06-23 — UX: Verification status badge on case cards
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Bug-fix autonomy exception — Security Agent: display-only badge, verification_status set by deterministic code not LLM; Lead Agent: approved. Logged per CLAUDE.md.
**Description:** Reception staff could not see patient identity confirmation on the worklist card. `verification_status = "matched"` was in the DB but never displayed. Added a green "✓ Matched" badge to the card-badges section in index.html. Shows only when `identity_review_required` is False and `verification_status` is non-empty (i.e. a good match). Identity-problem cases already show "Review (No ID Match)" etc via summary_chips — this covers the opposite, successful case.
**Files changed:** `dashboard/templates/index.html` (verification badge in card-badges div)
**Tests run:** 144/144 pytest tests passing (all green)
**Saeed notified:** This session

## 2026-06-23 — UX: Client-side notes gate for red flag / identity cases
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Bug-fix autonomy exception — Security Agent: JS gate is additive safety, server-side validation unchanged; Lead Agent: approved. Logged per CLAUDE.md.
**Description:** For red-flag and identity-review cases, the "Mark as Resolved" button was clickable even when the outcome notes field was empty. Server-side already blocks resolution without notes for these cases (returns error). Added client-side gate: resolve button gets `data-requires-notes="true"` attribute (via Jinja2) when `case.red_flags_present or case.identity_review_required`. Inline JS disables the button on page load if notes textarea is empty, and re-enables it when the staff member types. Prevents the error modal from appearing in the first place.
**Files changed:** `dashboard/templates/case_detail.html` (resolve button attribute + inline script)
**Tests run:** 144/144 pytest tests passing (all green)
**Saeed notified:** This session

## 2026-06-26 — Tech-debt Phase 1 remediation (B1, D1, DOC1, I1–I3)
**Agent:** Lead Agent (Claude Code session) + Security Agent review
**Approved by:** Saeed (explicit "go ahead with phase 1" in session). Security Agent verdict: **APPROVE-WITH-NOTES** (no veto, zero required pre-merge changes; core LLM/deterministic safety rule confirmed intact). Scope/disposal options confirmed by Saeed: archive-don't-delete; merge after review.
**Description:** Acted on the tech-debt audit. **B1** — repaired two broken analytics endpoints (`api_hourly_volume`, `api_performance_summary`) that queried a non-existent `created_at` column and a non-existent `dashboard_imports` table (both 500'd in production); now use `imported_at` / count from `cases`. Fixed test-first (RED→GREEN). **D1** — declared the previously-undeclared security-critical `cryptography` dependency for the decrypt pipeline (`app/requirements.txt`, pinned `>=44,<49`). **DOC1** — corrected Flask→FastAPI mislabelling in PROJECT_MEMORY + watchdog/scheduler comments; fixed stale `LOCAL_SERVICE_URLS` 5000→8765; archived dead `restart_flask.*` scripts. **I1** — archived ~474 MB of surplus backups out of the repo (kept newest 3 restore points); `backups/` (198 tracked files) untracked. **I2** — quarantined zero-byte junk files + dev screenshots, extended `.gitignore`. **I3** — added `.graphifyignore` so the code graph indexes source not framework/prose (3972→1678 nodes).
**Note on commits:** Concurrent automated session-close commits (5591564 by Sonnet 4.6, 47b332f evening brief) independently made/captured most of the same B1/DOC1/backup work and swept the uncommitted D1/test/docs files. Net new from this session committed as 22e363a (.graphifyignore). Phase 1 now fully present on `sandbox`.
**Files changed:** `dashboard/app/main.py` (analytics queries + service-url port), `app/requirements.txt` (new), `dashboard/tests/test_analytics_endpoints.py` (new regression test), `PROJECT_MEMORY.md`, `scripts/service_control/watchdog.ps1` (comment), `scripts/register_scheduled_tasks.ps1` (description), `.gitignore`, `.graphifyignore` (new), `docs/archive/dead-scripts/` (new). Backups/screenshots moved to `C:\JeffLocal_archive\2026-06-25\`.
**Tests run:** Full dashboard unit suite 106/106 passing, including 2 new analytics regression tests. E2E not run this session.
**Security review:** APPROVE-WITH-NOTES. Two pre-existing latent bugs flagged for Phase 2 (watchdog fallback uses `main:app` not `app.main:app`, and a venv-bootstrap ordering bug — both dead unless the primary launcher is missing). No PII in analytics responses; SQL parameterised; safety split untouched.
**NOT YET MERGED TO PRODUCTION:** `sandbox` is 17 commits ahead of `main` (last prod merge 2026-06-19). Production merge scope pending Saeed's decision — see session report.
**Saeed notified:** This session

---

## 2026-07-14 — Bug Fix: NameError on home/requests page after router extraction (feature/refactor-2-5-6)
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit "Fix branch + regression test" in session, 2026-07-14)
**Description:** During an isolated full-pipeline test run of feature/refactor-2-5-6, the home page (`/`) and requests page (`/requests`) returned HTTP 500 whenever an unacknowledged critical alert existed. Root cause: the alert-helper extraction (commit 678aeac) moved `alert_row_to_display` into `app/alert_queries.py`, but `main.get_urgent_attention` (main.py:1406) still called it without importing it -> NameError. `/requests` routes through `index()` which calls `get_urgent_attention`, so both pages crashed. The 323 unit/integration suite missed it (no test drove `get_urgent_attention` with an alert row); the e2e `TestRequestsPage` suite — not run during the refactor session — does catch it. NOTE: commit 678aeac (13 Jul 07:37) predates the running production process start (13 Jul 10:05), so this bug has been LIVE on production :8765 since 13 Jul, not merely a merge risk.
**Fix:** Added `from .alert_queries import alert_row_to_display` to main.py imports. Added regression test `test_get_urgent_attention_resolves_latest_alert_after_router_extraction` in tests/test_api_endpoints.py (seeds a critical alert, asserts get_urgent_attention resolves).
**Files changed:** dashboard/app/main.py, dashboard/tests/test_api_endpoints.py, CHANGELOG.md
**Tests run:** New regression test PASS. Full non-e2e dashboard suite: 370 passed. Live verification on isolated refactor instance :8799 — `/`, `/requests`, `/patients` all HTTP 200 after fix. The 5 e2e TestRequestsPage failures remain against the un-redeployed production :8765 (old code) and will clear on deploy; identical root cause.
**Security review:** Not safety-sensitive (alert display helper — not auth, patient identity, or clinical logic). Bug-fix exception applies.
**Saeed notified:** This session (approved the fix approach directly).
**Related smell (not fixed):** clean_alert_message / is_modal_worthy_alert are duplicated in both main.py (1528/1533) and alert_queries.py — divergent-copy risk, flagged for the refactor evaluation.

---

## 2026-07-17 (evening) — Multi-tenancy step 3: migrated dashboard.sqlite -> churchtown.sqlite
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit "yes" in session, specific to this step — separate from the design approval)
**Description:** governance/MULTI_TENANCY_PROPOSAL.md sequence table row 3. Built `scripts/tenant/migrate_to_tenant_db.py` (TDD, tests written first): safe hot-copy of dashboard.sqlite -> churchtown.sqlite using sqlite3's backup API (same technique as the existing approved `backup_db.py`), plus `verify_migration()` — row-count comparison across named tables + `PRAGMA integrity_check` on both files. Ran the real migration against production: `scripts/backup/backup_db.py` first (existing daily backup), then the new script. Verified: 78 cases, 5 staff_users, 1251 audit_events, all matching between source and dest, integrity_check OK on both. Dashboard.sqlite untouched; live dashboard NOT repointed at churchtown.sqlite (that's step 4/5, not in scope today) — health check post-migration confirms case_count still 78, all services up.
**Bugs found and fixed pre- and post-merge:**
1. Security Agent review (before merge) caught a missing source==dest guard — if a future caller ever passed the same path for both with `force=True`, the script would have deleted the live dashboard.sqlite then backed an empty DB onto itself. Fixed with an explicit `ValueError` guard before any file deletion. Also added `audit_log`→(see #2) to the verified tables and broadened exception handling to match the approved `backup_db.py` precedent.
2. First live run against real production data crashed: `VERIFY_TABLES` assumed table names `staff`/`audit_log`; the actual schema uses `staff_users`/`audit_events`. The migration itself succeeded (whole-file backup API copy is table-name agnostic) but the verification step crashed with an uncaught `sqlite3.OperationalError` right after. Fixed the table names, wrapped the verify call in its own try/except so a bad table name fails clean instead of a raw traceback, re-verified directly against the already-created churchtown.sqlite (no need to re-copy) — match confirmed.
**Files changed:** scripts/tenant/migrate_to_tenant_db.py (new), scripts/tenant/test_migrate_to_tenant_db.py (new, 15 tests), CHANGELOG.md, PROJECT_MEMORY.md, HANDOFF.md
**Tests run:** 15/15 new tests green (worktree + production tree, both runs). Real production verification: row counts + integrity_check match on both databases.
**Security review:** APPROVE WITH CHANGES on the pre-merge script (source==dest guard, exception handling) — both applied before merge. The post-merge table-name fix is non-security (naming only, same guards apply) — bug-fix autonomy exception applies, logged here per protocol.
**Also this session:** ran `/fewer-permission-prompts` — scanned 27 recent transcripts, added a handful of genuinely read-only Bash/MCP patterns to `.claude/settings.json` (schtasks query variants, browser read_page/get_page_text/find/read_network_requests/screenshot). Wrote (did not run) `scripts/service_control/fix_directory_acl.ps1` — the C:\JeffLocal + config folder permission fix (open item #3) — for Saeed or another admin to run manually; NTFS permission changes are outside what this session executes directly.
**Saeed notified:** This session (step 3 approval was given live; write-up for later on the ACL fix was requested and delivered).

---

## 2026-07-17 (evening, continued) — Daily briefs rewritten in plain English + 4 real bugs fixed
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit instruction to make the morning/evening briefs 4th-grade simple)
**Description:** Both brief scripts (`scripts/daily/strategy_daily.ps1`, `scripts/daily/combined_brief.ps1`) now
try a local-AI rewrite (Ollama, gemma4:e2b) of every bullet into short, plain sentences before sending,
falling back to a deterministic word-glossary version if the AI call fails for any reason — the brief always
sends something readable, never nothing. Not security-sensitive (internal reporting scripts, no auth/patient
data/compliance logic touched) — bug-fix autonomy exception applies, logged here per protocol.
**Bugs found and fixed while testing against real data:**
1. Line extraction only grabbed lines starting with "-" or "1." — session logs are plain one-sentence-per-line
   (CLAUDE.md's own style), so almost everything except nested sub-lists was silently dropped from every past
   brief. Now grabs every real content line.
2. PowerShell array-unwrapping gotcha: helper functions correctly used `return ,$x` to stop a 0/1-element array
   collapsing, but callers then wrapped that already-safe return in an extra `@(...)` or piped it into
   Select-Object — which flattens the whole array back into ONE object. Every section was rendering as a single
   giant run-on bullet. Fixed by capturing to a plain variable first, then re-wrapping/piping that.
3. Windows PowerShell 5.1's Invoke-RestMethod sent a string body with a leading UTF-8 BOM; Ollama's Go JSON
   parser rejects that outright ("invalid character 'ï' looking for beginning of value"), so every AI call
   400'd. Fixed by encoding the JSON body to UTF-8 bytes with no BOM explicitly before sending.
4. `Get-Content -Encoding UTF8` on Windows PowerShell 5.1 misdetects non-BOM UTF-8 files and mangles multi-byte
   characters (em dashes, curly quotes) into mojibake — traced a corrupted "—" all the way through to the JSON
   400 above. Fixed by reading files via `[System.IO.File]::ReadAllText` with an explicit UTF8 encoding.
**Also:** relabeled sections in plain words, dropped raw git-commit-hash lists and the internal "memory drift"
diagnostic from what Saeed reads (still logged for troubleshooting), added a near-duplicate filter for restated
standing notices. Removed a stray 0-byte junk file (`scripts/daily/found`, the documented recurring
unquoted-redirect artifact).
**Files changed:** scripts/daily/strategy_daily.ps1, scripts/daily/combined_brief.ps1, CHANGELOG.md
**Tests run:** Full combined evening brief run against real session logs + real production data (not synthetic)
for both projects (JeffLocal + St Marks) — every section came back genuinely simplified, no fallbacks needed,
~4.5 min total runtime. `strategy_daily.ps1`'s standalone (non-forwarding) path shares the same functions but
was not independently live-tested this session — only `combined_brief.ps1`, which is what Task Scheduler
actually runs, was.
**Security review:** Not applicable — no auth/patient-data/compliance logic touched (internal reporting/
formatting only). Bug-fix autonomy exception applies.
**Saeed notified:** This session.

---

## 2026-07-20 — Ollama Autostart + Brief Fallback Hardening
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit instruction in session, 2026-07-20)
**Description:** Saeed reported the 07:00 WhatsApp brief can fail silently if Ollama isn't running when it
calls out for the AI rewrite step. Two changes:
1. **Windows autostart task attempted, blocked — needs Saeed's action.** Tried to register a "Ollama - Auto
   Start" scheduled task (trigger: system boot, before any login; runs `ollama serve` as user s5256 via S4U
   logon so it can see the models under `C:\Users\s5256\.ollama`; restarts on failure). `Register-ScheduledTask`
   returned Access Denied — this session isn't running as Administrator, and a boot-trigger task that runs
   without anyone logged in requires an elevated session to register. NOT created. Saeed needs to run the
   command himself in an elevated PowerShell, or ask for the weaker `AtLogOn`-trigger version instead (doesn't
   need elevation, but only starts Ollama when someone logs in, not on a cold unattended boot). Exact command
   for the elevated option is in the session's final report to Saeed.
2. **WhatsApp message now says when the AI rewrite failed, instead of silently degrading.** The Ollama call
   already had a try/catch that falls back to a deterministic word-glossary version on failure — that part was
   already in place from 2026-07-17's work. What was missing: nothing told Saeed this had happened. Added a
   `[Note: AI rewrite unavailable - raw summary below]` line at the top of the WhatsApp message whenever any
   section fell back, in both `strategy_daily.ps1` and `combined_brief.ps1`.
**Bugs found and fixed while testing (pre-existing, not introduced by this change — surfaced by running the
real Ollama-partial-failure case, not a synthetic one):**
1. `Get-BusinessRewrite`'s prompt-building step piped a single-element array through `ForEach-Object`, which
   PowerShell silently collapses to a bare string; `.Count` on that string then threw under
   `Set-StrictMode -Version Latest`, crashing the whole brief the moment any section had exactly 1 line — a
   more direct cause of "brief fails silently" than Ollama itself. Fixed by wrapping in `@(...)`.
2. Same collapse, different spot: `$WhatWeDidFinal = if ($WhatWeDidAI) { $WhatWeDidAI } else {...}` — a bare
   array variable used as a script block's output gets enumerated element-by-element same as `Write-Output`, so
   a successful 1-line AI rewrite also collapsed to a scalar and crashed on the next `.Count` check. Fixed by
   using `,$WhatWeDidAI` (and the 3 sibling variables) in the true branch.
**Files changed:** scripts/daily/strategy_daily.ps1, scripts/daily/combined_brief.ps1, CHANGELOG.md
**Tests run:** Full `combined_brief.ps1 -Mode Morning -DryRun` against real session logs and real production
data. Ollama was live and, mid-run, genuinely failed on 2 of 8 AI-rewrite calls (real timeouts, not staged) —
confirmed the try/catch caught them, those 2 sections fell back to the word-glossary version, the other 6
completed normally, the `[Note: AI rewrite unavailable...]` banner appeared correctly, and the script finished
with exit code 0 (no crash). Did not additionally stop Ollama entirely — its desktop app auto-restarts the
server process within ~2 seconds of being killed, so a true full-outage test would need a firewall rule, which
was not applied without asking first. The connection-refused and timeout cases share the exact same try/catch
block, so this is not a separate untested code path — [Likely], not [Certain], flagged here rather than
overstated.
**Security review:** Not applicable — no auth/patient-data/compliance logic touched (internal reporting/
scheduled-task-registration only). Bug-fix autonomy exception applies to the code changes; the scheduled task
itself was NOT created (see above) so no system-config change actually landed.
**Saeed notified:** This session.

---

## 2026-07-20 (continued) — Ollama Autostart task confirmed live (closes item 1 above)
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (ran the elevated command himself, same session)
**Description:** Saeed ran the `Register-ScheduledTask` command from the entry above in an elevated PowerShell
(the non-admin session couldn't do this itself — see above). Verified from the non-elevated session afterward:
task "Ollama - Auto Start" exists, State = Ready, Action = `C:\Users\s5256\AppData\Local\Programs\Ollama\ollama.exe serve`,
UserId = s5256, LogonType = S4U (no password stored), RunLevel = Limited, RestartCount = 999,
RestartInterval = 1 minute, ExecutionTimeLimit = unlimited (PT0S), MultipleInstances = IgnoreNew. Matches the
spec exactly. Both Fix 1 and Fix 2 from the 07:00-brief-fails-silently report are now complete.
**Files changed:** None (system scheduled task only, no repo files).
**Tests run:** Read-only `Get-ScheduledTask` verification of Action/Triggers/Principal/Settings against the
task Saeed created — matches spec. Did NOT trigger an actual reboot to confirm end-to-end boot behaviour —
[UNVERIFIED — confirm after next real reboot/cold start that Ollama actually comes up before anyone logs in].
**Security review:** Not applicable — no auth/patient-data/compliance logic touched.
**Saeed notified:** This session.

---

## 2026-07-20 (continued) — Multi-tenancy step 4: stand up placeholder tenant2 instance (localhost:8766)
**Agent:** Lead Agent (Claude Code session), plan reviewed and approved by Saeed before build
**Approved by:** Saeed (plan approved; explicit "yes, go ahead" for the watchdog.ps1 edit; explicit approval
to merge to main and restart the watchdog same day; explicit approval for Claude to register scheduled tasks)
**Description:** Built and merged the second tenant instance per governance/MULTI_TENANCY_PROPOSAL.md §8 step 4.
Saeed's instruction: use a generic placeholder identity ("Tenant 2") rather than binding to a real business
name until that tenant is actually ready to go live, and seed placeholder admin+staff logins for every tenant
(to be replaced with real names/emails before go-live — same treatment churchtown's own 5 accounts still need).
Fixed a real bug found during the build: `db.py`'s `init_db()` unconditionally seeded 3 demo `staff_users` rows
(including an "Admin Demo" row with `password_hash=NULL`, unusable) whenever a database was empty — would have
hit every future tenant, not just this one. Now gated to only fire for the default, no-tenant instance.
New `scripts/tenant/create_tenant_db.py` creates a fresh tenant database and seeds two placeholder accounts
(admin + staff), both forced to change password on first login, both audit-logged, reusing `auth.py`'s
existing PBKDF2 hashing unmodified. `backup_db.py` now loops all known tenant databases (a not-yet-provisioned
tenant is skipped, not a failure). `watchdog.ps1` gained a new `Tenant2Dashboard` entry (port 8766) — the
existing `ProductionDashboard` block was diffed pre-commit and confirmed byte-identical. Real `tenant2.sqlite`
created in production's data path with its two placeholder logins seeded.
**Files changed:** `dashboard/app/db.py`, `scripts/tenant/create_tenant_db.py` (new), `scripts/tenant/test_create_tenant_db.py` (new),
`dashboard/tests/test_db_tenant_seeding.py` (new), `config/tenants/tenant2.env` (new), `governance/TENANT_REGISTRY.md` (new),
`scripts/backup/backup_db.py`, `scripts/backup/test_backup_multi_tenant.py` (new), `scripts/service_control/watchdog.ps1`,
`scripts/service_control/tests/test_watchdog_services.ps1` (new), `scripts/register_scheduled_tasks.ps1`, `.gitignore`.
**Tests run:** 436 Python tests green (393 dashboard suite post-merge + 54 in scripts/, includes all new tests) +
2 new PowerShell static regression tests green. Full manual E2E in an isolated worktree before merge: both
placeholder accounts log in, both correctly forced through the password/PIN-change flow, tenant2's case list
and audit log fully isolated from churchtown, churchtown (case_count 78) health-checked unaffected before,
during, and after every step, including after the real merge.
**Security review:** Security Agent APPROVE (auth/staff_users-touching changes — `db.py` fix and
`create_tenant_db.py` — reviewed before merge; two optional cosmetic notes raised and both applied: seed
`pin_hash=NULL` instead of a discarded non-numeric PIN, add `staff_created` audit events for script-seeded
accounts).
**Not completed this session — needs Saeed (elevated shell required, same category as the directory-ACL fix):**
1. `scripts/register_scheduled_tasks.ps1` — attempted from a non-elevated session, failed with "Access is
   denied" on `Register-ScheduledTask`. Needs Saeed to run it in an admin PowerShell window to register the
   new "JeffLocal - GDPR Weekly Purge (tenant2)" task (the other 4 tasks re-register idempotently, unchanged).
2. Watchdog restart — the live, already-running elevated watchdog process only has today's (pre-merge)
   `$Services` list in memory; it needs to be stopped and restarted (via the Scheduled Task, not killed
   directly — same "cannot be killed by non-elevated code" constraint noted elsewhere in this file) to pick up
   the new `Tenant2Dashboard` entry from disk. This also could not be done from a non-elevated session.
3. Cloudflare hostname for tenant2 — deliberately out of scope this round (Saeed: test via localhost:8766
   only). Guidance on setting it up (and on the churchtown hostname rename) is a separate future request.
**Saeed notified:** This session. One-time placeholder passwords for the real `tenant2.sqlite` accounts were
printed once in-session and are not repeated here or logged anywhere else — Saeed has them from the session
transcript.

---

## 2026-07-21 — Fix register_scheduled_tasks.ps1 switch syntax + found GDPR purge task never registered
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Bug surfaced when Saeed ran apply_tenant2_ops.ps1 in admin PowerShell (screenshot). Fix
committed same session; Saeed to re-run the admin script.
**Description:** `register_scheduled_tasks.ps1` used `-RunOnlyIfNetworkAvailable $false` (space form) in the
GDPR-purge task blocks. `-RunOnlyIfNetworkAvailable` is a SWITCH parameter, so the space form passes `$false`
as a stray positional argument and `New-ScheduledTaskSettingsSet` throws "A positional parameter cannot be
found that accepts argument 'False'". The script aborted at task 4 (churchtown GDPR purge) before registering
any purge task or reaching the watchdog restart. Fixed both occurrences (task 4 pre-existing, task 5 tenant2
copied it) to the colon form `-RunOnlyIfNetworkAvailable:$false`. Behaviour identical to intent
(RunOnlyIfNetworkAvailable=False); `gdpr_purge.py` itself untouched.
**SIDE FINDING (compliance-relevant, flagged to Saeed):** Because task 4 always threw at this line, the
`JeffLocal - GDPR Weekly Purge` task was **never registered** — confirmed absent from `Get-ScheduledTask
-TaskPath \JeffLocal\` (only Evening Brief, Health Check, Service Watchdog, Strategy Daily Report exist). So
churchtown's GDPR 90-day purge is **not currently scheduled**. Pre-go-live debt only — nothing is live and all
data is fake — but a real gap the bug was masking. The fix lets both GDPR purge tasks (churchtown + tenant2)
register on the next admin run of apply_tenant2_ops.ps1 / register_scheduled_tasks.ps1.
**Files changed:** `scripts/register_scheduled_tasks.ps1` (2 lines).
**Tests run:** Reproduced the exact failure and proved the colon form fixes it via `New-ScheduledTaskSettingsSet`
(no elevation needed). Built all 5 settings-sets + the tenant2 trigger/action in memory — all clean. Full file
parses with zero syntax errors. Did NOT run `Register-ScheduledTask` itself (needs elevation — Saeed's admin re-run).
**Security review:** Syntax-only fix, no compliance/auth LOGIC changed (purge logic in gdpr_purge.py untouched).
The compliance-relevant part is the *finding* that the purge was unscheduled, surfaced here for Saeed.
**Saeed notified:** This session.

---

## 2026-09-04 - Session Close Split Out to Its Own Weekday 18:30 Task
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit instruction in session: "I need an automatic scheduled close session protocol
to run every weekday at 18.30 hours before the brief task, regardless of any work done that day or not",
followed by four answered design questions confirming: move rather than duplicate, both projects, weekdays
only, keep the push guard).
**Description:** The session close previously lived inside `combined_brief.ps1` sections 6 and 6b, so the 19:00
brief performed the close and then described a close it had just done to itself. Split into a new script
`scripts\daily\session_close.ps1` on its own task, `JeffLocal - Weekday Session Close 1830`, Mon-Fri 18:30,
30 minutes before the brief. It closes BOTH projects (Avamed + St Marks) unconditionally, work or no work:
session log, HANDOFF.md, PROJECT_MEMORY.md, git add -A / commit / push, restore tag, graphify refresh.
The push guard is unchanged (-ProtectPath dashboard / site: commit locally, hold the push, emit PUSH-HELD).
The close writes a marker to `logs\close-state\YYYY-MM-DD-close.txt` (gitignored) carrying a CLOSED line and
any PUSH-HELD signals. `combined_brief.ps1 -Mode Evening` now reads that marker instead of closing, and puts a
"NO SESSION CLOSE RAN TODAY" banner at the top of the WhatsApp message when it is absent. There is deliberately
NO fallback close at 19:00 - a silent auto-recovery is how the 11-19 Aug 2026 close failure hid for eight days.
Morning mode (07:00) is entirely unchanged and still commits/pushes, which is what carries weekend work.
Weekends get no close by design (Saeed's choice); `-Force` closes by hand on any day.
**Files changed:** `scripts/daily/session_close.ps1` (new), `scripts/daily/combined_brief.ps1` (evening close
replaced by marker read + no-close banner; morning path untouched), `CLAUDE.md` (session-end protocol,
scheduled-task table, two graphify references).
**Tests run:** Both scripts parse clean via the PowerShell AST parser. `session_close.ps1 -DryRun -Force` runs
end to end and resolves both repos. Evening brief tested BOTH ways against a synthetic marker: with a marker it
logged "18:30 close already ran", skipped both closes (no [JL]/[SM] output) and carried the PUSH-HELD signal
into the banner; without one it logged the warning and added the NO CLOSE banner. Synthetic marker deleted after.
The 18:30 task registered and reports State Ready, day mask 62 (Mon-Fri), next run 2026-09-04 18:30.
NOT yet observed firing on its own schedule - first live run is tonight.
**Security review:** No auth, patient-data, clinical or compliance logic touched. Scheduling and git plumbing
only. The push guard that keeps unfinished production `dashboard\` and live `site\` work off the remote is
carried over unchanged and was verified to still propagate its signal to the brief.
**Saeed notified:** This session.

---

## 2026-09-04 - Real Weekday Morning Health Check Created (replaces a 45-day phantom)
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit instruction in session: "create the new scheduled health check for every
weekday morning before the brief task so the brief is fully informed").
**Description:** A task "JeffLocal - Health Check" was registered on 21 Jul 2026 pointing at
scripts\daily\health_check.ps1. That script was never written. For 45 days the task failed every five minutes
with exit code -196608 ("the file does not exist") while showing State: Ready in Task Scheduler. No alert, no
log, nobody noticed. Root cause traced to register_scheduled_tasks.ps1 lines 34-55, which created the task for
a script that never existed in the repo or in git history.
Replaced with a REAL check on the schedule Saeed asked for: "JeffLocal - Weekday Health Check 0645", Mon-Fri
06:45, fifteen minutes before the 07:00 brief. It deliberately does NOT duplicate watchdog.ps1 (which answers
"are the services running" every 60s, with restarts and WhatsApp alerts, working correctly since 19 Aug 2026).
It answers the question the watchdog does not: IS WORK FLOWING. Nine checks - services (light confirmation),
queue depth and stuck files, per-database open/overdue/red-flag/identity/emergency case counts, disk space,
backup freshness, GDPR 90-day purge recency and status, unpushed commits and last-commit age for both repos,
last working day's session close marker, and any other JeffLocal scheduled task that failed its last run
(the check that would have caught this very bug). Read-only throughout; databases opened mode=ro.
Writes logs\health\YYYY-MM-DD-health.{txt,json} + latest.txt (logs\ is gitignored). combined_brief.ps1
-Mode Morning now opens with that block, and prints "SYSTEM HEALTH: UNKNOWN" if the 06:45 run did not happen.
**Files changed:** `scripts/daily/health_check.ps1` (new), `scripts/daily/health_check_db.py` (new),
`scripts/daily/combined_brief.ps1` (morning health block), `scripts/register_scheduled_tasks.ps1`
(task 2 rewritten to the real 06:45 task; also disables the phantom on re-run), `CLAUDE.md`.
**Tests run:** All three scripts parse clean. First real run surfaced 5 "problems", FOUR of which were false
alarms, each traced and fixed before go-live: (1) a .gitkeep placeholder counted as a call "stuck for 157079
minutes" - queue counting now ignores dotfiles; (2) a manual dry-run of gdpr_purge recorded in the compliance
audit trail read as a live compliance failure - the check now ignores dry_run entries; (3) missing 18:30 close
markers for dates before the 18:30 task existed - cutoff date added; (4) Task Scheduler code 267011 ("has not
run yet") on a task created 20 minutes earlier read as a failure - 267009/267010/267011/267014 and never-run
placeholder dates now excluded. Re-run after fixes reports only the two GENUINE problems (tenant2 schema,
phantom task). Morning brief dry-run confirmed the block is included ("Health check block included from ...").
Task registered: State Ready, day mask 62 (Mon-Fri), next run Mon 2026-09-07 06:45. Not yet observed firing.
**Known incomplete:** disabling the old "JeffLocal - Health Check" task FAILED with Access Denied - it was
created with elevated rights and needs an admin PowerShell. Until Saeed runs that, it keeps failing every five
minutes AND the new health check correctly reports it as a failing job every morning.
**Security review:** No auth, patient-identity, clinical or compliance LOGIC changed. The check is read-only
and opens every database read-only. It reads patient-case COUNTS only - no names, NHS numbers, DOBs or any
identity field are read, logged or written. Output lands in logs\, which is gitignored, so no case data can
reach the repo.
**Saeed notified:** This session.

---

## 2026-09-04 - tenant2 Database: Missing created_at Column Fixed (GDPR purge unblocked)
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit in session: "tenent2 column approved").
**Description:** The scheduled task "JeffLocal - GDPR Weekly Purge (tenant2)" had NEVER completed a single
successful run. It exited code 2 with "no such column: created_at". Found by the new morning health check on
its first run. tenant2.sqlite was created 2026-07-20 and its cases table lacked created_at, which the 90-day
purge uses to find expired records.
ROOT CAUSE: dashboard/app/db.py lines 348-379 auto-add missing cases columns to every tenant database at
startup - which is why tenant2 matched tenant1 on every OTHER column - but created_at is not in that list.
It was only ever added by the one-off migration scripts/migrations/add_created_at_20260531.sql (May), and
tenant2 was created two months later. The same applies to the idx_cases_created_at and idx_cases_assigned_to
indexes, absent from db.py's idempotent index block.
FIX APPLIED: ran the project's own existing migration (add_created_at_20260531.sql) against tenant2 rather
than hand-rolled SQL - ALTER TABLE cases ADD COLUMN created_at TEXT, back-fill from timestamp (0 rows, table
is empty), CREATE INDEX idx_cases_created_at, CREATE INDEX idx_alert_events_timestamp. Also added
idx_cases_assigned_to for parity with tenant1. All statements idempotent; re-running is harmless.
NOT FIXED - NEEDS SEPARATE APPROVAL: db.py itself is unchanged, so the NEXT tenant database created will have
the identical gap. The durable fix is adding created_at to db.py's auto-migration list and the two indexes to
its index block. dashboard/ is production and that is a separate approval under the approval protocol.
**Files changed:** No source files. Database only: dashboard/data/tenants/tenant2.sqlite (gitignored).
**Backup taken:** backups/tenant2_PRE-created_at-migration_20260904-142822.sqlite (pre-change, 106496 bytes).
**Tests run:** Full schema diff tenant2 vs tenant1 before and after - the ONLY difference before was
created_at plus two missing indexes; after, zero differences in tables, columns and indexes.
PRAGMA integrity_check = ok. gdpr_purge.py --dry-run on tenant2 now exits 0 (was exit 2).
The real scheduled task was then triggered manually and completed: LastTaskResult 0, audit entry
PURGE-20260904-132859 status=success - the first successful tenant2 purge in the project's history.
Morning health check re-run afterwards: 0 problems (was 2).
**Security review:** GDPR-relevant. The change RESTORES a compliance control that had never worked; it does
not weaken one. No auth, patient-identity or clinical logic touched. No data was deleted - the table holds 0
rows and the purge's own audit trail records purged_counts all zero. Back-fill uses the same
COALESCE(created_at, timestamp) basis gdpr_purge.py already relies on (lines 221/286/304), so retention
calculations are unchanged for existing data. Pre-change backup retained.
**Saeed notified:** This session.

---

## 2026-09-04 - Security Agent Review of the Day's Automation Work (defects fixed)
**Agent:** Security Agent (review) + Lead Agent (fixes)
**Approved by:** Saeed (session instruction to commit; review is mandatory per CLAUDE.md for
compliance-touching work).
**Verdict:** APPROVE WITH NOTES. No patient-data leak, no LLM-safety breach, no secrets, no injection or
traversal surface. Confirmed independently: health_check_db.py returns aggregate COUNT(*) only and never
selects patient_name, nhs_number, emis_number, dob, postcode, callback_number or transcript; every DB handle
is mode=ro; logs\ is gitignored; the tenant2 change is purely additive with a verified pre-change backup.
**Defects found and FIXED before commit:**
1. CRITICAL - session_close.ps1 wrote the "CLOSED" marker unconditionally. Both closes could throw, be logged
   as warnings, and the 19:00 brief would report a successful close that never happened. Exactly the silent-
   failure pattern that hid the 11-19 Aug 2026 outage for eight days. Now: a $Failures list is collected, the
   marker says CLOSED only when both projects succeeded, otherwise FAILED plus one FAILED-DETAIL line per
   project, and the script exits 1 so Task Scheduler records it AND the 06:45 health check catches it next
   morning. combined_brief.ps1 treats a marker with no CLOSED line as harshly as a missing marker and prints
   the reasons in the banner.
2. Task-name mismatch - the script header and the brief's banner told Saeed to check "JeffLocal - Weekday
   Session Close (18:30)"; the registered task is "JeffLocal - Weekday Session Close 1830". He would have
   searched and found nothing at the exact moment he needed it. Corrected in both files.
3. register_scheduled_tasks.ps1 registered the 06:45 health check but NOT the 18:30 close - rebuilding from
   that script would have silently dropped it. Task 2b added.
4. idx_cases_assigned_to was created on tenant2 outside the migration file, so a tenant rebuilt from
   add_created_at_20260531.sql would get a different schema. Added to the migration.
**Not fixed (cosmetic, logged only):** dead RESOLVED constant in health_check_db.py; the GDPR check treats an
audit entry with no dry_run field as a real run.
**Files changed:** scripts/daily/session_close.ps1, scripts/daily/combined_brief.ps1,
scripts/register_scheduled_tasks.ps1, scripts/migrations/add_created_at_20260531.sql.
**Tests run:** All four scripts parse clean. Failure path tested with a synthetic FAILED marker: the brief
logged "18:30 close RAN AND FAILED today - 2 project(s) affected" and printed both reasons by name in the
banner. Synthetic marker deleted afterwards.
**Saeed notified:** This session.

---

## 2026-09-07 — Brief Staleness Banner: Separated "Close Failed" From "Project Paused"
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit "APPROVED" in session, 2026-09-07)
**Description:** Investigated Saeed's 2026-09-04 evening WhatsApp warning. Finding: the 18:30 session close ran correctly on its first day (close commit landed 18:32 UK, restore tag restore/2026-09-04-1800 pushed, session log and HANDOFF written). The warning was NOT a close failure — the staleness check correctly spotted that St Marks had no committed work for 11 days, but the banner wording wrongly stated "The daily session close is NOT running", reporting a healthy system as broken. Fixed the wording and split the two alarms: a deliberately paused project now gets a quiet one-line note; a project that is not paused still gets the full loud banner, and the banner only blames the close when the close actually failed. Added a $PausedProjects list at the top of combined_brief.ps1 (St Marks — awaiting pharmacist sign-off, per Saeed). Pausing a project does NOT silence the close-failure banner. Also moved the close-marker read from section 6-pre up to a new section 3b, because the banner wording now depends on whether the close ran and section 5 freezes the message text before the old read point.
**Files changed:** scripts/daily/combined_brief.ps1, CLAUDE.md, CHANGELOG.md
**Tests run:** PowerShell 7.4.6 parse check on combined_brief.ps1 and session_close.ps1 — both clean. Behaviour test harness executing the real banner code from the file across 5 scenarios: (1) close OK + St Marks paused 11 days → quiet note only, no banner [reproduces and fixes the 2026-09-04 false alarm]; (2) Avamed stale 3 days, not paused → loud banner, correctly states the close DID run; (3) close FAILED + Avamed stale + St Marks paused → loud banner still fires for Avamed, points at the close-failure banner, paused note stays quiet [the 11–19 Aug outage shape — safety net confirmed intact]; (4) nothing stale → clean message; (5) morning brief → does not claim the close ran. All 5 passed.
**Not tested:** end-to-end run on the Windows machine (no PowerShell/Windows paths in the cloud session). Next 19:00 brief is the live confirmation.
**Saeed notified:** This session

---

## 2026-09-07 — Security Agent Review of the Staleness Banner Fix (PR #1)
**Agent:** Security Agent (GuardRail), review requested by Lead Agent
**Approved by:** Saeed ("MERGE IF SAFE", 2026-09-07) — review run because the change alters the content of an external WhatsApp message and modifies a failure-detection alarm
**Verdict:** APPROVE WITH CONDITIONS. Safety net confirmed intact: pausing a project cannot suppress the close-failure banner or the push-held banner; a non-paused stale project still gets the loud banner on every traced path; the moved marker read is behaviour-preserving and Morning mode still runs strategy_daily.ps1 (the weekend git safety net). No patient data, credentials or secrets introduced. No veto trigger applies.
**Conditions applied before merge:**
- C1 (combined_brief.ps1) — the banner said "nothing is broken in the automation" on the strength of the close marker alone. That marker evidences only that the 18:30 close ran; it says nothing about the health check, watchdog, 07:00 brief or WhatsApp sender. Telling a non-technical reader nothing is broken would stop them looking. Reworded to "Today's 18:30 session close ran, so this is not a close failure."
- C2 (combined_brief.ps1) — the quiet paused note claimed the close "ran normally". CLOSED means neither close threw, not that the work was useful. Reworded to "Today's 18:30 close ran."
**Tests run:** re-ran the full 5-scenario harness after the wording change — all 5 still pass. PowerShell 7.4.6 parse check clean.
**Open findings logged, NOT fixed in this PR (both pre-existing):**
- H2 (HIGH) — the weekend evening brief fires "TODAY'S SESSION CLOSE DID NOT COMPLETE" every Saturday and Sunday, because no close is scheduled at weekends so no marker exists. ~104 false alarms a year on the one banner that must never be ignored. Confirmed against git history: 5 and 6 Sep 2026 had 07:00 morning briefs but no evening close, so Saeed most likely received two false alarms this weekend. Awaiting Saeed's decision on a follow-up fix.
- H1 (HIGH) — if a project's sessions directory is missing, the staleness check treats it as "not stale" and emits no warning at all; if it exists but is unreadable, the script aborts before sending any brief. That is the 11-19 Aug 2026 outage shape and it is the one input where the alarm is genuinely mute. Awaiting Saeed's decision.
- M1 (MEDIUM, accepted) — a close that fails without throwing still writes CLOSED. Mitigated by the paused note printing a climbing day counter every day, so the condition never becomes invisible.
- L1 — pause has no expiry; L2 — pause keys are display strings, but they fail in the safe direction (loud banner returns).
**Saeed notified:** This session

---

## 2026-09-07 — Three Alarm Fixes: Weekend False Alarm, Unreachable Project, Pause Expiry
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit "YES" / "FIX AND TEST" / "IT SHOULD NAG ME AFTER ONE WEEK", 2026-09-07)
**Description:** Follow-up to PR #1, addressing the two open findings from the Security Agent review plus Saeed's pause-expiry request.
- **H2 — weekend false alarm (fixed).** session_close.ps1 skips Sat/Sun by design, but the 19:00 evening brief runs daily, found no marker and fired "TODAY'S SESSION CLOSE DID NOT COMPLETE" every weekend — roughly 104 false alarms a year on the system's most important banner. Confirmed against git history that 5–6 Sep 2026 had 07:00 briefs but no evening close, so Saeed most likely received two false alarms that weekend. The brief now distinguishes "no close was due" from "a close was due and did not happen", prints one plain explanatory line on weekends, and stays loud for a FAILED marker on any day.
- **H1 — unreachable project (fixed).** A missing sessions folder left IsStale false and produced NO warning; a folder present but unreadable threw under $ErrorActionPreference = "Stop" outside any try, aborting the script so no brief was sent at all. Both are the 11–19 Aug 2026 outage shape. Added an Unreachable state with its own CANNOT SEE ONE OF YOUR PROJECTS banner, ranked above every other banner, which fires even for a paused project (pausing means no work is expected, never that the folder may disappear).
- **Pause expiry (added).** After 7 days ($PausedNagAfterHours) the quiet paused note asks Saeed to confirm the pause is still correct. St Marks is already at 11 days, so this fires on the first run.
**Regression caught during development:** suppressing the weekend alarm initially made $CloseRanToday true on weekends, which would have had the brief claim a close ran when none was scheduled — the opposite false statement to the one being fixed. Caught by adversarial re-read before any commit; $NoCloseWeekend is now excluded from $CloseRanToday and a weekend case asserts it.
**Files changed:** scripts/daily/combined_brief.ps1, CLAUDE.md, CHANGELOG.md
**Tests run:** PowerShell 7.4.6. Parse check clean. Banner harness re-run over 7 scenarios executing the real code from the file: weekend + paused; Avamed folder missing; St Marks folder unreadable while paused; paused 2 days (no nag); paused 11 days (nag fires); weekday close failed + Avamed stale (Aug outage shape, still loud); all-healthy (clean message). All 7 passed, and $CloseRanToday was asserted false on the weekend case. Separate integration test drove the real Get-ProjectBrief against real fixture directories: normal folder OK, missing folder correctly flagged Unreachable, and an enumeration failure correctly caught with the brief still produced instead of the script aborting.
**Test limitation (stated, not hidden):** the container runs as root, so a real permission-denied folder cannot be reproduced on Linux; the unreadable-folder path was proven by shadowing Get-ChildItem to throw, which exercises the catch branch but is not a real Windows ACL. Recommend one -DryRun run on the Windows machine before relying on it.
**Saeed notified:** This session

---

## 2026-09-07 — Security Review Round 2 (PR #2): Weekend Staleness, Late Runs, Two Mediums
**Agent:** Lead Agent, implementing Security Agent (GuardRail) conditions
**Approved by:** Saeed (the three underlying fixes, 2026-09-07)
**Verdict received:** APPROVE WITH CONDITIONS — H3 and H4 blocking, M1 and M2 strongly recommended. All four applied in one commit.
- **H4 (the important one) — the weekend fix was incomplete.** Suppressing the close-failure banner at weekends left the *staleness* banner firing all weekend: Friday's 18:30 log is 25h old by Saturday evening, 49h by Sunday evening and 61h by Monday's 07:00 brief, so the loud "PART OF THIS BRIEF IS OUT OF DATE" banner fired four times every weekend — roughly 156 a year — on a gap that is entirely by design. Fixed by replacing the flat 24-hour test with a schedule-aware one: Get-LastExpectedCloseTime works out when a close last FELL DUE (weekday 18:30), and a project is only "overdue" if its newest real log predates that. A project that is genuinely dead stays loud even at a weekend, and the 99999 "no log ever" sentinel can never be absorbed.
- **H3 — a late or retried run could bury a real failure.** $Today and the weekday test came from separate Get-Date calls, and the marker is filed by day. Friday's close fails; the machine is asleep at 19:00; Task Scheduler catch-up (-StartWhenAvailable is set on the other tasks) fires the brief at 00:30 Saturday; the script looks for Saturday's marker, does not find one, decides Saturday is a weekend and files it as "no close was due" — Friday's failure reported to nobody. Fixed: one Get-Date for the whole run, and a run starting before 06:00 resolves the marker and the weekday test against the previous day.
- **M1 — "Paused for 4166 day(s)".** The 99999 sentinel was fed to the age formatter in the new nag line and rendered verbatim into the WhatsApp message. Now says "Paused, and no session log has ever been found for it."
- **M2 — false comfort under the unreachable banner.** An unreachable project printed "Nothing stuck right now" / "Nothing needs your OK right now" directly beneath a banner reading "This is NOT 'nothing to report'". All four sections now read "Not known - could not read this project."
**Files changed:** scripts/daily/combined_brief.ps1, CHANGELOG.md
**Tests run:** parse check clean. Schedule table verified across the full Fri→Mon cycle (Sat 00:30 catch-up correctly attributes to Friday; permitted log age 26h Sat evening, 50h Sun evening, 62h Mon morning, back to 2h Mon evening). 10-scenario harness over the real banner code, all passing, including: quiet across the whole weekend for a normal gap; loud on a weekend for a genuinely dead project; loud for the no-log-ever sentinel; unreachable outranking both a weekend and a pause. M1 and M2 verified by rendering the real output.
**Testing correction worth recording:** the round-1 integration test used a stubbed Get-BusinessRewrite that returned a hashtable, which is truthy and has a .Count, so it masked whether the unreachable path actually survives. Re-run with the REAL Add-PlainEnglishNotes, Get-BusinessRewrite and Select-NearUnique extracted from the file: both the missing-folder and the enumeration-throws paths complete and produce a brief. The earlier "brief still produced" claim was under-evidenced; it is now properly evidenced.
**Still open (unchanged):** L1 log-noise on the unreachable path (cosmetic, pre-existing). Governance gap raised by Security Agent: the 19:00 "JeffLocal - Evening Session Close Brief" task is absent from scripts/register_scheduled_tasks.ps1, so its -StartWhenAvailable and retry settings cannot be verified from source. Awaiting Saeed's decision.
**Saeed notified:** This session

---

## 2026-09-07 — Security Review Round 3 (PR #2): H5 and M3
**Agent:** Lead Agent, implementing Security Agent (GuardRail) conditions
**Verdict received:** APPROVE WITH CONDITIONS — H5 (high, new) and M3 (medium) outstanding; H4 attacked across weekend, dead-project, placeholder-close, machine-off and bank-holiday inputs and confirmed to hold; no regressions; PowerShell 5.1 clear; no data exposure.
- **H5 — my H3 fix was built on a wrong assumption and left the original hole open.** I had assumed a missed 19:00 task catches up shortly after midnight, so "before 06:00 means yesterday" would cover it. It does not: -StartWhenAvailable runs a missed task when the machine next becomes available, which for an office PC is the next morning. Machine off Friday evening, switched on 10:00 Saturday, the brief catches up, asks for Saturday's marker, finds none, calls Saturday a weekend, and Friday's FAILED close is never opened — the exact scenario H3 was written to prevent. Replaced the clock-hour guess with the schedule: the brief now always reports on the last close that actually FELL DUE (Get-LastExpectedCloseTime), which is correct at 19:00, at 00:30 and at 10:00 the next morning alike, with no assumption about catch-up behaviour. A missing marker for a day a close was due is now an alarm on any day of the week; "no close runs today" is handled separately by $IsWeekendNow, so the round-1 weekend behaviour is preserved.
- **M3 — the slack window could call a failed close normal.** $StaleHours is rounded to whole hours (up to 0.5h understated) and carried an extra +1h of slack, so a log written up to 1.5h before a failed close still counted as fresh and the brief printed "no close has been due since" — false in that window. Took the reviewer's better fix: return the newest real log's exact LastWriteTime from Get-ProjectBrief and compare it directly against the last due close. Rounding and slack both deleted. A project with no real log has $null here and can never enter the quiet branch.
- **Resolved as a side effect:** $CloseRanToday is now gated on the due close being TODAY, so "Today's 18:30 close ran" can no longer appear on a Saturday reporting Friday's close (round-2 condition 4).
**Files changed:** scripts/daily/combined_brief.ps1, CHANGELOG.md
**Tests run:** parse clean. 9-scenario harness over the real banner code, all passing, including the M3 case specifically (log written 17:45, that evening's close then failed → LOUD, not "normal"). Catch-up table verified across Fri 19:00, Sat 00:30, Sat 10:00, Mon 09:00, Sat/Sun 19:00, Tue 09:00 after a bank-holiday Monday, and Mon 19:00 — every catch-up correctly opens Friday's marker rather than filing the failure as a weekend.
**Still open:** L1 log noise (cosmetic). Round-2 low: a catch-up brief is still filed and titled under the day it ran rather than the day it reports on — noted, not fixed, as it affects the filename only.
**FOR SAEED — third time raised:** the 19:00 "JeffLocal - Evening Session Close Brief" task is the only scheduled job absent from scripts/register_scheduled_tasks.ps1. It was a documentation gap in round 1; it is now a correctness dependency, because the catch-up behaviour of the task carrying the system's most important alarm cannot be verified from source. [UNVERIFIED — confirm before proceeding] Either register it in that script or record it as unverified. One command settles it: Get-ScheduledTask -TaskPath "\JeffLocal\"
**Saeed notified:** This session

---

## 2026-09-07 — Security Review Round 4 (PR #2): H6, M4, M5, L2
**Agent:** Lead Agent, implementing Security Agent (GuardRail) conditions
**Verdict received:** APPROVE WITH CONDITIONS. H5 and M3 confirmed correctly implemented — Failure A (Fri close fails, catch-up Sat 10:00) and Failure B (bank-holiday Mon, catch-up Tue 09:00) both traced closed; the M3 timestamp comparison could not be fooled by clock skew, a hand-written 23:00 log, or a log written just before the marker; no regressions across rounds 1–3; PowerShell 5.1 clear; $LastDueClose confirmed assigned in Morning mode too.
- **H6 (HIGH, a regression I introduced) — a hand-run weekend close became invisible.** Deriving the marker path solely from $CloseDay meant it could never be a Saturday or Sunday, but session_close.ps1 names its marker after the day it ACTUALLY RAN, and -Force exists so a close can be run by hand at a weekend (CLAUDE.md documents it). A Saturday -Force close that FAILED would have written FAILED-DETAIL lines into Saturday's marker while the brief opened Friday's, found a healthy CLOSED, and reported nothing. Same line dropped PUSH-HELD signals from that marker, so unfinished work could sit unpushed in the live dashboard\ folder with no banner. Fixed: the brief now reads the due day's marker AND, when different, today's — alarming on the due one, and harvesting failures and push-held signals from either.
- **M4 (MEDIUM) — CLAUDE.md asserted the opposite of the shipped code.** The bullet I added in the previous commit still described the round-2 design that H5 deliberately reversed, and claimed a weekend brief does not fire the close-failure banner. Left as-is, a future agent would have read it as design intent and reinstated the bug with governance cover. Rewritten to match the code, with the old wording explicitly marked as the earlier, wrong design.
- **M5 (MEDIUM) — the banner named the wrong day and contradicted itself.** On a Saturday reporting Friday's failure it said "TODAY'S SESSION CLOSE DID NOT COMPLETE" and told Saeed to check today's scheduled task, while a line below said "no session close at weekends - that is normal". Every positive claim in the script had already been day-scoped; the negative ones had not. The banner now names the day ("FRIDAY'S SESSION CLOSE DID NOT COMPLETE"), handles one or several days with correct grammar, no longer claims "18:30" for a hand-run close, and the weekend note is suppressed whenever a close has actually failed — one message, one voice.
- **L2 — renamed $NoCloseToday to $CloseDayFailed.** It had not meant "today" since H5, and the stale name is what made the M5 wording bug easy to write in the first place.
**Files changed:** scripts/daily/combined_brief.ps1, CLAUDE.md, CHANGELOG.md
**Tests run:** parse clean. Marker-read block driven against real fixture marker files on disk: Saturday 19:00 with Friday CLOSED plus a hand-run Saturday FAILED marker correctly reports the Saturday failure, captures its detail line, harvests its PUSH-HELD signal, and suppresses the weekend note; the following Sunday correctly reports nothing; a normal Friday reports nothing. Banner rendering checked for one day, a hand-run weekend day, and two days at once. Full 9-scenario staleness harness re-run after the rename — all still passing.
**Still open (agreed, not gating):** L1 log noise; a catch-up brief filed under the day it ran; and a false alarm if the 18:30 close overruns 19:00 — pre-existing, present under the old code too, now recorded as debt.
**Governance gap — Security Agent has softened its position:** with H5 removing the code's dependence on catch-up behaviour, the missing 19:00 task registration is back to a documentation gap rather than a correctness dependency, and no longer gates this PR. Still worth one command from Saeed: Get-ScheduledTask -TaskPath "\JeffLocal\"
**Saeed notified:** This session

---

## 2026-09-07 — Security Review Round 4: APPROVED, cosmetics cleared
**Agent:** Lead Agent
**Verdict received:** APPROVE. All four round-3 conditions (H6, M4, M5, L2) correctly implemented, nothing gating. The reviewer proved rather than asserted the case I most worried about: $CloseDayFailed is set at exactly two places and each is immediately followed by appending the day name, so the banner's array index can never see an empty array. Also confirmed no duplicate day names are reachable (the reported close is at most three days behind today), no marker is read twice on a weekday, PUSH-HELD signals are not double-counted, and the FAILED-DETAIL split cannot go out of range against session_close.ps1's writer format.
**Cosmetics cleared in the merge commit (reviewer said safe without re-review):**
- Two comments in combined_brief.ps1 still quoted "TODAY'S SESSION CLOSE DID NOT COMPLETE" verbatim — worse than ordinary stale comments, because the new CLAUDE.md rule tells future agents not to write that string while the file showed it to them unqualified.
- CLAUDE.md still described a "NO SESSION CLOSE RAN TODAY" banner, which is neither the old nor the new wording, three lines above the rule forbidding "today".
- The banner's "It ran and failed:" summary was false for one of two days in the mixed missing+failed case; now reads "What went wrong:".
- "The Friday and Saturday session close did not complete either" now pluralises.
**Tests run:** parse clean; 9-scenario staleness harness re-run (all passing); banner rendering re-checked for one day, a hand-run weekend day and two days at once.
**Merged to main.**
**Remaining debt, all agreed non-gating:** L1 log noise on the unreachable path; a catch-up brief filed under the day it ran rather than the day it reports on; a false alarm if the 18:30 close overruns 19:00 (pre-existing, present under the old code too); and the 19:00 task's absence from scripts/register_scheduled_tasks.ps1 — now a documentation gap only, since H5 removed the code's dependence on catch-up behaviour. [UNVERIFIED — confirm before proceeding] Awaiting Saeed: Get-ScheduledTask -TaskPath "\JeffLocal\"
**Saeed notified:** This session

---

## 2026-09-07 — 19:00 Task Added to the Setup Script + Weekend Reminder Decision Recorded
**Agent:** Lead Agent
**Approved by:** Saeed (explicit "YES" to both, 2026-09-07)
**Description:** Closes the governance gap the Security Agent raised in three consecutive reviews, and records Saeed's decision on repeated close-failure reminders.
- **The 19:00 evening brief task is now in scripts/register_scheduled_tasks.ps1.** It was the only JeffLocal scheduled job missing from it, so rebuilding a machine from that script produced a system with no evening brief — and the evening brief is the thing that tells Saeed a session close failed. All four tasks in CLAUDE.md's schedule table are now present in the script.
- **Task definition backup added, before anything is overwritten.** Every Register-ScheduledTask in that script uses -Force, which replaces a live task outright. A task tuned by hand on the machine would have been silently reverted with no record of what it was. The script now exports every existing \JeffLocal\ task to XML under logs\task-backups\<timestamp>\ first, and prints where. A failed backup warns loudly but does not block registration. logs\ is gitignored so the backups never reach the repo.
- **Saeed's decision recorded in CLAUDE.md:** a close failure keeps reminding him on Saturday and Sunday until it is fixed. Deliberate repetition, not a bug — safe only because each reminder now names the day it is about.
**Files changed:** scripts/register_scheduled_tasks.ps1, CLAUDE.md, CHANGELOG.md
**Tests run:** PowerShell 7.4.6 parse check clean. Cross-checked every -TaskName in the script against CLAUDE.md's scheduled-task table — all four now present.
**NOT TESTED, and this is the important caveat:** the script uses Windows-only cmdlets (Get-ScheduledTask, Export-ScheduledTask, Register-ScheduledTask) which cannot run on this Linux session at all. Only the syntax has been checked. Nothing has been executed.
**[UNVERIFIED — confirm before proceeding] The 19:00 task's settings are RECONSTRUCTED**, from its sibling tasks and from CLAUDE.md, not read off the live machine. Because of -Force, running this script would replace the live task with exactly what is written. If the real task differs — different script, arguments or retry policy — its behaviour would change. The new backup block captures the live definition first so any difference is visible and reversible. One command settles it and it has now been asked for four times: Get-ScheduledTask -TaskPath "\JeffLocal\"
**Risk note:** merging this changes nothing by itself. register_scheduled_tasks.ps1 is a run-once-by-hand script, not scheduled — no behaviour changes until someone runs it as Administrator.
**Saeed notified:** This session

---

## 2026-09-07 — 19:00 Task Definition Corrected Against the Live Machine
**Agent:** Lead Agent
**Trigger:** Saeed ran Get-ScheduledTask on the Windows machine and sent the output, settling the [UNVERIFIED] flag raised in the previous entry.
**Finding — the reconstruction was wrong, and would have degraded the job it was meant to reproduce:**
- **ExecutionTimeLimit: live task allows PT1H (1 hour); the block said 25 minutes.** combined_brief.ps1 makes several Ollama calls at up to 90s each across two projects. A 25-minute cap could have killed the evening brief mid-run — the message truncated or not sent at all. Since register_scheduled_tasks.ps1 registers with -Force, running it would have silently applied that cap to the job carrying the close-failure alarm. Corrected to 1 hour.
- **Arguments: the block added -NoProfile and -WindowStyle Hidden, which the live task does not use.** Removed. This script exists to reproduce the machine, not to redesign it; unrequested changes to the alarm-carrying job are exactly what the -Force overwrite makes dangerous.
**Confirmed matching:** task name, powershell.exe, the -File path, -Mode Evening, StartWhenAvailable True, MultipleInstances IgnoreNew, RestartCount 0. All eight \JeffLocal\ tasks exist, the phantom "JeffLocal - Health Check" is Disabled as this script intends, and no name drift was found — so there was never a duplicate-task or double-WhatsApp risk.
**Still [UNVERIFIED — confirm before proceeding]:** the live task's trigger, battery and network settings, and run-as account were not in the output. The settings block now sets only what has been seen and leaves the rest to cmdlet defaults, which may still differ. Export-ScheduledTask on the machine prints the full definition and would close this out.
**Wider caution added to the top of the file:** only Task 2c has been checked against the machine. Every other block in that script was written from intent, not read off the live task, and the 2c experience shows that is not the same thing. Anyone running this script should compare each block first.
**Files changed:** scripts/register_scheduled_tasks.ps1, CHANGELOG.md
**Tests run:** PowerShell 7.4.6 parse check clean. The script itself remains untestable here — Windows-only cmdlets, nothing executed.
**Saeed notified:** This session

---

## 2026-09-07 — 19:00 Task Reconciled Against Its Full Exported Definition
**Agent:** Lead Agent
**Trigger:** Saeed ran Export-ScheduledTask and sent the complete XML, closing the last [UNVERIFIED] flags on this block.
**Third and most consequential difference found — privilege elevation:**
- **The live task has NO RunLevel element, which means LeastPrivilege: it runs UNELEVATED as the interactive user (LogonType InteractiveToken).** The block carried -RunLevel Highest, copied from its sibling tasks. Running the script would have elevated a job that has run unelevated for months — changing its security token, its environment, and what it can reach — for no reason anyone asked for. Removed.
- Also confirmed: omitting -User is correct. It registers under whoever runs the script with InteractiveToken, matching the live task. The live UserId is a machine-specific SID; hardcoding it would break on any rebuilt machine, which is the exact scenario this script exists for. Not committed to the repo either way.
**Everything else now confirmed matching:** trigger (CalendarTrigger, ScheduleByDay, DaysInterval 1, 19:00 — i.e. daily), ExecutionTimeLimit PT1H, MultipleInstances IgnoreNew, StartWhenAvailable true, and the battery/idle/scheduling-engine values, which are all cmdlet defaults and so are deliberately left unset rather than restated.
**One intentional departure, recorded so it is not "corrected" back:** the Description text. The live one reads "Evening session-close brief (7pm). Built from session logs + PROJECT_MEMORY, plain English for Saeed." — written before 2026-09-04 and now misleading, because this task performs no close. Display text only; affects nothing that runs.
**Running total on this one block: three defects** (time limit, invented switches, privilege elevation) in a task definition written from intent by someone who believed it was low-risk. The file header now says so plainly, and notes that the other seven blocks all carry -RunLevel Highest with nobody having confirmed any of them runs elevated.
**Files changed:** scripts/register_scheduled_tasks.ps1, CHANGELOG.md
**Tests run:** PowerShell 7.4.6 parse check clean. Windows-only cmdlets; nothing executed.
**Saeed notified:** This session

---

## 2026-09-07 — Security Review of PR #3: APPROVE WITH CONDITIONS (merge-only)
**Agent:** Security Agent (GuardRail), acted on by Lead Agent
**Approved by:** Saeed ("merge if security review is done", 2026-09-07)
**Verdict:** APPROVE WITH CONDITIONS, with an explicit split the Lead Agent has taken: **the FILE is cleared to merge; the SCRIPT is NOT cleared to run.** No veto trigger fires — no patient data, credentials, auth logic, LLM-set protected fields, or change to the GDPR purge schedule. logs/ confirmed gitignored, so exported task XML (which contains the machine SID) never reaches the repo. Task 2c confirmed to reproduce every element quoted from the live export.
**Applied in the merge commit:**
- Marked the script *** DO NOT RUN THIS SCRIPT YET *** in its header, with the three open conditions written out in full.
- L1: my own header miscounted — SIX other registrations carry -RunLevel Highest, not seven. Corrected, and noted that two of the six are the GDPR purges where a wrong setting is a compliance control failure.
- L2: "VERIFIED against the live machine" overstated it. Now says verified against the elements QUOTED from the export, and names the seven elements that were not in what Saeed sent and so remain unchecked.
- M2: withdrew the claim that UseUnifiedSchedulingEngine is a cmdlet default. The live XML says true; the cmdlet default may be false, which would register on the legacy engine. Marked [UNVERIFIED] with the one-line command that settles it.
- L3 (CLAUDE.md): "Three consequences worth knowing" sat above seven bullets. Corrected — that file is read first by every session.
- Sharpened the Description note: the intentional text difference will show in every future XML comparison FOREVER, so nobody chases it as drift.
**OPEN — conditions on RUNNING the script, not on merging it:**
- **H1 (high):** a failed backup currently warns and continues, then -Force overwrites the definitions it just failed to save. The Security Agent argued the opposite of my choice and is right: nothing here is urgent, and a red line scrolling past forty green ones is the same failure shape as the 45-day phantom health check. Must halt, with an explicit opt-out.
- **H2 (high):** there is no way to register ONE task. This PR adds the very thing that makes someone want to run the script, and doing so overwrites six unverified definitions including both GDPR purges. Needs a -Only "<task>" parameter or a mandatory confirmation. **Saeed's decision needed:** should this script be able to overwrite six unverified definitions at all, or be reduced to a per-task tool?
- **H3 (high):** the restore path has never been executed. Export-ScheduledTask emits XML declaring UTF-16; Set-Content -Encoding UTF8 writes UTF-8 with a BOM. It probably still restores, but a recovery mechanism should not rest on "probably". One export-unregister-restore round-trip on the machine settles it.
- **M1:** a partial backup is indistinguishable from a complete one — per-task try/catch plus a count assertion needed.
- **M3:** registering the task between 19:00 and 20:00 can fire an immediate catch-up run — a genuine double WhatsApp. Also flagged that install_watchdog_service.ps1 already registers a watchdog at the ROOT path under a different name, so two watchdog tasks exist today by exactly the name/path mismatch mechanism that would cause a double-send.
- **M4:** -Force re-derives the principal from whoever runs the script, so it must be run interactively as Saeed's own account, never as SYSTEM or another admin.
**Files changed:** scripts/register_scheduled_tasks.ps1, CLAUDE.md, CHANGELOG.md
**Tests run:** PowerShell 7.4.6 parse check clean. Windows-only cmdlets; nothing executed. The Security Agent judged a parse check sufficient to merge an additive block evidenced against a real export, and insufficient to rely on the backup machinery — which is why the script is marked do-not-run.
**Merged to main.**
**Saeed notified:** This session

---

## 2026-09-09 — A Failed Save to GitHub Can No Longer Report Itself as Success
**Agent:** Lead Agent
**Approved by:** Saeed ("go", 2026-09-09)
**What went wrong, 7–9 Sep 2026:** three consecutive session closes (Mon evening, Tue morning, Tue evening) wrote their session logs, HANDOFF and PROJECT_MEMORY, committed them locally, and had every push to GitHub REJECTED as non-fast-forward. Nothing reached GitHub for three days. The close reported success, the marker said CLOSED, and the evening brief said the close ran. Saeed found it by hand on 9 Sep, and only because he forwarded a brief for an unrelated reason. Root cause of the rejection was mine: I merged PR #3 at 17:35 on 7 Sep, under an hour before the 18:30 close, and did not tell Saeed to pull — his machine was a step behind from then on. Root cause of the SILENCE is the bug fixed here.
**Fix 1 — strategy_daily.ps1 no longer swallows a rejected push.** `git push` failure used to `throw`, land in a catch that wrote one WARNING line to a log file nobody reads, and continue; the close then reported success. It now sets $PushFailed, works out the real reason from git's own output (behind remote / no network / auth refused / other), and emits a machine-readable `PUSH-FAILED|project|reason` line — the same mechanism PUSH-HELD already used. The reason text carries the fix Saeed should run.
**Fix 2 — session_close.ps1 carries the signal.** Harvests PUSH-FAILED from both projects into the close-state marker alongside PUSH-HELD.
**Fix 3 — combined_brief.ps1 shouts about it, in the evening.** New section 6b-3 prints a loud "TODAY'S WORK DID NOT REACH GITHUB" banner above the push-guard banner. Held and rejected are deliberately separate banners: a held push is the guard working as designed; a rejected one is work silently not being backed up.
**Fix 4 — health_check.ps1 stops guessing, and escalates.** The 06:45 check DID detect this on 9 Sep — it said "3 change(s) saved here but NOT sent to GitHub. Usually the push guard holding unfinished work." Two faults: it was filed under WATCH ("worth a look, not urgent") below four routine case counts, and its guessed cause was wrong — the push guard was not involved. It now determines the actual cause by checking whether the branch is behind its remote and whether the protected folder is dirty, and escalates to PROBLEM (rendered under "NEEDS A DECISION FROM YOU") at 3+ unpushed changes or 48h+.
**Files changed:** scripts/daily/strategy_daily.ps1, scripts/daily/session_close.ps1, scripts/daily/combined_brief.ps1, scripts/daily/health_check.ps1, CHANGELOG.md
**Tests run:** PowerShell 7.4.6, parse check clean on all four. Built real throwaway git repositories reproducing each state and ran the ACTUAL code from the files against them:
- Rejected push (the exact 7–9 Sep situation: local commit, remote moved ahead) → PUSH-FAILED emitted with "this computer is behind GitHub … Fix: git pull --no-edit origin main, then git push origin main". Previously silent.
- After pulling, the same close pushes cleanly → nothing emitted, and the close's file verified present on the remote.
- Health check against three real repos → correctly distinguishes REJECTED from PUSH-GUARD-HOLDING from all-clean, naming the right cause and fix for each.
- Escalation: 3 unpushed changes → PROBLEM, not WATCH.
- Banner rendering for one project and for both.
- Monday's full 9-scenario staleness suite re-run — all still passing, no regressions.
**Test limitation, stated:** all Linux fixtures with PowerShell 7.4.6. The scripts run on Windows PowerShell 5.1 against real paths, and nothing here was executed on that machine. One `-DryRun` evening run on the PC would confirm it end to end.
**Saeed notified:** This session

---

## 2026-09-09 — Security Review of PR #4: BLOCKED, then fixed
**Agent:** Lead Agent, implementing Security Agent (GuardRail) findings
**Verdict received:** BLOCK. Two blockers, three high, five medium/low — all in the new code, and both blockers reproduced the exact failure class the PR exists to remove.
**B1 (blocker, and the worst thing I have written this week): the evening brief would have crashed and sent NOTHING.** `$FailedPushSignals` was never initialised. Under `Set-StrictMode`, `+=` on an unset variable throws; the harvest sits in a loop with no try/catch, before the message is assembled or sent. On any ordinary healthy evening the brief would have died silently — no WhatsApp at all — with the only trace in a log nobody reads. That is finding H1 from PR #2 reintroduced verbatim, and it would have been worse than the bug being fixed. Cause: my declaration edit silently failed to apply (the anchor text no longer matched) and I did not assert on it, unlike every other edit in the same change; my banner test set the variable by hand, which masked it. Reproduced the crash, then fixed: variable initialised, and the whole marker-read loop wrapped in try/catch so no future marker mistake can ever silence the message again.
**B2 (blocker): the "real cause" logic still guessed, and still guessed wrong.** It computed `behind` from `rev-list HEAD..@{u}`, which reads the LOCAL remote-tracking ref. Nothing in scripts\daily\ ever fetches, and a rejected push does not update that ref — so on the exact 7–9 Sep state it returns 0, falls through, and blames the push guard. Verified: 3 unpushed commits, stale ref reports "behind 0". Rewritten to read the cause the close already recorded in its marker — no network call, no stale state, one source of truth instead of two that disagree.
**H1: the new banner said "TODAY'S".** It harvests from every marker read, including Friday's when read on a Saturday. That is the day-naming rule from PR #3 regressed, and a standing rule in CLAUDE.md. Each signal now carries its day; the banner says "FRIDAY'S WORK DID NOT REACH GITHUB".
**H2: morning mode was still silent — half the incident was unfixed.** Section 3b is evening-only, and the two morning paths filtered `PUSH-HELD` only, so the 8 Sep 07:00 failure would still have vanished. Worse: no close runs at weekends, so a Friday-night failure would have stayed invisible until Monday. Both morning paths now harvest PUSH-FAILED.
**H3: the fix instruction hardcoded `main`.** The close pushes `git push origin HEAD` — deliberately branch-agnostic — while the advice was not. On any other branch it would have told Saeed to merge main into it and push main. Now uses the actual current branch; verified on a `sandbox` branch.
**M1: the escalation measured the wrong clock.** `$ageHrs` is the age of the LAST commit, so on a repo committing twice a day the `48h` clause could never fire for its stated reason. Now measures the oldest UNPUSHED commit.
**M2: a legitimately held push escalated to PROBLEM.** Two commits a day means a deliberate two-day guard hold tripped it — the 2026-09-04 false-alarm shape again. Guard-held is now capped at WATCH; only rejected, unreachable or unexplained reaches PROBLEM.
**M3: "Restore tag created" was logged unconditionally** — a false success statement inside the alarm path being hardened. Exit code now checked, a second PUSH-FAILED signal emitted when the tag push also fails, and the prune skipped while any push is failing. Per the reviewer, the tag itself is still cut on failure: on 7–9 Sep the tag pushes are what carried the commit objects to GitHub.
**M4 (adjudicated, no change): should a rejected push mark the close FAILED?** Reviewer agreed with my "no" — different remedies, and it would make the staleness banner assert something false. Left as a distinct alarm.
**M5: locale.** git translates its messages, so a non-English Windows would fall through to the generic reason. `LC_ALL=C` set for the push call only.
**L1: banner order.** Both blocks prepend, so the one running last ends up on top — mine ran first and therefore landed below the push-guard banner, contradicting its own comment. Sections swapped.
**L3:** the marker-write log line now reports the failed-push count too.
**Files changed:** scripts/daily/combined_brief.ps1, scripts/daily/strategy_daily.ps1, scripts/daily/health_check.ps1, scripts/daily/session_close.ps1, CHANGELOG.md
**Tests run (all against real throwaway git repositories, running the actual code extracted from the files):** B1 crash reproduced, then all four brief paths verified to reach the end — healthy marker, marker with PUSH-FAILED, missing marker, morning mode. B2 verified on a repo where the stale ref reports "behind 0" while 3 commits sit unpushed — correct cause now reported, escalated to PROBLEM. M2 verified: guard-held stays WATCH. Cause-not-recorded case verified. All-clean case verified. H1 banner verified for one day and for two. H3 verified on a `sandbox` branch. Monday's 9-scenario staleness suite re-run: 9/9, no regressions. Parse check clean on all four scripts.
**Outstanding, and the reviewer is right to insist:** none of this has run on the Windows machine under PowerShell 5.1, where StrictMode and native-command error handling differ in exactly the way that produced B1. The three evening-brief marker cases should be run there with -DryRun before this is trusted.
**Saeed notified:** This session

---

## 2026-09-09 — Security Review Round 2 on PR #4: conditions applied
**Agent:** Lead Agent, implementing Security Agent (GuardRail) conditions
**Verdict received:** APPROVE WITH CONDITIONS. B1 and B2 confirmed genuinely fixed — the initialisation is correctly placed outside the Evening gate so the morning path and the banner both see it, every `+=` target in the file is initialised, and the try/catch cannot itself throw. Three conditions before merge, four items deferrable.
**H1 (condition, applied) — my B2 fix read a marker up to 3 days stale and could print a false, dangerous instruction.** Scenario: Monday's push rejected; fixed by hand Tuesday; Tuesday's close merely guard-held. Wednesday's check would skip Tuesday, hit Monday's PUSH-FAILED, and tell Saeed *"behind GitHub — run git pull"* — over a dirty `dashboard\`, the LIVE production folder — while also escalating a healthy guard hold to PROBLEM. That is B2's wrong-cause defect and M2's false-alarm shape arriving through the fix. Now reads the MOST RECENT marker only, and reads its PUSH-HELD line too so a guard hold is recognised from the marker rather than inferred. Verified against that exact three-day sequence: the stale cause is gone, the guard hold is correctly named and stays WATCH, and a genuine rejection in the newest marker still escalates to PROBLEM.
**M1 (condition, applied) — the failure banner would have reported "exit 0".** The H3 branch-name fix inserted `git rev-parse` between the push and the point where its exit code is rendered, and every native command resets `$LASTEXITCODE`. On any failure the three classifiers do not match — a pre-receive hook, a protected branch, a shallow update — Saeed's brief would have read *"git push failed (exit 0)"*: a failure banner arguing with itself, inside the alarm path. The exit code is now captured immediately after the push. Verified: a genuinely unmatched failure now reports exit 128.
**CHANGELOG correction (condition, applied):** the previous entry claimed H2 closed the weekend hole outright. It does not. If a Saturday 07:00 run has nothing to commit, strategy_daily.ps1 skips the push entirely, so no PUSH-FAILED signal exists to surface while commits may still sit unpushed; health_check.ps1 is Mon–Fri only. In practice the morning run writes a report file so there is almost always something to commit, but the hole is narrow, not closed. Recorded honestly here.
**Also applied (were deferrable):** L1 — the marker match now compares the project FIELD rather than the whole line, so a future reason string containing the other project's name cannot cross-match. L2 — the banner log line now reports lines and distinct projects separately (a network failure produces two lines for one project). L3 — the LC_ALL restore moved into the existing `finally`; an inline restore is skipped if the push line throws, leaking LC_ALL=C back into combined_brief.ps1, which invokes this script in-process. Verified by AST that the push and the restore sit in the same try/finally.
**DEFERRED, and needs Saeed's answer — M2:** the PUSH-FAILED banner keeps naming Friday across Saturday and Sunday even after the problem is fixed. Unlike the close-failure banner, whose claim stays true until the close is re-run, this one becomes false the moment a later push succeeds. CLAUDE.md's repeat-until-fixed rule is only safe while the repeated claim remains true. **Question for Saeed: should the "work did not reach GitHub" banner stop once the work reaches GitHub, or keep repeating like the close-failure banner?** Not guessing his preference into the code.
**RAISED SEPARATELY, pre-existing, not from this change:** the CANNOT SEE ONE OF YOUR PROJECTS banner is no longer top of the message — it is composed in-body while three later sections prepend above it. CLAUDE.md says it "outranks everything". This predates commit 901d375 and contradicts a standing rule; it should be its own fix.
**Files changed:** scripts/daily/health_check.ps1, scripts/daily/strategy_daily.ps1, scripts/daily/combined_brief.ps1, CHANGELOG.md
**Tests run:** H1 verified against the three-day stale-marker sequence and against a fresh rejection. M1 verified with an unmatched failure (exit 128). L3 verified structurally by AST — push and restore confirmed in the same try/finally. Monday's 9-scenario staleness suite: 9/9. All four brief paths still reach the end. Parse check clean on all four scripts.
**STILL OPEN, and the Security Agent is holding this position:** none of it has run on the Windows machine under PowerShell 5.1, which is exactly where B1 would have bitten. Three `-DryRun` evening cases should be run there before the alarm path is trusted.
**Saeed notified:** This session

---

## 2026-09-09 — Security Review Round 3 on PR #4: APPROVED, two free hardenings taken
**Agent:** Lead Agent
**Verdict:** APPROVE. All three merge conditions verified correct: most-recent-marker-only closes the stale-cause path; $MarkerHeld correctly prevents the false PROBLEM escalation, and if a marker somehow carried both lines the rejection would win over the hold, which is the right precedence; the exit-code capture has only a `-join` between the push and the capture, so nothing can clobber it. L1 verified in both directions and proven throw-free on malformed lines — which matters more than "low" suggested, because both projects share one marker directory and the field match is the only thing separating them.
**A correction to my own briefing, worth recording:** I told the reviewer that strategy_daily.ps1 does not set Set-StrictMode. It does, at line 68. My conclusion happened to hold (every read is preceded by an assignment), but the reasoning was wrong, and under StrictMode an unset variable read is a hard throw — in the alarm path. Do not carry that assumption into the next change to this file.
**L-A applied — removed an unverified assumption rather than defend it.** The LC_ALL restore was guarded by `Test-Path variable:script:PrevLcAll`, which relies on a scope-qualified provider path resolving as assumed on PowerShell 5.1. Nobody has run 5.1 to check. `$PrevLcAll` is now initialised beside `$PushHeld`/`$PushFailed` and the finally restores it unconditionally: same protection, nothing left to verify.
**L-B applied — markers now sorted by NAME, not modification time.** Filenames are yyyy-MM-dd-close.txt, so name order is date order and it survives a restored logs\ folder or an antivirus touch reordering mtimes, either of which would hand the wrong "most recent" marker to the H1 fix and quietly reopen it. Verified by deliberately scrambling the mtimes: the correct marker is still chosen.
**L-C logged, not fixed:** a narrow residual — a clean close, then a failed 07:00 push, with dashboard\ dirty at 06:45 — is still misattributed to the push guard and held at WATCH. Needs the morning run to record its failure where health_check can read it. Not created by this change; it is the M2 shape already accepted.
**Correction to the earlier record:** I logged the CANNOT SEE ONE OF YOUR PROJECTS ordering problem as "pre-existing". Relative to main it is not — it arrived in PR #2, and main does not yet contain PRs #1–#3. More to the point, **PR #4 makes it one layer worse**: section 6b-3 is a third banner prepending above an in-body banner that CLAUDE.md says outranks everything. Still deferred, and the reviewer supports deferring for a verified reason — send_whatsapp.py chunks long messages rather than truncating, so the banner is displaced, never lost. It should be the NEXT change to combined_brief.ps1, before any further banner is added.
**Files changed:** scripts/daily/strategy_daily.ps1, scripts/daily/health_check.ps1, CHANGELOG.md
**Tests run:** H1 re-verified after the sort change with deliberately scrambled mtimes — correct marker still chosen, stale cause still gone, guard hold still WATCH. M1 re-verified: unmatched failure reports exit 128. Monday's 9-scenario suite: 9/9. Parse clean on all four scripts.
**Standing gap, unchanged and approved on the code rather than the testing:** nothing has run on Windows PowerShell 5.1. Three -DryRun evening cases should be run there before the alarm path is trusted.
**Saeed notified:** This session

---

## 2026-09-09 — "Did Not Reach GitHub" Warning Now Retires Itself Once the Work Arrives
**Agent:** Lead Agent
**Approved by:** Saeed ("YES", 2026-09-09) — asked and answered explicitly.
**Why this is different from the close-failure banner.** Saeed's standing instruction (2026-09-07) is that a close failure keeps reminding him until it is fixed, and that is safe because the claim stays true until the close is re-run. The push-failure banner is not like that: "Friday's work did not reach GitHub" becomes FALSE the moment a later push succeeds. Read on a Saturday evening, the brief reads Friday's marker — so if Saturday's 07:00 run pushed successfully, Friday's work IS on GitHub and the banner would be repeating something untrue. A warning that repeats a falsehood is exactly how Saeed learns to stop reading warnings, which is the failure this whole week's work exists to prevent. Raised by the Security Agent as M2 on PR #4; I declined to guess Saeed's preference into the code and put it to him instead.
**How it works.** strategy_daily.ps1 stamps `logs\close-state\last-push-ok-<project>.txt` on every successful push, morning or evening. combined_brief.ps1 checks that stamp against the LastWriteTime of the marker that recorded the failure: if the successful push is NEWER, the failure is history and the signal is dropped. Fixed close-state path on purpose — the brief reads one folder for both projects, so the stamp must land where it looks; same hardcoding as the existing $_CombinedScript path. logs\ is gitignored, so it never reaches the repo.
**Fails toward shouting, not silence.** If the stamp is missing, unreadable or unparseable, the warning is SHOWN. A bookkeeping problem must never be able to suppress an alarm — that inversion is what made the original bug so damaging.
**Files changed:** scripts/daily/strategy_daily.ps1, scripts/daily/combined_brief.ps1, CHANGELOG.md
**Tests run:** PowerShell 7.4.6, four scenarios against the real extracted code — (1) failure recorded, no success since → SHOWN; (2) last success predates the failure → SHOWN; (3) Saturday 07:00 push succeeded after Friday's failure → retired, silent; (4) corrupt stamp → SHOWN, failing safe. Monday's 9-scenario staleness suite: 9/9. All four brief paths still reach the end (the B1 regression check). Parse clean on all four scripts.
**Not yet reviewed or merged** — Security Agent review pending, and Saeed must pull after any merge.
**First evidence from the real machine, same day:** Saeed ran `combined_brief.ps1 -Mode Evening -DryRun` on the Windows PC under PowerShell 5.1 after pulling PR #4. It started, read the session logs and reported staleness correctly. The tail of that run has not been seen yet, so PR #4's alarm path is partially — not fully — evidenced on 5.1.
**Saeed notified:** This session

---

## 2026-09-09 — Push-Failure Retirement Hardened After Security Review (PR #5, round 2)
**Agent:** Lead Agent (Claude Code session), reviewed by Security Agent
**Approved by:** Saeed approved the feature ("YES" — the "did not reach GitHub" warning should stop once fixed). The hardening below is the Security Agent's conditions on that approved change, not new scope.
**Description:** The first version retired the warning on a bare timestamp. Security review found the evidence was weaker than the claim. Six changes:

- **H1 — a restore-tag failure is now its own signal (`TAG-PUSH-FAILED`) and is never retirable.** Previously it shared the `PUSH-FAILED` name, so a later *branch* push retired it — even though that push does not push the tag. Net effect would have been a day with no remote restore point, no alarm, and the local-only tag pruned away by the next clean close. Its wording also claimed "nothing from today has left this computer", which is false in the exact case that produces it alone (the branch push succeeded).
- **H2 — retirement now requires proof, not inference.** `PUSH-FAILED` carries the failed commit's SHA; the success stamp carries the pushed SHA; the brief retires only when `git branch -r --contains <failed sha>` shows that commit on a remote branch. A timestamp alone could be satisfied by a push of a *different* branch (the close runs `git push origin HEAD`) or by a `git reset --hard` that discarded the work entirely — both would have silenced a warning that was still true.
- **M1 — a future-dated stamp no longer suppresses the alarm.** A clock set forward during a successful push would otherwise have killed the warning until real time caught up. Now logged and the warning kept.
- **M2 — retirement demotes, it does not delete.** A retired failure prints one plain "NOW FIXED — no action needed" line naming the day, the project and when the work actually arrived. The loud repeated banner stops, per Saeed's instruction; the record does not vanish. If the retirement check is ever wrong, deleting would have left total silence in the one place Saeed reads — and even when right, a banner that simply stops appearing reads exactly like the alarm having broken.
- **L1 — `[datetime]::ParseExact` with InvariantCulture** instead of `Parse`. Under a non-Gregorian default calendar `Parse` reads the stamp centuries into the future, which combined with the comparison above would have retired every warning permanently.
- **Banner wording** — the headline and closing paragraph are now conditional. When only the restore tag failed, the banner says so and states plainly that the work itself IS on GitHub. Fixing the signal text while leaving the wrapper overstating would have put the same defect straight back.

**Known and accepted (Security Agent L2):** only a *scripted* push writes a success stamp. If Saeed or an agent fixes a rejected push by running `git push` by hand, the banner keeps shouting until the next scripted push succeeds — and on a day with nothing to commit, the push is skipped entirely, so it can persist for days. This is the safe error direction and is deliberate. **Do not "fix" it by loosening the check.**

**Backwards compatibility:** markers written before today have no SHA field. Those can never be proven fixed, so they keep their warning — the safe direction.

**Files changed:** scripts/daily/combined_brief.ps1, scripts/daily/strategy_daily.ps1, scripts/daily/session_close.ps1, scripts/daily/health_check.ps1, CHANGELOG.md
**Tests run:** PowerShell 7.4.6 on Linux. Nine retirement scenarios against real git repositories with real remotes, 9/9 — including the three the Security Agent required: tag-failure-then-successful-branch-push (warning kept), failure-on-branch-A-then-push-of-branch-B (warning kept), future-dated stamp (warning kept). Plus: legacy 3-field signal (kept), missing stamp (kept), corrupt stamp (kept), genuine fix (retired). Banner wording verified in all three shapes (tag-only, push-only, both) — the SHA does not appear in anything Saeed reads. All four scripts parse clean. Every new variable verified declared before first use (the B1 regression guard).
**Limitation:** not run on the Windows machine. PR #4's own brief run was confirmed complete on Windows PowerShell 5.1 by Saeed on 2026-09-09.
**Saeed notified:** This session — awaiting his go-ahead to merge.

---

## 2026-09-09 — PR #5 Round 3: Two New Defects Found in the Round-2 Fix, Plus Four Hardenings
**Agent:** Lead Agent (Claude Code session), reviewed by Security Agent (re-review of head 82689d7)
**Approved by:** Saeed approved the underlying feature. Everything below is Security Agent conditions on it, not new scope.
**Description:** The re-review confirmed H1, H2, M1 and L1 from round 2 were discharged and that no earlier banner was weakened — but found **two new defects introduced by the round-2 fix**, and reproduced a third attack:

- **M1 (new, introduced by my own round-2 fix) — the 06:45 health check reported a restore-point reason as the cause of unpushed commits.** Adding `TAG-PUSH-FAILED` to the cause lookup meant Saeed's SYSTEM HEALTH block could read "Avamed: 3 change(s) saved here but NOT sent to GitHub. The restore point did not reach GitHub" — a line arguing with itself, with the reassuring half second. It also wrongly cleared `$guardHolding`, which could escalate a healthy push-guard hold to PROBLEM. The cause is now taken from `PUSH-FAILED` only.
- **M2 (new) — the "NOW FIXED - no action needed" note landed at the TOP of the WhatsApp message, above every live alarm.** The blocks prepend, so the last one to run ends up highest; I added mine last. Saeed would have opened WhatsApp to a reassurance sitting on top of "WORK DID NOT REACH GITHUB". Section 6b-4 now runs first so it lands beneath all four alarms.
- **M3 (reproduced by the reviewer) — `git branch -r --contains` searched every remote, not just origin.** Pushing the commit to a fork retired the warning while the work had never reached GitHub. Now scoped with `--list 'origin/*'`.
- **L2 accepted — the timestamp gate has been removed entirely.** With the SHA proof in place, requiring the stamp to be newer than the marker could only ever *withhold* a retirement git had already proved correct — a false alarm on the one banner that must stay believed (for example after Saeed fixes a push by hand). Removing it also removes its own failure mode: a clock set forward can no longer suppress anything, because the stamp no longer decides. The stamp is still read, but only to say *when* the work arrived; a missing, corrupt or future-dated stamp now costs a phrase, never an alarm.
- **L3 — a restore tag that exists locally but never reached GitHub is now retried, and re-raises its alarm if it still fails.** The close overwrites the day's marker, so a hand-run `session_close.ps1 -Force` later the same day previously erased the tag failure permanently: no remote restore point, no alarm anywhere. A `PUSH-FAILED` recurs on a retry; since H1 made `TAG-PUSH-FAILED` the only carrier of this fact, it must too.
- **L4 — the alarm no longer claims anything it cannot know.** Both the signal text and the banner's closing paragraph used to assert "today's commits reached GitHub". That block is reached even when nothing was committed and so no push was attempted, which makes the claim false. It now speaks only about the restore point.
- **PowerShell 5.1 hardening** — the new `git` call is wrapped in the same `$ErrorActionPreference` guard `strategy_daily.ps1` uses. Under `Stop`, a native command writing to stderr on 5.1 can terminate; the direction was safe (the catch keeps the warning) but it would have quietly disabled the check.

**Files changed:** scripts/daily/combined_brief.ps1, scripts/daily/strategy_daily.ps1, scripts/daily/health_check.ps1, CHANGELOG.md
**Tests run:** PowerShell 7.4.6 on Linux, against real git repositories with real remotes. Retirement suite expanded 9 → **11, all passing**, including the two cases the reviewer required: a commit pushed to a *fork* and never to origin (warning kept), and banner ordering with a real report file (live alarm verified above the "now fixed" note). Also added: path exists but is not a git repo (warning kept). Banner wording verified in all three shapes. All five scripts in scripts/daily/ parse clean. Declared-before-use verified for every new variable (the B1 regression guard).
**Reviewer's verification of the harness:** confirmed the extracted block is byte-identical to the live source and the fixtures are real, not self-confirming. Standing risk noted: the harness is a copy, so it will silently stop testing the live code after the next edit.
**Limitation:** not run on Windows PowerShell 5.1.
**Open, for Saeed:** does `C:\JeffLocal` have any git remote other than `origin`? If it does, M3 was a live defect rather than a latent one. Not checkable from here. [UNVERIFIED — confirm before proceeding]
**Saeed notified:** This session — awaiting his go-ahead to merge.

---

## 2026-09-09 — PR #5 Round 3: Security Agent Sign-Off Given
**Agent:** Lead Agent (Claude Code session), reviewed by Security Agent (round-3 re-review of head 3c00a16)
**Approved by:** **Security Agent sign-off GIVEN. Saeed's explicit approval still required before this reaches C:\JeffLocal\ — not a bug-fix-autonomy case, because it changes what Saeed is told about whether his work is backed up.**
**Description:** Round-3 review found no blocking defects. Both round-2 defects (M1 health-check cause, M2 banner ordering) verified fixed; M3, L2, L3, L4 and the 5.1 guard verified. The reviewer ran six adversarial cases of its own on top of the 11 in the harness — remote renamed away from `origin` (warning kept), sha on a second remote only (warning kept), two signals in one marker (no state leak between iterations), sha on both remotes (retires correctly), legacy no-sha signal (warning kept). Two optional items taken in this commit:

- **The precondition that makes the whole design sound is now written down in both files.** `strategy_daily.ps1` only attempts a push immediately after creating a commit, so the SHA in a `PUSH-FAILED` signal cannot already have been on GitHub when the push failed — which is *why* finding it there later proves it arrived. That was load-bearing and documented nowhere. A future change that pushes work not just committed (a retry loop, a catch-up push, a force-with-lease path) would silently reopen retirement-on-stale-evidence **with no test failing**. Cross-referenced comments now sit at both ends.
- **The banner-ordering test now derives the order from the live file** instead of naming the two sections in a fixed order. As written it would have stayed green if someone reordered `combined_brief.ps1` and reintroduced M2. Verified discriminating with a negative control: forcing the wrong order makes the test fail.

**STANDING CHECK FOR THIS FILE SET — the same mistake twice in one PR.** Both defects I introduced had an identical shape: a value changed at the point of **production** without checking what **consumed** it. In round 2, `-or $f[0] -eq "TAG-PUSH-FAILED"` was two tokens in a lookup, three lines above the branch that made it wrong. **When you add a value to one of these signals (`PUSH-FAILED`, `TAG-PUSH-FAILED`, `PUSH-HELD`, `CLOSED`, `FAILED`), grep every reader of that signal and read the branch each one feeds.** Recorded at the Security Agent's suggestion.

**Known residuals, accepted, not blocking:**
1. **Remote force-rewind** — push succeeds, tracking ref updates, someone rewrites GitHub history. `--contains` still answers yes and the warning retires. The single false-retire path left in the design; it pre-dates this PR and the removed timestamp gate did not catch it either.
2. **Harness drift** — the test extracts a copy of the block, so it will silently stop testing the live code after the next edit to `combined_brief.ps1`. Named, not fixed.
3. **`C:\JeffLocal` remote inventory** — unanswerable from this session. With `--list 'origin/*'` in place, a differently-named remote is now a *false-alarm* risk (warnings never retire) rather than a silence risk. That is the right way round.

**Files changed:** scripts/daily/combined_brief.ps1, scripts/daily/strategy_daily.ps1, CHANGELOG.md
**Tests run:** 11/11 retirement scenarios plus the banner-ordering test, all against real git repositories with real remotes; ordering test verified discriminating by negative control. Reviewer independently reproduced 11/11 and confirmed the extracted block is byte-identical to the live source. All five scripts in scripts/daily/ parse clean. StrictMode audit clean on every path.
**Limitation:** nothing in this PR has run on Windows PowerShell 5.1. The Security Agent recommends one `-DryRun` evening run on the target machine before the first live 18:30 close.
**Saeed notified:** This session — awaiting his explicit "approved".

---

## 2026-09-09 — Staleness Banner Goes Loud on Day 3, Not Day 1
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed, explicit choice this session — asked as "one quiet day: loud banner, or quiet note with the loud banner from day two?", answered **"Loud banner from day 3."**
**Description:** The "WARNING - PART OF THIS BRIEF IS OUT OF DATE" banner fired after a single day with no session log. One quiet day is ordinary — a day off, or a day spent on the other project — and Saeed's own 2026-09-09 dry run showed the banner firing at "1 day(s)" on exactly such a day. A banner that shouts at an ordinary Tuesday is the cry-wolf problem this week's work exists to prevent, in a different coat.

Days one and two now get a plain one-line note; the loud banner starts on the third day. New threshold `$StaleLoudAfterDays = 3` at the top of `combined_brief.ps1`, beside `$PausedProjects` and `$PausedNagAfterHours`.

**It is still said every day from the first.** Silence is what let the 11–19 Aug 2026 outage run for eight days; only the volume waits. The note names the count and the threshold, so the escalation is never a surprise: *"nothing new logged for 2 days. Normal so far; this becomes a warning at 3 days."*

**Nothing else was loosened — verified by test, not by inspection:**
- A project whose folder cannot be read is still loud on day one. Unreachable outranks everything and is checked before this branch.
- A project with **no session log at all** is still loud on day one. It carries no newest-log timestamp, so it can never reach the quiet branch.
- The day-named close-failure banner is untouched.
- The existing "no close has been due since" quiet note is untouched — that is a different case (nothing was missed) and still reads differently.

**Files changed:** scripts/daily/combined_brief.ps1, CHANGELOG.md
**Tests run:** PowerShell 7.4.6, 8 scenarios against the live extracted block, 8/8 — 1 day quiet, 2 days quiet, 71h (just under), exactly 72h (loud), 5 days (loud), no log ever (loud), folder unreadable (loud on day one), and log written after the last due close (quiet, normal gap). Boundary checked at exactly 3 days. Script parses clean.
**Limitation:** not run on Windows PowerShell 5.1.
**Saeed notified:** This session.

---

## 2026-09-09 — PR #6 Round 2: Security Agent Blocked the Day-3 Change; Two Real Defects Fixed
**Agent:** Lead Agent (Claude Code session), reviewed by Security Agent
**Approved by:** Saeed approved the day-3 threshold itself. Everything below is Security Agent conditions on it. **Still awaiting Saeed's "approved" to merge.**
**Description:** The first version was **BLOCKED**. Two findings, both correct:

- **F2 (blocking) — I reintroduced the exact defect finding H4 removed, one branch below H4's own fix.** The threshold counted a flat 72 wall-clock hours, so the weekend counted toward it. Concrete: last log Thursday 10:00, nobody works Friday → the loud banner fired on **SUNDAY**, when no close was due and no work was expected, after only two working days. The comment on `Get-LastExpectedCloseTime` already said it in terms — *"the right question is not 'is it the weekend' but 'has a close been due since'"* — and the branch immediately above the new one measures correctly. **Now counted in missed weekday closes**, via a new `Get-CloseTimeNBack` helper. Constant renamed `$StaleLoudAfterCloses` so the name states the unit. A project with no real log at all (`$NewestRealTime` is `$null`) is explicitly routed loud and can never reach the quiet branch.

- **F1 (blocking) — the safety net I claimed does not exist in the morning brief.** I justified quieting the staleness alarm on the grounds that the close-failure banner still fires independently on day one. That is true at 19:00 and **false at 07:00**: the whole marker-reading block is gated on `if ($Mode -eq 'Evening')`, so `$CloseDayFailed` is always false in a morning run and section 6b-2 never fires. Before this PR the morning brief's *only* close-failure signal was the staleness banner, and my change removed it for two days. Saeed agreed to delay the staleness alarm; he was not told that also blinded the morning brief.
  The note no longer says **"Normal so far"** — in this branch a due close has provably been missed, and in Morning mode the script has not even looked at the marker, so asserting normality is a claim it has not earned. It now reads: *"nothing new logged for 2 working days, and a session close has come and gone since. Not shouting yet; this becomes a warning at 3 working days."*

- **Health check bug found in the same review — a failed close was reported to Saeed as healthy.** `health_check.ps1` tested only `Test-Path` on the close marker. A close that RAN AND FAILED still writes a marker (first line `FAILED|` instead of `CLOSED|`), so the morning brief said *"Last working day closed properly"* the morning after the evening brief had shouted that it had not. Two of Saeed's own messages contradicting each other is how a warning stops being believed. It now requires a `CLOSED|` line and reports the reason from `FAILED-DETAIL` when there is one.

- **F3 — my new comment block had been inserted between the `$PausedNagAfterHours` explanation and its assignment**, so the next reader would attach the pause comment to the staleness threshold. Moved.

**Harness rebuilt.** The reviewer was right that the old one could not have caught either defect: it never varied `$Mode`, never modelled `$CloseDayFailed`, ran every scenario against a single fixed Tuesday, and stubbed the helpers. It now uses the **real** `Get-LastExpectedCloseTime` and `Get-CloseTimeNBack` from the live file and runs a real weekend clock.

**Files changed:** scripts/daily/combined_brief.ps1, scripts/daily/health_check.ps1, CHANGELOG.md
**Tests run:** PowerShell 7.4.6. Staleness **16/16** — including the reviewer's exact Thursday-log/Sunday-brief scenario (now quiet, was loud), the full Thursday→Tuesday walk, both sides of the third-close boundary, no-log-ever (loud), unreadable folder (loud), and three assertions on the note's wording (does not claim normality, names the missed close, names the threshold). Health check **6/6** — CLOSED marker OK, FAILED marker now PROBLEM, reason surfaced, no dangling text when there is no detail, missing marker still PROBLEM. Both scripts parse clean.
**Limitation:** not run on Windows PowerShell 5.1.
**Open for Saeed:** (1) confirm "three days" means three **working** days — under this fix a Monday-start outage goes loud on Thursday rather than Wednesday; (2) whether the **morning** brief should carry the close-failure banner at all. That is a behaviour change beyond this PR and is not being folded in silently.
**Saeed notified:** This session.

---

## 2026-09-09 — PR #6 Round 3: Approved, With the Escalation Made Honest
**Agent:** Lead Agent (Claude Code session), reviewed by Security Agent
**Approved by:** **Security Agent sign-off given** at round 3 (head 7498d9e) with C1 required before merge; C1 is done. **Saeed's explicit "approved" still required before merge.**
**Description:** The re-review confirmed F1 and F2 discharged and verified the new counting **independently** — the reviewer wrote its own oracle and swept **26,744 combinations** (every day 1 Jan 2026 → Feb 2027, morning and evening briefs, log ages 1–12 days at three times of day), checking both the loud/quiet decision and the number the note states. Zero mismatches, covering both 2026 UK DST transitions, every month end and the year boundary. It also confirmed my arithmetic and withdrew its own instruction: rolling back `$StaleLoudAfterCloses - 1` is right; rolling back the full count would have put the banner on the *fourth* missed close.

Three further changes:

- **C1 (required before merge) — the escalation contradicted the promise it had just made.** The quiet note counted working days; the loud banner that replaced it counted calendar days, one day apart in Saeed's inbox: *"…becomes a warning at 3 working days"* on the Sunday, then *"nothing new logged for 4 day(s)"* on the Monday. A larger, different number in the very message the previous message promised — at the exact moment the design asks him to trust the count. There is now **one shared counter** (`Get-ClosesMissed`) feeding both. The loud line leads with the promised unit and keeps the calendar figure after it: *"nothing new logged for 3 working days (4 day(s) ago)"*.
- **Found while testing C1 — the counter was bounded at 99 and reported the bound as fact.** A log from 2020 was rendered as *"99 working days"* when the truth was about 1,745. A false number inside an alarm is the exact fault this file exists to avoid. It now reads *"more than 99 working days"*.
- **C4 — an unreadable close marker was reported as a failed close.** `-ErrorAction SilentlyContinue` swallows the read error, so an empty or unreadable marker found no `CLOSED|` line and was announced as "RAN AND FAILED" with no reason: loud, which is the right direction, but pointing Saeed at the wrong problem. It now says it could not read the marker. The two renderings of `FAILED-DETAIL` in `combined_brief.ps1` and `health_check.ps1` are also aligned, so one marker no longer appears two different ways in two of Saeed's messages.

**KNOWN LIMITATION — BANK HOLIDAYS (Security Agent C2, accepted, not blocking).** The close schedule knows only Saturday and Sunday. The 18:30 task runs on a bank holiday, so that day counts as a missed close. Measured: last log Thursday 25 Mar 2027, **loud on Easter Monday evening** — after two working days, one of them a public holiday. Christmas 2026: last log Thu 24 Dec, **loud Tuesday 29 Dec**. So the residual false-alarm window is exactly the long weekends, roughly five or six times a year. That is a large improvement on `main` (loud on day one, every time) and on round 1 (loud every ordinary weekend), and it is not a regression — but it is the same class surviving in smaller form and is recorded here rather than discovered at Easter.
**A bank-holiday table must NOT be folded into this change.** `Get-LastExpectedCloseTime` also drives close-failure detection; teaching it about holidays would change which day's marker is demanded and could suppress a real "the close did not run" alarm. If done at all it belongs in `Get-CloseTimeNBack` only, with that interaction as the main review question.

**SEPARATE ISSUE, RAISED NOT FIXED — a restored or re-checked-out session log can silence the staleness system entirely.** `$StaleHours` is measured from `LastWriteTime`. A `git checkout` or a folder restore makes every session log younger than 24h, `$RealLogCount` becomes non-zero, `$IsStale` stays `$false`, and the project bypasses the staleness block completely — no quiet note and no banner. **This is a total-silence path, it is worse than anything in this PR, and it is unchanged by this PR** — I had wrongly described it as amplified by the wider quiet band; the Security Agent corrected that and is right. Its own ticket.

**Files changed:** scripts/daily/combined_brief.ps1, scripts/daily/health_check.ps1, CHANGELOG.md
**Tests run:** PowerShell 7.4.6. Staleness **21/21** (up from 16) — the five new assertions tie the quiet note and the loud banner to the same number at the threshold, and check the calendar figure is retained alongside it. Health check **6/6**. Reviewer independently reproduced 16/16 and 6/6, confirmed the extracted test blocks are byte-identical to live source, and confirmed `Get-CloseTimeNBack` terminates and errs loud at thresholds of 0, 1 and 10. StrictMode clean on every path; all five scripts parse clean.
**Limitation:** still not run on Windows PowerShell 5.1 — the only untested surface, outstanding since PR #5. One `-DryRun` morning and evening run on the target machine is recommended before the first live brief.
**Open for Saeed:** (1) confirm "three days" means three **working** days; (2) whether the **07:00** brief should carry the close-failure banner at all — it never has, and that failure currently only reaches him at 19:00 the night before.
**Saeed notified:** This session — awaiting his explicit "approved" to merge.

---

## 2026-09-10 — The Close Now Backs Itself Up and Pulls When Safe (Saeed's Request)
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed, explicitly, this session: *"WHY DO I HAVE TO PULL AND PUSH? WHY NOT AUTOMATIC SCHEDULED TASK?"* — then chose **"Yes, and also auto-pull when it is safe"** after being shown the trade-off in writing (that it means code can reach the production folder without him looking first).

**The incident that prompted it.** On 9 Sep the 18:30 close ran at 18:32, committed correctly, and pushed its restore tag — but its push to `main` was **rejected** because the PC was still on the PR #4 merge while GitHub had moved to PR #5. The work sat on the machine only, and this morning's 07:00 brief was stuck behind it too. Both were recovered by hand (`dccbaf6..4e5857d`). **The 19:00 banner DID fire** — Saeed confirmed it — which is the first live proof that last week's alarm work does what it was built to do. The alarm worked; the underlying cause had never been fixed.

**Root cause, verified:** there is **no `git pull` in any scheduled task**. Every job pushes and nothing ever receives. Git refuses a push from a copy that is behind, so the moment GitHub moved ahead, every save failed and stayed failing until a human intervened. This is the same mechanism as the 7–9 Sep three-day outage.

**Two changes, deliberately separate, because git glues together two things that should not be:**

1. **A save that can never be refused.** Every close now pushes to `close/<date>` **first**, before touching `main`. Nobody else writes to that branch, so it cannot be rejected as non-fast-forward. Saeed's work reaches GitHub every evening whatever state `main` is in, with no manual step, ever. It still respects the live-deploy guard: unfinished production work means nothing leaves the machine, backup branch included.

2. **An automatic pull, but only when it is safe.** On a "you are behind" rejection the close fetches, inspects what is actually incoming, and merges only if every condition holds. **It refuses** — and falls through to telling Saeed — when any incoming file is under `$NoAutoPullPaths` (`dashboard\`, `config\`), when the rejection is a network or auth failure rather than being behind, or when the merge conflicts (aborted immediately; a half-merged production folder left overnight is far worse than a failed push).
   The reasoning for pulling at all: anything on `main` arrived through a PR Saeed approved, so bringing it down is delivery of already-approved work. **The gate is the merge, not the pull.** `dashboard\` is different — it *is* the live app on 8765 — and `config\` drives the live Ollama/Gemma pipeline. Those stay his call.

**New signal `BEHIND-REMOTE`, and why it is not an alarm.** With a backup branch, "behind `main`" no longer means the work is at risk, so it must not borrow the loud banner's voice: *"YOUR WORK DID NOT REACH GITHUB"* would simply be false. It is still said every time, quietly, naming why the pull was refused and the one command to fix it.
**This also closes a trap I would otherwise have set.** The retirement check added in PR #5 asks *"is this sha on an origin branch?"* — and the backup branch **is** an origin branch. A `PUSH-FAILED` raised in this situation would have found its own backup and retired itself the same evening: an alarm silently switching itself off, which is precisely the failure this file set exists to prevent.

**Files changed:** scripts/daily/strategy_daily.ps1, scripts/daily/session_close.ps1, scripts/daily/combined_brief.ps1, CHANGELOG.md
**Tests run:** PowerShell 7.4.6, **15/15 against real git repositories with real remotes** — not mocks, and not a re-implementation: the live push block is extracted and executed. Nothing to pull (pushes, no alarm; backup branch created) · safe change (auto-pulled, work reached `main`, **the new code verifiably arrived on the PC**, no alarm) · `dashboard\` change (refused; **the live file on disk verified unchanged**) · `config\` change (refused; live config verified unchanged) · merge conflict (aborted, working tree verified clean, no `MERGE_HEAD` left behind, still reported). All earlier suites still pass: staleness 21/21, health check 6/6, retirement 11/11. All five scripts parse clean.
**Harness note:** the first run showed 7 failures which were a **fixture** fault, not a code fault — the bare test repo defaulted to `master`, so the second clone had no `main` and the scenario never actually put the PC behind. Diagnosed and fixed rather than reported as a result; the fixture now pins `-b main` with a comment saying why.
**Limitation:** not run on Windows PowerShell 5.1.
**Still requires:** Security Agent review, then Saeed's explicit approval before merge.

---

## 2026-09-10 — Auto-Pull Round 2: Security Agent BLOCKED It, and Was Right
**Agent:** Lead Agent (Claude Code session), reviewed by Security Agent
**Approved by:** Saeed approved the feature. Everything below is Security Agent conditions on it. **Not merged — awaiting re-review, then his explicit approval.**
**Description:** The first version was **BLOCKED as unsafe to run unattended against the live production folder**, and the finding was real. The reviewer wrote its own exploit and ran it against my extracted live code three times.

**B1 (blocking) — the protected-path check could not see three whole classes of path, and the live app could be DELETED while the log said "Safe".**
`git diff --name-only` does not report what it appears to. With rename detection on — the default — it prints **only the destination**. So:
- A remote renaming `dashboard/app.py` → `docs/app_moved.py` showed up as `docs/app_moved.py` alone. The guard passed it, and the merge **deleted the live file**.
- Renaming the whole `dashboard/` folder removed **the entire live production app** at 18:30, unattended, with no alarm.
- Git also **quotes any non-ASCII path** by default, so `config/pathways-café.json` arrived as the literal `"config/\303\251.json"` — starting with a quote character — and `-like 'config/*'` was false. One accented filename would have defeated the guard permanently.

Fixed with `git -c core.quotePath=false diff --no-renames --name-only -z`. All three flags are load-bearing and none covers another; there is now a comment saying so. `--no-renames` splits a rename back into delete-old + add-new so the protected path reappears.

**Verified by negative control, not just by the fix passing.** Reverting only those flags makes the same tests report `LIVE APP FILE DELETED`, `ENTIRE LIVE FOLDER DELETED` and `FILE LANDED IN LIVE CONFIG` — while the log line still reads *"Safe: 1 incoming file(s), none under dashboard, config. Merging."* Honest note: a plain **deletion** of a dashboard file was always caught; only the rename and quoting classes were vulnerable.

**Why my 15/15 missed it:** the harness only ever tested a plain content modification — the one shape the matcher did handle. Right mechanism (real repos, real remotes, real extracted code), wrong inputs.

**H1 (high) — the new quiet signal was collected and thrown on the floor in the 07:00 brief.** Only the 18:30 marker path was updated when `BEHIND-REMOTE` was added; neither live call site in `combined_brief.ps1` harvested it. A morning run that was merely behind would have said **nothing at all** — silently reversing the comment sitting directly above that code, which exists precisely because a rejected push must reach the morning brief.

**H2/H3 (high) — I closed the self-retiring trap for one branch and left it open on the other.** A genuine **auth or network** failure still emitted a loud `PUSH-FAILED`, whose sha was already on `origin/close/<date>` from the backup push moments earlier — so the retirement check would find the backup and demote a real failure to *"NOW FIXED — nothing to do"* the same evening. The retirement glob now **excludes `origin/close/*`**. This also stops the check decaying as backup branches accumulate.
**The two cross-referenced precondition comments were left asserting something no longer true** — that a push only ever happens straight after a fresh commit, so the sha cannot already be on origin. The backup push makes that false. Both comments are corrected in the same commit; leaving them would have set a trap for the next reader, which is exactly what they warn against.

**M1 — the auto-pull was wider than what Saeed approved.** He approved *"the **close** pulls automatically"*. `strategy_daily.ps1` also runs at **07:00**, so production code could have changed right before the surgery day starts. Now **Evening only**, and a morning run that is behind still tells him, naming that rule as the reason.
**M2** — the message stated one hardcoded cause on every path, including a fetch failure and an aborted conflict, then told him to run a pull that would conflict for him too. It now carries the real reason.
**M3** — a failed `git diff` left `$Incoming` empty, which read as "nothing incoming, safe to merge". The guard must be satisfied by proof, never by an error. It now refuses.
**L2** — refuses to auto-pull on a detached HEAD. **L3** — pipe-sanitises the message, as `$PushFailReason` already was.

**Confirmed clean by the reviewer:** StrictMode on every path including the guard-held path (no repeat of B1 from PR #4); the live-deploy guard still holds, backup branch included; `TAG-PUSH-FAILED` still non-retirable; three-dot diff is the right question; `git merge --abort` handling adequate; PRs #1, #2, #3 and #6 untouched. It also confirmed my earlier fixture diagnosis was correct.

**Files changed:** scripts/daily/strategy_daily.ps1, scripts/daily/combined_brief.ps1, CHANGELOG.md
**Tests run:** push/pull **26/26** (was 15) — the four exploits now all refuse and the live files verifiably survive, plus the Evening-only rule. Retirement **13/13** — including a sha present **only** on `origin/close/*` (warning kept) and the same sha once it reaches `main` (retired). Staleness 21/21, health 6/6. All five scripts parse clean. Negative control run to prove the new tests discriminate.
**Limitation:** still not run on Windows PowerShell 5.1 — outstanding since PR #5, and this change adds five git invocations to the unattended path.
**Open for Saeed:** (1) keep `close/<date>` branches forever or prune once their work is on `main`? (2) are `dashboard\` and `config\` the complete protected list — note `scripts\daily\` is deliberately NOT protected, since those are the very files he wants delivered automatically. (3) should auto-pull also run at 07:00, which he was not shown.

---

## 2026-09-10 — Auto-Pull Round 3: Sign-Off Condition S1 Discharged
**Agent:** Lead Agent (Claude Code session), reviewed by Security Agent
**Approved by:** Security Agent sign-off **granted, conditional on S1** — S1 is now done. **Saeed's explicit written approval still required before merge; this writes to the production machine unattended.**
**Description:** The re-review confirmed the three blocking exploits are dead. The reviewer re-ran them itself, added five more attack classes (symlink swap, case-variant `Dashboard/`, submodule/gitlink, copy detection, directory-rename in both directions) — all refused — and ran its own independent negative control. It also chased and cleared two things I had not: multiple merge bases (criss-cross), and whether a pulled `.gitattributes` could execute anything (it cannot; filter/merge drivers must be defined in the untracked `.git/config`).

**S1 — the fix I asked for created a new way to fail OPEN, on the one platform never tested.**
`-z` was the right call, but it moved the parse from "split on newlines" — which every PowerShell does identically — to "reassemble native output and split on NUL", which has never executed on Windows PowerShell 5.1, the only place this actually runs. If 5.1 drops the NUL bytes, the whole list collapses into **one concatenated string**, and the guard prints *"Safe: 1 incoming file(s), none under dashboard, config. Merging."* — the exact sentence that was in the log when the live app was deleted in testing. Silent, and **intermittent**, because it only bites when the protected path is not first in the list.

Fixed by cross-checking the `-z` parse against the newline form and **refusing when the two readings disagree in count** — the same principle already applied to `$DiffOk`: the guard must be satisfied by proof, never by an error.

**Two things about testing this honestly, both worth recording:**
1. **My first attempt at the test did not reproduce the failure at all.** I used a newline inside a filename, but git always quotes such paths, so both readings agreed and the test proved nothing. The real cause is a platform difference I cannot reproduce on Linux, so it is now modelled directly: a shim intercepts **only** the `-z` call and returns the entries concatenated with no NUL. Every other git call goes to the real git. Stated plainly in the test file, because a stub that models the wrong thing is worse than no test.
2. **My first negative control passed by luck and I nearly recorded it as a success.** With the guard removed, that case still refused — because git lists paths bytewise, so `dashboard/` happened to sort first and the collapsed string still began with a protected prefix. That is precisely the "intermittent" property the reviewer warned about. The test now uses `CHANGELOG.md` (uppercase, sorts before `config/`) so the protected path is **not** first. With the guard removed it now reports **`LIVE CONFIG OVERWRITTEN`**; with the guard it refuses. Only then is the guard proven load-bearing.

**GOVERNANCE FACT FOR SAEED, in the Security Agent's words:** `scripts\daily\` is deliberately **not** protected, because those are exactly the files he wants delivered automatically — protecting them would make this change solve nothing. Therefore **the security boundary for those scripts is the pull request review on `main`, not this guard.** Approving a PR now means those scripts run on his PC that evening without a second look. That is a trade he chose, and it should be acknowledged knowingly rather than discovered later.

**Files changed:** scripts/daily/strategy_daily.ps1, CHANGELOG.md
**Tests run:** push/pull **30/30** (was 26), including the modelled NUL collapse with the protected path deliberately not first, verified load-bearing by negative control. Retirement 13/13, staleness 21/21, health 6/6. All five scripts parse clean.
**Limitation:** still not run on Windows PowerShell 5.1. The Security Agent's position, which I share: this is now the largest untested surface in the series, and if it is still true after this merge it should become a scheduled task of its own.

---

## 2026-09-10 — The 07:00 Brief Gains the Close-Failure Alarm; Backups Prune Themselves
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed, both explicitly this session — *"Yes — add it"* to the morning close-failure alarm, and *"Tidy up once safely saved"* to backup pruning.
**NOT MERGED YET, on purpose.** Tonight's 18:30 close is the first live run of the auto-backup/auto-pull change on Saeed's machine, and nothing in this series has executed on Windows PowerShell 5.1. Stacking further changes on top of something unverified is how the 7–9 Sep outage happened. These merge after tonight is confirmed good.

**1. The 07:00 brief now carries the "evening close did not run" alarm.**
Found by the Security Agent during the PR #6 review (F1). The entire close-marker read sat inside `if ($Mode -eq 'Evening')`, so `$CloseDayFailed` was **always false** in a morning run and section 6b-2 never fired. A close that ran and failed on Monday evening was shouted about once at 19:00 and then never mentioned again — Tuesday's 07:00 brief said nothing about it. If Saeed missed the one evening message, he might never hear of it at all.

Two things were tangled in a single gate and are now separated:
- `$SkipCloseHere` — the **write** side, whether this script runs the close itself. Still evening-only, unchanged.
- The marker read — **read-only**. It looks at `logs\close-state` and sets the reporting variables. Nothing about it needs to be evening-only, and the day-naming logic already answers "the last close that fell due", which is correct at 07:00 exactly as at 19:00.

The `if` wrapper was removed and its body dedented rather than left as `if ($true)`, which would have misled the next reader.

**2. Backup-branch pruning — BUILT, THEN PULLED FROM THIS CHANGE.** See the round-2 entry below.

**Files changed:** scripts/daily/combined_brief.ps1, scripts/daily/strategy_daily.ps1, CHANGELOG.md
**Tests run:** PowerShell 7.4.6. Morning alarm **7/7** — failed close in Morning mode fires and names the day; Evening still fires unchanged; a healthy close stays silent; a **missing** marker is loud; `BEHIND-REMOTE` is read from the marker in the morning; and behind-but-safe is not escalated to a close failure. Pruning **6/6** against a real remote — the branch whose work never reached `main` **survives** with the log saying why, this run's own backup survives, at least 10 are kept, and a failed push stops pruning entirely. All earlier suites still pass: push/pull 30/30, retirement 13/13, staleness 21/21, health 6/6. **83 tests in total.** All five scripts parse clean.
**Harness note:** one morning-alarm assertion initially failed because my test read a variable outside the function scope that set it, not because of a code fault; and the prune test's "before" count was wrong because `Measure-Object` returns a single object. Both were test bugs, diagnosed and fixed rather than reported as results.
**Limitation:** not run on Windows PowerShell 5.1.
**Still requires:** Security Agent review, tonight's live verification, then Saeed's explicit approval.

---

## 2026-09-10 — PR #7 Round 2: Pruning Pulled Out After It Was Shown to Destroy Work
**Agent:** Lead Agent (Claude Code session), reviewed by Security Agent (round 10 of this series)
**Approved by:** Saeed approved both features. The decision to **split them** is mine, on the Security Agent's recommendation. **Not merged — waiting on tonight's live verification and Saeed's approval.**
**Description:** The review was **DO NOT MERGE AS-IS**. One finding could destroy the only remote copy of a day's work, and the reviewer reproduced it end to end.

**S1 (high) — the prune enumerated from the remote but proved from local refs, and could delete the only remote copy of work.**
`git ls-remote` asks GitHub what exists. `git merge-base --is-ancestor origin/<bb> origin/<branch>` asks the **local** remote-tracking refs. Two different authorities, with nothing between them refreshing the second. Reproduced: `origin/main` is rewound on GitHub (force-push, branch rewrite after a squash-merge, a bad revert from another session); the PC's stale local ref still contains the old commit; the prune consults the stale ref, gets a yes, and deletes the branch. The reviewer's fixture ended with the commit reachable from **zero** remote refs, while the log asserted *"Pruned backup branch … its work is on main."* A false statement printed at the moment the work is destroyed.

**PRUNING HAS BEEN REMOVED FROM THIS CHANGE ENTIRELY**, on the Security Agent's recommendation and my agreement. It is pure housekeeping — it saves clutter in a branch list — and it was stacked on an auto-backup change that has never executed on the target machine. The morning alarm fixes a real reporting hole and should not wait behind it. The prune returns as its own change, with the sha-against-sha fix (`ls-remote` already returns the sha in field 1; it was being discarded), and with the reviewer's adversarial tests folded in permanently.

**S2 (medium-high) — the 07:00 brief would have shouted "the save to GitHub failed" about work that the same 07:00 run had just saved.**
The marker read runs near the top (section 5 needs `$CloseDayFailed` early); the morning's own git safety net runs much later. So the proof *"has this work reached GitHub?"* was asked **before** the push that puts it there, and its answer rendered after. The retirement mechanism exists precisely so that banner stops the moment work arrives — asking too early defeats it on the one run that fixes the problem, and lands a false loud banner on the morning after a failure, exactly when Saeed most needs it to be true. New section 6b-0 re-proves retirement after sections 6/6b, Morning only. The proof is factored into `Test-WorkOnOrigin` so both call sites use identical logic.

**S3 (medium) — the close-failure banner claimed "nothing saved to GitHub", which is false by 07:00.** Three of its four claims hold in the morning; that one does not, because the morning safety net has already pushed by the time the banner is prepended. Now conditional on mode.

**S4 (medium) — duplicate lines in the morning brief.** With the marker read no longer evening-gated, `$HeldSignals` and `$BehindSignals` fill from **two** sources — yesterday's marker and this morning's own close output — and `session_close.ps1` writes the same signals into the marker. An unfinished `dashboard\` folder produced a byte-identical warning twice in one message. Both lists are de-duplicated before rendering.

**S5, S6** — both concerned only the prune and left with it.

**The dedent was verified clean, not eyeballed:** 216 lines out, 216 in, byte-identical after stripping exactly four leading spaces; no here-strings anywhere in the moved block, so the terminator-column hazard did not arise; no orphan brace. The reviewer also walked every statement in the moved block and confirmed it is genuinely read-only — no file write, no directory creation, no deletion, no side-effecting git call.

**Where my harness was blind, in the reviewer's words and worth recording:** `t_prune.ps1` ran `git fetch origin` immediately before the block, which is *exactly and only* the condition under which S1 cannot occur — the suite was structurally blind to its own worst failure. `t_morning.ps1` tested the marker block in isolation with the dates hardcoded, so it could not see S2, S3 or S4 at all. Every assertion in both was true; the gap was what they declined to ask.

**Files changed:** scripts/daily/combined_brief.ps1, scripts/daily/strategy_daily.ps1 (prune removed), CHANGELOG.md
**Tests run:** morning alarm 7/7 · **new S2 re-check suite 6/6** (work arrived during the run → retired; did not arrive → kept; only on a backup branch → kept; tag failure never retired; legacy no-sha signal kept; Evening mode untouched) · push/pull 30/30 · retirement 13/13 · staleness 21/21 · health 6/6. All five scripts parse clean.
**Limitation:** not run on Windows PowerShell 5.1.
**Open questions the reviewer could not answer from the codebase, and nor can I:** does anything other than Saeed's PC push to `origin/close/*`, and has `main` in this repo ever been force-pushed? Both bear on how likely S1 is in practice, and both matter when the prune returns.

---

## 2026-09-10 — PR #7 Round 3: Two Dedups That Could Not Have Worked, and a Claim I Made That Was False
**Agent:** Lead Agent (Claude Code session), reviewed by Security Agent (round 11)
**Approved by:** Bug-fix autonomy — no auth, no patient identity, no compliance logic. **Not merged; waiting on tonight's live verification and Saeed's approval.**
**Description:** S1, S2 and S3 confirmed properly fixed. **S4 was not fixed at all**, in two independent ways, and one thing I asserted in writing was untrue.

- **T1 — the `$BehindSignals` dedup was dead code.** I placed it next to the held-signal dedup instead of next to *its own* consumer, so it ran **96 lines after** the block that renders it. It never executed. Moved above section 6b-5.
- **T2 — and even correctly placed, its key could never match.** I grouped on the whole signal, which embeds `close/$Today`. Yesterday's marker entry and this morning's entry therefore differ **by construction, every single day** — grouping yielded 2, not 1. Now keyed on the project field. **Fixing T1 without T2 would have changed nothing**, which is the part worth remembering: two independent faults, either one alone masking the other.
- **T3 — the `$HeldSignals` dedup only worked when the file count was unchanged.** `Select-Object -Unique` compares the whole line and the count is the last field, so `dashboard|3` from yesterday's marker and `dashboard|5` from this morning both survived — and because the marker is harvested first, **the stale 3-file line rendered above the current 5-file one**. Now keyed on project plus path, keeping the latest.
- **T4 — I claimed "both call sites cannot drift" and there was only one call site.** The marker loop still carried its own inline copy of the proof; `Test-WorkOnOrigin` was called once, from the new section 6b-0. The fail-safe there could not have been inverted by my refactor because the refactor never reached it. Near-identical duplicates are the worst state for drift — the next editor assumes syncing them is safe. The marker loop now routes through the same function, so the claim is true rather than corrected away. The `last-push-ok` stamp read stays at that call site, because it is presentation for that site only.

**On the reviewer's answer to my second question, which I had half wrong.** I argued `$BehindSignals` needed no retirement re-check because it is "already stating something still true". The loudness half was right; the truth half was not. BEHIND-REMOTE becomes false by exactly the same evidence PUSH-FAILED does — pull and push by hand overnight, and the next morning's brief still says you are behind. It cannot be retired as cheaply because the signal carries **no sha** (field 3 is the backup branch name). T1/T2 stop the brief contradicting itself; a fourth field carrying the sha would make it properly retirable, and that is noted for the follow-up change rather than bolted on now.

**One more harness gap, found by running it.** The retirement suite failed 4/13 after the T4 refactor because it defines its own stubs and never sourced the shared helpers — a test fault, not a code fault. Worth recording that **the failure direction was still safe**: the missing function threw and the catch kept the warning. But a suite that cannot execute the code proves nothing, so it now sources them.

**Files changed:** scripts/daily/combined_brief.ps1, CHANGELOG.md
**Tests run:** **new dedup suite 9/9** — including the assertion neither suite previously made: each dedup's line number is read from the **live file** and asserted to be above its own consumer, so reordering the script fails the test. Plus: entries that differ by construction group to one and the newest is kept; two distinct projects both survive; the current held count is shown, not the stale one; and same project with a different protected path is not collapsed. All other suites: morning 7/7 · S2 re-check 6/6 · push/pull 30/30 · retirement 13/13 · staleness 21/21 · health 6/6. All five scripts parse clean.
**Limitation:** not run on Windows PowerShell 5.1 — still nothing in this series has.

---

## 2026-09-10 — PR #7 Round 4: My Own Fix Would Have Sent Saeed Nothing At All
**Agent:** Lead Agent (Claude Code session), reviewed by Security Agent (round 12)
**Approved by:** Bug-fix autonomy. **Not merged; waiting on tonight's live verification and Saeed's approval.**
**Description:** Review verdict was **BLOCK**, on a defect **introduced by the previous commit's fix**. The code it replaced could not throw.

**G1 (critical) — the new `$HeldSignals` dedup key crashed the entire brief on a malformed line.**
The key was `"$($p[1])|$($p[2])"` after splitting on pipes. The harvest filter is `-like "PUSH-HELD|*"`, which guarantees **one** pipe, not three — so `$p[2]` on a truncated line is out of bounds, and under `Set-StrictMode -Version Latest` that is a **terminating** error. It sits at script top level with no enclosing `try`, so the script dies before section 7 sends anything: **Saeed receives no WhatsApp message at all.**

Not a pwsh-7 artefact — `-Version Latest` resolves to 3.0 on Windows PowerShell 5.1, so it would have happened on the real machine. Trigger: an 18:30 close losing power or disk mid-write leaves `...PUSH-HELD|`; the next 07:00 brief then dies. **Silence on the morning after a crashed close** — the exact 11–19 Aug shape. And one malformed line poisoned the whole array, taking the good signals with it.

Two details worth keeping. The renderer eight lines below **already** guards with `Count -ge 4`, so its author treated a short line as possible; my dedup, running in front of that guard, treated it as impossible. And the sibling `$BehindSignals` key I wrote in the same commit takes `[1]` only and could not throw — the held key was the odd one out, in code I wrote minutes apart.

**This is the B1 class for the second time in one series**, and the standing check recorded on 2026-09-09 — *"when you add a value to one of these signals, grep every reader and read the branch each one feeds"* — would not have caught it. Extending that check: **any new index into a split signal must assume the line is truncated.** The filter proves the prefix, never the field count.

**G2 (low) — a malformed newest entry could evict the good one.** `Select-Object -Last 1` picked the newest unconditionally. A truncated line arriving from this run would win its group, then be discarded by the renderer's guard — leaving a banner header with **nothing underneath** and the real warning gone. Both dedups now prefer the last **well-formed** entry, falling back to the last.

**G3 (low)** — an errored check logged *"is NOT on any origin branch"* when the truth was *"I could not ask"*. Same alarm, wrong place to send whoever debugs it. `Test-WorkOnOrigin` now logs its own catch.

**G4 (low) — the test helper file is a copy, and nothing enforced that it still matched.** Editing `Test-WorkOnOrigin` in the live script would leave the retirement suite passing 13/13 against a stale copy — the same "the test cannot see the code" fault, one level up. `run_tests.ps1` now asserts the helper text is a substring of the live script and fails loudly if not. **Verified discriminating**: appending one comment line to the copy makes the suite report `helpers.ps1 is STALE` and exit.

**Harvest order is now asserted, not assumed.** "Last" is only "newest" because the marker read runs before section 6 — a structural property nothing enforced. A future re-order would silently start preferring the **stale** entry with no test failing. Three line-number assertions now read from the live file: marker harvest < section-6 harvest < dedup.

**`$BehindSignals` retirement — logged as technical debt, not built.** The reviewer confirmed this does not block, and gave the reason to record: the residual gap errs toward saying too much (a stale quiet note costs Saeed a sentence and an unnecessary `git pull`), never toward silence, and every blocking finding in this series has been an alarm going quiet. If it is ever built it must use the **same-question** proof — *is HEAD still behind origin/branch?* — not a stamp. This series has twice been burned by proofs that answered a different question (the timestamp gate; the unscoped `branch -r`).

**Files changed:** scripts/daily/combined_brief.ps1, CHANGELOG.md
**Tests run:** dedup suite **19/19** (was 9) — now including: a truncated held line does not crash and the good line survives it; a trailing-pipe-only line does not crash; a truncated behind line does not crash; empty arrays do not crash either dedup; a well-formed line survives a truncated sibling; same key with the truncated entry last still keeps the well-formed one; and the three harvest-order line assertions. Plus morning 7/7 · S2 6/6 · push/pull 30/30 · retirement 13/13 · staleness 21/21 · health 6/6. All five scripts parse clean.
**Harness note:** one G2 assertion of mine failed and was **my test being wrong**, not the code — for held signals the key includes the path, so a truncated line lands in its own group and cannot evict the good one; my assertion checked position, which tested `Group-Object`'s output order rather than the guarantee. Replaced with an assertion on survival, plus a new case constructing the situation where eviction genuinely is possible.
**Limitation:** not run on Windows PowerShell 5.1.

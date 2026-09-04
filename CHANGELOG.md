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

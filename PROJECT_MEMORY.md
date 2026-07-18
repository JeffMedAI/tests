# PROJECT MEMORY — JeffLocal
# READ THIS FIRST at every session start, before doing anything else.
# Last updated: 2026-07-18 (18:00 automated session-end — no commits today)
# Maintained by: Claude (update at end of every session)

---

## WHO YOU ARE TALKING TO

**Saeed** â€” Founder, Avamed. Owner and sole approver of all production changes.
Email: 5256863@gmail.com | Phone: 07440 333938
GitHub: Avamedio (215987900+Avamedio@users.noreply.github.com)
Repo: https://github.com/JeffMedAI/tests (branch: sandbox)

---

## WHAT THIS PROJECT IS

**JeffLocal** â€” On-premises AI patient triage system for UK GP surgeries (Avamed).
Patients call the surgery â†’ Jeff (voice AI) captures reason â†’ verifies patient â†’
applies safety rules â†’ delivers structured task to reception staff on a dashboard.
No clinical decisions. Admin intake only. All AI runs locally (Ollama/Gemma).
No patient data leaves the building.

**Core safety rule:** Ollama extracts and drafts. Deterministic code verifies,
matches, validates, and finalises. LLM output NEVER overrides verified patient data.

**Live dashboard:** https://dashboard.app-avamed.uk (Cloudflare tunnel â†’ localhost:8765)
**Pilot site:** Churchtown Medical Centre, Southport â€” NOT YET LIVE

---

## CRITICAL PATH DISTINCTION â€” READ EVERY SESSION

```
PRODUCTION  = C:\JeffLocal\dashboard\        Port 8765  Watchdog-managed  LIVE

Sandbox directory was REMOVED on 2026-06-07. There is no sandbox directory.
Development happens on git feature branches. Test locally, get approvals, merge.
Git branch name "sandbox" has NO relationship to file paths.
Always verify the actual file path before editing.
```

---

## APPROVAL PROTOCOL

Saeed's explicit "approved" in chat is required for:
- Any change to production files (C:\JeffLocal\dashboard\)
- Any change to auth.py, enforce_auth.py, or patient_matcher.py
- Any new external dependency
- Any database migration on live data
- Any scope or architecture change
- Any marketing or external-facing content

"Do it yourself" is NOT authorisation. Approvals do NOT carry over between sessions.
Re-confirm every session.

---

## AGENT TEAM

```
Agent    | Role
-------- | ---------------------------------------------------
lead     | Orchestrator, human liaison
backend  | FastAPI, Python, Ollama, n8n webhook
frontend | Dashboard UI, CSS, Jinja2
database | SQLite, migrations, GDPR purge
test     | pytest + Playwright E2E
security | GDPR, NHS, OWASP â€” VETO authority over all PRs
devops   | Git, deployment, Task Scheduler
strategy | Docs, reports, governance, marketing
```

---

## CURRENT STATUS -- 2026-07-18 (updated)

### NOTHING IS LIVE — READ BEFORE JUDGING SEVERITY BELOW
**All patient data in the system is FAKE** (Saeed, 2026-07-17). Neither Churchtown nor St Marks is
live. Neither goes live until compliant, tested, and approved by the partners. So the items below
are **pre-go-live debt to clear, not active incidents** — no real patient data is at risk today.
They must all be closed before either business goes live. (An earlier version of this section used
incident language; that was overstated.)

### TOP OF THE LIST — SECURITY, NEEDS SAEED (found 2026-07-16)
1. **`/api/n8n/test-intake-batch` accepts UNAUTHENTICATED requests.** `JEFF_WEBHOOK_SECRET`
   is unset, so `n8n.py:319` skips HMAC verification and returns — the request proceeds. The
   route is reachable via the Cloudflare tunnel, writes queue envelopes and spawns a pipeline
   subprocess. Its own docstring says it "will be removed before production deployment" — it
   wasn't. `test_mode` is NOT a guard: it is read from the caller's own payload. The 2026-05-30
   HMAC review recommended the fix (N1); never implemented. **Impact today is limited — no real
   patients, no staff accounts** — but this must close before go-live. Touches auth → Saeed's
   sign-off required.
2. **Real HMAC secret COMMITTED TO GIT** — `config/security/keys/voice_agent_hmac_secret.txt`,
   64 bytes, tracked since ff699b5, pushed to GitHub. Needs **ROTATION** — it is in history,
   so deleting/untracking does not help. The `config/*secret*` ignore rule never matched it
   because gitignore globs do not cross `/`.
3. **`C:\JeffLocal` AND `C:\JeffLocal\config` are writable by Authenticated Users** (verified
   directly). This is the root cause that made a secrets-loader RCE reachable. Fixing only the
   flagged `Authenticated Users` ACE is NOT enough — `CodexSandboxUsers`, an orphan SID, and a
   generic-rights ACE (renders as `-536805376`) also grant write. Needs BOTH directories, plus
   a service-restart test.
   **FIX SCRIPT READY 2026-07-17 evening:** `scripts\service_control\fix_directory_acl.ps1` — reads
   current permissions, removes the 4 bad grantees from both folders, verifies, reminds you to
   restart-test. Written but NOT run (changing Windows security settings is not something Claude
   runs directly). **REMINDER: Saeed asked to be reminded to run this — carry forward every
   session until done.**

### What is working
- **CLAUDE.md updated 2026-07-17 evening per Saeed's direct instruction:** honesty rule and
  confidence-tag rule reaffirmed (both already existed as rules 4/5), /caveman + /superpowers now
  explicitly always-on for every response (not just session start), fourth-grade-simple-English
  language added throughout. Read CLAUDE.md itself for the exact wording, don't rely on this bullet.
- **`.claude/settings.json` permission allowlist expanded 2026-07-17 evening** (`/fewer-permission-prompts`
  run) — added genuinely read-only Bash/MCP patterns found in 27 recent transcripts. Full list in
  git history / CHANGELOG.
- **Multi-tenancy steps 1-2 MERGED AND DEPLOYED 2026-07-17** (06af07e, 390f774). Secrets loader
  (allowlisted, ACL-checked, never logs values) + `JEFFLOCAL_DB_PATH` env var (TDD'd) +
  `-Tenant` launcher param (no-flag path verified byte-for-byte unchanged) + tenant onboarding
  scaffolding (template + Test Tenant 1 placeholder). Security Agent: APPROVE, two rounds, one
  real bug caught and fixed before merge (silently-failed env var set could have let a tenant
  fall through to the DEFAULT database — cross-tenant data mixing). New committed, mutation-tested
  PowerShell regression suite (`scripts/service_control/tests/test_load_tenant_config.ps1`) —
  this repo had no PS test framework before today. 391 Python tests + 12 PS assertions, all green
  on the production tree post-merge. Also cleaned ~19 stray 0-byte files (root + dashboard/) left
  by unquoted `<`/`>` characters reaching git-bash as real redirect operators — recurring since
  26 June, harmless (all empty), root cause documented in session log.
- Production dashboard LIVE at dashboard.app-avamed.uk (port 8765) — **redeployed 2026-07-17 on merged main (ebd395f)**, health-checked (case_count 78)
- **Dashboard beep FIXED and DEPLOYED 2026-07-17** (merge b53847a). Saeed reported a beep ~every
  minute. Root cause was two stacked bugs: (1) `import_handoffs()` re-upserted EVERY handoff file
  on every pass — only failures moved out to `failed/`, successes stayed in the inbox and were
  re-read forever by the 60s in-process `_background_importer()` loop (never appears in the access
  log); (2) `upsert_case()` preserved 9 staff fields but NOT `imported_at`, so each pass re-stamped
  it to "now". Five test handoffs from 14 Jul were re-imported every 60s for two days, making
  two-day-old cases look brand new — `/api/cases/new-since` then correctly reported 5 "new" cases
  and the client beeped 5x at once, once a minute. The beep poll was never at fault. **Also fixed
  analytics**: `api_hourly_volume` reads `imported_at`, so stale cases were counted as today's
  arrivals every day. Fix: `FIRST_SEEN_FIELDS` preserves `imported_at`; successful files retire to
  `outputs/handoff_json/processed/`. Verified live: `imported_at` held still across 70s.
- **CASE-LOSS REGRESSION found and fixed same session** (ebd395f). The retire fix made running
  pytest in the production tree MOVE real pending handoffs: `main.py`'s startup hook calls
  `import_handoffs(conn)` with no dir → the real inbox, and TestClient fires that hook;
  `test_render_pages.py` also hardcoded the production dir. A test run imported the case into a
  throwaway DB and retired the file, so production's importer never saw it → patient's case
  silently lost. Proven with a canary. Fixed via an autouse fixture in conftest.py + `_handoff_copy()`
  + a guard test. Canary now survives a full suite run.
- **389 tests passing** in the production tree
- Watchdog monitoring 4 services: ProductionDashboard, N8n, Ollama, CloudflareTunnel -- CLEAN
- WhatsApp alerts: LIVE
- **375/375 tests passing** (335 unit/integration + 40 Playwright e2e — main branch, post router-decouple merge)
- **Router-coupling reduction COMPLETE, MERGED, AND DEPLOYED 2026-07-16** (this was the Fable 5 follow-up flagged 2026-07-15: 107 back-references from routers into main.py). main.py: 2,011 → 136 lines. New `app/case_domain.py` (81 names, pure business logic) and `app/paths.py` (path constants) extracted; 6 routers now import directly from case_domain/consts/db/models/paths instead of deferred `from ..main import X`. Back-references cut from 107 to 1 (system.py's `app.routes` inspection — genuine, documented circular-import exception). Security Agent AST-diff confirmed all 79 relocated functions/constants byte-identical, no behaviour change. Commit bccc6ed on main, production redeployed and confirmed via live health check + live Playwright e2e (40/40).
- **restart_all.ps1 FIXED 2026-07-16** (commit 6a4e59f) — no longer passes nonexistent -DashOnly/-N8nOnly to watchdog.ps1; verified working live for -DashOnly during this session's redeploy. -N8nOnly path still unverified live.
- **Item #2 (split main.py) COMPLETE, MERGED, AND DEPLOYED 2026-07-15** -- main.py: 4,782 → 2,011 lines (verified byte count, not estimated), zero inline @app routes remain, all routes in app/routers/. 3 bugs found and fixed pre-merge, Security Agent approved, independent Fable 5 evaluation done (honest score 4.5/10 — code moved cleanly but didn't reduce coupling; superseded by the 2026-07-16 decoupling work above). Commit 79bd895 on main.
- **Full 25-case isolated pipeline test 2026-07-14/15**: safety invariant held, all 6 red flags caught (incl. one buried mid-ramble), all 25 resolved correctly.
- **Fresh 5-case PRODUCTION batch test 2026-07-15**: all 5 imported and resolved via genuine browser clicks post-redeploy, 0 deadletter, locked safety fields (priority/safe_to_queue) confirmed unchanged after resolving the red-flag case.
- All security/quality fixes (Phase 1+2+3) APPLIED and in production (main branch)
- test_user account in DB (id=5, role=staff, PBKDF2 hash, test_pass)
- **n8n WF03 (Red Flag Scan) FIXED 2026-07-08** -- now succeeds on schedule (08:50 UTC confirmed)
- **n8n WF04 (Overdue Scan) FIXED 2026-07-08** -- same fix applied, next run 09:00 UTC
- **19 previously-approved backlog commits (20-26 Jun) found stranded, unpushed, in a side worktree** -- folded into the 2026-07-15 push to origin/main. GitHub `main` was nearly 3 weeks behind local state before this.

### Bugs found + fixed 2026-07-14/15 (pre-merge, Security Agent approved)
1. **`alert_row_to_display` NameError** -- `/` and `/requests` crashed (500) whenever a critical alert exists. Live on production since 13 Jul (predates process start). FIXED: added missing import, regression test added.
2. **`/api/search` batch_id column** -- queried a non-existent column, 500 on every page's search. Pre-existing (inherited from pre-refactor main.py, not introduced by the split). FIXED: removed batch_id, falls back to call_id.
3. **Notes-gate bypass** -- `update_case()` auto-filled a default outcome note before checking whether the case needed real staff notes, so red-flag/identity cases could resolve via the full-update path with no notes. Pre-existing (same bug in old main.py). FIXED: reordered to match the already-correct `quick_action()` pattern.
4. Also removed 2 dead duplicate functions (`clean_alert_message`, `is_modal_worthy_alert`) left behind in main.py after the alert extraction — real copies live in alert_queries.py.

### Bugs found in 2026-06-19 pipeline test run
1. **verification_status null** — REANALYSED 2026-06-23. Handoff JSON DOES contain `verification_status = "matched"` (confirmed from actual test JSON files). Pipeline and importer both correct. UX badge added 2026-06-23.
2. **canonical_request_type null** — FIXED 2026-06-24. Root cause: case_detail.html used raw `request_type` instead of `request_type_class` for badge CSS. Legacy subtypes (e.g. test_results_enquiry) got no styling. Now uses `request_type_class` (canonical).
3. **resolved_by not in /api/cases/{call_id} response** — FIXED 2026-06-23.
4. **cases sort to bottom when call_timestamp_sort is null** — FIXED 2026-06-23.

### UX improvements identified (priority order)
1. Client-side notes gate — disable Resolve button until notes filled for red flag/identity cases
2. Red flag visual treatment — unmissable styling (red border/background, not just a dot)
3. Verification status badge on case cards (needs Bug 1 fixed first)
4. Third-party caller badge (derived from pathway, not manual)
5. "Urgent Review" label → "999 Emergency" for red flag cases
6. "Assign to me" step to prevent two staff working same case
7. Worklist auto-refresh / polling (every 30s)
8. Human-readable request type labels when canonical_request_type null
Full detail: docs/reports/test-run-20260619-172712.md

### All security/quality fixes (Phase 1+2+3) -- in production
1. jefflocal_staff_id cookie auth bypass -- REMOVED
2. /api/alerts/ from public allowlist -- REMOVED
3. LLM identity fields blocked from patient matching pipeline -- DONE
4. SafeToQueueOverride in Get-JeffHandoffDisposition -- DONE
5. Per-user random salt for password/PIN hashing -- DONE
6. Session tokens hashed before DB storage -- DONE
7. Post-password-change redirect loop -- FIXED
8. DB indexes: sessions(expires_at), sessions(user_id), audit_events(timestamp) -- DONE
9. Import loop crash fix -- DONE
10. GDPR purge wired to production DB -- DONE
11. Dead code (unreachable elseif in Jeff.Handoff.ps1) -- REMOVED

### Blocking Pilot 1 go-live
- No real staff accounts (need names, roles, emails from Saeed)
- Governance gates 1-7 not completed
- Avamed not yet a registered company
- JEFF_WEBHOOK_SECRET not set -- must be set before any live Jeff traffic
- NHS SBS framework bid postponed to next submission window (Saeed decision 2026-06-19)

### Pending Saeed approvals / actions
1. **The 3 security items at the top of this file** — unauthenticated intake endpoint, HMAC
   secret in git history (needs rotation), directory ACLs on C:\JeffLocal + config.
   **REMINDER — fix script for item 3 is ready:** `scripts\service_control\fix_directory_acl.ps1`.
   Saeed to run manually (admin PowerShell). Carry this reminder forward every session until done.
2. **Multi-tenancy — IN BUILD, steps 1-3 of 8 done and deployed 2026-07-17.** Saeed decided
   (2026-07-16, clarified 2026-07-17): **separate database per tenant.** A tenant = a GP practice
   (Churchtown + 4 more planned) **or** St Marks. St Marks is simply tenant #2, a stand-alone
   pharmacy — NOT a special case, and it will never have "tenant pharmacies" beneath it. Each
   tenant's staff get logins scoped to their own tenant. **Avamed super-admin = a tenant switcher**
   (SETTLED 2026-07-17): switch tenant on the dashboard, view each tenant's data individually to
   provide support. NOT a merged cross-tenant view; NOT for practice staff. See
   governance/MULTI_TENANCY_PROPOSAL.md (§6 settled, §8 sequence). **Gates every tenant's go-live,
   including St Marks.**
   **Built and merged to main 2026-07-17:** step 1 (secrets loader, 06af07e) and step 2
   (`JEFFLOCAL_DB_PATH` env var + `-Tenant` launcher param + tenant onboarding scaffolding,
   390f774). No-tenant behaviour (today's production) is unchanged — verified. Test Tenant 1 is
   a placeholder fixture; St Marks confirmed by Saeed as the first REAL tenant to onboard (step 4).
   **Blocked from actually running any tenant** by open item #3 (config dir ACL) — see that item.
   **Step 3 DONE 2026-07-17 evening:** `scripts/tenant/migrate_to_tenant_db.py` built (TDD),
   Security-reviewed (1 real bug caught: missing source==dest guard, fixed pre-merge), merged to
   main, run against real production data with Saeed's on-the-day sign-off. Verified: 78 cases,
   5 staff_users, 1251 audit_events, all matching, integrity_check OK on both dashboard.sqlite and
   the new churchtown.sqlite. dashboard.sqlite untouched; live dashboard NOT yet repointed at
   churchtown.sqlite (that's step 4/5). One post-merge bug fixed same session: VERIFY_TABLES had
   wrong table names (staff/audit_log vs real staff_users/audit_events) — migration itself was
   unaffected (whole-file copy is table-name agnostic), only the verify step crashed; fixed and
   re-verified without re-copying. See CHANGELOG.md 2026-07-17 (evening) entry for full detail.
   **Next:** step 4, stand up the stmarks tenant instance + hostname + its staff accounts — still
   blocked by open item #3 (config dir ACL) below.
3. **Real staff accounts** -- provide names, roles, emails to unblock pilot go-live
4. **Governance gates 1-7 sign-off** -- cannot be delegated
5. **JEFF_WEBHOOK_SECRET** -- set before any live Jeff traffic (see #1 — endpoint is open until then)
6. **n8n API key rotation** -- confirmed "later"
7. **St Marks privacy-policy line** — drafted on branch `draft/privacy-avamed-processor` in
   SMCPHARMA, NOT pushed (that repo auto-deploys). Needs pharmacist/DPO review.

### St Marks integration — CODE COMPLETE, DELIBERATELY OFF
**St Marks is a TENANT** — a stand-alone pharmacy, tenant #2 alongside the GP practices. It is not
a special case and will never have "tenant pharmacies" beneath it. Multi-tenancy itself is for the
GP practices under JeffLocal (Churchtown + 4 more planned); St Marks just happens to be the tenant
that made the missing segregation visible first.

Both sides built and tested. **Do NOT set `STMARKS_INTAKE_SECRET` on either side.** The flow stays
off until multi-tenancy lands, otherwise St Marks data lands in the same database Churchtown staff
will later have accounts on. Avamed is the PROCESSOR for both controllers, so keeping tenants' data
apart is our Article 28/32 obligation. The same rule applies to standing up GP practice #2 — no
tenant's intake goes on into a shared database. See governance/STMARKS_DATA_SHARING_NOTE.md.
- JeffLocal side: `POST /api/intake/stmarks-contact` merged + deployed (da24bb2). Inert — fails
  closed with 503 while the secret is unset.
- St Marks side: `forwardToJeffLocal()` in SMCPHARMA/src/index.js, committed+pushed (f9209d9),
  tested via wrangler dev against an isolated local dashboard. Skips silently with no secret.

### Open technical tasks (priority order)
```
RANK | TASK                                               | AGENT    | STATUS
-----+----------------------------------------------------+----------+------------------
 1   | Fix n8n.py:319 HMAC fail-open; remove              | Security | SAEED SIGN-OFF (auth logic).
     | /api/n8n/test-intake-batch                         |          | Endpoint is OPEN right now.
 2   | Rotate voice_agent_hmac_secret.txt (in git history) | Security | SAEED. Rotation, not untracking.
 3   | ACLs on C:\JeffLocal + config (Auth'd Users write)  | DevOps   | SAEED. Both dirs, all ACEs. NOW
     |                                                    |          | ALSO BLOCKS TENANT ONBOARDING:
     |                                                    |          | verified 2026-07-17 the new
     |                                                    |          | tenant-config ACL check correctly
     |                                                    |          | refuses to start ANY tenant while
     |                                                    |          | config/ is writable like this.
 4   | Multi-tenancy: SEPARATE DB PER TENANT              | Backend  | STEPS 1-3 DONE + DEPLOYED
     | tenant = a GP practice OR St Marks. Avamed         |          | 2026-07-17 (commits 06af07e,
     | super-admin = tenant switcher, one tenant at a     |          | 390f774, 7d9792d, d0d1393).
     | time. (supersedes old "tenant_id / Phase 2")       |          | churchtown.sqlite created +
     |                                                    |          | verified. Step 4 (stand up
     |                                                    |          | stmarks instance) next, still
     |                                                    |          | blocked by item #3 (config ACL).
 5   | Merge feature/secrets-loader                       | DevOps   | DONE 2026-07-17 (06af07e).
     |                                                    |          | Security APPROVE after fixes.
 6   | Add lint (ruff/pyflakes) to test gate              | DevOps   | pyflakes caught 2 real bugs on
     |                                                    |          | 2026-07-16 that tests missed
 7   | Fix evening-brief script's corrupted-tail bug      | DevOps   | strategy_daily.ps1
 8   | index.html has 96 NUL bytes appended               | Frontend | grep sees it as BINARY and
     |                                                    |          | silently skips it. Use grep -a.
 9   | .pyc files are TRACKED in git (breaks git stash)   | DevOps   | Build artifacts in git
 10  | cases.created_at schema drift under GDPR purge     | Database | gdpr_purge.py:286 keys on a column
     |                                                    |          | absent from db.py/SCHEMA_V1.sql
 11  | purge_old_data.ps1 not registered in schtasks      | DevOps   | Security review; pre-existing
 12  | Remove legacy static-salt password fallback        | Backend  | verify auth.py before removing
 13  | n8n API key rotation                               | DevOps   | Before go-live
 14  | PostgreSQL instead of SQLite (Item #3)             | Database | Phase 2 — gives row-level security
```

### Item #2 router extraction log — COMPLETE
```
MODULE                        | ROUTES                                          | COMMIT   | STATUS
------------------------------+-------------------------------------------------+----------+--------
app/helpers.py                | shared helpers                                  | 6e8b6ed  | DONE
app/consts.py                 | dashboard constants                             | 9906852  | DONE
app/templates_config.py       | templates singleton                             | 770d97d  | DONE
app/routers/auth.py           | /login, /logout, /profile, /api/change-password | 88d8baf  | DONE
app/routers/staff.py          | /admin/staff/*, /api/staff/*                    | b1a6e87  | DONE
app/alert_queries.py + alerts | /api/alerts/*, /alerts/*                        | 678aeac  | DONE
app/routers/analytics.py      | /api/analytics/*, /api/patient-card, /api/search | fedacfb | DONE
app/routers/n8n.py            | /api/n8n/* (incl. test-intake-batch)            | d71ddf3,7fc1030 | DONE
app/routers/system.py         | /favicon.ico, /api/health, /api/services/*, etc | 984b9e4  | DONE
app/routers/pages.py          | /, /requests, /patients, /reports, /settings,   | 7004592  | DONE
                              | /import, /api/import                            |          |
app/routers/cases.py          | /case/*, /api/cases/*, /api/calls/*/recording   | abc48e0  | DONE
```
main.py: 4,782 → 2,011 lines. Zero inline @app routes. MERGED TO MAIN 2026-07-14, DEPLOYED TO PRODUCTION 2026-07-15 (commit 79bd895).

### Completed this session (2026-07-15, continuation)
- Full isolated 25-case pipeline test (real n8n webhook, live Ollama, production untouched) — safety invariant held, all 6 red flags caught, all 25 resolved correctly
- Independent Fable 5 evaluation of the refactor — score 4.5/10, corrected 2 of the Lead's own claims (pre-existing vs refactor-caused), found 107 main.py<->router back-references (coupling not reduced)
- Fixed 3 bugs (alert import NameError, /api/search batch_id, notes-gate ordering), Security Agent APPROVE
- Merged feature/refactor-2-5-6 into main (79bd895), discovered + pushed 19 stranded Saeed-approved backlog commits
- Redeployed production :8765 onto merged main (C:\JeffLocal itself is the production directory — was checked out on the feature branch, which is how the crash bug went live)
- Fresh 5-case batch sent through real n8n webhook into production, resolved via genuine browser clicks incl. the red-flag case — locked fields (priority/safe_to_queue) confirmed unchanged after resolve

### Completed previous session (2026-07-14 full session)
- app/routers/pages.py: 7 page routes extracted (commit 7004592), 8 structural tests GREEN
- app/routers/cases.py: 10 case routes extracted (commit abc48e0), 11 structural tests GREEN
- app/routers/n8n.py: test-intake-batch + 10 helpers added (commit 7fc1030)
- test_api_endpoints.py: monkeypatches updated for all moved functions
- 323/323 tests GREEN (branch feature/refactor-2-5-6)
- main.py: 4,634 → 2,010 lines — ZERO inline routes remain

### Completed previous session (2026-07-08)
- gemma4:e4b (9.6 GB) installed — confirmed fallback model available (commit a168af8)
- SQLite hot backup script: scripts/backup/backup_db.py — 22/22 TDD tests GREEN, Task Scheduler entry JeffLocal-SQLiteBackup at 02:15 daily (commit a168af8)
- graphify updated: 1801 nodes, 3785 edges

### n8n fix notes (2026-07-08)
- Root cause: 3 endpoints called by n8n had no auth bypass → 302 HTML redirect → n8n crash
- Fix: renamed all 3 to `/api/n8n/` prefix (covered by AUTH_PUBLIC_PREFIXES at main.py:101)
  - GET /api/red-flags → /api/n8n/red-flags (main.py:2497)
  - GET /api/overdue → /api/n8n/overdue (main.py:2520)
  - POST /api/alerts/log → /api/n8n/alerts/log (main.py:3390)
- n8n workflow nodes updated via scripts/service_control/fix_n8n_auth_urls.py
- WARNING: n8n MCP update_workflow always fails — always use Python HTTP PUT script
- WARNING: when fixing n8n auth, audit ALL HTTP nodes in a workflow (not just the first)
DONE 2026-06-26:
- Investigated missing session log issue. Root cause: auto-generated log used plain prose, brief parser needs bullets.
- Fixed strategy_daily.ps1: Evening mode now auto-writes bullet-format session log if no human session ran.
- Fixed strategy_daily.ps1: Evening mode now creates/prunes restore tags automatically after each day.
- Deleted all pre-Phase1AB backup folders (PRE_PHASE1AB_20260602*, RESTORE_POINT_20260529, p1_ux_20260523*) — Saeed approved. All code preserved in git history.
- Fixed main.py: LOCAL_SERVICE_URLS port 5000→8765; api_hourly_volume and api_performance_summary use imported_at not created_at.
- Restore tags pruned to 3: restore/2026-06-24-1800, restore/2026-06-25-1800, restore/2026-06-26-1800.
- Added .graphifyignore — scopes code graph to source only, excluding .claude/, docs/, backups/ (graph: 3972→1678 nodes).
- Logged tech-debt Phase 1 remediation in CHANGELOG.md (B1/D1/DOC1/I1–I3 items). Security verdict: APPROVE-WITH-NOTES.
- Commits: 5591564 → 22e363a → e12a19c

DONE 2026-06-24:
- Pipeline batch AVA-LIVE-20260624: 5/5 cases end-to-end, safety invariants confirmed
- Staff simulation PASS — locked fields intact on all 5 resolved cases
- Fix: request_type_class used for badge CSS in case_detail.html (Bug #2 root cause)
- Fix: outcome_notes textarea id + label for (WCAG label association)
- Fix: resolve button title tooltip (disabled state explains why)
- Fix: JS notes gate WHY comment + getElementById
- Fix: case card tabindex=0 + Enter/Space keydown (keyboard nav)
- Fix: resolve button min-height 44px (WCAG touch target)
- Fix: resolved red-flag rows keep faint left border (audit trail)
- Fix: _TS_SORT constant extracted from duplicate COALESCE expression

DONE 2026-06-23:
- UX: verification status badge, red flag card treatment, notes gate
- resolved_by + resolved_at in API response
- Worklist sort fallback, patient hint SQL fix
- Webhook renamed jefflocal-test-intake → ava-live-intake (17 files + n8n workflow)
- 9 stale docs archived

---

## KEY FILE PATHS

```
C:\JeffLocal\PROJECT_MEMORY.md                  â† THIS FILE â€” update every session
C:\JeffLocal\CLAUDE.md                          â† Rules (read every session)
C:\JeffLocal\docs\sessions\                     â† Per-session summaries
C:\JeffLocal\docs\reports\                      â† Daily reports (YYYY-MM-DD.md)
C:\JeffLocal\dashboard\app\main.py              â† PRODUCTION FastAPI app
C:\JeffLocal\dashboard\app\auth.py              â† Auth module
C:\JeffLocal\dashboard\app\db.py                â† Database module
C:\JeffLocal\app\process_queue.ps1              â† PowerShell pipeline
C:\JeffLocal\app\modules\Jeff.Handoff.ps1       â† Handoff disposition logic
C:\JeffLocal\app\build_handoff.ps1              â† Handoff builder
C:\JeffLocal\scripts\daily\send_whatsapp.py     â† WhatsApp alert sender
C:\JeffLocal\scripts\service_control\watchdog.ps1 â† Service watchdog
C:\JeffLocal\logs\service_control\alerts_muted  â† DELETE THIS to re-enable WhatsApp alerts
C:\JeffLocal\config\model_settings.json         â† model: gemma4:e2b, temp: 0.1
C:\JeffLocal\config\pathways.json
C:\JeffLocal\config\routing_rules.json
C:\JeffLocal\config\model_monitoring.json
```

---

## GIT STATE

```
Repo:    https://github.com/JeffMedAI/tests
Branch:  main. C:\JeffLocal (the repo root) IS the production directory — its checked-out
         branch determines what code runs on :8765. Confirmed on main as of 2026-07-15.
         ALWAYS verify with `git branch --show-current` before assuming this.
Main:    merged 2026-07-14 (feature/refactor-2-5-6 → main, Saeed approved, commit 79bd895),
         deployed to production 2026-07-15.
Latest:  39ea3d8 fix: replace 4th-grade brief tone with non-technical business/PM tone
         (2026-07-17 22:21). No commits since — checked 2026-07-18 18:00 automated session-end,
         nothing landed today.
Previous: d0d1393 fix: correct VERIFY_TABLES to real schema, harden verify error handling —
         post-merge bug fix, table names corrected (staff_users/audit_events), 15/15 green.
Previous: 84bea00 chore: expand read-only Bash/MCP permission allowlist (.claude/settings.json).
Previous: 7d9792d Merge feature/multitenancy-db-migrate into main — multi-tenancy step 3:
         migrate_to_tenant_db.py (TDD, Security APPROVE WITH CHANGES — source==dest guard added
         pre-merge). Real migration run against production 2026-07-17 evening, Saeed-approved on
         the day: churchtown.sqlite created and verified (78 cases, 5 staff_users, 1251
         audit_events, integrity OK both sides). dashboard.sqlite untouched, live dashboard not
         yet repointed.
Previous: 390f774 Merge feature/multitenancy-db-path into main — multi-tenancy step 2:
         JEFFLOCAL_DB_PATH env var (TDD'd) + -Tenant launcher param (no-flag path verified
         unchanged) + tenant onboarding scaffolding (template + Test Tenant 1 placeholder).
         Security APPROVE after 2 rounds (real bug closed: silently-failed env var set could
         have let a tenant fall through to the default database). New committed, mutation-tested
         PS regression suite. 391 tests + 12 PS assertions green. Deployed to disk 2026-07-17
         (launcher/config plumbing, not live Python — dashboard process itself not restarted).
Previous: 06af07e Merge feature/secrets-loader into main — step 1 of multi-tenancy. Allowlisted
         secrets loader for JEFF_WEBHOOK_SECRET/STMARKS_INTAKE_SECRET, directory-ACL checked,
         never logs values. Security APPROVE after striking overclaims (false test_mode-gating
         claim, ACL "trust boundary" overclaim) and capping the refused-key log line. 2026-07-17.
Earlier: bccc6ed Merge feature/router-decouple-main into main — extracted case_domain.py (81
         names) and paths.py out of main.py (2,011→136 lines), cut router↔main.py back-refs
         from 107 to 1 (system.py's documented app.routes exception). Security Agent AST-diff
         approved (byte-identical relocations). 375/375 tests green, production redeployed via
         restart_all.ps1 -DashOnly, live e2e re-run 40/40. Deployed and confirmed 2026-07-16.
Earlier still: 6a4e59f fix: restart_all.ps1 no longer passes nonexistent switches to watchdog.ps1 —
         was passing -DashOnly/-N8nOnly through to watchdog.ps1 (which only accepts -Once/
         -Force/-IntervalSeconds), crashing with "parameter cannot be found". Now restarts
         each service directly via the same launchers watchdog uses, and passes -Once for the
         full-restart path so it no longer hangs.
Earlier: 79bd895 Merge feature/refactor-2-5-6 into main — router-split complete (main.py
         4,782→2,011 lines), 3 bugs fixed and Security-reviewed pre-merge (alert-import crash,
         /api/search batch_id, notes-gate bypass). Plus 19 previously-unpushed backlog commits
         (20-26 Jun) folded into the same push — found stranded in a side worktree, now on
         origin/main. Production redeployed 2026-07-15 and confirmed running this code.
test_user: id=5, role=staff, username=test_user (Playwright E2E)
```

---

## TECHNICAL STACK

```
Dashboard:    FastAPI (Python 3.14), Jinja2 templates, SQLite
AI:           Ollama / gemma4:e2b (confidence floor 0.72, fallback gemma4:e4b)
Auth:         Session cookies (httponly, samesite=lax) â€” tokens hashed in DB
Database:     SQLite at dashboard\data\dashboard.sqlite
Remote:       Cloudflare tunnel (HTTPS termination external)
Workflow:     n8n (localhost:5678, webhook: ava-live-intake)
Voice agent:  Jeff (Hostcomm UK, external, posts to n8n webhook)
Monitoring:   Watchdog (restarts services if down, checks every 60s)
```

---

## KNOWN PROCESS RULES (hard lessons)

1. **Sandbox removed 2026-06-07.** No sandbox directory exists. Dev work on git branches.
   Production = port 8765, C:\JeffLocal\dashboard\. Always verify path before editing.

2. **Cookie security:** All cookie-setting calls must work correctly under Cloudflare HTTPS.

3. **Agents do not self-authorise production changes.** Saeed's "approved" in chat required.

4. **Approvals do not carry over between sessions.** Re-confirm every session.

5. **Security Agent reviews ALL PRs** â€” even one-line changes. Veto is independent.

6. **WhatsApp incident 2026-06-01** â€” NEVER use coordinate-based navigation to select a
   WhatsApp chat recipient. ALWAYS use search-by-name/number, verify header, THEN send.
   If header does not match: ABORT. Rule enforced in send_whatsapp.py.

7. **Watchdog elevated process** -- Task Scheduler registered watchdog as elevated.
   Cannot be killed by non-elevated code. Only admin Task Manager can kill it.
   Resolved 2026-06-08: ghost process killed via admin Task Manager, alerts re-enabled.
   Lock file guard prevents duplicate instances going forward.

8. **Legacy static-salt password fallback** -- auth.py verify_password() still accepts old
   static-salt format for accounts not yet upgraded. Remove once all staff have logged in once.

9. **C:\JeffLocal is the production directory itself** -- its git branch determines what code
   actually runs on :8765 (uvicorn serves these files directly, no separate deploy copy).
   Switching branches here changes production code under the running process; a restart is
   required to load it. Always check `git branch --show-current` in C:\JeffLocal before
   assuming production is on main — this is how a crash bug shipped live 13 Jul (2026-07-15).

10. **restart_all.ps1 fixed 2026-07-15** (commit 6a4e59f) -- previously passed
    `-DashOnly`/`-N8nOnly` through to watchdog.ps1, which only accepts `-Once`/`-Force`/
    `-IntervalSeconds`, crashing with "parameter cannot be found". Now restarts each service
    directly via the same launchers watchdog uses (`_launch_dashboard.ps1`/`_launch_n8n.ps1`),
    and passes `-Once` to watchdog for the full-restart path so it no longer hangs.

11. **Session cookies expire after 1 hour** (max_age=3600). Long manual dashboard sessions can
    get logged out mid-form — re-login and retry, no data loss.

12. **19:00 evening-brief automation can commit to main mid-session** (documented, by design —
    fallback session-end write if no human close has happened yet). Fetch before assuming your
    local view of main is current. It also has a bug: leaves PROJECT_MEMORY.md's session-end
    checklist truncated — check scripts\daily\strategy_daily.ps1 if this recurs.

---

## SESSION STARTUP CHECKLIST

```
1. Read CLAUDE.md
2. Read this file (PROJECT_MEMORY.md)
3. Read docs\sessions\ â€” yesterday's and today's logs
4. git log --oneline -10
5. Read docs\reports\{yesterday}.md
6. Produce session start report, WAIT for Saeed's go-ahead
```

---

## SESSION END CHECKLIST

```
1. Write session summary to docs\sessions\YYYY-MM-DD-HHMM.md
2. Update this file â€” status, tasks, git state
3. git add PROJECT_MEMORY.md docs\sessions\ && git commit -m "memory: session YYYY-MM-DD"
4. git push origin HEAD
5. Tell Saeed: "Session saved. Memory updated. Ready to pick up tomorrow."
```

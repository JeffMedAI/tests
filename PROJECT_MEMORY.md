# PROJECT MEMORY â€” JeffLocal
# READ THIS FIRST at every session start, before doing anything else.
# Last updated: 2026-07-07 (auto-updated 18:00)
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

## CURRENT STATUS -- 2026-07-08

### What is working
- Production dashboard LIVE at dashboard.app-avamed.uk (port 8765)
- Watchdog monitoring 4 services: ProductionDashboard, N8n, Ollama, CloudflareTunnel -- CLEAN
- WhatsApp alerts: LIVE
- **144/144 pytest tests passing** (unit/integration — test_locked_fields.py refactoring added 40 tests)
- **40/40 Playwright E2E tests passing** (installed 2026-06-19, 4 fixes applied)
- **sandbox branch merged to main** (2026-06-19, via git worktree, Saeed approved)
- **Full pipeline test run 2026-06-19**: 5 fresh cases (CSV-FRESH-20260619-1315) sent end-to-end, all 5 resolved via staff simulation. Safety invariants confirmed — LLM cannot override priority or verification_status.
- All security/quality fixes (Phase 1+2+3) APPLIED and in production (main branch)
- test_user account in DB (id=5, role=staff, PBKDF2 hash, test_pass)
- **n8n WF03 (Red Flag Scan) FIXED 2026-07-08** -- now succeeds on schedule (08:50 UTC confirmed)
- **n8n WF04 (Overdue Scan) FIXED 2026-07-08** -- same fix applied, next run 09:00 UTC

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
1. **Real staff accounts** -- provide names, roles, emails to unblock pilot go-live
2. **Governance gates 1-7 sign-off** -- cannot be delegated
3. **JEFF_WEBHOOK_SECRET** -- set in environment before any live Jeff traffic
4. **n8n API key rotation** -- confirmed "later"

### Open technical tasks (priority order)
```
RANK | TASK                                              | AGENT    | STATUS
-----+---------------------------------------------------+----------+------------------
 1   | Remove legacy static-salt password fallback       | Backend  | PENDING (NOTE: already done in auth.py — verify before removing from list)
 2   | n8n API key rotation                              | DevOps   | Before go-live
 3   | Set JEFF_WEBHOOK_SECRET                           | DevOps   | Before live traffic
 4   | Run full Playwright E2E suite post-UX changes     | Test     | Next session
 5   | Split main.py into modules (refactor/split-main-py branch) | Backend | PENDING — plan written, not started
 6   | Multi-tenancy tenant_id                           | Database | Phase 2
```

### Completed this session (2026-07-08)
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
Branch:  sandbox (production code)
Main:    merged 2026-06-19 (sandbox → main via worktree)
Latest:  a168af8 feat: SQLite hot backup — TDD tests, script, Task Scheduler entry
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







































# PROJECT MEMORY â€” JeffLocal
# READ THIS FIRST at every session start, before doing anything else.
# Last updated: 2026-06-07 (auto-updated 07:00)
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
**Pilot site:** Churchtown Medical Centre, Southport

---

## CRITICAL PATH DISTINCTION â€” READ EVERY SESSION

```
PRODUCTION  = C:\JeffLocal\dashboard\        Port 8765  Watchdog-managed  LIVE
SANDBOX     = C:\JeffLocal\sandbox\dashboard\ Port 5000  Manual start      SAFE TO EDIT

Git branch name "sandbox" does NOT mean you are in the sandbox directory.
Always verify the path before editing. Production changes require Saeed approval.
```

---

## APPROVAL PROTOCOL

Saeed's explicit "approved" in chat is required for:
- Any change to production files (C:\JeffLocal\dashboard\)
- Any change to enforce_auth.py or patient_matcher.py
- Any new external dependency
- Any database migration on live data
- Major document changes
- Any marketing content before external publication

"Do it yourself" is NOT authorisation. Approvals do NOT carry over between sessions.
Re-confirm every session.

---

## AGENT TEAM (8 agents â€” all CLAUDE.md files at C:\JeffLocal\sandbox\agents\)

```
Agent      | File                              | Role
---------- | --------------------------------- | ------------------------------------
lead       | lead/lead_CLAUDE.md               | Orchestrator, human liaison
backend    | backend/backend_CLAUDE.md         | Flask, Python, Ollama, n8n webhook
frontend   | frontend/frontend_CLAUDE.md       | Dashboard UI, CSS, React/Jinja2
database   | database/database_CLAUDE.md       | SQLite, migrations, GDPR purge
test       | test/test_CLAUDE.md               | pytest + Playwright E2E
security   | security/security_CLAUDE.md       | GDPR, NHS, OWASP, PR veto authority
devops     | devops/devops_CLAUDE.md           | Git, deployment, Task Scheduler
strategy   | strategy/strategy_CLAUDE.md       | Docs, reports, marketing
```

Security Agent has VETO authority over all PRs. Lead Agent enforces vetoes.

---

## CURRENT STATUS (as of 2026-06-07 13:35 — watchdog recovery, n8n key rotation, deploy readiness)

### What is working
- Production dashboard LIVE at dashboard.app-avamed.uk
- Cookie fix: LIVE in production
- All 4 missing config files: DONE
- N1/N2 fixes: DONE and VERIFIED
- Watchdog: REWRITTEN — all 5 services, restart cap 3/hr, WhatsApp alerts
- WhatsApp daily report delivery: DONE (07:00 scheduled, confirmed delivered)
- Strategy Agent: fully onboarded
- **Test suite: ALL 149 tests passing** — commit 43df75a
- **Watchdog: FIXED (PS5.1 compat)** — commit ce422eb
- **Digit-normalized search: INCORPORATED** — commit 136f415
- E2E call flow test: Stages 1-4 PASSING
- HMAC-SHA256 webhook verification: DONE — 14/14 tests
- Password reset end-to-end: DONE — 28/28 tests
- GDPR 90-day purge script: DONE — atomic, dry-run mode
- G1 governance breach: FORMALLY CLOSED
- **Case detail header: COMPACT (3-row inline)** — commit 43df75a
- **Sticky header: DONE** — commit 43df75a
- **Pill consistency: DONE** (summary_chips everywhere) — commit 43df75a
- **Pipeline safety: RED FLAG REGEX FIXED** (pains plural, contractions, arm pain, carer signal) — commit 43df75a
- **Ollama fail-safe: DONE** (failure → staff_review_required=true) — commit 43df75a
- **Internal codes sanitized in display text** — commit 43df75a
- **Session sign-out bug FIXED** (secure=True removed from HTTP cookie) — commit 43df75a
- **Locked fields hidden from non-admin** — commit 43df75a
- **Inline copy icons** on identifiers, staff task, patient record note — commit 43df75a
- **34-item safety/UX audit completed** — critical pipeline issues fixed; 20+ UX items queued
- NHS SBS Framework proposal: DRAFTED
- n8n webhook path confirmed: jefflocal-test-intake
- WhatsApp Business integration: DAY 1 COMPLETE — awaiting Meta credentials from Saeed
- **Watchdog fully recovered (2026-06-07)** — scheduled task re-registered (JeffLocal-Watchdog-task via XML import), Registry Run key restored, _launch_sandbox.ps1 created, sandbox dashboard UP
- **n8n encryption key rotated (2026-06-07)** — new key active, no credentials lost
- **Sandbox deploy-ready (2026-06-07)** — Security Agent APPROVED 6-file deploy after secure=True cookie fix. AWAITING SAEED APPROVAL TO DEPLOY.

### Blocking Pilot 1 go-live
- No real staff accounts (need names, roles, emails from Saeed)
- No dedicated pilot URL confirmed
- Governance gates 1-7 not completed

### Pending Saeed approvals (action required)
1. **[DEPLOY READY] Deploy sandbox → production** — Security Agent APPROVED. 6 files: __init__.py, audit.py, auth.py, importer.py, models.py, main.py. Excludes whatsapp_*.py (Phase 2). Say "approved" to proceed.
2. **[ADMIN REQUIRED] Create GDPRPurge-Production scheduled task** — Register-ScheduledTask failed "Access is denied" in normal PowerShell. Open elevated PowerShell (Run as Administrator) and create: Python = C:\JeffLocal\sandbox\dashboard\.venv\Scripts\python.exe, script = C:\JeffLocal\scripts\daily\gdpr_purge.py, args = --db "C:\JeffLocal\dashboard\data\dashboard.sqlite" --days 90, trigger = Daily at 02:00
3. **WhatsApp Day 2 ACTION: Complete Meta Business account setup** — see docs/project_documents/Meta_WhatsApp_Setup_Guide.md — estimated 60 min.
4. **WhatsApp governance: Accept Meta DPA** — required before go-live (see governance/WHATSAPP_GDPR_ADDENDUM.md)
5. **NHS SBS registration on Ariba Network** — DEADLINE 23 June 2026. Register at ariba.com before submission.
6. **[DONE] n8n encryption key rotated (2026-06-07)** — new key active. Old key `L3cUkqVwNM3gSaVUwdb0E4/wYXSNJ7Ci` retired. No credentials were stored so no re-import needed.

### Pending research / future tasks
- OpenJarvis pilot: onboarding plan READY at docs\project_documents\Jarvis_Onboarding_Plan.md.

### Open technical tasks (priority order)
```
RANK  | TASK                          | AGENT          | STATUS
------+-------------------------------+----------------+-----------------------------------
 1    | HMAC payload verification n8n | Backend Agent  | Assigned — IR-01, sec review req'd
 2    | Password reset end-to-end     | Backend Agent  | COMPLETE (sandbox) — SECURITY APPROVED, deploy pending Saeed
 3    | GDPR 90-day purge script      | Database Agent | COMPLETE (sandbox) — prod gate pending Saeed
 4    | E2E pipeline gap (n8n→DB)     | Backend Agent  | NEW — Stage 3 blocked by this
 5    | All 149 tests passing         | Test Agent     | COMPLETE — commit 1aba9aa
 6    | Full Playwright E2E suite     | Test Agent     | Pending (after tasks 1 and 4 done)
 7    | Multi-tenancy tenant_id       | Database Agent | Pending
 8    | Daily task scripts            | DevOps Agent   | Pending
 9    | Issue #1 retroactive sign-off | Strategy Agent | Pending (LOW)
```

### Pending Saeed actions (blocking pilot go-live)
```
A | Real staff accounts (names, roles, emails)  | Unblocks password reset acceptance + go-live
B | Dedicated pilot URL confirmation             | Unblocks governance docs + DevOps Cloudflare config
C | Governance gates 1–7 sign-off               | Blocks go-live — cannot be delegated to agents
```

### Assignment brief
Full assignment briefs with acceptance criteria:
  docs\reports\phase1_assignments_2026-05-30.md

---

## KEY FILE PATHS

```
C:\JeffLocal\PROJECT_MEMORY.md                     â† THIS FILE â€” update every session
C:\JeffLocal\docs\project_documents\JeffLocal_Master_Strategy_v1.2.docx   <- Master strategy doc
C:\JeffLocal\docs\project_documents\JeffLocal_Dispatch_Report_20260529.docx <- Latest dispatch report
C:\JeffLocal\rules\                                 <- rules system (output, quality, boundaries)
C:\JeffLocal\governance\GOVERNANCE_FRAMEWORK.md     â† Governance rules
C:\JeffLocal\governance\CHANGE_LOG.md               â† All approved changes
C:\JeffLocal\docs\reports\                          â† Daily reports (YYYY-MM-DD.md)
C:\JeffLocal\docs\reports\2026-05-29.md             â† Today's full session log
C:\JeffLocal\sandbox\agents\                        â† All 8 agent CLAUDE.md files
C:\JeffLocal\scripts\daily\strategy_daily.ps1       â† Daily report script (07:00)
C:\JeffLocal\dashboard\app\main.py                  â† PRODUCTION Flask app
C:\JeffLocal\sandbox\dashboard\app\main.py          â† SANDBOX Flask app
C:\JeffLocal\backup\PRODUCTION_BACKUP_20260522_143554\ â† Production backup
C:\JeffLocal\backups\RESTORE_POINT_20260529\        â† Latest restore point
```

---

## GIT STATE

```
Repo:    https://github.com/JeffMedAI/tests
Branch:  sandbox
Latest:  b8b91b3 feat: caveman daily briefing format ÔÇö tighter morning report
Tag:     RESTORE_20260529
Author:  215987900+Avamedio@users.noreply.github.com
```

---

## TECHNICAL STACK

```
Dashboard:      Flask (Python 3.14), Jinja2 templates, SQLite
AI:             Ollama / gemma4:e2b (confidence floor 0.72, fallback gemma4:e4b)
Auth:           Session cookies (httponly, samesite=lax, secure=True via Cloudflare)
Database:       SQLite at dashboard\data\dashboard.sqlite
Remote access:  Cloudflare tunnel (HTTPS termination external)
Workflow:       n8n (localhost:5678)
Voice agent:    Jeff (external, posts to n8n webhook)
Monitoring:     Watchdog (restarts dashboard if down), checks every 5 min
```

---

## SESSION STARTUP CHECKLIST (run this every time)

```
1. Read this file (PROJECT_MEMORY.md) â€” done when you are reading this
2. Read today's daily report: docs\reports\{today}.md (if exists)
3. Check git: git log --oneline -5
4. Check pending approvals list above
5. Report to Saeed before doing anything:
   - What is pending (approvals, tasks)
   - What is recommended next
   - Any blockers
   Then WAIT for Saeed's go-ahead.
```

---

## SESSION END CHECKLIST (run this at end of every session)

```
1. Update "Current Status" section above
2. Update "Open technical tasks" table
3. Update "Pending Saeed approvals" list
4. Update "GIT STATE" with latest commit hash
5. git add PROJECT_MEMORY.md && git commit -m "memory: update session YYYY-MM-DD"
6. git push origin HEAD
```

---

## KNOWN PROCESS RULES (hard lessons)

1. Production breach 2026-05-29 — git branch name does NOT indicate environment.
   Always verify path before editing. Production = port 8765, C:\JeffLocal\dashboard\.
   Sandbox = port 5000, C:\JeffLocal\sandbox\dashboard\.

2. All cookie-setting calls must include secure=True (Cloudflare handles HTTPS externally).

3. Agents do not self-authorise production changes. “I thought it was safe” is not
   sufficient. Saeed's “approved” in the chat is required.

4. Approvals do not carry over between sessions. Re-confirm every session.

5. Security Agent must review ALL PRs, even one-line changes.

6. WhatsApp incident 2026-06-01 — NEVER use coordinate-based navigation to select a
   WhatsApp chat recipient. Chat list order changes between sessions. ALWAYS use
   search-by-name/number, verify the chat header shows the correct recipient, THEN send.
   If header does not match: ABORT. Script: scripts\daily\send_whatsapp.py.
   Rule also in: sandbox\agents\backend\backend_CLAUDE.md (W1 INCIDENT section)
   and governance\GOVERNANCE_FRAMEWORK.md (Agent Communication Protocols).

---
*Update this file at the end of every session. It is the single source of truth
for project state and the first thing to read when starting fresh.*












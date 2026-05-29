# PROJECT MEMORY — JeffLocal
# READ THIS FIRST at every session start, before doing anything else.
# Last updated: 2026-05-29
# Maintained by: Claude (update at end of every session)

---

## WHO YOU ARE TALKING TO

**Saeed** — Founder, Avamed. Owner and sole approver of all production changes.
Email: 5256863@gmail.com | Phone: 07440 333938
GitHub: Avamedio (215987900+Avamedio@users.noreply.github.com)
Repo: https://github.com/JeffMedAI/tests (branch: sandbox)

---

## WHAT THIS PROJECT IS

**JeffLocal** — On-premises AI patient triage system for UK GP surgeries (Avamed).
Patients call the surgery → Jeff (voice AI) captures reason → verifies patient →
applies safety rules → delivers structured task to reception staff on a dashboard.
No clinical decisions. Admin intake only. All AI runs locally (Ollama/Gemma).
No patient data leaves the building.

**Core safety rule:** Ollama extracts and drafts. Deterministic code verifies,
matches, validates, and finalises. LLM output NEVER overrides verified patient data.

**Live dashboard:** https://dashboard.app-avamed.uk (Cloudflare tunnel → localhost:8765)
**Pilot site:** Churchtown Medical Centre, Southport

---

## CRITICAL PATH DISTINCTION — READ EVERY SESSION

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

## AGENT TEAM (8 agents — all CLAUDE.md files at C:\JeffLocal\sandbox\agents\)

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

## CURRENT STATUS (as of 2026-05-29 18:00)

### What is working
- Production dashboard LIVE at dashboard.app-avamed.uk
- Session cookie fix: written, tested, AWAITING SAEED SIGN-OFF
  (approval pack: C:\JeffLocal\APPROVAL_PACK_COOKIE_FIX_FINAL.md)
- Sidebar R3/R1/R2 implemented in sandbox, synced to production
- Bell badge on topbar: LIVE (deployed 2026-05-29, accepted by Saeed)
- All 4 missing config files created (model_settings, routing_rules, pathways, model_monitoring)
- Watchdog REWRITTEN (2026-05-29 Dispatch): now covers all 5 services (prod 8765, sandbox 5000,
  n8n 5678, Ollama 11434, Cloudflare tunnel) — restart cap 3/hr, WhatsApp alerts, CRITICAL on cap hit
  PENDING: git commit + Task Scheduler registration (Saeed to run manually — see session 2026-05-29-2000.md)
- Strategy Agent: fully onboarded (2026-05-29)
- Daily report script: UPDATED with state verification (drift detection vs PROJECT_MEMORY)
- WhatsApp daily report delivery: built and committed (5c80d76)

### Blocking Pilot 1 go-live
- No real staff accounts (need names, roles, emails from Saeed)
- No dedicated pilot URL confirmed (options: churchtown / pilot1 / gp .app-avamed.uk)
- Governance gates 1-7 not completed
- Cookie fix not yet deployed (needs Saeed sign-off)

### Pending Saeed approvals (action required)
1. Cookie expiry fix — approval pack ready at APPROVAL_PACK_COOKIE_FIX_FINAL.md
2. Sandbox "Status Degraded" fix — 1-line change in sandbox/dashboard/app/main.py
3. Sidebar sandbox changes — close as "already promoted" (production already has these)
4. TOOLING: Claude Desktop reinstall broke PowerShell computer-use (typing disabled, click-only). Needs fixing so Claude can type into PowerShell/terminal again. Check Claude Desktop settings or raise with Anthropic support.

### Open technical tasks (priority order)
```
HIGH   | Cookie fix deployment          | Backend Agent    | Awaiting Saeed sign-off
HIGH   | N1: externalise log path       | Backend Agent    | Pending
HIGH   | N2: log exception in nav count | Backend Agent    | Pending
HIGH   | Sandbox degraded fix           | Backend Agent    | Awaiting Saeed sign-off
MEDIUM | Full Playwright E2E suite      | Test Agent       | Pending
MEDIUM | n8n webhook integration tests  | Test Agent       | Pending
MEDIUM | GDPR 90-day purge script       | Database Agent   | Pending
MEDIUM | Multi-tenancy tenant_id        | Database Agent   | Pending
MEDIUM | Daily task scripts             | DevOps Agent     | Pending
LOW    | Issue #1 retroactive sign-off  | Strategy Agent   | Pending
```

---

## KEY FILE PATHS

```
C:\JeffLocal\PROJECT_MEMORY.md                     ← THIS FILE — update every session
C:\JeffLocal\JeffLocal_Master_Strategy_v1.2.docx   ← Master strategy doc
C:\JeffLocal\JeffLocal_Dispatch_Report_20260529.docx ← Latest dispatch report
C:\JeffLocal\APPROVAL_PACK_COOKIE_FIX_FINAL.md     ← Cookie fix approval pack (ready)
C:\JeffLocal\governance\GOVERNANCE_FRAMEWORK.md     ← Governance rules
C:\JeffLocal\governance\CHANGE_LOG.md               ← All approved changes
C:\JeffLocal\docs\reports\                          ← Daily reports (YYYY-MM-DD.md)
C:\JeffLocal\docs\reports\2026-05-29.md             ← Today's full session log
C:\JeffLocal\sandbox\agents\                        ← All 8 agent CLAUDE.md files
C:\JeffLocal\scripts\daily\strategy_daily.ps1       ← Daily report script (07:00)
C:\JeffLocal\dashboard\app\main.py                  ← PRODUCTION Flask app
C:\JeffLocal\sandbox\dashboard\app\main.py          ← SANDBOX Flask app
C:\JeffLocal\backup\PRODUCTION_BACKUP_20260522_143554\ ← Production backup
C:\JeffLocal\backups\RESTORE_POINT_20260529\        ← Latest restore point
```

---

## GIT STATE

```
Repo:    https://github.com/JeffMedAI/tests
Branch:  sandbox
Latest:  64b0620 — restore point 2026-05-29
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
1. Read this file (PROJECT_MEMORY.md) — done when you are reading this
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

3. Agents do not self-authorise production changes. "I thought it was safe" is not
   sufficient. Saeed's "approved" in the chat is required.

4. Approvals do not carry over between sessions. Re-confirm every session.

5. Security Agent must review ALL PRs, even one-line changes.

---
*Update this file at the end of every session. It is the single source of truth
for project state and the first thing to read when starting fresh.*

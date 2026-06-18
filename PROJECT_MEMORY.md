# PROJECT MEMORY â€” JeffLocal
# READ THIS FIRST at every session start, before doing anything else.
# Last updated: 2026-06-18 (auto-updated 07:00)
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
backend  | Flask, Python, Ollama, n8n webhook
frontend | Dashboard UI, CSS, Jinja2
database | SQLite, migrations, GDPR purge
test     | pytest + Playwright E2E
security | GDPR, NHS, OWASP â€” VETO authority over all PRs
devops   | Git, deployment, Task Scheduler
strategy | Docs, reports, governance, marketing
```

---

## CURRENT STATUS -- 2026-06-18 (18:00)

### What is working
- Production dashboard LIVE at dashboard.app-avamed.uk (port 8765)
- Watchdog monitoring 4 services: ProductionDashboard, N8n, Ollama, CloudflareTunnel -- CLEAN
- WhatsApp alerts: LIVE -- mute flag removed, tab fix and dedup active
- Phase 1+2+3 security/quality sprint: ALL 11 fixes APPLIED, Lead Agent APPROVED
- **Full end-to-end pipeline verified 2026-06-08**: Jeff webhook -> n8n -> dashboard -> Ollama -> DB -> case visible
- n8n WF06 fixed: no longer injects N8NTEST- prefixes; passes Jeff identifiers unchanged
- **104/104 pytest tests passing (2026-06-18)**: all unit/integration tests green. E2E blocked on playwright not installed.
- Governance gate artifacts created (Gates 2, 5, 6, 7): VALIDATION_RULES.json, PATHWAY_REGISTRY.md, HANDOFF_TEMPLATES.json, SCHEMA_V1.sql, DISASTER_RECOVERY_PLAN.md, RELEASE_GATE_CRITERIA.md, PIPELINE_HEALTH.md, DATABASE_HEALTH.md, runbooks

### Changes this session (2026-06-18) -- sandbox branch, PENDING Saeed approval to merge
1. **CLAUDE.md updated**: 8 rules (was 5) + restore point protocol added to session end
2. **test_importer.py rewritten**: 5 RAWMOCK file-dependent tests replaced with tmp_path JSON fixtures (TC- IDs)
3. **test_dashboard_active_metrics.py fixed**: test_reopen uses authed_client fixture (old jefflocal_staff_id cookie removed)
4. **N8NTEST prefix validation reverted**: hallucinated block removed from main.py; test deleted

### Still pending from prior sessions -- sandbox branch, PENDING Saeed approval to merge
1. **Panel layout fix** (commit a7c21d4): Compact action bar; full scrollable body in detail panel.
2. **Role-based sidebar redesign** (commit c00dc8c): Reception and Manager views separated in the left sidebar.
3. **Review confirmation checkbox** (commit 0c5f189): Added to detail panel — receptionist must tick before marking a case as reviewed.
4. **Review gate refined** (commit c230e91): Custom checkbox design with amber (unchecked) → green (checked) visual transition.

### ⚠️ Pending merge to production
- All five feature commits above are on the sandbox branch.
- Awaiting Saeed's explicit approval before merge to C:\JeffLocal\dashboard\.

### All security/quality fixes (Phase 1+2+3) -- Lead Agent endorsed 2026-06-08
1. jefflocal_staff_id cookie auth bypass -- REMOVED
2. /api/alerts/ from public allowlist -- REMOVED
3. LLM identity fields blocked from patient matching pipeline -- DONE
4. SafeToQueueOverride in Get-JeffHandoffDisposition -- DONE
5. Per-user random salt for password/PIN hashing -- DONE
6. Session tokens hashed before DB storage -- DONE (Saeed override 2026-06-08)
7. Post-password-change redirect loop -- FIXED
8. DB indexes: sessions(expires_at), sessions(user_id), audit_events(timestamp) -- DONE
9. Import loop crash fix -- DONE (failed files -> failed/ subdir, loop never crashes)
10. GDPR purge wired to production DB -- DONE
11. Dead code (unreachable elseif in Jeff.Handoff.ps1) -- REMOVED

### Blocking Pilot 1 go-live
- No real staff accounts (need names, roles, emails from Saeed)
- Governance gates 1-7 not completed
- Avamed not yet a registered company (blocks NHS SBS bid -- DEADLINE 23 June 2026)
- JEFF_WEBHOOK_SECRET not set -- HMAC verification currently skipped (must be set before live traffic)

### Pending Saeed approvals / actions
1. **NHS SBS Ariba registration** -- DEADLINE 23 June 2026. Register at ariba.com.
2. **Real staff accounts** -- provide names, roles, emails to unblock pilot go-live
3. **Governance gates 1-7 sign-off** -- cannot be delegated
4. **JEFF_WEBHOOK_SECRET** -- set in environment before any live Jeff traffic
5. **n8n API key rotation** -- confirm go-ahead

### Open technical tasks (priority order)
```
RANK | TASK                                         | AGENT    | STATUS
-----+----------------------------------------------+----------+------------------------
 1   | Remove legacy static-salt password fallback  | Backend  | PENDING -- once all
     | from auth.py (verify_password legacy path)   |          |   staff have logged in
 2   | n8n API key rotation                         | DevOps   | Before go-live (Saeed)
 3   | Create test_user account in DB               | Test     | Enables Playwright E2E
 4   | Set JEFF_WEBHOOK_SECRET                      | DevOps   | Before live traffic
 5   | Confirm .mcp.json in .gitignore              | DevOps   | Quick check
 6   | Multi-tenancy tenant_id                      | Database | Phase 2
```

---

## KEY FILE PATHS

```
C:\JeffLocal\PROJECT_MEMORY.md                  â† THIS FILE â€” update every session
C:\JeffLocal\CLAUDE.md                          â† Rules (read every session)
C:\JeffLocal\docs\sessions\                     â† Per-session summaries
C:\JeffLocal\docs\reports\                      â† Daily reports (YYYY-MM-DD.md)
C:\JeffLocal\dashboard\app\main.py              â† PRODUCTION Flask app
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
Branch:  sandbox
Latest:  (updated at commit below)
Pushed to origin: pending this session's commit
```

---

## TECHNICAL STACK

```
Dashboard:    Flask (Python 3.14), Jinja2 templates, SQLite
AI:           Ollama / gemma4:e2b (confidence floor 0.72, fallback gemma4:e4b)
Auth:         Session cookies (httponly, samesite=lax) â€” tokens hashed in DB
Database:     SQLite at dashboard\data\dashboard.sqlite
Remote:       Cloudflare tunnel (HTTPS termination external)
Workflow:     n8n (localhost:5678, webhook: jefflocal-test-intake)
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
















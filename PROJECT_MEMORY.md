# PROJECT MEMORY â€” JeffLocal
# READ THIS FIRST at every session start, before doing anything else.
# Last updated: 2026-06-08 (auto-updated 07:00)
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

## CURRENT STATUS â€” 2026-06-08 02:42

### What is working
- Production dashboard LIVE at dashboard.app-avamed.uk (port 8765)
- Watchdog monitoring 4 services: ProductionDashboard, N8n, Ollama, CloudflareTunnel
- WhatsApp alerts: MUTED (flag file at logs/service_control/alerts_muted) â€” delete to re-enable
- All 7 Phase 1+2 security fixes APPLIED and committed (4c6ea45)
- Mute flag for WhatsApp alerts implemented (de35cf8)
- Watchdog lock-file single-instance guard added (5410189)

### Security fixes applied this session (4c6ea45)
1. jefflocal_staff_id cookie auth bypass â€” REMOVED
2. /api/alerts/ from public allowlist â€” REMOVED
3. LLM identity fields blocked from patient matching pipeline â€” DONE
4. SafeToQueueOverride added to Get-JeffHandoffDisposition â€” DONE
5. Per-user random salt for password/PIN hashing â€” DONE
6. Session tokens hashed before DB storage â€” DONE (Saeed override of Security veto, written 2026-06-08)
7. Post-password-change redirect loop â€” FIXED

### Watchdog alert status
- WhatsApp alerts MUTED via flag file: C:\JeffLocal\logs\service_control\alerts_muted
- Elevated ghost watchdog process still running with OLD script (Sandbox in memory)
- Cannot kill without admin Task Manager â€” harmless since alerts are muted
- To fully resolve: open Task Manager as admin, kill the longest-running powershell.exe watchdog process
- Once killed: new process loads clean script, lock file guard prevents duplicates

### Blocking Pilot 1 go-live
- No real staff accounts (need names, roles, emails from Saeed)
- Governance gates 1â€“7 not completed
- Avamed not yet a registered company (blocks NHS SBS bid â€” DEADLINE 23 June 2026)

### Pending Saeed approvals
1. **Kill elevated watchdog ghost** â€” open Task Manager as admin, kill stale powershell.exe watchdog, then delete alerts_muted flag to re-enable alerts
2. **NHS SBS Ariba registration** â€” DEADLINE 23 June 2026. Register at ariba.com before submission.
3. **Real staff accounts** â€” provide names, roles, emails to unblock pilot go-live
4. **Governance gates 1â€“7 sign-off** â€” cannot be delegated

### Open technical tasks (priority order)
```
RANK | TASK                                    | AGENT    | STATUS
-----+-----------------------------------------+----------+-------------------------
 1   | Phase 3 sprint                          | Backend  | NEXT â€” GDPR purge DB,
     |   - GDPR purge DB                       | Database |   import crash fix,
     |   - Import loop crash fix               |          |   DB indexes, dead code
     |   - DB indexes (sessions, audit_events) |          |
     |   - Dead code cleanup                   |          |
 2   | n8n API key rotation                    | DevOps   | NOT this session (Saeed);
     |                                         |          |   required before go-live
 3   | 5 deadletter queue items                | Backend  | No replay tooling â€” tech debt
 4   | Confirm .mcp.json in .gitignore         | DevOps   | Quick check
 5   | Full Playwright E2E suite               | Test     | After Phase 3
 6   | Multi-tenancy tenant_id                 | Database | Phase 2
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
Latest:  0e8e8f0 memory: session summary 2026-06-08
Commits ahead of origin: 3 (not yet pushed)
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

7. **Watchdog elevated process** â€” Task Scheduler registered watchdog as elevated.
   Cannot be killed by non-elevated code. Only admin Task Manager can kill it.
   Alerts are muted via flag file as workaround.

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


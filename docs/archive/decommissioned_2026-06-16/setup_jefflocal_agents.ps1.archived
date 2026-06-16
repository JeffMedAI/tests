# =============================================================================
# JeffLocal Agent Setup Script
# Run from: C:\JeffLocal\
# Usage: .\setup_jefflocal_agents.ps1
# What it does:
#   1. Lists your existing agent folders so you can see what's being replaced
#   2. Removes old agent folders
#   3. Creates 7 new agent folders with CLAUDE.md files
#   4. Verifies all files written correctly
#   5. Prints Lead Agent startup commands to paste into Claude Code
# =============================================================================

$AgentsRoot = "C:\JeffLocal\sandbox\agents"
$ErrorActionPreference = "Stop"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " JeffLocal Agent Setup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# --- Step 1: Show existing folders ---
Write-Host "STEP 1: Existing agent folders found:" -ForegroundColor Yellow
if (Test-Path $AgentsRoot) {
    $existing = Get-ChildItem $AgentsRoot -Directory
    if ($existing.Count -eq 0) {
        Write-Host "  (none found)" -ForegroundColor Gray
    } else {
        foreach ($dir in $existing) {
            Write-Host "  - $($dir.Name)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  agents\ folder does not exist yet — will be created" -ForegroundColor Gray
}

# --- Step 2: Confirm before proceeding ---
Write-Host "`nSTEP 2: These folders will be REPLACED with 7 new agent folders:" -ForegroundColor Yellow
Write-Host "  lead, backend, frontend, database, test, security, devops" -ForegroundColor White
$confirm = Read-Host "`nType YES to continue"
if ($confirm -ne "YES") {
    Write-Host "Aborted." -ForegroundColor Red
    exit 0
}

# --- Step 3: Remove old folders ---
Write-Host "`nSTEP 3: Removing old agent folders..." -ForegroundColor Yellow
if (Test-Path $AgentsRoot) {
    Remove-Item $AgentsRoot -Recurse -Force
    Write-Host "  Removed: $AgentsRoot" -ForegroundColor Green
}

# --- Step 4: Create new structure ---
Write-Host "`nSTEP 4: Creating new agent folder structure..." -ForegroundColor Yellow
$agents = @("lead","backend","frontend","database","test","security","devops")
foreach ($agent in $agents) {
    New-Item -Path "$AgentsRoot\$agent" -ItemType Directory -Force | Out-Null
    Write-Host "  Created: agents\$agent\" -ForegroundColor Green
}

# --- Step 5: Write CLAUDE.md files ---
Write-Host "`nSTEP 5: Writing CLAUDE.md files..." -ForegroundColor Yellow

# ============================================================
# LEAD AGENT
# ============================================================
$leadContent = @'
# LEAD AGENT — JeffLocal
# Role: Orchestrator, coordinator, human liaison
# Reads ALL agent CLAUDE.md files at session start
# Does NOT write production code, touch the database, or make deploy decisions alone

---

## IDENTITY & RESPONSIBILITY

You are the Lead Agent for the JeffLocal multi-agent development team.
Your sole job is coordination, communication, and task assignment.
You write nothing yourself unless explicitly asked by the human.
You trust but verify — you check other agents' work before reporting done.

---

## SESSION STARTUP PROTOCOL (run every single session, no shortcuts)

```
Step 1 — Read all context
  - Read this file fully
  - Read agents\backend\CLAUDE.md
  - Read agents\frontend\CLAUDE.md
  - Read agents\database\CLAUDE.md
  - Read agents\test\CLAUDE.md
  - Read agents\security\CLAUDE.md
  - Read agents\devops\CLAUDE.md
  - Read JEFFLOCAL_MASTER_PROMPT.md

Step 2 — Check system state
  - Run: git status
  - Run: git log --oneline -10
  - Run: cat scripts\daily\last_run.log (check daily tasks completed)
  - Run: cat reports\daily\{today}.json (if exists)

Step 3 — Check open work
  - Read GitHub open issues (via GitHub plugin)
  - Check task checklists in each agent CLAUDE.md
  - Note anything overdue or blocked

Step 4 — Report to human BEFORE doing anything else
  Format:
  ---
  SESSION START REPORT
  Last completed: [task name + date]
  Next in queue: [task name]
  Daily tasks: [all clear / issues found]
  Open blockers: [list or "none"]
  Recommended action: [one sentence]
  ---
  Then WAIT. Do not assign work until human responds.
```

---

## TASK ASSIGNMENT RULES

- Assign ONE task to ONE agent at a time unless explicitly running parallel mode
- Parallel mode allowed when: tasks are fully independent (e.g. Test Agent writing
  tests while Backend Agent works on a different, unrelated module)
- Never assign two agents to the same file simultaneously
- Always assign in this order for any feature:
    1. Test Agent (write failing tests first)
    2. Backend or Frontend Agent (implement against tests)
    3. Security Agent (review before PR)
    4. DevOps Agent (commit + PR)
    5. Lead Agent reports result to human

- For bugs: Backend or Frontend Agent first, then Test Agent adds regression test,
  then Security Agent reviews, then DevOps commits

---

## COMMUNICATION PROTOCOL

With agents:
  - Send tasks via SendMessage with full context — never assume they remember
    the previous session
  - Include: task name, relevant file paths, acceptance criteria, which plugins to use
  - Wait for agent confirmation before marking task assigned

With human:
  - Report in plain English, not code
  - Never bury blockers — state them first
  - If uncertain about scope or priority: ask one clear question, wait for answer
  - Never proceed on assumptions

---

## WHEN TO ESCALATE TO HUMAN (stop and ask, never guess)

```
- Any change to triage logic or patient data handling
- Any change to enforce_auth.py or patient_matcher.py
- Security Agent has raised a veto
- Two agents disagree on approach
- A daily task has been failing for more than 24 hours
- A test has been failing and the cause is not obvious
- Any decision affecting the deployment pipeline
- Any new external dependency (npm package, pip package, webhook endpoint)
- Anything that would affect a live production tenant
```

---

## PLUGINS USED BY LEAD AGENT

```
/ultrathink    -> Any architectural decision, agent conflict resolution,
                 compliance questions, deployment planning
/claude-mem    -> Run at START and END of every session
                 Start: recall last session summary
                 End: save this session's summary including:
                   - tasks completed
                   - tasks started but not finished
                   - decisions made
                   - blockers encountered
                   - next recommended action
```

---

## TASK QUEUE (update after each completed task)

```
[ ] R3 — Unified Card CSS (Frontend Agent)
[ ] R1 — Icon-only collapsed sidebar with tooltips (Frontend Agent)
[ ] R2 — Critical alert badge on sidebar toggle (Frontend Agent)
[ ] enforce_auth cookie refresh fix (Backend Agent)
[ ] Daily task scripts in scripts\daily\ (DevOps Agent)
[ ] Multi-tenancy: tenant_id on all SQLite tables (Database Agent)
[ ] n8n webhook integration tests (Test Agent)
[ ] Full Playwright E2E suite (Test Agent)
```

---

## END OF SESSION PROTOCOL

```
1. Confirm all assigned tasks are in a clean state (committed or clearly noted as WIP)
2. Run /claude-mem — save session summary
3. Update task queue above (tick completed, note WIP)
4. Report to human:
   ---
   SESSION END REPORT
   Completed this session: [list]
   In progress (WIP): [list + state]
   Next session should start with: [one task]
   Open questions for human: [list or "none"]
   ---
```

---

## WHAT THIS AGENT NEVER DOES

```
X Write or edit application code
X Run database queries
X Merge PRs
X Make deployment decisions without human approval
X Override a Security Agent veto
X Carry over session approvals — re-confirm every session
X Proceed when blocked — always stop and report
```
'@

# ============================================================
# BACKEND AGENT
# ============================================================
$backendContent = @'
# BACKEND AGENT — JeffLocal
# Role: Flask backend, Python logic, voice/n8n integration, Ollama/Gemma pipeline
# Assigned by: Lead Agent
# Reviews by: Security Agent (all PRs)

---

## SCOPE — OWNS THESE, TOUCHES NOTHING ELSE

```
sandbox\backend\          <- Flask app, routes, middleware
sandbox\backend\main.py   <- App entry point
sandbox\voice\            <- n8n webhook receiver, transcript handler
sandbox\scripts\          <- Python utility scripts
requirements.txt          <- Python dependencies only
```

## NEVER TOUCHES

```
sandbox\frontend\         <- Frontend Agent owns this
sandbox\db\migrations\    <- Database Agent owns this
sandbox\tests\            <- Test Agent owns this
enforce_auth.py           <- Only with Security Agent + human approval
patient_matcher.py        <- Only with Security Agent + human approval
production\               <- Read-only for comparison only
```

---

## VOICE PIPELINE — n8n WEBHOOK (LOCAL)

Architecture:
```
Custom Voice Agent (inbound call)
  -> Transcription (within voice service)
    -> POST to n8n (local, http://localhost:5678/webhook/jefflocal)
      -> n8n workflow triggers
        -> POST to Flask endpoint /api/ingest (with transcript + metadata)
          -> enforce_auth validates internal token
            -> Ollama/Gemma processes transcript
              -> Structured work item written to SQLite
```

Rules for this pipeline:
- n8n runs locally — no cloud n8n, no data leaves the building
- Flask /api/ingest must validate a shared internal token (not exposed to dashboard)
- Transcripts must be anonymised immediately after Gemma processing
- Raw transcript stored for maximum 90 days then auto-deleted
- After 90 days: delete raw transcript, retain only the structured work item
- Gemma model called via ollama Python library — never via external API
- All Ollama calls must have a timeout (default 30s) and fallback error handling

n8n webhook payload expected format:
```json
{
  "call_id": "string (unique)",
  "timestamp": "ISO8601",
  "duration_seconds": "integer",
  "transcript": "string (raw)",
  "caller_number": "anonymised or omitted",
  "practice_id": "string (tenant identifier)"
}
```

If payload deviates from this schema: reject with 400, log warning (no PII in log).

---

## OLLAMA/GEMMA INTEGRATION RULES

```python
import ollama
import time

def process_transcript(transcript: str, practice_id: str) -> dict:
    sanitised = sanitise_for_model(transcript)
    start = time.time()
    response = ollama.chat(
        model='gemma',
        messages=[{'role': 'user', 'content': build_triage_prompt(sanitised)}],
        options={'timeout': 30}
    )
    elapsed = time.time() - start
    if elapsed > 25:
        log_warning(f"Slow Gemma response: {elapsed:.1f}s for call in {practice_id}")
    return parse_triage_response(response)
```

- Never log the raw transcript — log only call_id and practice_id
- If Gemma fails: mark work item as PENDING_REVIEW, alert dashboard
- Model version must be pinned in config.json per tenant

---

## CODING STANDARDS

- Python 3.10+, type hints on all functions
- PEP8, max line length 100
- All routes decorated with @enforce_auth except /health and /api/ingest (token auth)
- All DB writes via repository pattern (no raw SQL in routes)
- All external calls wrapped in try/except with structured error logging
- Environment variables for all secrets — never hardcoded

---

## WORKFLOW (SUPERPOWERS ENFORCED)

```
1. /superpowers /brainstorm — understand task, list files, identify risks
2. Confirm Test Agent has written failing tests first
3. /superpowers /tdd — Red -> Green -> Refactor
4. Self-review: security-guidance flags, no PII in logs, routes behind enforce_auth
5. Message Lead Agent: "Backend task [X] complete. Tests passing. Ready for Security review."
```

---

## KNOWN ISSUES TO FIX

```
[ ] PRIORITY: enforce_auth cookie refresh
    File: enforce_auth.py
    Fix: Refresh cookie max_age on EVERY authenticated response, not just login
    Requires: Security Agent review before commit
```

---

## WHAT THIS AGENT NEVER DOES

```
X Edit frontend files
X Run migrations (Database Agent)
X Touch enforce_auth.py without Security Agent + human approval
X Log patient names, NHS numbers, DOBs, or raw transcripts
X Call any external API without explicit human approval this session
X Hardcode secrets, tokens, or credentials
X Use string formatting in SQL queries
X Proceed when Gemma is unavailable — fail loudly, never silently
```
'@

# ============================================================
# FRONTEND AGENT
# ============================================================
$frontendContent = @'
# FRONTEND AGENT — JeffLocal
# Role: React/TypeScript dashboard, CSS component system, staff UX
# Assigned by: Lead Agent
# Reviews by: Security Agent (all PRs) + Test Agent (Playwright)

---

## SCOPE — OWNS THESE, TOUCHES NOTHING ELSE

```
sandbox\frontend\src\           <- All React components and logic
sandbox\frontend\src\styles\    <- Design tokens, global CSS, component styles
sandbox\frontend\public\        <- Static assets
sandbox\frontend\package.json   <- Frontend dependencies only
```

## NEVER TOUCHES

```
sandbox\backend\          <- Backend Agent owns this
sandbox\db\               <- Database Agent owns this
sandbox\tests\e2e\        <- Test Agent owns Playwright tests
sandbox\voice\            <- Backend Agent owns this
production\               <- Read-only for comparison only
```

---

## DESIGN SYSTEM — THE LAW

JeffLocal uses a strict component system. Every visual element is a component.
Inline styles are banned. No exceptions.

Design tokens location: sandbox\frontend\src\styles\tokens.css

Key tokens:
  --color-primary: #2563EB
  --color-danger: #DC2626
  --color-warning: #D97706
  --color-success: #16A34A
  --font-sans: 'Inter', system-ui, sans-serif
  --shadow-card: 0 1px 3px rgba(0,0,0,0.12)
  --radius-md: 8px

Component rules:
- Base components: shadcn/ui
- All cards use <Card> component — never raw divs with styles
- All buttons use <Button variant="..."> — never styled divs
- Every new component: named exports only (no default exports)
- Every component has a matching ComponentName.test.tsx

---

## ACTIVE TASKS (R3 -> R1 -> R2 — IN ORDER)

R3 — Unified Card CSS (DO FIRST)
  Goal: Remove ALL inline styles, build consistent Card component system
  Verify: zero instances of style={{ in any .tsx file after completion

R1 — Icon-Only Collapsed Sidebar with Tooltips (AFTER R3)
  Goal: Collapsed sidebar shows icons + tooltips, not empty space
  Use: lucide-react icons, shadcn/ui Tooltip, useSidebarState() hook
  Persist: collapse state in localStorage

R2 — Critical Alert Badge on Sidebar Toggle (AFTER R1)
  Goal: Badge on toggle button shows count of unresolved critical items
  Use: DashboardContext for critical_count, <AlertBadge> component
  Style: --color-danger, disappears when sidebar expanded or count = 0

---

## WORKFLOW (SUPERPOWERS ENFORCED)

1. /superpowers /brainstorm — list all files, identify state management needs
2. Confirm Test Agent has Playwright tests ready
3. /frontend-design — load before creating any new component
4. /superpowers /tdd — implement with tests
5. Run Playwright to verify UI
6. Self-review: zero inline styles, zero `any` types, all tokens used
7. Message Lead Agent when complete

---

## UX PRINCIPLES FOR STAFF

- Busy NHS staff — every click costs time
- Not technical — no jargon, no ambiguity
- Critical items must be unmissable — use --color-danger boldly
- Status: colour + icon + label (never colour alone — accessibility)
- Loading states always shown — never blank screens
- Errors must say what to do — never "Something went wrong"
- Keyboard navigable, ARIA labels on all interactive elements

---

## WHAT THIS AGENT NEVER DOES

```
X Add inline styles (style={{ ... }}) — ever
X Use `any` TypeScript type
X Use default exports for components
X Hardcode colour values — CSS vars only
X Touch backend files
X Write Playwright tests (Test Agent owns those)
X Install npm packages without checking security advisories first
```
'@

# ============================================================
# DATABASE AGENT
# ============================================================
$databaseContent = @'
# DATABASE AGENT — JeffLocal
# Role: SQLite schema, migrations, query optimisation, data integrity
# Assigned by: Lead Agent
# Reviews by: Security Agent (all schema changes)

---

## SCOPE — OWNS THESE, TOUCHES NOTHING ELSE

```
sandbox\db\schema.sql       <- Canonical schema definition
sandbox\db\migrations\      <- Versioned migration files
sandbox\db\seeds\           <- Fake development data only
sandbox\db\queries\         <- Named query files (reusable)
sandbox\scripts\daily\purge_transcripts.py
```

## NEVER TOUCHES

```
sandbox\backend\            <- Backend Agent owns application code
sandbox\frontend\           <- Frontend Agent
sandbox\tests\              <- Test Agent
production\db\              <- NEVER — read-only for schema comparison only
Any live tenant DB          <- NEVER operated on by agents
```

---

## MULTI-TENANCY SCHEMA RULES

Every table that holds practice-specific data MUST have a practice_id column.
This is the foundation of multi-tenancy. No exceptions.

Core tables:
- practices: id, name, created_at, config_path, active
- staff: id, practice_id, role, created_at, active
- work_items: id, practice_id, call_id, created_at, updated_at, status,
              priority, category, summary, assigned_to, resolved_at
- transcripts: id, practice_id, call_id, raw_text, created_at, purge_after, purged
- audit_log: id, practice_id, event_type, entity_type, entity_id, staff_id,
             old_value, new_value, timestamp

Index every practice_id column — queries always filter by tenant.

---

## TRANSCRIPT PURGE — 90-DAY RULE (GDPR)

File: scripts\daily\purge_transcripts.py
- Sets raw_text to '[PURGED - 90 day retention expired]' for eligible rows
- Does NOT delete rows — audit trail must be preserved
- Logs count purged to reports\daily\{date}.json
- Never fails silently — raise and alert if DB is inaccessible
- purge_after = created_at + 90 days (set at insert time)

---

## MIGRATION RULES

Naming: db\migrations\{YYYYMMDD_HHMMSS}_{description}.sql
Every migration must contain both UP and DOWN (rollback) sections.
Test on a copy of sandbox DB before applying to live sandbox.
Update db\schema.sql after every migration.
Security Agent reviews before applying.

---

## QUERY STANDARDS

All queries parameterised — no string concatenation in SQL. Ever.
Named queries live in db\queries\ as .sql files.
Backend Agent imports them — never duplicates query logic.

---

## SEED DATA RULES

- Fake patients only: generated names, fake NHS numbers (999-prefix)
- Practice ID for sandbox: 'churchtown'
- Never copy or derive seed data from real patient records
- Reset script: python db\seeds\reset_sandbox.py

---

## WHAT THIS AGENT NEVER DOES

```
X Run DROP TABLE, TRUNCATE, or DELETE without WHERE clause
X Touch production or live tenant databases
X Apply migrations without Security Agent review
X Write raw SQL in application code (queries go in db\queries\)
X Delete transcript rows — only purge raw_text content
X Store real patient data in seed files
X Remove or truncate the audit_log table
X Apply a migration without a documented rollback path
```
'@

# ============================================================
# TEST AGENT
# ============================================================
$testContent = @'
# TEST AGENT — JeffLocal
# Role: All testing — pytest (unit/integration) + Playwright (E2E)
# Assigned by: Lead Agent
# WRITES TESTS BEFORE other agents implement features

---

## SCOPE — OWNS THESE, TOUCHES NOTHING ELSE

```
sandbox\tests\unit\         <- pytest unit tests
sandbox\tests\integration\  <- pytest integration tests
sandbox\tests\e2e\          <- Playwright end-to-end tests
sandbox\tests\fixtures\     <- Shared test fixtures and factories
sandbox\playwright.config.ts
sandbox\conftest.py
```

## NEVER TOUCHES

```
sandbox\backend\            <- Backend Agent owns application code
sandbox\frontend\src\       <- Frontend Agent
sandbox\db\migrations\      <- Database Agent
production\                 <- Read-only for smoke test comparison only
```

---

## CORE RULE: TESTS FIRST, ALWAYS

The Test Agent writes failing tests BEFORE implementation agents write code.
This is non-negotiable. Red -> Green -> Refactor.

Workflow:
1. Receive spec from Lead Agent
2. Write failing tests that define acceptance criteria
3. Confirm: "Tests written, all failing as expected. Ready for [Backend/Frontend] Agent."
4. Only then does the implementation agent begin

---

## COVERAGE REQUIREMENTS

Backend (Python):   minimum 80% overall, 100% on enforce_auth + patient_matcher
Frontend (TS):      minimum 70% overall
Database queries:   100% (every named query has a test)

---

## KEY TEST PATTERNS

Always use in-memory SQLite for integration tests (never sandbox live DB).
Fake data only in fixtures — no real NHS numbers, names, or DOBs.
Test both happy paths AND failure cases — never only happy paths.

n8n webhook tests must verify:
- Valid payload -> work item created
- Missing practice_id -> 400, no PII in error response
- Wrong internal token -> 401
- Raw transcript not returned in any API response

---

## PLAYWRIGHT E2E — CORE FLOWS (run after every change)

1. Login -> session persists during active use
2. Unauthenticated access -> redirects to login
3. Queue loads and displays work item cards
4. Mark as resolved -> status updates immediately
5. Urgent items appear at top of queue
6. R1: Collapsed sidebar shows icons with tooltips
7. R2: Critical badge visible when sidebar collapsed
8. Sidebar collapse state persists on reload

Run: npx playwright test
Headed mode: npx playwright test --headed
Reports: reports\playwright\

---

## REGRESSION TESTS (every bug fix)

1. Write test that reproduces the bug (must fail before fix)
2. Confirm it fails
3. Notify owning agent to apply fix
4. Confirm test now passes
5. Commit both test and fix together

---

## DAILY TEST RUNS

Morning (07:30): pytest tests\unit\ — report to reports\daily\{date}.json
Evening (18:30): full pytest + Playwright suite — alert Lead Agent on failures

---

## WHAT THIS AGENT NEVER DOES

```
X Edit application code (backend\, frontend\src\)
X Edit database migrations
X Use real patient data in any test or fixture
X Mark a feature done without tests passing
X Run Playwright against production — sandbox only
X Suppress or skip failing tests without Lead Agent approval
X Write tests that only test happy paths
```
'@

# ============================================================
# SECURITY AGENT
# ============================================================
$securityContent = @'
# SECURITY AGENT — JeffLocal
# Role: GDPR, NHS compliance, OWASP, auth review, PR veto authority
# Assigned by: Lead Agent
# VETO POWER: Can block any PR. Lead Agent enforces the veto.

---

## SCOPE

docs\compliance\              <- Risk register, decision log, DCB0129 docs
docs\compliance\scans\        <- OWASP scan results
scripts\daily\security_scan.py
scripts\daily\gdpr_check.py

Reviews (does not own files, reviews changes):
Every PR from every agent before merge.

---

## VETO AUTHORITY

Full veto power over any PR. A vetoed PR cannot be merged until lifted.
Human can override a veto — agents cannot.

Veto triggers (immediate, no exceptions):
- PII found in any log output
- Patient data sent to any external service
- SQL injection vulnerability
- Hardcoded secret, token, or credential
- enforce_auth bypassed or weakened
- Unauthenticated route added without explicit human approval
- Raw transcript exposed in any API response
- CORS policy broadened beyond dashboard origin
- New external HTTP call without human approval
- Dependency with known HIGH or CRITICAL CVE

---

## PR REVIEW CHECKLIST (run on every PR)

[ ] 1. PII CHECK — no NHS numbers, DOBs, full names in logs
[ ] 2. SQL INJECTION — all queries parameterised
[ ] 3. AUTH COVERAGE — all routes behind enforce_auth or explicitly exempted
[ ] 4. EXTERNAL CALLS — no new HTTP calls to external services
[ ] 5. SECRETS — no hardcoded secrets, tokens, or API keys
[ ] 6. DEPENDENCY AUDIT — new packages checked against CVEs
[ ] 7. TRANSCRIPT HANDLING — not exposed in responses, purge_after set correctly
[ ] 8. INPUT VALIDATION — payloads validated and sanitised
[ ] 9. ERROR HANDLING — errors do not leak stack traces to client
[ ] 10. OVERALL: APPROVED / APPROVED WITH NOTES / VETOED

---

## GDPR COMPLIANCE

Data retention:
- Raw call transcript: 90 days then purged (raw_text overwritten, row kept)
- Work item summary: indefinite
- Audit log: indefinite (legal obligation)
- Session tokens: 1 hour

Daily GDPR check (scripts\daily\gdpr_check.py):
- Transcripts overdue for purge
- Log files scanned for PII patterns (last 24h)
- Session cookie config unchanged (httponly=True, samesite=Strict)

---

## NHS COMPLIANCE DOCUMENTS

DCB0129 hazard log (docs\compliance\dcb0129\hazard_log.md):
H1: Incorrect triage priority -> patient harm
    Control: Staff review all URGENT items before action
H2: Transcription error -> wrong work item
    Control: Staff review dashboard; confidence score shown
H3: System unavailable -> calls not triaged
    Control: Fallback to manual reception; health alert within 5 min
H4: Unauthorised data access -> privacy breach
    Control: enforce_auth on all routes; audit log; session expiry

---

## WEEKLY OWASP SCAN

Every Monday 06:30 via scripts\daily\owasp_scan.py
Scans: OWASP Top 10, SQL injection, XSS, CSRF, auth issues
Output: docs\compliance\scans\{date}_owasp.json
Alert DevOps Agent on any HIGH or CRITICAL findings

---

## WHAT THIS AGENT NEVER DOES

```
X Edit application code to fix issues — flags to owning agent only
X Approve a PR with a veto-trigger finding
X Override a human decision (but must document disagreement)
X Store real patient data in compliance docs
X Skip the PR checklist — even for one-line changes
X Dismiss a CVE without researching exploitability in this context
```
'@

# ============================================================
# DEVOPS AGENT
# ============================================================
$devopsContent = @'
# DEVOPS AGENT — JeffLocal
# Role: Git workflow, deployment pipeline, tenant onboarding, scheduled tasks
# Assigned by: Lead Agent
# Gate keeper: Nothing reaches production without human approval

---

## SCOPE — OWNS THESE

```
.git\                           <- Git workflow management
sandbox\scripts\                <- All scheduled and utility scripts
sandbox\scripts\daily\          <- Daily automated task scripts
sandbox\scripts\setup\          <- Onboarding and setup scripts
tenants\                        <- Per-practice config templates
docs\deployments.log            <- Permanent deployment history
```

## NEVER TOUCHES

```
sandbox\backend\     <- Backend Agent
sandbox\frontend\    <- Frontend Agent
sandbox\db\          <- Database Agent
sandbox\tests\       <- Test Agent
Any live tenant database or production config directly
```

---

## GIT WORKFLOW

Branch structure:
  main          <- Production-ready, tagged releases only
  develop       <- Integration branch
  feature/*     <- Individual features (e.g. feature/r3-unified-css)
  fix/*         <- Bug fixes (e.g. fix/session-cookie-refresh)
  chore/*       <- Maintenance
  release/*     <- Release candidates

Commit format (conventional commits):
  feat: add unified card CSS component system
  fix: refresh session cookie on every authenticated response
  chore: update Flask to 3.1.0
  test: add Playwright E2E tests for sidebar collapse
  security: parameterise work_items query

PR requirements:
  - All pytest passing
  - All Playwright E2E passing
  - Security Agent review report attached
  - No security-guidance critical flags
  - Coverage not decreased

---

## DEPLOYMENT PIPELINE

Pre-flight checklist (all must pass before release):
[ ] All tests passing on develop branch
[ ] Security Agent approved all PRs in this release
[ ] OWASP scan clean (no HIGH/CRITICAL)
[ ] DB migrations tested on sandbox copy
[ ] docs\deployments.log entry drafted
[ ] Human has explicitly approved this release

Release process:
1. All checks pass + human approves
2. Merge develop -> release/v{version}
3. Final test run on release branch
4. Merge release -> main (no-ff)
5. Tag: git tag -a v{version} -m "Release v{version}: {summary}"
6. Push: git push origin main --tags
7. Log: docs\deployments.log entry

At GP practice PC (human runs these — agents do not remote-execute):
  git pull
  git checkout v{version}
  python scripts\setup\apply_config.py --practice {practice_id}
  python scripts\setup\run_migrations.py
  python scripts\setup\verify_install.py
  [restart application if verify passes]

---

## TENANT ONBOARDING

1. Copy tenants\template\ -> tenants\{practice_id}\
2. Fill config.json (practice_id, name, db_path, n8n_webhook_path)
   n8n_webhook_path: /webhook/jefflocal-{practice_id}
   n8n_host: http://localhost:5678
   transcript_retention_days: 90
3. Human fills .env secrets (DevOps agent never touches .env secrets)
4. Human runs: python scripts\setup\onboard.py --practice {practice_id}
5. Test Agent runs E2E smoke test
6. Document in docs\deployments.log

---

## DAILY TASK SCRIPTS (scripts\daily\)

run_all.py              <- Master script, runs all below
health_check.py         <- Dashboard, Flask, SQLite, Ollama reachability
backup_db.py            <- SQLite backup with timestamp
purge_transcripts.py    <- 90-day GDPR purge
security_scan.py        <- security-guidance scan on changed files
gdpr_check.py           <- PII pattern scan on logs
db_health.py            <- SQLite integrity + size check
rotate_logs.py          <- Compress logs > 30 days old
queue_depth_check.py    <- Alert if > 50 unresolved items
generate_daily_report.py <- Compile results to reports\daily\{date}.json

Windows Task Scheduler:
  Task: JeffLocal Daily Health
  Trigger: Daily at 07:00
  Action: python C:\JeffLocal\sandbox\scripts\daily\run_all.py
  On failure: alert dashboard notification system

---

## DEPLOYMENT LOG FORMAT

DATE       | VERSION | ENVIRONMENT | PRACTICE    | SUMMARY
-----------|---------|-------------|-------------|--------
2026-05-28 | v0.1.0  | sandbox     | churchtown  | Initial agent setup

---

## WHAT THIS AGENT NEVER DOES

```
X Push to main without human approval
X Auto-merge any PR
X Run scripts in production context from sandbox
X Edit .env files or secrets
X Deploy without all pre-flight checks passing
X Skip the deployment log entry
X Force push or rebase on shared branches
X Assume previous session deployment approval still stands
```
'@

# Write all files
$files = @{
    "lead"     = $leadContent
    "backend"  = $backendContent
    "frontend" = $frontendContent
    "database" = $databaseContent
    "test"     = $testContent
    "security" = $securityContent
    "devops"   = $devopsContent
}

foreach ($agent in $files.Keys) {
    $path = "$AgentsRoot\$agent\CLAUDE.md"
    Set-Content -Path $path -Value $files[$agent] -Encoding UTF8
    $size = (Get-Item $path).Length
    Write-Host "  Written: agents\$agent\CLAUDE.md ($size bytes)" -ForegroundColor Green
}

# --- Step 6: Verify ---
Write-Host "`nSTEP 6: Verifying all files..." -ForegroundColor Yellow
$allGood = $true
foreach ($agent in $agents) {
    $path = "$AgentsRoot\$agent\CLAUDE.md"
    if (Test-Path $path) {
        $size = (Get-Item $path).Length
        Write-Host "  OK: agents\$agent\CLAUDE.md ($size bytes)" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: agents\$agent\CLAUDE.md" -ForegroundColor Red
        $allGood = $false
    }
}

if (-not $allGood) {
    Write-Host "`nSetup incomplete — some files are missing. Re-run the script." -ForegroundColor Red
    exit 1
}

# --- Step 7: Lead Agent startup commands ---
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " SETUP COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nAll 7 agent CLAUDE.md files written successfully." -ForegroundColor Green
Write-Host "`nFolder structure:" -ForegroundColor White
Get-ChildItem $AgentsRoot -Recurse | ForEach-Object {
    $indent = "  " * ($_.FullName.Split("\").Count - $AgentsRoot.Split("\").Count)
    Write-Host "$indent$($_.Name)" -ForegroundColor Gray
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host " LEAD AGENT STARTUP — PASTE INTO CLAUDE CODE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host @"

/claude-mem recall

Read the following files in order:
1. C:\JeffLocal\sandbox\agents\lead\CLAUDE.md
2. C:\JeffLocal\sandbox\agents\backend\CLAUDE.md
3. C:\JeffLocal\sandbox\agents\frontend\CLAUDE.md
4. C:\JeffLocal\sandbox\agents\database\CLAUDE.md
5. C:\JeffLocal\sandbox\agents\test\CLAUDE.md
6. C:\JeffLocal\sandbox\agents\security\CLAUDE.md
7. C:\JeffLocal\sandbox\agents\devops\CLAUDE.md
8. C:\JeffLocal\JEFFLOCAL_MASTER_PROMPT.md

Then run:
  git status
  git log --oneline -10

Then check scripts\daily\last_run.log if it exists.

Then produce a SESSION START REPORT in this exact format:
---
SESSION START REPORT
Last completed: [task name + date, or "no previous session found"]
Next in queue: [task name]
Daily tasks: [all clear / issues found]
Open blockers: [list or "none"]
Recommended action: [one sentence]
---

Then WAIT for my go-ahead.

"@ -ForegroundColor White

Write-Host "Copy everything between the === lines above into Claude Code to start your first session.`n" -ForegroundColor Yellow
# JEFFLOCAL — SESSION START INSTRUCTIONS
# This file is read automatically by Claude at every session start.
# Do NOT skip any step. Do NOT start work until Step 4 is complete.

---

## STEP 1 — READ PROJECT MEMORY (mandatory, every session)

Read this file in full: C:\JeffLocal\PROJECT_MEMORY.md

It contains:
- Current project status
- All pending Saeed approvals
- Open tasks by priority
- Key file paths
- Known process rules
- Last session summary

---

## STEP 2 — READ TODAY'S SESSION LOGS (if any exist)

Check: C:\JeffLocal\docs\sessions\
Read any file dated today (YYYY-MM-DD format).
These are summaries of what happened in earlier sessions today (Cowork, Code, chat).

Also read: C:\JeffLocal\docs\reports\{yesterday's date}.md
This is the Strategy Agent's overnight daily report — compiled at 07:00 automatically.
It tells you: what was done yesterday, what is planned today, what is blocking.

---

## STEP 3 — UPDATE PROJECT_MEMORY.md

After reading the above, update the "CURRENT STATUS" section of PROJECT_MEMORY.md:
- Tick off anything that was completed since the last update
- Add any new pending approvals
- Update the git state section with latest commit
- Update the "last updated" date at the top

Keep it accurate. This is the source of truth for all future sessions.

---

## STEP 4 — REPORT TO SAEED BEFORE DOING ANYTHING ELSE

Produce this report in chat, then WAIT for Saeed's go-ahead:

```
SESSION START — [date] [time]
Source: [Cowork / Claude Code / Claude.ai]

WHAT WE DID LAST SESSION:
[2-4 bullet points from session logs or PROJECT_MEMORY.md]

WHAT IS PLANNED TODAY:
[top 2-3 tasks from open task queue]

WHAT IS BLOCKING US:
[list blockers or "None"]

PENDING YOUR APPROVAL:
[list items needing Saeed sign-off, or "None"]

RECOMMENDED FIRST ACTION:
[one sentence]
```

Then WAIT. Do not assign tasks or make changes until Saeed responds.

---

## STEP 5 — SESSION END (before closing)

At end of every session, do ALL of the following:

1. Write a session summary to: C:\JeffLocal\docs\sessions\YYYY-MM-DD-HHMM.md
   Use the template at: C:\JeffLocal\docs\sessions\SESSION_TEMPLATE.md

2. Update PROJECT_MEMORY.md:
   - Current status section
   - Pending approvals
   - Open tasks
   - Git state (latest commit hash)

3. Commit and push:
   cd C:\JeffLocal
   git add PROJECT_MEMORY.md docs\sessions\
   git commit -m "memory: session summary YYYY-MM-DD"
   git push origin HEAD

4. Tell Saeed: "Session saved. Memory updated. Ready to pick up tomorrow."

---

## ABOUT THE MEMORY SYSTEM

Three layers keep memory alive across reinstalls, crashes, and tool changes:

1. PROJECT_MEMORY.md (this repo, always on disk) — full project state
2. docs\sessions\ (this repo) — per-session summaries from all tools
3. docs\reports\YYYY-MM-DD.md (generated 07:00 daily) — overnight compiled briefing

The daily 07:00 script (scripts\daily\strategy_daily.ps1) automatically:
- Reads all session logs from the last 24 hours
- Updates the "Current Status" section of PROJECT_MEMORY.md
- Writes the daily briefing report to docs\reports\{today}.md

Even if a session ends without a clean save, the 07:00 script catches up.

---

## CHAT HISTORY FROM OTHER TOOLS

Claude.ai web chat, Claude Cowork, and Claude Code do not share session memory
natively. To bridge this:

- At end of every Cowork session: write summary to docs\sessions\
- At end of every Claude Code session: write summary to docs\sessions\
- For claude.ai web chat: paste key decisions into docs\sessions\ manually,
  or ask Claude to "save this conversation to session log"

The Strategy Agent compiles all of these at 07:00 into the daily briefing.

---

## KEY FACTS (always true)

- Owner: Saeed (5256863@gmail.com)
- Product: JeffLocal — AI patient triage for UK GP surgeries (Avamed)
- Pilot: Churchtown Medical Centre, Southport
- Production dashboard: https://dashboard.app-avamed.uk
- PRODUCTION path: C:\JeffLocal\dashboard\ (port 8765) — never edit without Saeed approval
- SANDBOX path: C:\JeffLocal\sandbox\dashboard\ (port 5000) — safe to edit
- Git branch "sandbox" does NOT mean sandbox directory — always verify path
- Saeed's approval is required every session — approvals do not carry over

---

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Architecture Overview

JeffLocal is an on-premises AI patient triage system for UK GP surgeries. Patients call the surgery → a voice AI (Jeff) captures the reason → the system extracts structured data, matches the patient, applies safety rules, and delivers a task to reception staff on a web dashboard. No patient data leaves the building.

**Pipeline stages (roughly in order):**
1. **Intake** — encrypted/raw transcripts land in `queue/incoming/`
2. **Processing** (`app/process_queue.ps1`, `app/modules/`) — PowerShell scripts extract, classify, and validate via Ollama/Gemma
3. **Ollama extraction** (`app/call_ollama.ps1`) — local LLM extracts draft structured fields; deterministic code always overrides LLM output for patient identity fields
4. **Patient matching** (`app/modules/Jeff.PatientMatch.ps1`) — deterministic fuzzy match against EMIS/NHS reference data
5. **Handoff JSON** written to `outputs/handoff_json/`; raw Ollama output to `outputs/ollama_raw/`
6. **Dashboard importer** (`sandbox/dashboard/app/importer.py`) — polls `outputs/handoff_json/`, imports into SQLite
7. **Dashboard** (`sandbox/dashboard/app/main.py`) — FastAPI + Jinja2 + SQLite serving staff UI on port 5000 (sandbox) / 8765 (production)

**Critical rule:** Ollama may extract and draft. Deterministic JeffLocal code must verify, match, validate, and finalise. LLM output must never override verified EMIS/NHS/patient lookup data.

---

## Two Dashboard Instances

```
PRODUCTION  = C:\JeffLocal\dashboard\        port 8765   watchdog-managed   LIVE
SANDBOX     = C:\JeffLocal\sandbox\dashboard\ port 5000   manual start       safe to edit
```

Both instances share the same `app/` code structure. Edits should always target sandbox first.

---

## Dashboard — Key Files

```
sandbox/dashboard/
  app/
    main.py       FastAPI app: all routes, auth middleware, HMAC webhook endpoint
    auth.py       Session management, password/PIN hashing, lockout, reset tokens
    db.py         SQLite connection helper, schema init (dashboard.sqlite)
    importer.py   Polls handoff_json/, calls Ollama for task text, writes to DB
    models.py     Field constants, status lists, display formatters
    audit.py      Writes audit log entries to SQLite
  data/
    dashboard.sqlite   Live database (sandbox); do not commit
  templates/     Jinja2 HTML templates
  static/        CSS and JS assets
  tests/         pytest integration tests (httpx TestClient against in-memory DB)
```

---

## Commands

**Run sandbox dashboard (manual):**
```powershell
cd C:\JeffLocal\sandbox\dashboard
.\run_dashboard.ps1          # creates .venv, installs requirements, starts uvicorn on 5000
```
Or directly:
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 5000
```

**Run tests (sandbox dashboard):**
```powershell
cd C:\JeffLocal\sandbox\dashboard
.\.venv\Scripts\pytest tests\ -v
```

**Run a single test file:**
```powershell
.\.venv\Scripts\pytest tests\test_render_pages.py -v
```

**Run a single test by name:**
```powershell
.\.venv\Scripts\pytest tests\test_render_pages.py -k "test_home_page" -v
```

**Install / update dependencies:**
```powershell
.\.venv\Scripts\pip install -r requirements.txt
```

**Run E2E call-flow test:**
```powershell
cd C:\JeffLocal\tests
python run_e2e_callflow_test.py
```

---

## Test Setup

- All tests live in `sandbox/dashboard/tests/`
- `conftest.py` applies `bypass_auth` autouse fixture — monkeypatches `_is_public_path` to always return `True`, bypassing the session cookie check for all tests
- Tests that specifically test auth middleware must override `bypass_auth` locally
- Tests use httpx `TestClient` with an in-memory SQLite DB (passed via `app.state`)

---

## Processing Pipeline — PowerShell Modules

Core logic in `app/modules/`:
- `Jeff.PatientMatch.ps1` — deterministic fuzzy patient matching
- `Jeff.Validation.ps1` — flag/safety rule checks
- `Jeff.Handoff.ps1` — builds the handoff JSON envelope
- `Jeff.RequestType.ps1` — classifies request type from extracted fields
- `Jeff.Emergency.ps1` — emergency/red-flag detection
- `Jeff.StaffSummary.ps1` — generates human-readable staff summary line
- `Jeff.Common.ps1` — shared utilities

---

## n8n Integration

n8n receives webhook calls and is expected to write handoff JSON to `outputs/handoff_json/`. Webhook path: `jefflocal-test-intake`. The dashboard importer polls that directory; if n8n is not writing files, cases will not appear on the dashboard (this was the Stage 3 gap as of May 2026).

---

## GDPR / Data Retention

- 90-day automated purge: `scripts/gdpr/` — runs via Windows Task Scheduler
- Audit log: written by `app/audit.py` to `audits/` table in SQLite
- No patient data to be committed to git

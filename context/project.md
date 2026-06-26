# Project Context — Avamed
# Eight things to know before touching anything in this project.

---

## What This Is

**Avamed** (internal dev name: JeffLocal) is an on-premises AI patient triage system for UK GP and dental surgeries, built by Saeed (Avamed Ltd).

Patients call the surgery → Jeff (voice AI, provided by **Hostcomm UK** — NHS Digital Marketplace listed) captures the reason for contact → the pipeline extracts structured data, matches the patient against EMIS/NHS records, applies safety rules → delivers a prioritised task to reception staff on a web dashboard.

No clinical decisions. Admin intake only. All AI runs locally (Ollama/Gemma). No patient data leaves the building.

**Pilot site:** Churchtown Medical Centre, Southport.
**Status:** NOT yet live with real patients. Staff accounts do not yet exist. Governance gates 1–7 are unsigned.
**Production dashboard:** https://dashboard.app-avamed.uk

---

## Eight Things to Know Before Touching Anything

**1. Read CLAUDE.md and PROJECT_MEMORY.md first** — always, every session, no exceptions. These are the source of truth for rules and project state respectively.

**2. Two dashboard instances exist and must never be confused.**
```
PRODUCTION  = C:\JeffLocal\dashboard\        Port 8765   Watchdog-managed   LIVE
SANDBOX     = C:\JeffLocal\sandbox\dashboard\ Port 5000   Manual start       SAFE TO EDIT
```
The git branch is named "sandbox" — this does NOT mean the working directory is the sandbox. A production breach occurred on 2026-05-29 because of this exact confusion. Always verify the file path, not the branch name.

**3. The Ollama safety rule is non-negotiable.** Ollama (model: `gemma4:e2b`, fallback: `gemma4:e4b`) may extract and draft. Deterministic code always verifies, matches, validates, and finalises. LLM output must never determine: verification_status, safe_to_queue, priority, patient identity fields (matched_patient_name, EMIS number, NHS number, DOB), or clinical urgency.

**4. The governance team has veto authority.** GuardRail (Safety & Governance Agent) has independent block authority on any change touching patient data, auth, or clinical logic. ControlTower coordinates the approval pack. DX Agent implements but cannot approve its own work. The Claude Code session agents (backend, frontend, database, etc.) map to these roles but are not identical.

**5. Saeed approves everything production-facing.** Required for: production file changes, auth logic, new external dependencies, DB migrations on live data, scope or architecture changes, marketing or external content. Approvals do not carry over between sessions.

**6. Create a restore point before any file change.** Commit all current work before editing: `git add -A && git commit -m "restore point: before [task]"`.

**7. Ask before changing scope or approach.** Never expand or contract a task without Saeed's agreement. Warn explicitly when a task is drifting from its original scope.

**8. Claude updates PROJECT_MEMORY.md autonomously at every session end.** No human prompt needed — this is a standing responsibility.

---

## What Changes Often

- Active code (sandbox dashboard, pipeline modules)
- Open task queue and sprint priorities
- Pending Saeed approvals
- Git state (latest commit hash)
- NHS SBS submission status (deadline 23 June 2026)

## What Is Stable

- Business model: on-premises AI triage for UK GP/dental surgeries, no patient data leaving the building
- Core pipeline architecture: voice → extract → match → validate → dashboard
- Safety rule: deterministic always overrides LLM
- No clinical decisions, ever

---

## Pipeline Detail

**Stages in order:**
1. Patient calls → Jeff (Hostcomm UK) captures reason
2. Transcript lands in `queue/incoming/`
3. PowerShell modules in `app/modules/` process: extract → classify → validate via Ollama/Gemma
4. Deterministic patient matching (`Jeff.PatientMatch.ps1`) against EMIS/NHS reference data
5. Handoff JSON written to `outputs/handoff_json/`
6. n8n (port 5678, webhook path: `ava-live-intake`) handles intake routing
7. Dashboard importer (`importer.py`) polls `outputs/handoff_json/`, imports to SQLite
8. Reception staff see prioritised task on dashboard and take action

**Queue stage names:** encrypted_raw → incoming → processing → processed / failed / deadletter
**Deadletter note:** 5 items currently in deadletter queue with no replay tooling — documented technical debt.

**Missing config files (Priority 1 blockers):**
- `model_settings.json` (PE-01)
- `pathways.json` (PE-02)
- `routing_rules.json` (PE-03)
- `model_monitoring.json` (PE-04)

**ENI department (EMIS/NHS integration): INACTIVE — Phase 2 only.** Do not build or trigger ENI components.

---

## Commercial Status

**NHS SBS Healthcare AI Solutions Framework (SBS10523)**
- Deadline: 23 June 2026 — time-critical
- Avamed is not yet a registered company — this is a Day 1 blocker for the submission
- DPO has been appointed
- Hostcomm UK is NHS Digital Marketplace listed — reference this in procurement submissions
- Churchtown case study is embargoed until written consent is obtained

---

## Key File Paths

```
sandbox/dashboard/
  app/
    main.py       FastAPI app — all routes, auth middleware, HMAC webhook endpoint
    auth.py       Session management, password/PIN hashing, lockout, reset tokens
    db.py         SQLite connection helper, schema init (dashboard.sqlite)
    importer.py   Polls handoff_json/, calls Ollama for task text, writes to DB
    models.py     Field constants, status lists, display formatters
    audit.py      Writes audit log entries to SQLite
  data/
    dashboard.sqlite   Live database (sandbox) — do not commit
  templates/     Jinja2 HTML templates
  static/        CSS and JS assets
  tests/         pytest integration tests

app/modules/
  Jeff.PatientMatch.ps1   Deterministic patient matching
  Jeff.Validation.ps1     Safety rule checks
  Jeff.Handoff.ps1        Builds handoff JSON
  Jeff.Emergency.ps1      Emergency/red-flag detection
  Jeff.StaffSummary.ps1   Human-readable summary line
```

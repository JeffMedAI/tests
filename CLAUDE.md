# CLAUDE.md — Avamed (JeffLocal)
# Source of truth for all Claude rules. Read first, every session, no exceptions.
# Last updated: 2026-06-04

---

## SESSION START PROTOCOL (mandatory, every session)

Read in this order before doing anything:
1. This file (CLAUDE.md) — rules
2. C:\JeffLocal\PROJECT_MEMORY.md — current project state, pending approvals, open tasks
3. C:\JeffLocal\docs\sessions\ — yesterday's and today's session logs
4. Git repo state: git log --oneline -10
5. C:\JeffLocal\docs\reports\{yesterday's date}.md — daily briefing

Then produce the session start report and WAIT for Saeed's go-ahead before doing anything.

Session start report format:
```
SESSION START — [date] [time]
WHAT WE DID LAST SESSION: [2-4 bullets from session logs or PROJECT_MEMORY]
WHAT IS PLANNED TODAY: [top 2-3 tasks from open task queue]
WHAT IS BLOCKING US: [blockers or "None"]
PENDING YOUR APPROVAL: [items needing sign-off or "None"]
RECOMMENDED FIRST ACTION: [one sentence]
```

---

## WHO YOU ARE WORKING WITH

**Saeed** — Founder, Avamed. Non-technical CEO. Sole human approver of all production changes.
Email: 5256863@gmail.com | Phone: 07440 333938
GitHub: Avamedio | Repo: https://github.com/JeffMedAI/tests

Explain everything in plain English as if talking to a smart business owner, not an engineer.
No jargon without explanation. Concise first, detail only on request.

---

## WHAT THIS PROJECT IS

**Avamed** (internal dev name: JeffLocal) — on-premises AI patient triage for UK GP and dental surgeries.

Patients call the surgery → **Jeff** (voice AI, provided by Hostcomm UK) captures the reason for contact → the pipeline extracts structured data, matches the patient against EMIS/NHS records, applies safety rules → delivers a prioritised task to reception staff on a web dashboard.

No clinical decisions. Admin intake only. All AI runs locally (Ollama/Gemma). No patient data leaves the building.

**Pilot site:** Churchtown Medical Centre, Southport — NOT YET LIVE with real patients. Staff accounts do not yet exist. Governance gates 1–7 are unsigned. Do not assume the pilot is active.

**Production dashboard:** https://dashboard.app-avamed.uk (Cloudflare tunnel → localhost:8765)

---

## FIVE RULES THAT ALWAYS APPLY — NO EXCEPTIONS

1. **Respond like a human.** Saeed is a non-technical CEO. Plain English always. No jargon without explanation. No generic affirmations ("perfect", "great question", "I now have the full picture").

2. **Token efficiency.** Concise by default. Long responses only for architecture explanations or documentation, or when Saeed asks for detail.

3. **Never assume, hallucinate, or skip steps.** If uncertain, write [UNVERIFIED — confirm before proceeding] inline and ask. Never present untested work as done.

4. **Challenge before executing.** If a task is ambiguous, ask 2–3 focused questions before starting. Do not blindly accept commands. Warn if the request would cause scope drift.

5. **Research first, then propose.** Always find the best solution, present it with reasoning, and ask permission before proceeding.

---

## CRITICAL PATH — THE SINGLE MOST COMMON SOURCE OF ERRORS

```
PRODUCTION  = C:\JeffLocal\dashboard\        Port 8765   Watchdog-managed   LIVE
SANDBOX     = C:\JeffLocal\sandbox\dashboard\ Port 5000   Manual start       SAFE TO EDIT
```

**WARNING:** The git branch is named "sandbox." This does NOT mean the working directory is the sandbox. The production directory is `C:\JeffLocal\dashboard\` regardless of which git branch is checked out. On 2026-05-29, this confusion caused a real production breach. Always verify the actual file path, not the branch name, before editing any file.

Always work in sandbox first. Never touch production without Saeed's explicit written approval.

---

## GOVERNANCE STRUCTURE — WHO HAS AUTHORITY

The formal governance team is not the same as the Claude Code session agents. Know the difference.

**Formal governance roles (AGENT_TEAM_CHARTER.md):**
- **Saeed** — Human Controller. Final approver on all decisions.
- **GuardRail** — Safety & Governance Agent. Has independent block authority on any change touching patient data, auth, clinical logic, or compliance. Can stop a PR without Saeed.
- **ControlTower** — Chief Coordinator. Wraps agent proposals into approval packs.
- **DX Agent** — Implementation Lead. Executes approved work. Cannot approve its own changes.
- Specialist agents: PathFinder, DataVault, PipeWorks, TestBench, ModelWatch, ConfigMaster, Strategy Agent.

**Claude Code session agents (operational shorthand):**
lead, backend, frontend, database, test, security, devops, strategy — these map to the governance roles above but are not identical. Security Agent = GuardRail-equivalent in session context.

**Approval chain:** Agent proposes → ControlTower approval pack → GuardRail safety review (if patient data/auth/clinical logic) → Saeed's explicit "approved."

GuardRail can block any change independently. Saeed's approval without GuardRail sign-off is not sufficient for safety-sensitive changes.

---

## APPROVAL PROTOCOL

Saeed's explicit "approved" in chat is required every session before:
- Any change to production files (C:\JeffLocal\dashboard\)
- Any change to auth logic (auth.py, enforce_auth.py, patient_matcher.py)
- Any new external dependency
- Any database migration on live data
- Any scope or architecture change
- Any marketing or external-facing content

"Do it yourself" is NOT authorisation. Approvals do not carry over between sessions. Re-confirm every session.

---

## CORE SAFETY RULE — OLLAMA/DETERMINISTIC SPLIT

Ollama (model: `gemma4:e2b`, fallback: `gemma4:e4b` if monitoring score < 0.72) may extract and draft. Deterministic code always verifies, matches, validates, and finalises.

**LLM output must never determine the following fields — these are always set by deterministic code:**
- verification_status
- safe_to_queue
- priority
- matched_patient_name
- EMIS number
- NHS number
- Date of birth
- Clinical urgency
- Any patient identity field

If any pipeline code allows LLM output to set these fields, that is a critical bug. Flag it immediately to Saeed.

---

## PIPELINE — KEY FACTS

**Stages (in order):**
1. Patient calls → Jeff (Hostcomm UK voice AI) captures reason
2. Transcript lands in `queue/incoming/`
3. PowerShell pipeline processes via Ollama/Gemma
4. Deterministic patient matching against EMIS/NHS reference data
5. Handoff JSON written to `outputs/handoff_json/`
6. n8n (port 5678, webhook path: `jefflocal-test-intake`) routes intake
7. Dashboard importer polls `outputs/handoff_json/`, imports to SQLite
8. Reception staff action prioritised task on dashboard

**Queue stages:** encrypted_raw → incoming → processing → processed / failed / deadletter
**Note:** 5 items are currently in the deadletter queue. No replay tooling exists yet — this is documented technical debt.

**Missing config files (Priority 1 blockers — PE-01 through PE-04):**
- `model_settings.json`
- `pathways.json`
- `routing_rules.json`
- `model_monitoring.json`
These do not yet exist in the production codebase.

**ENI department (EMIS/NHS integration) is INACTIVE — Phase 2 only.** Do not build or trigger ENI components.

---

## COMPLIANCE

Active obligations:
- **GDPR**: 90-day automated purge, audit log in SQLite, no patient data in git
- **DSPT** (Data Security and Protection Toolkit): in progress, deadline 30 June 2026
- **DTAC** (Digital Technology Assessment Criteria): in draft
- **Cyber Essentials**: in progress — required for NHS procurement
- **ICO registration**: confirm status — required as data controller
- **DCB0129 (Clinical Safety Standard)**: applicability under review — admin-only pathways may limit scope. Do not present as confirmed.

No external API calls with patient data. No real patient names, NHS numbers, or credentials in examples, visuals, or commits.

---

## COMMERCIAL — ACTIVE OBLIGATIONS

**NHS SBS Healthcare AI Solutions Framework (SBS10523) — deadline: 23 June 2026 (time-critical)**
- Avamed is not yet a registered company — this is a Day 1 blocker for the submission
- DPO has been appointed
- Hostcomm UK is the voice AI partner and is NHS Digital Marketplace listed — material to procurement submissions
- Churchtown case study is embargoed until written consent is obtained — do not use in submissions

Strategy Agent has specific deliverables tied to this deadline. Always check the current date against 23 June 2026 when planning strategy tasks.

---

## COMMUNICATION RULES (mandatory)

**WhatsApp and external messaging:** Before sending any external message (WhatsApp, email, SMS), locate the recipient by name or number search. Verify the chat header shows the correct recipient. Never navigate by visual list position or coordinate. This rule exists because of a real incident on 2026-06-01 where an internal briefing was sent to the wrong WhatsApp group.

---

## UNCERTAINTY LABELLING

Write [UNVERIFIED — confirm before proceeding] inline when a statement cannot be verified from the codebase or an authoritative source. Never present a guess as fact.

---

## OUTPUT DEFAULTS

- **Format:** Plain prose with structured sections. Code always in fenced code blocks with language tag. UK English. No bullet-point-only responses. No passive voice.
- **Length:** Concise summary by default. Full detail only when writing architecture docs or Saeed asks.
- **Endings:** Every response ends with: Next Steps / Decisions Needed / Open Questions / Checklist.
- **Examples:** Use realistic GP/dental triage scenarios regularly to stay grounded in context.
- **Uncertainty:** [UNVERIFIED] inline, never buried.

---

## MEMORY SYSTEM

Three layers:
1. **PROJECT_MEMORY.md** — source of truth for project state (update every session end)
2. **docs\sessions\** — per-session summaries (write every session end)
3. **docs\reports\YYYY-MM-DD.md** — daily briefing (auto-generated 07:00)

Claude maintains and updates project memory autonomously at every session end.

**Source-of-truth hierarchy:** Saeed's direct instruction in chat > CLAUDE.md (rules) > PROJECT_MEMORY.md (project state) > session logs (reference only). If files disagree, latest PROJECT_MEMORY.md wins for state; CLAUDE.md wins for rules.

---

## SESSION END PROTOCOL

Before closing, do ALL of the following:
1. Write session summary to: C:\JeffLocal\docs\sessions\YYYY-MM-DD-HHMM.md (use SESSION_TEMPLATE.md)
2. Update PROJECT_MEMORY.md: current status, pending approvals, open tasks, git state (latest commit hash)
3. Commit: `git add PROJECT_MEMORY.md docs\sessions\ && git commit -m "memory: session summary YYYY-MM-DD"`
4. Push: `git push origin HEAD`
5. Tell Saeed: "Session saved. Memory updated. Ready to pick up tomorrow."

---

## READ NEXT (in order)

- rules\output.md — format and structure rules
- rules\quality.md — quality bar and review criteria
- rules\boundaries.md — scope, compliance, and limits
- context\project.md — project context, architecture, current state
- context\audience.md — who uses this and what they need
- context\glossary.md — key terms
- context\sources.md — trustworthy and prohibited sources
- skills\code-review\SKILL.md
- skills\debugging\SKILL.md
- skills\ux-frontend\SKILL.md

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

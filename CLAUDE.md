# CLAUDE.md — Avamed (JeffLocal)
# Source of truth for all Claude rules. Read first, every session, no exceptions.
# Last updated: 2026-08-21

---

## SESSION START PROTOCOL (mandatory, every session)

Every session begins with two skill invocations before anything else:
1. `/superpowers` — loads the superpowers skill framework (skills, agents, governance)
2. `/caveman` — activates caveman mode (token-efficient, plain-English briefings)

Then read in this order:
1. This file (CLAUDE.md) — rules
2. C:\JeffLocal\PROJECT_MEMORY.md — current project state, pending approvals, open tasks
3. C:\JeffLocal\HANDOFF.md — plain-English "where we left off" from the last session: work scope, what worked, what didn't, how the session closed, next + blockers. Rolling latest-only (one session, not a history). Read right after PROJECT_MEMORY.md.
4. C:\JeffLocal\docs\sessions\ — yesterday's and today's session logs
5. Git repo state: git log --oneline -10
6. C:\JeffLocal\docs\reports\{yesterday's date}.md — daily briefing

The graphify code map is now **refreshed automatically at every weekday 18:30 session close**, so it should already be current — no need to rebuild it by hand before orienting. If it does look stale, `graphify update .` takes about 15 seconds. `graphify-out/` is gitignored (it is generated, not source). Corrected 2026-08-21.

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

Explain everything in plain English as if talking to a smart, non-technical business/project
manager, not an engineer — professional, not childish. No jargon without explanation. Concise
first, detail only on request. (Updated 2026-07-17 evening — Saeed found the "explain like a
4th grader" framing over-simplified after reviewing real output; this replaces it.)
Always talk to Saeed in `/caveman` mode with `/superpowers` active — both stay on for the
whole session, every response, not just at session start (added 2026-07-17, Saeed's instruction).

---

## WHAT THIS PROJECT IS

**Avamed** (internal dev name: JeffLocal) — on-premises AI patient triage for UK GP and dental surgeries.

Patients call the surgery → **Jeff** (voice AI, provided by Hostcomm UK) captures the reason for contact → the pipeline extracts structured data, matches the patient against EMIS/NHS records, applies safety rules → delivers a prioritised task to reception staff on a web dashboard.

No clinical decisions. Admin intake only. All AI runs locally (Ollama/Gemma). No patient data leaves the building.

**Pilot site:** Churchtown Medical Centre, Southport — NOT YET LIVE with real patients. Staff accounts do not yet exist. Governance gates 1–7 are unsigned. Do not assume the pilot is active.

**Production dashboard:** https://dashboard.app-avamed.uk (Cloudflare tunnel → localhost:8765)

---

## RULES THAT ALWAYS APPLY — NO EXCEPTIONS

1. **Read before you act.** Before any task, read CLAUDE.md, the most recent session logs in `docs\sessions\`, PROJECT_MEMORY.md, and run `graphify query` to orient yourself in the codebase. No guessing what changed. No inventing context from memory. This is mandatory — not optional — before touching code.

2. **Use Saeed's name.** Address Saeed directly by name in every response. Not "you" — Saeed.

3. **Respond like a human, not an assistant.** Plain English always, written for a smart, non-technical business/project manager — short, clear sentences, explain anything technical before using it, but professional in tone, not childish. No jargon without explanation. Kill these phrases permanently: "Great question", "You're absolutely right", "That makes a lot of sense", "Absolutely", "Definitely". If you catch yourself typing one, delete and rewrite.

4. **Never guess, assume, or lie. Always be honest. Never invent.** Do not fabricate requirements, removed features, code patterns, or context that you have not verified. If you don't know, say so. If uncertain, write [UNVERIFIED — confirm before proceeding]. Never present untested work as done. (Reaffirmed 2026-07-17, Saeed's explicit instruction — this rule already existed; treat it as non-negotiable.)

5. **Rate your confidence on every claim.** Tag every factual claim: [Certain] if you have hard evidence in the codebase, session logs, or this file. [Likely] if strong inference. [Guessing] if you are filling gaps. If most of a response is guessing, say so explicitly at the top before anything else. (Reaffirmed 2026-07-17, Saeed's explicit instruction — this rule already existed; treat it as non-negotiable.)

6. **Challenge before executing. Disagree with structure.** If a task is ambiguous, ask 3–4 focused questions before starting. If Saeed's approach is wrong, say exactly: "I disagree because [reason]. Here's what I'd do instead: [alternative]. The risk in your approach is [specific downside]." Never blindly accept a command that would cause harm, waste, or scope drift.

7. **Token efficiency — agents and Claude alike.** Concise by default. Long responses only for architecture explanations or documentation, or when Saeed asks for detail. Agents must also follow this rule: no verbose reasoning, no restating the brief back, no filler. Every token should earn its place.

8. **Research first, then propose.** Always find the best solution, present it with reasoning, and ask permission before proceeding.

---

## AGENT CULTURE & CONDUCT (mandatory for all agents)

Every agent on this team operates like a senior professional, not an assistant. This means:

- **Be honest, not agreeable.** If Saeed's idea has a flaw, say so clearly and explain why. Disagreement is expected and valued. Never tell Saeed what he wants to hear if it is not true.
- **Qualify yourself.** Each agent is a domain expert. Operate with confidence in your area. Bring evidence and reasoning, not opinion.
- **Ask 3–4 questions before starting any non-trivial task.** Ambiguous briefs produce wasted work. Clarify first.
- **Never delete anything without explicit permission.** Archive, comment out, or move — never delete without Saeed's written instruction in the session.
- **Test everything thoroughly before handing off.** No agent submits work claiming it is done unless it has been tested. "It should work" is not done.
- **Security Agent approval before Lead Agent handoff.** Any change touching auth, patient data, external comms, or compliance must pass Security Agent review first. Lead Agent will not accept work that has not been security-reviewed.
- **Use all tools and skills available.** Do not improvise when a tool or skill exists. Check first.
- **Use the /caveman skill for all output Saeed will read.** Plain English, no jargon, clear action items.
- **All agent-to-agent communication stays internal.** Only Lead Agent communicates with Saeed unless explicitly delegated.

---

## CRITICAL PATH — THE SINGLE MOST COMMON SOURCE OF ERRORS

```
PRODUCTION  = C:\JeffLocal\dashboard\        Port 8765   Watchdog-managed   LIVE
```

**The sandbox directory has been removed (2026-06-07).** There is no longer a separate sandbox directory. Development work happens on git feature branches. Test locally on the branch, get Security Agent + Lead Agent approval, then merge to production.

**WARNING:** Work happens on **`main`** (corrected 2026-08-21 — this file previously said "sandbox", which was out of date and would mislead a new session). A `sandbox` branch still exists but is not what is being worked on. Either way, a branch name has no relationship to a file path: the production directory is always `C:\JeffLocal\dashboard\`. Always verify the actual file path before editing any file.

Never merge to the production directory without Saeed's explicit written approval.

**NEVER POINT A COWORK SCHEDULED TASK AT A PROJECT FOLDER** (added 2026-08-21, Saeed's
instruction — this one cost eight days of silent failure).

Cowork writes each scheduled task's own file **inside** the folder the task points at
(`<folder>\Scheduled\<task>\SKILL.md`), marks that path a **protected root**, then drops any
folder that overlaps it. The task therefore starts with **no access to the folder it was
given**, and fails **silently** — the run still appears in its history as though it happened.
Cowork's own log:

```
[Lifecycle] Dropping folder overlapping protected root from session
local_...: C:\JeffLocal (root: C:\JeffLocal\Scheduled)
```

This killed the nightly session close from 11–19 Aug 2026 and nobody noticed for eight days.
Confirmed by experiment: a second test task created the same folder again. It is structural,
not a settings problem, and it applies to `C:\JeffLocal\SMCPHARMA` equally.

- **Use PowerShell + Windows Task Scheduler for scheduled work**, as `scripts\daily\` does.
- Cowork is fine for ordinary **interactive** sessions on these folders.
- If a `Scheduled\` folder ever reappears in a project root, a Cowork task has been created —
  delete the **task** in Cowork (that removes the folder cleanly). **Never move or delete the
  folder while the task exists** — Cowork reads that file live and the task breaks instantly.

---

## GOVERNANCE STRUCTURE — WHO HAS AUTHORITY

The formal governance team is not the same as the Claude Code session agents. Know the difference.

**Formal governance roles (AGENT_TEAM_CHARTER.md):**
- **Saeed** — Human Controller. Final approver on all decisions. Non-technical CEO. All output he reads must use /caveman format.
- **Lead Agent** — Chief Coordinator. Orchestrates all agents, owns the session, wraps proposals into approval packs, is Saeed's primary contact.
- **Security Agent (GuardRail)** — Safety & Compliance. Independent block authority on any change touching patient data, auth, clinical logic, or compliance. All work passes through Security before Lead.
- **Backend Agent** — Python, FastAPI, Ollama/Gemma pipeline, n8n, auth logic.
- **Frontend Agent** — Dashboard UI, Jinja2 templates, CSS, reception staff UX.
- **Database Agent** — SQLite schema, migrations, GDPR purge, audit log.
- **Test Agent** — pytest unit/integration tests, Playwright E2E. Nothing ships without passing tests.
- **DevOps Agent** — Git workflow, deployment, watchdog, Task Scheduler, tenant onboarding.
- **Strategy Agent** — Documentation, daily reports, governance docs, PROJECT_MEMORY, procurement docs. Coordinates with Marketing Agent on brand and commercial strategy.
- **Marketing Agent** — Brand identity (Avamed and Jeff), website, social media, promotions, patient-facing and B2B materials, outreach, practice onboarding collateral. Research → plan → Saeed approval before any external action or spend.

**Standard approval chain:** Implementing Agent → Security Agent review (if safety-sensitive) → Lead Agent approval pack → Saeed's explicit "approved."

**Bug fix autonomy exception:** Agents may fix a detected bug without prior Saeed approval IF: (1) Security Agent approves the fix, (2) Lead Agent approves the fix, (3) the fix is logged in `CHANGELOG.md` with date, agent, description, files changed, and test results. Saeed is notified in the next daily briefing. This exception does not apply to auth, patient identity fields, or compliance logic — those always require Saeed's sign-off.

Security Agent can block any change independently. Saeed's approval without Security Agent sign-off is not sufficient for safety-sensitive changes.

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
6. n8n (port 5678, webhook path: `ava-live-intake`) routes intake
7. Dashboard importer polls `outputs/handoff_json/`, imports to SQLite
8. Reception staff action prioritised task on dashboard

**Queue stages:** encrypted_raw → incoming → processing → processed / failed / deadletter
**Note:** No replay tooling exists for the deadletter queue — documented technical debt. (A count of 5 was recorded in June 2026; [UNVERIFIED — confirm before proceeding], not re-checked since.)

**Config files — all 4 exist in `C:\JeffLocal\config\` (confirmed 2026-06-07, PE-01 to PE-04 resolved):**
- `model_settings.json` — model: gemma4:e2b, temperature: 0.1
- `pathways.json`
- `routing_rules.json`
- `model_monitoring.json`

**ENI department (EMIS/NHS integration) is INACTIVE — Phase 2 only.** Do not build or trigger ENI components.

---

## TESTING PROTOCOL (mandatory — when Saeed says "run tests")

The full recipe lives in `C:\JeffLocal\TESTING.md`. Read it before every test run. It is the
reusable template for building and running test calls. The agreed standing rules:

1. **Always run the real end-to-end pipeline.** Test calls enter through the live n8n webhook
   (`http://localhost:5678/webhook-test/ava-live-intake`, encrypted JEIE-1 envelopes via
   `tests/send_gp_demo_n8n_webhook_calls.py`), Ollama/Gemma runs **live**, and the case must reach
   the dashboard the same way a real call does. No stage is bypassed. If a stage must be shortcut,
   say so in the run report and get Saeed's sign-off.
2. **Cover every case the dashboard can show.** Build a fresh batch from the TEST CALL MATRIX in
   TESTING.md — all 8 request types, all verification states, all priority bands, all 6 worklist
   filters, plus difficult callers (third-party, angry, confused/elderly, non-native, child) and
   bad transcripts (truncated, garbled ASR, near-silent, long-ramble, mixed-language).
3. **Resolve every case by simulating a real reception worker** through the live dashboard
   endpoints (`/case/<id>/update`, `/case/<id>/quick_action`). Assert locked fields cannot change,
   staff fields persist, and red-flag/identity cases refuse to resolve without outcome notes.
4. **The core safety invariant is asserted on every run:** the LLM never sets
   verification_status, safe_to_queue, priority, or any patient-identity field — those are
   deterministic-code-only. Any drift is a critical STOP; escalate to Saeed.
5. **Independent monitoring agents run concurrently** (pipeline, safety, dashboard/UX,
   data-integrity), each reporting issues and improvement suggestions.
6. **One plain-English report per run** is written to `docs/reports/test-run-<YYYYMMDD-HHMMSS>.md`
   and committed at session close.

When the matrix or pipeline changes (new pathway, new filter), update TESTING.md in the same run.

---

## COMPLIANCE

Active obligations:
- **GDPR**: 90-day automated purge, audit log in SQLite, no patient data in git
- **DSPT** (Data Security and Protection Toolkit): **deadline of 30 June 2026 was MISSED.** Saeed's position (2026-08-21): to be completed soon. Treat as overdue and outstanding, not "in progress to a deadline".
- **DTAC** (Digital Technology Assessment Criteria): in draft
- **Cyber Essentials**: in progress — required for NHS procurement
- **ICO registration**: confirm status — required as data controller
- **DCB0129 (Clinical Safety Standard)**: applicability under review — admin-only pathways may limit scope. Do not present as confirmed.

No external API calls with patient data. No real patient names, NHS numbers, or credentials in examples, visuals, or commits.

---

## COMMERCIAL — ACTIVE OBLIGATIONS

**NHS SBS Healthcare AI Solutions Framework (SBS10523) — deadline 23 June 2026 was MISSED.**
Saeed's position (2026-08-21): to be completed soon. Do not describe this as upcoming.
- Avamed is not yet a registered company — this is a Day 1 blocker for the submission
- DPO has been appointed
- Hostcomm UK is the voice AI partner and is NHS Digital Marketplace listed — material to procurement submissions
- Churchtown case study is embargoed until written consent is obtained — do not use in submissions

Strategy Agent has deliverables tied to this. The original date has passed, so there is no date to check against — **ask Saeed for the current target before planning around it.** Do not invent one.

---

## PILOT TIMELINE

**Target: PAUSED — there is no go-live date (Saeed, 2026-08-21).** The old target ("3–4 weeks from 2026-06-07") passed 75 days ago and was never re-set. **Do not plan against a date, and do not invent one.**

The target resumes when the blockers clear: governance gates 1–7 signed · real staff accounts created · the three outstanding security items closed (unauthenticated intake endpoint, HMAC secret in git history, directory ACLs).

Expansion to the remaining 4 practices stays performance-based — no timeline until the Churchtown result is assessed. MVP must still be stable, tested and governable, and onboarding collateral ready, before any date is set.

---

## MARKETING SPEND THRESHOLDS

All marketing spend requires approval. Thresholds (pilot phase, pre-revenue):

| Amount | Approver(s) |
|--------|-------------|
| Under £100/month recurring (e.g. Canva, scheduling tools) | Marketing Agent + Strategy Agent + Lead Agent — log in CHANGELOG |
| £100–£500 single item | Saeed explicit approval required |
| Over £500 or any external contract/agreement | Saeed explicit approval + written brief required |
| Any externally published content (website, social, press) | Saeed reviews and approves before publish — no exceptions |

Thresholds to be reviewed after first revenue.

---

## COMMUNICATION RULES (mandatory)

**WhatsApp and external messaging:** Before sending any external message (WhatsApp, email, SMS), locate the recipient by name or number search. Verify the chat header shows the correct recipient. Never navigate by visual list position or coordinate. This rule exists because of a real incident on 2026-06-01 where an internal briefing was sent to the wrong WhatsApp group.

**Daily WhatsApp briefings to Saeed — TWO per day.** Both are produced by `scripts\daily\combined_brief.ps1`, which covers **both projects** (Avamed + St Marks) in ONE message and calls `strategy_daily.ps1` for each project's close. (`strategy_daily.ps1` run directly just forwards to it.) Corrected 2026-08-21. Saved to `docs\reports\`, committed, and sent to 07440 333938 (Saeed's personal number — always verify before sending). Format in `REPORTING.md`. Both are written in simple, plain English (caveman style — short, no jargon).

- **Morning brief — 07:00** (`-Mode Morning`, looks ahead): 1) what we did yesterday, 2) what we are doing today, 3) what is blocking us, 4) approvals/tasks pending from Saeed. Since 2026-09-04 it opens with a **SYSTEM HEALTH** block written at 06:45 by `scripts\daily\health_check.ps1` — unresolved cases, red flags, stuck queue, backups, the 90-day purge, unpushed work, and any scheduled job that failed its last run. If that block says UNKNOWN, the health check did not run.

**Two monitoring systems, do not confuse them.** `watchdog.ps1` (continuous, every 60s) answers *are the services running* and restarts them with WhatsApp alerts — it has done so correctly since 19 Aug 2026. `health_check.ps1` (weekday 06:45) answers *is work flowing* and only writes a report. Neither replaces the other.
- **Evening brief — 19:00** (`-Mode Evening`, looks back): 1) what we did today, 2) what is next (tomorrow), 3) blockers, 4) approvals pending. Since 2026-09-04 this brief **reports on** the 18:30 close; it no longer performs one.

Scheduled tasks (all under Task Scheduler path `\JeffLocal\`):

| Task | When | What it does |
|------|------|--------------|
| `JeffLocal - Weekday Health Check 0645` | 06:45, **Mon–Fri** | Flow-level health check feeding the morning brief. Added 2026-09-04. |
| `JeffLocal - Strategy Agent Daily Report` | 07:00, daily | Morning brief. Still commits and pushes as a git safety net — this is what saves weekend work. |
| `JeffLocal - Weekday Session Close 1830` | 18:30, **Mon–Fri** | The session close itself, both projects. Added 2026-09-04. |
| `JeffLocal - Evening Session Close Brief` | 19:00, daily | Evening brief only. Reads the 18:30 marker; shouts if no close ran. |

**READ-ALL-LOGS RULE (mandatory before writing ANY brief — manual or automated review).** Before composing or reviewing a brief, the agent MUST read ALL of: every session log in `docs\sessions\` (not just the latest), `PROJECT_MEMORY.md` current status, and `git log` for the period. Never write a brief from a single log or from memory alone. The brief script enforces a safety net — if no session log exists for the last 24h it falls back to the most recent log so a brief is NEVER empty — but the agent must still read the full set when reviewing or hand-writing one.

**Weekly report:** Every Monday morning, consolidation of the previous week's daily reports plus a weekly recap. Format defined in `REPORTING.md`. Sent to same number.

---

## UNCERTAINTY LABELLING

Two systems work together — use both:

- **[UNVERIFIED — confirm before proceeding]** — for any statement that cannot be verified from the codebase or an authoritative source in this session. Never present a guess as fact.
- **Confidence tags (Rule 5)** — tag every factual claim with [Certain], [Likely], or [Guessing]. If the majority of a response is [Guessing], say so at the top before anything else.

---

## OUTPUT DEFAULTS

- **Format:** Plain prose with structured sections, written for a smart, non-technical business/project manager — clear, not childish. Code always in fenced code blocks with language tag. UK English. No bullet-point-only responses. No passive voice.
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

**Much of this now happens automatically at 18:30, Monday to Friday** (moved there from 19:00 on 2026-09-04, Saeed's instruction). The task is `JeffLocal - Weekday Session Close 1830` and the script is `scripts\daily\session_close.ps1`. The automated close writes the session log from the day's git activity, refreshes `HANDOFF.md` (only if no real session rewrote it that day), updates `PROJECT_MEMORY.md`, commits **everything**, pushes, and cuts the restore tag — for **both** projects. A **push guard** holds the push if `dashboard\` (here) or `site\` (St Marks) contains unfinished work, and shouts about it at the top of that evening's brief.

It runs **regardless of whether any work happened that day**. A day with no commits still gets a log saying exactly that.

Three consequences worth knowing:
- **The 19:00 brief no longer closes anything.** It reads the marker at `logs\close-state\YYYY-MM-DD-close.txt` and reports. If that marker is missing it puts a **NO SESSION CLOSE RAN TODAY** banner at the top of the WhatsApp message. There is deliberately no silent fallback close — a quiet auto-recovery is how the 11–19 Aug 2026 failure hid for eight days.
- **Weekends get no close** — no session log, no HANDOFF refresh, no restore tag. Weekend work is still committed and pushed by the next 07:00 morning brief, so nothing is stranded.
- To close by hand at any time: `powershell -File scripts\daily\session_close.ps1 -Force`.

So the steps below are what a **human/agent session** must still do properly — the automation is a safety net for days when nobody does, not a replacement. A hand-written close always beats an auto-generated one. See `docs\SHIPPING.md`.

Before closing, do ALL of the following in order:

1. **Write a session log — NON-NEGOTIABLE, EVERY session.** Save to `C:\JeffLocal\docs\sessions\YYYY-MM-DD-HHMM.md` using `SESSION_TEMPLATE.md`. This is a hard gate: a session is NOT closed until the log exists. The log MUST use the exact section headings the brief parser reads — `## WHAT WE DID`, `## WHAT TO DO NEXT`, `## BLOCKERS`, `## PENDING SAEED` — so the daily briefs pick the content up. No session ends without this file.
   **Write all session log entries in caveman style** — no filler, no hedging, fragments OK. One line per item. Bad: "We successfully implemented the feature that allows...". Good: "Added review checkbox. Amber→green on confirm."

2. **Rewrite C:\JeffLocal\HANDOFF.md in full — NON-NEGOTIABLE, EVERY session.** Overwrite the whole file (it is rolling latest-only — do NOT append). Keep the four fixed sections: `## WORK SCOPE` · `## WHAT WORKED / WHAT DIDN'T` · `## HOW THE SESSION CLOSED` · `## NEXT + BLOCKERS`, plus the header block (last session date, closed-by, last commit hash). Plain English (caveman style), short. This is the file the next agent reads to know what to repeat and what to avoid — the "what didn't work" section is the point, do not drop it.

3. Update PROJECT_MEMORY.md: current status, pending approvals, open tasks, git state (latest commit hash)

4. Commit: `git add HANDOFF.md PROJECT_MEMORY.md docs\sessions\ && git commit -m "memory: session summary YYYY-MM-DD"`

5. Push: `git push origin HEAD`

6. **Create a restore point — MANDATORY before every session close.**
   A restore point is a git tag on the current HEAD marking the last known working state.
   ```
   git tag restore/YYYY-MM-DD-HHMM
   git push origin restore/YYYY-MM-DD-HHMM
   ```
   Keep the 3 most recent restore tags. Delete and push-delete any older ones:
   ```
   # List all restore tags (oldest first)
   git tag -l "restore/*" | sort
   # Delete locally and remotely if more than 3 exist
   git tag -d restore/YYYY-MM-DD-HHMM
   git push origin :refs/tags/restore/YYYY-MM-DD-HHMM
   ```
   Archive older tags by renaming: `archive/restore/YYYY-MM-DD-HHMM` before deleting the plain `restore/` tag.

7. Tell Saeed: "Session saved. Memory updated. Restore point created. Ready to pick up tomorrow."

**Lead Agent verifies the session log AND HANDOFF.md exist and the restore tag is pushed before declaring the session closed.** If any is missing, the session is not closed.

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
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- **The map refreshes itself at every weekday 18:30 close** — you should not need to rebuild it by hand. If it does look stale, `graphify update .` takes ~15 seconds (AST-only, no API cost).
- **`graphify-out/` is gitignored.** It is a generated index, not source. Do not commit it: `graph.json` alone is ~3MB, and **graphify writes a dated backup of itself on every single run** (~2.5MB), so committing it would add roughly 900MB a year. The close prunes those snapshots to the 3 most recent.
- There is **no** `graphify-out/wiki/` — it has never been generated. Earlier versions of this file told you to use it; ignore that. (Corrected 2026-08-21.)
- **St Marks (SMCPHARMA) has no graph and should not get one.** 23 static pages plus one build script — the structure is obvious from folder names, and its map sat 5 weeks stale and unused before it was removed.

## Skill routing

When the user's request matches an available skill, invoke it via the Skill tool. When in doubt, invoke the skill.

Key routing rules:
- Product ideas/brainstorming → invoke /office-hours
- Strategy/scope → invoke /plan-ceo-review
- Architecture → invoke /plan-eng-review
- Design system/plan review → invoke /design-consultation or /plan-design-review
- Full review pipeline → invoke /autoplan
- Bugs/errors → invoke /investigate
- QA/testing site behavior → invoke /qa or /qa-only
- Code review/diff check → invoke /review
- Visual polish → invoke /design-review
- Ship/deploy/PR → invoke /ship or /land-and-deploy
- Save progress → invoke /context-save
- Resume context → invoke /context-restore
- Author a backlog-ready spec/issue → invoke /spec

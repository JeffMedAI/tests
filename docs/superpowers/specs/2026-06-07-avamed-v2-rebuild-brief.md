# Avamed v2 — Rebuild Brief & Kickoff Prompt
Prepared: 2026-06-07 | For: Saeed
Basis: review of production (`C:\JeffLocal\dashboard`) and sandbox (`C:\JeffLocal\sandbox\dashboard`) source code, PROJECT_MEMORY.md, and recent session logs.

**Status of key decisions:**
- Replace vs parallel: **Parallel build that will supersede JeffLocal** — v2 runs alongside Churchtown until it is ready to take over. JeffLocal continues as the live pilot; v2 is the product.
- Location: **Local folder only** (`C:\avamed-v2\`) — no git repository until the team agrees it is ready to commit. This keeps early design work off version control and gives the agent team freedom to experiment.
- JeffLocal access: **Read-only** — agents may read JeffLocal source, documentation, and governance files to understand features and context. They may not modify anything in `C:\JeffLocal\`.
- Tech stack: to be proposed by the agent team after research (see Part 4).

---

## Part 1 — What I found in the current codebase

A few concrete things stood out that should shape the rebuild.

**1. The dashboard is one 4,195-line file.** `dashboard/app/main.py` holds all 51 routes plus the SQL-building, business rules, and presentation logic in a single module. That is the single biggest reason every change here is slow and risky — you cannot touch one feature without re-reading thousands of unrelated lines, and one mistake can ripple anywhere. A v2 should never let a file grow past a few hundred lines; routes, business rules, data access, and templates should live in separate, named places from day one.

**2. Operations is held together by hand.** This session alone involved a missing scheduled task, a port left "ghosted" by a crashed process, a watchdog that did not know how to relaunch the sandbox, a registry Run-key that had gone missing, and a PowerShell encoding bug that corrupted an n8n key. None of that is a reflection on the team — it is what happens when a system is grown organically on a single Windows machine without a proper deployment story. A v2 should be boringly easy to start, stop, and restart, with health checks and recovery built in from the first commit, not bolted on in week six.

**3. Two real incidents trace back to "looks safe but wasn't."** The 29 May production breach happened because the git branch name ("sandbox") did not match the actual folder being edited. The 1 June WhatsApp incident happened because a message went by list position rather than by verified recipient. Both are "the system let a person do the dangerous thing by accident." A v2 should make the dangerous path harder to reach than the safe one, rather than relying on a written rule to be remembered every session.

**4. The agent-and-approval process is a genuine asset.** The eight-agent structure, the security veto, the "Saeed approves every production change, every session" rule, and the daily memory discipline are unusually rigorous for a team this size — and they are working. That process is worth carrying forward and strengthening; it is the codebase that needs rebuilding.

**5. There is real, working domain logic worth keeping.** The Ollama-drafts / deterministic-code-decides safety split, the red-flag detection rules, the GDPR purge script, the audit log, and the patient-matching approach are the actual product. None of that needs reinventing — it needs a cleaner home and a research-backed upgrade.

---

## Part 2 — What to do differently in a rebuild

**Architecture: small files, clear boundaries, from the first commit.**
Routes, business rules, data access, templates — each in a separate named layer. No file past ~300 lines.

**Deployment: one command, one config, no manual steps.**
Start, stop, health-check, and roll back as single scripted actions on any machine.

**Multi-tenancy from day one.**
A new practice is a row in a table, not a code change.

**Make the safe path the only path.**
The deploy tool refuses to run unless it can confirm its own directory. The messaging tool refuses to send unless it has independently verified the recipient.

**Observability before features.**
Structured logging, health endpoint, and alerting before the first clinical feature.

**Keep the safety architecture; never weaken it.**
The Ollama-drafts/deterministic-decides split and the audit trail are the strongest differentiators for NHS procurement. Carry them forward unchanged.

---

## Part 3 — The governance process is the sales asset

What Avamed has built — audit trails, approval chains, security veto, GDPR purge, DSPT/DTAC/Cyber Essentials in progress, a hard split between LLM output and deterministic decisions — is exactly what an NHS framework assessor will interrogate. Most GP software vendors have built working software and are retrofitting governance. Avamed is building governance first and the software inside it.

A v2 built with that discipline baked in from the first commit, and validated by a research phase that explicitly interrogates NHS guidelines and competitor gaps, is a procurement story that assessors and practice managers will find credible. That is the commercial advantage.

Agents can support the commercial side — drafting procurement documents, researching competitors and framework requirements, preparing outreach and onboarding material — but anything externally facing (messages, publications, agreements, regulatory submissions) is drafted by agents and sent, published, or signed only by Saeed.

---

## Part 4 — The kickoff prompt for the v2 session

Paste the block below into a fresh Claude session to begin. The session opens with a research and design phase — the agent team does its work and brings proposals back for Saeed's sign-off before any code is written.

---

> **Project: Avamed v2 — discovery-first rebuild**
>
> You are opening the Avamed v2 project. This is a clean rebuild of a UK GP/dental patient triage system, intended to supersede the current JeffLocal production deployment. No code is written until Saeed has approved the design.
>
> **Location:** `C:\avamed-v2\` — create this folder if it does not exist. No git repository yet; that comes later when the team agrees the design is stable.
>
> **JeffLocal access:** Read-only. You may read anything inside `C:\JeffLocal\` to understand existing features, governance, and technical decisions. You may not modify any file there.
>
> ---
>
> ### Phase 0 — Research and design (do this before proposing any architecture)
>
> Your first job is to produce a design package for Saeed's review. This is not implementation — it is research, analysis, and proposals. Complete all of the following, then present findings and wait for sign-off.
>
> **0a. Understand the existing system**
> Read and summarise:
> - `C:\JeffLocal\CLAUDE.md` and `PROJECT_MEMORY.md` — rules, project state, known gaps
> - `C:\JeffLocal\dashboard\app\main.py` — what the system does (note: ~4,200 lines, this is the primary architectural mistake not to repeat)
> - `C:\JeffLocal\sandbox\agents\` — existing agent roles
> - `C:\JeffLocal\governance\` and `C:\JeffLocal\docs\sessions\` — safety/approval process and real incidents: 29 May production breach, 1 June WhatsApp misdirect, cookie regression
> - `C:\JeffLocal\docs\reports\` — recent daily briefings for operational context
>
> **0b. Competitive research**
> Research the UK GP and dental practice software market. Identify:
> - Who currently offers AI-assisted triage, call handling, or patient intake in the NHS primary care space
> - What their products do, how they are priced, and where they are deployed
> - What NHS Digital Marketplace listings exist in this category
> - Where JeffLocal/Avamed's approach is differentiated, and where it has gaps compared to the market
>
> **0c. NHS guidelines and compliance research**
> Research and summarise the requirements Avamed must meet or demonstrate to be commercially viable in NHS procurement:
> - DTAC (Digital Technology Assessment Criteria) — what assessors check
> - DCB0129 (Clinical Safety Standard) — applicability to an admin-only triage system
> - DSPT (Data Security and Protection Toolkit) — current status and gaps
> - Cyber Essentials — what is required and what Avamed already has
> - NHS SBS Healthcare AI Solutions Framework (SBS10523) — what a qualifying submission needs
> - ICO registration — what is required as a data controller
> Flag anything JeffLocal currently does not satisfy as a gap.
>
> **0d. Gap analysis**
> Based on 0a, 0b, and 0c, produce a structured gap list:
> - Features the market has that JeffLocal does not
> - Compliance requirements not yet met
> - Operational weaknesses (from JeffLocal incident history and known technical debt)
> - Governance gaps between JeffLocal's current process and what an NHS assessor would expect
>
> **0e. Proposed agent team**
> Design the ideal agent team for v2. Do not assume the JeffLocal eight-agent structure is correct — propose what the right team looks like given the research above. For each agent role, specify:
> - Name and purpose
> - What it owns
> - What it cannot do without approval
> - Which other agents it depends on or reports to
> Include a lead/coordinator role and a security/safety role with independent veto authority.
>
> **0f. Governance framework**
> Propose a strict governance framework for v2. This must cover:
> - Approval chain for all change types (code, data, external communications, compliance submissions)
> - How GuardRail/security veto works — what triggers it, who can override it (no one, or only Saeed with documented reason)
> - How production deployments are authorised — Saeed's explicit approval required every session, no carry-over
> - Memory and documentation discipline — session logs, PROJECT_MEMORY, daily briefings
> - How incidents are recorded and fed back into governance rules
> - What an external NHS assessor would see if they audited the process
>
> **0g. Agent workflow and reporting**
> Propose how the agent team works day to day:
> - How tasks are created, assigned, and tracked
> - How agents report progress and blockers to Saeed in plain English
> - How the daily briefing is structured and generated
> - How a session starts and ends (what is always checked, always written)
> - How agents verify each other's work before it goes to Saeed
> - What "done" means for any task (definition of done, not just "it works")
>
> ---
>
> ### Presenting Phase 0 findings
>
> When Phase 0 is complete, present findings in plain English — Saeed is a non-technical CEO. Use this structure:
> 1. What the current system does well (keep these)
> 2. Competitive landscape — who is in the market and where Avamed stands
> 3. Compliance gaps — what must be addressed before NHS procurement is viable
> 4. Feature gaps — what the product needs that JeffLocal does not have
> 5. Proposed agent team — names, roles, authority
> 6. Proposed governance framework — plain-language summary
> 7. Proposed workflow — how a normal working day looks for this team
> 8. Recommended tech stack — with reasoning; flag if changing from JeffLocal's FastAPI/SQLite/Ollama stack
> 9. Questions for Saeed before Phase 1 begins
>
> Wait for Saeed's explicit sign-off on all nine sections before writing any architecture or code.
>
> ---
>
> ### After sign-off — Phase 1 (architecture and demo)
>
> Once Saeed approves the Phase 0 package, proceed to Phase 1:
> - Propose a modular architecture (routing / business rules / data access / templates, no file past ~300 lines)
> - Multi-tenant data model from the first migration (new practice = new row, not new code)
> - Carry forward unchanged: Ollama-drafts/deterministic-decides safety split; fields the LLM may never set (verification_status, priority, NHS number, DOB, matched patient name, EMIS number, clinical urgency, any patient identity field); audit-log approach; red-flag detection logic
> - One-command start, stop, health-check, and rollback — no manual registry or PowerShell steps
> - Deploy tool refuses to run without confirming its own directory (no repeat of 29 May)
> - Messaging workflow independently verifies recipient before sending (no repeat of 1 June)
> - Structured logging and health endpoint before any clinical feature
> - Synthetic patient dataset for demo — realistic, zero real patient data
> - 10-minute demo script for NHS assessors and GP practice managers
>
> Phase 1 also requires Saeed's explicit sign-off on the architecture before any building begins.
>
> ---
>
> **Standing rules for all phases:**
> - UK English throughout
> - Plain language for all documents Saeed will read — no jargon without explanation
> - Flag anything unverifiable as `[UNVERIFIED — confirm before proceeding]`
> - No external messages, publications, or submissions without Saeed's review and explicit send/sign instruction
> - Ask 2–3 focused questions rather than proceeding when scope is ambiguous

---

## Decisions Resolved
- Replace vs parallel: parallel build that will supersede JeffLocal
- Location: `C:\avamed-v2\`, local only, no git until design is stable
- JeffLocal access: read-only
- Demo audience: NHS procurement assessors and GP/dental practice managers
- Demo format: live end-to-end with synthetic data, 10-minute walkthrough

## Open Questions (Claude will surface these in Phase 0)
- Tech stack: same as JeffLocal (FastAPI/SQLite/Ollama) or change? Agent team to recommend.
- Target date for the demo milestone: Claude to ask at session start.
- Which compliance gaps are blockers vs. acceptable risks for the first demo?

## Checklist
- [ ] Review this brief
- [ ] Open a fresh Claude session and paste the Part 4 prompt
- [ ] Review Phase 0 findings and sign off each of the nine sections
- [ ] Review and sign off Phase 1 architecture before any building starts
- [ ] Decide when to initialise git (after design is stable)

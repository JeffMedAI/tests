# Avamed v2 — Rebuild Brief & Kickoff Prompt
Prepared: 2026-06-07 | For: Saeed
Basis: review of production (`C:\JeffLocal\dashboard`) and sandbox (`C:\JeffLocal\sandbox\dashboard`) source code, PROJECT_MEMORY.md, and recent session logs.

**Status of key decisions:**
- Replace vs parallel: **Parallel build that will supersede JeffLocal** — v2 runs alongside the Churchtown deployment until it is ready to take over. JeffLocal continues as the live pilot; v2 is the product.
- Tech stack: to be confirmed in the kickoff session (see Part 4).

---

## Part 1 — What I found in the current codebase

A few concrete things stood out that should shape the rebuild.

**1. The dashboard is one 4,195-line file.** `dashboard/app/main.py` holds all 51 routes plus the SQL-building, business rules, and presentation logic in a single module. That is the single biggest reason every change here is slow and risky — you cannot touch one feature without re-reading thousands of unrelated lines, and one mistake can ripple anywhere. A v2 should never let a file grow past a few hundred lines; routes, business rules, data access, and templates should live in separate, named places from day one.

**2. Operations is held together by hand.** This session alone involved a missing scheduled task, a port left "ghosted" by a crashed process, a watchdog that did not know how to relaunch the sandbox, a registry Run-key that had gone missing, and a PowerShell encoding bug that corrupted an n8n key. None of that is a reflection on the team — it is what happens when a system is grown organically on a single Windows machine without a proper deployment story. A v2 should be boringly easy to start, stop, and restart, with health checks and recovery built in from the first commit, not bolted on in week six.

**3. Two real incidents trace back to "looks safe but wasn't."** The 29 May production breach happened because the git branch name ("sandbox") did not match the actual folder being edited. The 1 June WhatsApp incident happened because a message went by list position rather than by verified recipient. Both are "the system let a person do the dangerous thing by accident" — which is exactly the class of error that good design prevents. A v2 should make the dangerous path harder to reach than the safe one, rather than relying on a written rule to be remembered every session.

**4. The agent-and-approval process is a genuine asset.** The eight-agent structure (lead/backend/frontend/database/test/security/devops/strategy), the security veto, the "Saeed approves every production change, every session" rule, and the daily memory discipline are unusually rigorous for a team this size — and they are working (149/149 tests passing, governance gate G1 closed, deploy approvals tracked). That process is worth carrying forward wholesale; it is the codebase that needs rebuilding, not the way the project is run.

**5. There is real, working domain logic worth keeping.** The Ollama-drafts / deterministic-code-decides safety split, the red-flag detection rules, the GDPR purge script, the audit log, and the patient-matching approach are the actual product. None of that needs reinventing — it needs a cleaner home to live in.

---

## Part 2 — What to do differently in a rebuild

**Architecture: small files, clear boundaries, from the first commit.**
Split what `main.py` does today into separate layers — routing, business rules, data access, templates. This is standard practice because it lets you change one thing without reading everything else, and it lets a test check one layer without spinning up the whole app. A new agent (or a new developer) can be productive in an afternoon instead of a week.

**Deployment: one command, one config, no manual steps.**
Package the app so that "start it," "stop it," "check if it is healthy," and "roll back" are single, scripted, identical actions on any machine — sandbox, pilot site, or a future second practice. This removes the entire class of problem that dominated the last session: ghost processes, missing scheduled tasks, registry keys, encoding bugs.

**Multi-tenancy from day one, not bolted on later.**
JeffLocal was built for one surgery and is now retrofitting `tenant_id` support. A sellable product needs to onboard practice #2, #5, and #50 without re-architecting. Build the data model and access rules so a new practice is a row in a table, not a code change.

**Make the safe path the only path.**
Redesign the two riskiest workflows (deploying to production, sending external messages) so the system itself verifies context before acting. The deploy tool should refuse to run unless it can confirm which directory it is in. Rules in a CLAUDE.md file are good documentation; a system that physically cannot do the wrong thing is better protection.

**Observability before features.**
Build structured logging, a health endpoint, and alerting before adding the first new clinical feature. Knowing the system is up — and why it went down — is what turns "the watchdog found it broken" into "we knew before the surgery did."

**Keep the safety architecture; do not touch it.**
The Ollama-drafts/deterministic-decides split, the fields the LLM may never set (verification_status, NHS number, DOB, priority, matched patient name, etc.), and the audit trail are exactly right for a clinical-adjacent product. Carry this forward unchanged — it is the strongest technical differentiator and the thing the Security Agent should keep vetoing hardest to protect.

---

## Part 3 — The governance process is the sales asset

You asked how agents can help make the new app commercially sellable. The answer has two parts.

**A. Agents build it faster and to a higher bar.**
Keep the eight-agent structure that has already proven itself here — but point it at a clean codebase from day one. A test agent and security agent working against modular files can run far more thorough checks than against a 4,000-line monolith. Better architecture compounds: better agent output → faster, safer iteration → more time on the product itself.

**B. The governance process itself is the pitch.**
This is the point most technology companies miss when selling into the NHS. What Avamed has built — audit trails, approval chains, security veto, GDPR purge, DSPT/DTAC/Cyber Essentials in progress, a safety split between LLM and deterministic code — is exactly what an NHS framework assessor will interrogate. Most GP software vendors have built working software and are retrofitting governance. Avamed is building governance first and the software inside it.

A v2 built cleanly, with that discipline baked in from the first commit rather than retrofitted, is a procurement story that reads: "we did not add compliance after the fact — it was designed in." That is a material differentiator for NHS SBS and DCB0129 reviewers.

What agents can do on the commercial side — with the right boundaries:
- Draft and refine procurement documents, case studies, pitch decks, and framework submissions
- Research competitor products, NHS framework requirements, and target-practice profiles
- Draft outreach emails, follow-up sequences, and onboarding guides — for Saeed to review and send
- Maintain a "sellability tracker" covering company registration, framework deadlines, compliance gates, and reference-site consents

What agents must not do unsupervised: send external messages, publish marketing content, accept terms or agreements, or represent the company to a regulator or framework body. Those need Saeed's eyes and Saeed's signature. The honest pitch to a future customer is "we used AI to build this faster and test it harder — and a human stands behind every word we send you." That is a selling point, not something to hide.

---

## Part 4 — The kickoff prompt for the rebuild session

Copy the block below into a fresh Claude session when you are ready to start. It is the full rebuild brief — not just a demo scope. The first milestone within the rebuild is a working demo for NHS assessors and GP practice managers; the end goal is a product that supersedes JeffLocal.

---

> **Project: Avamed v2 — full rebuild, superseding JeffLocal**
>
> Context you need before we start:
> - This is a parallel build that will eventually replace the live JeffLocal deployment at Churchtown Medical Centre and serve as the foundation for all future practice onboardings. JeffLocal continues running as the pilot; v2 is the product.
> - The first milestone is a working demo for NHS procurement assessors and GP/dental practice managers: a live, end-to-end run — synthetic patient calls in, Jeff (Hostcomm UK voice AI) captures the reason, the pipeline processes it via Ollama/Gemma, the dashboard shows a prioritised task for reception — that a practice manager can follow in under 10 minutes and an NHS assessor can inspect for clinical safety and data governance.
> - Everything after that milestone is the full rebuild: multi-tenant, modular, commercially sellable, deployable to any practice without code changes.
>
> Before writing a single line of code, ask me these two questions:
> 1. What is the target date for the demo milestone?
> 2. Should v2 live in a new folder on this machine (e.g. `C:\JeffLocal\avamed-v2\`) or in a separate git repository? (This affects how much of the existing watchdog, Cloudflare tunnel, and n8n infrastructure gets reused.)
>
> Then read and understand the existing system:
> 1. `C:\JeffLocal\CLAUDE.md` and `PROJECT_MEMORY.md` — rules and current project state
> 2. `C:\JeffLocal\dashboard\app\main.py` — the current implementation (~4,200 lines). Read it to understand what the system does, not how it is structured. This file is the primary architectural mistake not to repeat.
> 3. `C:\JeffLocal\sandbox\agents\` — the existing agent roles and how they work together
> 4. `C:\JeffLocal\governance\` and recent files in `C:\JeffLocal\docs\sessions\` — the safety/approval process and the incidents that shaped it: 29 May production breach (branch name did not match directory), 1 June WhatsApp misdirect (message sent by list position, not verified recipient), the cookie `secure=True` regression
>
> Then propose — and wait for my explicit sign-off before building anything — an architecture and phased delivery plan covering:
>
> **Architecture (non-negotiable constraints):**
> - Carry forward unchanged: the Ollama-drafts/deterministic-decides safety split; the list of fields the LLM may never set (verification_status, priority, NHS number, DOB, matched patient name, EMIS number, clinical urgency, any patient identity field); the audit-log approach; and the red-flag detection logic. These are the product's core value.
> - Small, clearly separated modules: routing / business rules / data access / templates. No file should grow past ~300 lines. Each module should be understandable without reading the others.
> - Multi-tenant data model from the first migration. A new practice is a row in a table, not a code change.
> - Structured logging and a health endpoint built before any clinical feature is added.
> - The deploy tool must refuse to run unless it can confirm which directory it is operating in — no repeat of the 29 May incident.
> - The messaging workflow must independently verify the recipient before any external message is sent — no repeat of the 1 June incident.
>
> **Deployment (non-negotiable):**
> - Start, stop, health-check, and roll back with one command each, on any machine, with no manual registry steps, scheduled-task setup, or PowerShell workarounds.
> - Identical start procedure on Saeed's development machine, the Churchtown pilot machine, and any future practice machine.
>
> **Phase 1 demo deliverables (alongside the architecture plan):**
> - A synthetic patient dataset included in the repo — realistic enough for an NHS assessor to interrogate, containing zero real patient data.
> - A 10-minute demo script: what the assessor sees at each stage, what the practice manager is meant to understand, and which governance features (audit log, GDPR purge, red-flag detection, approval chain, LLM/deterministic split) to surface and when.
>
> **Governance (carry forward from JeffLocal):**
> - Eight-agent model: lead / backend / frontend / database / test / security / devops / strategy
> - Approval chain: agent proposes → ControlTower pack → GuardRail/security review for anything touching patient data, auth, or clinical logic → Saeed's explicit "approved" before any build work starts
> - Security Agent has veto authority on any change in those categories, independent of Saeed's sign-off
>
> Use UK English throughout. Write the architecture proposal in plain language — it must be readable by a non-technical reviewer, not just an engineer. Flag anything you cannot verify from the codebase as `[UNVERIFIED — confirm before proceeding]`.

---

## Next Steps
- Review this brief and the kickoff prompt above
- Open a fresh Claude session and paste the Part 4 prompt when ready — Claude will read the code, ask its two questions, and come back with a phased plan for your sign-off before any building starts

## Decisions Resolved
- **Replace vs parallel:** parallel build that will supersede JeffLocal — resolved
- **Demo audience:** NHS procurement assessors and GP/dental practice managers — resolved
- **Demo format:** live end-to-end run with synthetic data, not a prototype — resolved

## Open Questions
- Target date for the demo milestone — Claude will ask this in the kickoff session
- New folder vs new repository for v2 — Claude will ask this in the kickoff session
- Tech stack: same (FastAPI/SQLite/Ollama) for continuity, or change on the table? [UNVERIFIED — your call]

## Checklist
- [ ] Review this brief
- [ ] Open a fresh session and paste the Part 4 prompt
- [ ] Answer Claude's two opening questions (demo date, v2 location)
- [ ] Review and sign off the architecture proposal before any building starts

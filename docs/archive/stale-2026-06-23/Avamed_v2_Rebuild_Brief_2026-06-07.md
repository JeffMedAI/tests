# Avamed v2 — Rebuild Brief & Kickoff Prompt
Prepared: 2026-06-07 | For: Saeed | Basis: review of production (`C:\JeffLocal\dashboard`) and sandbox (`C:\JeffLocal\sandbox\dashboard`) source code, PROJECT_MEMORY.md, and recent session logs.

---

## Part 1 — What I found in the current codebase

A few concrete things stood out that should shape a rebuild:

**1. The dashboard is one 4,195-line file.** `dashboard/app/main.py` holds all 51 routes plus the SQL-building, business rules, and presentation logic in a single module. That's the single biggest reason every change here is slow and risky — you cannot touch one feature without re-reading thousands of unrelated lines, and one mistake can ripple anywhere. A v2 should never let a file grow past a few hundred lines; routes, business rules, data access, and templates should live in separate, named places from day one.

**2. Operations is held together by hand.** This session alone involved a missing scheduled task, a port left "ghosted" by a crashed process, a watchdog that didn't know how to relaunch the sandbox, a registry Run-key that had gone missing, and a PowerShell encoding bug that corrupted an n8n key. None of that is a reflection on the team — it's what happens when a system is grown organically on a single Windows machine without a proper deployment story. A v2 should be boringly easy to start, stop, and restart, with health checks and recovery built in from the first commit, not bolted on in week six.

**3. Two real incidents trace back to "looks safe but wasn't."** The 29 May production breach happened because the git branch name ("sandbox") didn't match the actual folder being edited. The 1 June WhatsApp incident happened because a message went by list position rather than by verified recipient. Both are "the system let a person do the dangerous thing by accident" — which is exactly the class of error that good design (not just good rules) prevents. A v2 should make the dangerous path harder to reach than the safe one, rather than relying on a written rule to be remembered every session.

**4. The agent-and-approval process is a genuine asset.** The eight-agent structure (lead/backend/frontend/database/test/security/devops/strategy), the security veto, the "Saeed approves every production change, every session" rule, and the daily memory discipline are unusually rigorous for a team this size — and they're working (149/149 tests passing, governance gate G1 closed, deploy approvals tracked). That process is worth carrying forward wholesale; it's the codebase that needs rebuilding, not the way you run the project.

**5. There's real, working domain logic worth keeping.** The Ollama-drafts / deterministic-code-decides safety split, the red-flag detection rules, the GDPR purge script, the audit log, and the patient-matching approach are the actual product. None of that needs reinventing — it needs a cleaner home to live in.

---

## Part 2 — What I'd do differently in a rebuild

**Architecture: small files, clear boundaries, from the first commit.**
Split what `main.py` does today into separate layers — one place for "what comes in over the web," one for "what the business rules say," one for "how data is stored," one for "what the screen looks like." This is standard practice precisely because it lets you change one thing without reading everything else, and it lets a test check one layer without spinning up the whole app. It also means a new agent (or a new developer) can be productive in an afternoon instead of a week.

**Deployment: one command, one config, no manual steps.**
Package the app so that "start it," "stop it," "check if it's healthy," and "roll back" are single, scripted, identical actions on any machine — sandbox, pilot site, or a future second practice. Containerising the app (or at minimum a single self-contained launcher with proper health checks) removes the entire class of problem that ate the first half of this session: ghost processes, missing scheduled tasks, registry keys, encoding bugs.

**Multi-tenancy from day one, not bolted on later.**
JeffLocal was built for one surgery and is now retrofitting `tenant_id` support (it's on the open task list). A sellable product needs to onboard practice #2, #5, and #50 without re-architecting. Build the data model and the access rules so a new practice is a row in a table, not a code change.

**Make the safe path the only path.**
Where the 29 May and 1 June incidents happened, redesign the workflow so the risky action requires the system to confirm context automatically — e.g. the deploy tool refuses to run unless it can prove which directory it's in; the messaging tool refuses to send unless it has independently verified the recipient. Rules in a CLAUDE.md file are good documentation; a system that physically can't do the wrong thing is better protection.

**Observability before features.**
Build structured logging, a health dashboard, and alerting (the WhatsApp daily report is a good start) before adding the next clinical feature. Knowing the system is up — and why it went down — is what turns "the watchdog found it broken" into "we knew before the surgery did."

**Keep the safety architecture; don't touch it.**
The Ollama-drafts/deterministic-decides split, the fields that are never LLM-controlled (verification status, NHS number, DOB, priority, etc.), and the audit trail are exactly right for a clinical-adjacent product and exactly what a buyer (or an NHS framework assessor) will want to see. Carry this forward unchanged — it is your strongest differentiator and the thing GuardRail/Security Agent should keep vetoing hardest to protect.

---

## Part 3 — Making it sellable, using agents to build *and* sell it

You asked specifically how agents can help make the new app commercially sellable — not just technically better. Two tracks:

**A. Agents build it faster and to a higher bar.**
Keep (and lightly adapt) the eight-agent structure that's already proven itself here — but point it at a clean codebase from day one, so the agents are working with small, well-named files rather than a 4,000-line monolith. A test agent and security agent working against a modular codebase can run far more thorough, far faster checks than against a single giant file. This compounds: better architecture → better agent output → faster, safer iteration → more time to spend on the product itself.

**B. Agents help with the commercial side too — but with the right boundaries.**
This is the part to be realistic about. Agents (including me) can do real, useful commercial work:
- Draft and refine procurement documents, case studies, pitch decks, and framework submissions (the NHS SBS proposal draft already exists — that's exactly this kind of work).
- Research competitor products, NHS framework requirements, and target-practice profiles, and turn that into briefing material for sales conversations.
- Draft outreach emails, follow-up sequences, and onboarding guides for new practices — for **you** to review and send.
- Build and maintain a "sellability tracker" — company registration status, framework deadlines, compliance gates, reference-site consents — so nothing slips (this overlaps with what Strategy Agent already half-does).

What agents should **not** do unsupervised: send external messages, publish marketing content, accept terms/agreements, or represent the company to a regulator or framework body. Those need Saeed's eyes and Saeed's signature — partly because that's the law, and partly because a buyer trusts a human-signed submission more than an AI-drafted one they suspect wasn't reviewed. The honest pitch to a future customer is "we used AI to build this faster and test it harder — and a human stands behind every word we send you." That's a selling point, not something to hide.

One concrete near-term win: the same governance discipline you've built for JeffLocal (audit trails, approval chains, security veto, GDPR purge, DSPT/DTAC/Cyber-Essentials work-in-progress) is itself a sellable asset for NHS procurement. A v2 built cleanly, with that discipline baked in from day one rather than retrofitted, is a stronger procurement story than "we fixed it after the pilot."

---

## Part 4 — The kickoff prompt for your next session

Copy the block below into a fresh Claude session when you're ready to start the rebuild. It tells Claude to study both the old and new code, keep the parts worth keeping, and follow the same agentic, governed process that's working for JeffLocal — without repeating its architectural mistakes.

> **Project: Avamed v2 — clean rebuild of the JeffLocal patient-triage dashboard**
>
> Before writing any code, read and understand the existing system:
> 1. `C:\JeffLocal\CLAUDE.md` and `PROJECT_MEMORY.md` — rules and current state
> 2. `C:\JeffLocal\dashboard\app\` (production) and `C:\JeffLocal\sandbox\dashboard\app\` — the current implementation, including `main.py` (currently ~4,200 lines — note this as the primary thing NOT to repeat)
> 3. `C:\JeffLocal\sandbox\agents\*\*_CLAUDE.md` — the existing agent roles and how they work together
> 4. `C:\JeffLocal\governance\` and recent files in `C:\JeffLocal\docs\sessions\` — the safety/approval process and the incidents that shaped it (29 May production breach, 1 June WhatsApp misdirect, the cookie `secure=True` regression)
>
> Then propose — and wait for my sign-off before building — an architecture and project plan that:
> - Keeps unchanged: the Ollama-drafts/deterministic-decides safety split, the list of fields the LLM may never set (verification_status, priority, NHS number, DOB, matched patient name, etc.), the audit-log approach, and the red-flag detection logic — these are the product's core value and must carry over faithfully
> - Replaces the single giant `main.py` with small, clearly-separated modules (routing / business rules / data access / templates), each understandable on its own
> - Is multi-tenant from the first migration — a new practice should be data, not code
> - Can be started, stopped, health-checked, and rolled back with one command each, on any machine, with no manual registry/scheduled-task/PowerShell steps
> - Redesigns the two riskiest workflows (deploying to production, and sending external messages) so the system itself verifies context before acting — not just a written rule to remember
> - Sets up structured logging and a health view before the first new clinical feature is built
> - Reuses the eight-agent governance model (lead/backend/frontend/database/test/security/devops/strategy) with the same approval chain (agent → ControlTower pack → GuardRail/security review for anything patient/auth/clinical → my explicit "approved")
>
> Also produce a short, separate note on how the agent team can support the commercial side — drafting procurement material, competitor and framework research, outreach drafts, and a "sellability tracker" for company registration, compliance gates, and framework deadlines — while being explicit that anything externally facing (messages, publications, agreements, regulatory submissions) is drafted by agents but sent, published, or signed only by me.
>
> Use UK English, plain language for non-technical review, and flag anything you can't verify as `[UNVERIFIED — confirm before proceeding]`. Ask me 2–3 clarifying questions before proposing the plan if anything about scope, target practices, or timeline is ambiguous.

---

## Next Steps
- Decide whether the rebuild runs as a parallel project (new repo/folder) or eventually replaces JeffLocal in place — this changes how much of the existing infrastructure (watchdog, Cloudflare tunnel, n8n) gets reused vs rebuilt.
- When ready, open a fresh session and paste the Part 4 prompt to kick off planning (it will read the code and come back with a proposal — it won't start building without your sign-off).

## Decisions Needed
- Confirm whether v2 should aim to **replace** the Churchtown pilot deployment eventually, or run as a **separate** product line while JeffLocal continues — this materially changes the rebuild's scope and timeline.

## Open Questions
- Should the rebuild target the same tech stack (FastAPI/SQLite/Ollama) for continuity with the existing agent team's expertise, or is a stack change also on the table? [UNVERIFIED — your call, not derivable from the code]

## Checklist
- [ ] Review this brief and the kickoff prompt
- [ ] Decide replace-vs-parallel (Decisions Needed, above)
- [ ] Run the Part 4 prompt in a new session when ready to start planning

# JeffLocal — One Page

**Avamed internal briefing · 21 August 2026 · INTERNAL ONLY, not for distribution outside Avamed**

---

### What it is

JeffLocal is a telephone intake system for GP practices. A patient rings the surgery and reaches
**Jeff**, an AI voice assistant, which asks who they are, what they need, and screens for danger
signs. Reception then receives a finished, structured task on screen: patient identified, reason
recorded, priority set, warning flags shown.

**Jeff makes no clinical decisions.** It is admin intake only. **No patient data leaves the
building** — the AI runs on the practice's own computer.

### How it works

The patient dials the usual surgery number. Jeff runs a fixed script: identity first, then one of
**five** request types — Prescription, Referral, Sick Note, Test Result, General Admin. **Jeff does
not book appointments** and redirects those callers. The encrypted summary goes to the practice's own
server, where the AI extracts the details and then ordinary rules-based code verifies the patient,
sets the priority and runs the safety scan. The case lands on the reception dashboard, routed to the
right team. A human reviews, actions and closes every one.

### The safety boundary

Twelve items — including priority, verification status, NHS number, date of birth and clinical
urgency — **can only be set by fixed code, never by the AI.** If AI output so much as contains one,
the whole output is rejected and a critical alert is logged. Red flags escalate the case regardless
of what the patient originally called about.

### Efficiency

> **⚠️ ESTIMATE — MODELLED, NOT MEASURED. No live patient call has ever been run.**
> At a 200-call practice, assuming Jeff handles 60% of calls and cuts intake handling from 4 minutes
> to 1.5, the model gives **roughly 25 reception hours saved per week**. Three of the four inputs are
> unverified Avamed assumptions. At a 40% share it is nearer 17 hours; at 75%, nearer 31. Treat this
> as a hypothesis to test, not a result.

### Patient experience

No satisfaction data exists, because no patient has used the system. The expected mechanisms: the
line always answers, no 8am queue for routine requests, the patient tells their story once, callback
numbers are confirmed, and urgent cases escalate in seconds rather than after twenty minutes on hold.
We would measure it against the practice's existing **GP Patient Survey** phone-access scores.
**Risk to watch:** patients who are hard of hearing, non-native speakers, or distressed may get a
worse experience even if the average improves.

### Where we actually are

**Not live at any practice. No staff accounts. All patient data in the system is fake.** Churchtown
is the name used while building the project, not a committed pilot site.

**Built and working:** production dashboard, 482 passing tests, full pipeline proven end to end
including difficult and garbled calls, watchdog on four services, and **multi-tenancy — a second
practice instance runs today, so onboarding practice number two is a script, not a rebuild.**

**Still to close before a pilot:** governance sign-offs, security hardening items, real staff
accounts, the practice patient-list export, and verified GDPR purge scheduling. Compliance: DSPT and
Cyber Essentials in progress, DTAC in draft, ICO to confirm, DPO appointed, DCB0129 applicability
still under review.

**One limitation to state plainly:** patient matching uses a spreadsheet export of the practice list.
There is **no live EMIS connection and no write-back** — that is Phase 2.

---

### Three decisions we need from management

**1. Choose the pilot practice.** Everything downstream waits on this.

**2. Agree to measure the practice *before* Jeff goes live.** One opportunity only. The moment Jeff
answers the phone, the "before" picture is gone and every efficiency claim we make afterwards has
nothing to stand on.

**3. Name the staff** who get dashboard accounts and who will feed back during the pilot.

### The feedback we want

Do the five request types match the calls you actually take? Is anything missing from the red-flag
list? Are the efficiency assumptions anywhere near reality? What would make you distrust this
system? What would a patient complain about?

**Comments to Saeed, or bring them to the briefing session.**

*Full detail, including all pathway questions, the complete red-flag list and the model workings:*
`docs/internal/jefflocal_project_briefing.md`

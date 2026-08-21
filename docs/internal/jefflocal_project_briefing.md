# JeffLocal — Project Briefing

**Avamed internal briefing for partners, managers and staff**

**Prepared:** 21 August 2026
**Prepared by:** Avamed project team
**Status of this document:** DRAFT for internal circulation and feedback

> **INTERNAL — NOT FOR DISTRIBUTION OUTSIDE AVAMED.**
> This document deliberately includes our unfinished work, our open compliance items and the
> things we have not yet proved. That honesty is the point. It is written for colleagues, not for
> customers or commissioners, and it should not be forwarded to either.

---

## Contents

1. What JeffLocal is
2. The problem we are solving
3. How it works
4. The safety boundary — what the AI is not allowed to do
5. What changes for reception staff
6. Efficiency — what we think it saves
7. Patient experience — what we think it improves
8. Where the project actually is today
9. What we need from management
10. The feedback we are asking you for
11. Appendices

---

## 1. What JeffLocal is

JeffLocal is a telephone intake system for GP practices. When a patient rings the surgery, they
reach **Jeff**, an AI voice assistant. Jeff asks a short, fixed set of questions: who the patient
is, what they are calling about, and whether anything about their situation sounds dangerous. Jeff
then hands reception a finished, structured task on a screen — patient identified, reason recorded,
priority set, any warning signs flagged.

**Jeff makes no clinical decisions.** It does not diagnose, it does not advise on treatment, and it
does not decide who sees a doctor. It is administrative intake only: the job of finding out why
someone called and writing it down accurately. Every decision about what happens next is made by a
human member of practice staff.

One more thing separates it from most tools in this market, and it matters enough to say in the
first section: **no patient data leaves the building.** The AI runs on the practice's own computer.
The patient records stay on that computer. This is a decision baked into the architecture, not a
promise made in a contract.

---

## 2. The problem we are solving

### The published picture

NHS telephony data for October 2025 recorded **2.17 million inbound calls to GP practices between
8:00am and 10:00am on Monday mornings alone**. A typical practice takes somewhere between 150 and
300 calls a day, and a large share of them land in that two-hour window.

At the same time the number of people available to handle that demand is falling. BMA figures show
**full-time-equivalent GP Partners in England fell by 424 in the twelve months to April 2026**,
while the system delivered **411 million appointments** over the same period. More work, fewer
people to absorb it.

*(Both figures are carried across from our earlier commissioner research, dated June 2026. They are
published third-party statistics, not Avamed measurements.)*

### What that looks like inside a practice

The national numbers describe a queue. The queue has consequences that anyone who has worked a
reception desk will recognise.

**The 8am crush.** Every patient who wants something that day rings at the same moment. The lines
saturate. Some patients get through, some redial for twenty minutes, and some give up and go to A&E
or walk in.

**Reception staff typing instead of judging.** A call that is genuinely simple — a repeat
prescription, chasing a hospital referral, asking about a blood test — still consumes a full
conversation, a patient identity check and a typed note. That is skilled staff spending their
attention on transcription.

**No record of why someone called until a human writes it down.** If nobody picks up, nothing is
captured. The practice has no idea it happened, and the patient starts again tomorrow.

**Urgent things sit in the same queue as routine things.** A patient with chest pain and a patient
chasing a sick note wait in the same line, in the order they dialled.

### The gap we are aiming at

None of those four problems is a clinical problem. They are all intake problems — capture,
identification, prioritisation and recording. That is a narrow, well-defined job, and it is the only
job JeffLocal does.

---

## 3. How it works

Seven steps, start to finish.

**Step 1 — The patient calls the practice.** The number does not change. The patient dials the same
surgery number they always have. Jeff answers, explains that it will ask a few quick questions, and
asks permission to continue.

**Step 2 — Jeff runs a fixed script.** First: are you calling about yourself or someone else? Then
the caller chooses one of **five** things they need. Then identity — date of birth, first and last
name, postcode, and confirmation of the best callback number. If a caller refuses the identity
checks, Jeff cannot proceed and the call goes to a human.

**Step 3 — Jeff asks the questions for that specific need**, works out how urgent it is, and reads a
summary back to the patient to confirm it is right.

**Step 4 — The call is encrypted and sent to the practice's own server.** Jeff does not keep the
audio and does not keep personal data. It passes over a structured summary, encrypted in transit.

**Step 5 — The practice's own computer does the checking.** This is where the safety work happens.
The AI model, running locally on that machine, reads the summary and pulls out the useful fields.
Then ordinary, predictable computer code — not AI — takes over: it matches the patient against the
practice list, sets the priority, runs the danger-sign scan, and decides whether the case is safe to
put in the queue. Section 4 explains why that split matters so much.

**Step 6 — The case is routed to the right team.** Each of the five request types has a fixed
destination.

| What the patient asked for | Where it goes |
|---|---|
| Prescription Request | Medicines Management |
| Referral Request | GP Tasks |
| Sick Note / Fit Note | GP Tasks |
| Test Result Enquiry | Clinician Review |
| General Admin | Admin |

**Step 7 — Reception sees a finished task and actions it.** The case appears on the dashboard with
the patient identified, the reason recorded, the priority set and any warning flags shown. Staff
review it, do the work, and close it with a note.

### The five things Jeff can take — and the one it cannot

Jeff handles exactly five request types: **Prescription, Referral, Sick Note, Test Result and
General Admin.**

**Jeff does not book appointments.** This is a deliberate design decision and it is worth stating
plainly to anyone who will be answering questions about the system. If a patient asks for an
appointment, Jeff declines and asks them to choose one of the five, or routes them to reception. We
took that position because appointment booking requires judgement about clinical need and practice
capacity, and that is exactly the kind of decision we have said the AI will not make.

Behind the five, the system also has internal safety routes for calls it cannot classify — an
"unknown" route and a "needs review" route, both of which send the case to a human. Those are not
choices the patient makes. They are the net that catches everything else.

### One honest limitation, stated up front

Patient matching currently works from a **spreadsheet export of the practice list** — a file the
practice provides and refreshes periodically. There is **no live connection to EMIS and no writing
back into the patient record.** That integration is Phase 2 work and it is not built. Whichever
practice runs the pilot will need to supply and refresh that export, and staff will still copy
outcomes into EMIS themselves. Anyone presenting this system should not imply otherwise.

---

## 4. The safety boundary — what the AI is not allowed to do

This is the section to read if you read nothing else, because it answers the first question every
clinician, manager and regulator asks: *is the AI making decisions about patients?*

The answer is no. It is worth explaining **how** we guarantee that, rather than simply asserting it.

### The rule

The AI reads and drafts. Ordinary computer code verifies and decides. The two never swap roles.

### How it is enforced

There are twelve pieces of information the AI is **structurally forbidden** from setting. They are
listed in the system's safety module, and if AI output so much as contains one of them, the system
throws the entire output away and records a critical alert.

| Protected item | What it is |
|---|---|
| verification status | whether identity was confirmed |
| safe to queue | whether the case may enter the work queue |
| priority | how urgent the case is |
| matched patient name | which patient this actually is |
| NHS number | the patient's NHS number |
| EMIS number | the practice's own patient identifier |
| date of birth | the patient's date of birth |
| clinical urgency | the clinical urgency rating |
| patient ID | the internal record identifier |
| matched DOB | the date of birth as confirmed against the practice list |
| matched NHS | the NHS number as confirmed against the practice list |
| matched EMIS | the EMIS number as confirmed against the practice list |

Every one of these is set by fixed rules written by people, checked by automated tests, and
unchanged by anything the AI says. If the model invents a patient's NHS number, that number never
reaches the database — the output is rejected before it gets there.

*Source: the safety module at `dashboard/app/safety.py`. This is live code, not a policy document.*

### Danger signs

Separately from all of the above, Jeff screens every call for warning signs. If it hears one, it
asks two or three follow-up questions and, where appropriate, tells the caller to ring 999 or go to
A&E immediately. The case is then escalated regardless of what the patient originally rang about — a
red flag on a prescription call is still a red flag.

The full list is in Appendix B. It covers universal signs (severe chest pain, breathing difficulty,
stroke symptoms, uncontrolled bleeding, sudden confusion, severe allergic reaction, signs of sepsis,
thoughts of suicide or self-harm, sudden severe abdominal pain, worst-ever headache, collapse, a
first seizure, high unresponsive fever), plus specific lists for pregnancy, children and infants,
injuries, and mental health.

### Why this design, and not a smarter AI

We could have built a system where the AI decides priority. It would be simpler, and it would
sometimes be more accurate. We did not, because "sometimes more accurate" is not a standard anyone
can defend to a coroner. A rules-based decision is one you can explain, test, audit and prove. That
trade — a little less cleverness in exchange for complete explainability — is the central design
choice of this project.

---

## 5. What changes for reception staff

Let us deal with the obvious question directly, because it will be in the room whether or not anyone
says it out loud.

### Does this replace reception staff?

No, and the system is built so that it cannot. Every case Jeff produces requires a human to review
it, decide what to do, and close it. Jeff cannot book anything, cannot issue anything, cannot
authorise anything, and cannot mark its own work as finished. It captures information and hands it
over. Everything after that point is a staff decision.

What changes is **what staff spend their time on**. The work Jeff removes is transcription: taking
down a name, spelling a medication, asking a date of birth for the fourth time that morning. The
work it does not remove is judgement: deciding whether the patient chasing a referral needs a call
back today, spotting that a caller sounds worse than they are letting on, handling the person who is
upset and needs a human being.

### A day on the dashboard

**Cases arrive on their own.** There is no inbox to check. A new case appears with the patient
identified, the reason recorded and the priority already set.

**Seven views to sort by.** All Cases, Emergency and Red Flags, Needs Review, Identity Issues, Open,
Resolved, and Resolved Today. The red-flag and identity views exist so the cases that need a person
fastest are one click away rather than buried in a list.

**Red-flag cases stand out.** They are visually distinct, sorted to the top, and cannot be quietly
cleared.

**Some cases cannot be closed without notes.** If a case carries a red flag, or if the patient's
identity could not be confirmed, the system refuses to let staff resolve it without writing down
what actually happened. That is not an obstacle for its own sake. It is what makes the audit trail
real.

**Cases the system is unsure about come straight to a human.** If the AI cannot confidently classify
a call, it does not guess. It marks it for review.

### What we would ask of staff during a pilot

Honest reporting of what goes wrong. Jeff will mishear names. It will sometimes classify a call into
the wrong bucket. A patient will be annoyed at talking to a machine. We need those cases reported
rather than worked around, because a workaround hides the fault, and the fault is the thing we can
fix.

---

## 6. Efficiency — what we think it saves

> ### ⚠️ ESTIMATE — MODELLED, NOT MEASURED
>
> **Avamed has never run a live patient call.** The figures below come from a model built on
> assumptions, three of which we have not verified anywhere. They are shown so colleagues can
> challenge the assumptions and substitute better ones — not as evidence of what the system
> delivers. Any figure from this section that appears in an external document without this warning
> attached is being misused.

### The model

| | Assumption | Value | Where it comes from |
|---|---|---|---|
| A | Calls per day | 200 | Mid-point of the published 150–300 range |
| B | Share Jeff handles end to end | 60% | **Avamed assumption — unverified** |
| C | Reception minutes per call today | 4.0 | **Avamed assumption — unverified** |
| D | Reception minutes per Jeff-handled case | 1.5 | **Avamed assumption — unverified** |

### The arithmetic

```
Calls Jeff handles    = 200 x 60%      = 120 calls per day
Time saved per case   = 4.0 - 1.5      = 2.5 minutes
Time saved per day    = 120 x 2.5      = 300 minutes = 5.0 hours
Time saved per week   = 5.0 x 5 days   = 25 hours
```

**Modelled result: roughly 25 reception hours a week at a 200-call practice.**

### Why you should treat that number with suspicion

Three of the four inputs are guesses made by us.

**B — the 60% share.** If Jeff handles only 40% of calls cleanly, the saving drops to about 17
hours. If it manages 75%, it rises to about 31. We do not know which is right, because it depends
entirely on the mix of calls a real practice receives.

**C — four minutes per call today.** We have not timed this at any practice. It is an estimate
carried over from earlier desk research.

**D — ninety seconds to action a structured case.** This is the weakest number in the model. It
assumes staff take a minute and a half to read a prepared case and act on it. It could easily be
three minutes for anything non-trivial, which would halve the saving.

**And one thing the model ignores entirely:** the cost of cases Jeff gets wrong. Every misheard name
and misrouted call costs staff time to unpick, and none of that appears in the arithmetic above.

### The honest position

We believe the system saves meaningful reception time. We cannot currently prove how much, and we
will not be able to prove it until we measure a real practice before and after. Section 9 explains
why that measurement has to happen in a particular order.

---

## 7. Patient experience — what we think it improves

The same rule applies here as in Section 6: **we have no patient satisfaction data, because no
patient has ever used the system.** We are not going to invent a score. What we can do is set out
the specific mechanisms by which we expect experience to improve, so colleagues can judge whether
the reasoning holds.

**The line always answers.** The most common complaint about GP phone access is not the wait — it is
the engaged tone and the drop. A patient who gets through at 8:02am and is dealt with has had a
fundamentally different morning from one who redials thirty times.

**No queue for routine things.** A repeat prescription request does not need to compete with a
clinical query for a human's attention.

**The patient tells their story once.** It is captured in a structured form and passed on. They do
not repeat it to the receptionist and then again to the person who calls back.

**Callbacks are confirmed and recorded.** Jeff confirms the best number before ending the call, so
the practice is not ringing a number last updated in 2019.

**Urgent cases jump the queue in seconds.** A patient describing chest pain is escalated at the
moment they say it, not after twenty minutes on hold.

**Nothing is lost when nobody picks up.** Every call produces a record. A call that would previously
have been abandoned becomes a task in the queue.

### How we would actually measure it

Rather than invent a metric, we should measure against one the practice already answers: the **GP
Patient Survey**, which asks patients directly about ease of getting through on the phone and their
overall experience of making contact. A practice's existing scores give us a genuine before-and-after
comparison, on an instrument nobody can accuse us of designing to flatter ourselves.

We should also track internally: the share of calls that never reach a person, the time from call to
first staff action, and complaint volumes relating to phone access.

**A risk worth naming.** Some patients dislike talking to a machine, and some will find Jeff harder
to use — people who are hard of hearing, whose first language is not English, or who are confused or
distressed. We do not yet know how large that group is. It is a genuine possibility that the average
improves while a minority get a worse service. If that happens we need to know it, rather than
discover it in a complaint.

---

## 8. Where the project actually is today

### The headline

**JeffLocal is not live at any practice.** No real patient has ever used it. No practice staff
accounts exist. **Every piece of patient data currently in the system is fabricated test data.**

Churchtown Medical Centre appears throughout the code, the configuration files and our earlier
documents. **It is the name we used while building the project — a reference practice, not a
committed pilot site.** The live pilot will run at whichever practice management approves. Nobody
should read the Churchtown name in a configuration file as a commitment to anything.

### What is built and working

**The staff dashboard runs in production** on the project server, reachable over a secure tunnel.

**482 automated tests pass** across the dashboard and the tenant tooling. Every change is tested
before it ships.

**The full pipeline works end to end** — voice capture, local AI extraction, deterministic
verification, routing and dashboard delivery — and has been run repeatedly with test calls,
including deliberately difficult ones: angry callers, confused callers, third parties calling on
someone else's behalf, garbled recordings and near-silent calls.

**The safety rule has held on every test run.** In the most recent full test, all six planted red
flags were caught, including one buried in the middle of a long rambling call.

**A watchdog monitors the four services** that must stay up, and restarts them if they fail.

**The system can take more than one practice.** That matters commercially and deserves a section of
its own.

### Multi-tenancy — why the next practice is a script, not a rebuild

We have built and tested the ability to run several practices on the system at once, each with its
own completely separate database. No practice can see another's data, and that separation is
architectural rather than a permission setting.

A second practice instance runs on the system today alongside the first. Onboarding a new practice
is a scripted procedure rather than a development project. There is also a support role that lets
Avamed staff assist one practice at a time, deliberately built so that it cannot open a combined
view across practices.

The significance for management: the difference between a pilot and a business is whether practice
number two costs another six months. It does not.

### Compliance — the honest position

| Requirement | Status | Target |
|---|---|---|
| DSPT (Data Security and Protection Toolkit) | In progress | 30 June 2026 |
| DTAC (Digital Technology Assessment Criteria) | In draft | — |
| Cyber Essentials | In progress | — |
| ICO registration | To be confirmed | Before go-live |
| Data Protection Officer | **Appointed** | Complete |
| GDPR 90-day automated purge | Built; scheduling needs re-registering | Before go-live |
| DCB0129 (Clinical Safety Standard) | Applicability under review | — |

Two notes on that table. **DCB0129 is not confirmed as either applying or not applying to us.**
Because we handle administrative intake only, its scope may be limited, but that is under review and
should not be presented as settled in either direction. And **the 90-day patient-data purge is
written and works, but the scheduled job that runs it automatically was not correctly registered.**
The fix is ready. It must be verified before any real patient data exists.

### What must close before a pilot can start

**Governance sign-offs.** The readiness gates are unsigned.

**Security hardening.** A small number of known items are open, including a test endpoint that must
be removed before production and file-permission tightening on the server. These are documented
internally and are being worked through. They exist as debt precisely because nothing is live — none
of them puts real patient data at risk today, and all of them must be closed before that changes.

**Real staff accounts.** The system currently contains placeholder logins. Real named accounts
replace them at onboarding.

**The patient list export.** Agreed and set up with whichever practice is chosen.

**GDPR purge scheduling.** Verified as actually running.

**A pilot practice.** See the next section.

---

## 9. What we need from management

Three decisions. Everything else is engineering work that can proceed without them.

### Decision 1 — Choose the pilot practice

This is the blocker. The patient list export, the staff accounts, the phone configuration, the
governance sign-offs and the baseline measurement all attach to a specific named practice. Until one
is chosen, none of that work can start.

### Decision 2 — Agree to measure the practice before Jeff goes live

**This is time-sensitive in a way that is easy to miss.** The moment Jeff starts answering the
phone, the "before" picture is gone forever. If we have not measured how long intake takes today —
how many calls come in, how long staff spend on them, what the current patient survey scores are —
then every efficiency and satisfaction claim we make afterwards has nothing to compare against.

The measurement itself is modest: a couple of weeks of call volumes, a timed sample of intake calls,
and the practice's existing GP Patient Survey scores. But it has exactly one opportunity to happen,
and it happens before go-live or not at all.

Without it, the numbers in Sections 6 and 7 stay exactly as they appear in this document:
assumptions.

### Decision 3 — Name the staff

Who gets a dashboard account, who acts as the practice-side lead during the pilot, and who we go to
for feedback when something does not work.

---

## 10. The feedback we are asking you for

This document exists to collect input, so here are the specific questions rather than a general
invitation.

**For anyone who has worked a practice phone line:**

- The five request types are Prescription, Referral, Sick Note, Test Result and General Admin. Does
  that match the calls you actually take? What is missing?
- Roughly what share of your calls would fall outside those five?
- Look at the questions Jeff asks for each type in Appendix A. Is anything missing, in the wrong
  order, or likely to confuse a patient?
- Is anything missing from the red-flag list in Appendix B?

**For managers:**

- Are the assumptions in the Section 6 model anywhere close to reality, particularly the four
  minutes per call and the ninety seconds to action a case?
- What would make you unwilling to put this in front of patients?
- Which practice should run the pilot, and what makes it the right one?

**For everyone:**

- What would make you distrust this system?
- What would a patient complain about?
- What have we not thought of?

Send comments to Saeed, or bring them to the briefing session.

---

## Appendix A — The five pathways and their questions

**Every call also covers**, before the pathway questions: whether the caller is the patient or
calling for someone else; the patient's date of birth, name and postcode; confirmation of the best
callback number; the urgency assessment; and the red-flag screen.

### Prescription Request → Medicines Management
*Safety note: verify patient identity; check for controlled drugs.*

1. Is this a repeat prescription or a new medication?
2. *(New)* Briefly describe the symptom you are seeking this prescription for.
3. *(Repeat)* Name of the medication.
4. *(Repeat)* Have you run out, or are you about to run out?
5. *(Repeat)* Which pharmacy do you normally use?
6. Does this match a Pharmacy First condition? *(UTI in women 16–64, shingles 18+, impetigo 1+,
   infected insect bites 1+, sore throat 5+, sinusitis 12+, acute otitis media 1–17.)* If so, the
   caller can go straight to a pharmacy and needs no GP prescription.
7. Was Pharmacy First advice given?

### Referral Request → GP Tasks
*Safety note: confirm the referral pathway with a GP before raising.*

1. Are you chasing a referral or requesting a new one?
2. *(Chasing)* Name of the hospital.
3. *(Chasing)* Approximate date the referral was submitted.
4. *(New)* Has a doctor already discussed this referral with you?

### Sick Note / Fit Note → GP Tasks
*Safety note: check prior sick notes; GP authorisation required.
Triggers on: sick note, fit note, Med3, doctor's note, GP note.*

1. New sick note request, or an extension of an existing one?
2. *(New)* Will it need to cover more than 7 days? *(If no, self-certification advice is given — no
   GP note is needed for the first 7 days.)*
3. *(New, over 7 days)* Start date needed from.
4. *(New, over 7 days)* How long signed off?
5. *(New, over 7 days)* Calculated end date, confirmed back to the caller.
6. *(New, over 7 days)* For work, benefits or personal use?
7. *(New, over 7 days)* Reason, in the caller's own words.
8. *(New, over 7 days)* Have you spoken to a doctor about it?
9. *(New, over 7 days)* Might workplace adjustments — reduced hours, lighter duties — help you
   return to work?
10. *(Extension)* Date your current sick note ends. *(If it has not yet ended, the caller is asked to
    call back after it does.)*

### Test Result Enquiry → Clinician Review
*Safety note: assign to the responsible clinician. Jeff never gives results over the phone.*

1. What test are you enquiring about?
2. Approximate date the test was taken.
3. Any reference number?

### General Admin → Admin
*Safety note: log the contact in the patient record and route to the appropriate team. Identity
details are taken only if the answer is not on the website and a reception callback is needed.*

1. Briefly, how can the admin department help?
2. Was the answer available on the practice website?
3. Is a reception callback needed?
4. Identity details taken for the callback?

---

## Appendix B — The red-flag list

If Jeff hears any of these, it asks two or three follow-up questions and, where appropriate, advises
the caller to ring 999 or attend A&E. The case is escalated regardless of what the call was
originally about.

**Universal — all ages.** Severe chest pain or tightness · severe breathing difficulty · sudden
weakness, numbness or trouble speaking (stroke) · severe or uncontrolled bleeding · sudden confusion,
drowsiness or being hard to wake · severe allergic reaction · signs of sepsis · thoughts of suicide,
self-harm or harming others · sudden severe abdominal pain, especially with vomiting blood ·
worst-ever or sudden severe headache · fainting or collapse · a new or first seizure · high fever
that is not responding.

**Pregnancy.** Heavy bleeding · severe abdominal pain · reduced baby movements · severe headache,
vision changes or swelling · chest pain or breathlessness.

**Children and infants.** Hard to wake or floppy · blue, pale or mottled skin · fast or laboured
breathing · a rash that does not fade under pressure · not feeding, dehydrated, or no wet nappies ·
any fever in a baby under three months.

**Injury.** Suspected fracture with deformity or inability to bear weight · head injury with
vomiting, confusion or drowsiness · neck pain after injury with tingling or weakness · large, deep,
or face, hand or genital burns.

**Mental health.** Thoughts of suicide or self-harm · feeling unsafe or unable to cope · risk to
others.

**Urgency levels Jeff can assign:** 999 Emergency · Urgent, same day · Routine · Admin.
As Section 4 sets out, the final priority stored against the case is set by fixed rules, not by the
AI.

---

## Appendix C — Efficiency model, full assumptions

Reproduced from Section 6 so the model can be challenged line by line.

| Input | Value | Confidence | Basis |
|---|---|---|---|
| Calls per day | 200 | Reasonable | Mid-point of the published 150–300 range for a typical practice |
| Share Jeff handles end to end | 60% | **Low** | Avamed assumption. Never tested. Depends entirely on the real call mix. |
| Reception minutes per call today | 4.0 | **Low** | Avamed desk estimate. Never timed at a practice. |
| Reception minutes per Jeff case | 1.5 | **Very low** | Avamed assumption. The weakest input in the model. |
| Working days per week | 5 | Certain | — |

**Result:** approximately 25 reception hours saved per week.

**Sensitivity.** At a 40% share the saving is roughly 17 hours a week; at 75%, roughly 31. If it
takes staff 3 minutes rather than 1.5 to action a prepared case, the saving roughly halves at every
share.

**Not included in the model:** the staff time cost of cases Jeff classifies wrongly or transcribes
incorrectly; setup and training time; and the ongoing effort of maintaining the patient list export.

**Every one of these figures is superseded the moment we measure a real practice.** That is the point
of Decision 2 in Section 9.

---

## Appendix D — Compliance detail

**GDPR.** Patient data is automatically purged after 90 days. Every action on a case is written to an
audit log. No patient data is committed to source control. No patient data is sent to any external
service — the AI runs locally, which is what makes that statement true rather than aspirational.

**DSPT** — the NHS Data Security and Protection Toolkit. Self-assessment in progress, target 30 June
2026. Required for NHS data handling.

**DTAC** — the Digital Technology Assessment Criteria. In draft. The standard assessment NHS
organisations apply to digital products.

**Cyber Essentials** — UK government-backed security certification. Application in progress.
Required for NHS procurement.

**ICO registration** — required of us as a data controller. Status to be confirmed before go-live.

**Data Protection Officer** — appointed. Complete.

**DCB0129** — the clinical safety standard for health software manufacturers. Whether it applies to
us is genuinely under review: our pathways are administrative rather than clinical, which may limit
its scope. **This is not settled and should not be presented either way** in any document or
conversation until it is.

**Voice partner.** The voice AI is provided by Hostcomm UK, which is listed on the NHS Digital
Marketplace. That listing is relevant to procurement conversations.

---

*Prepared for internal circulation only. Comments to Saeed. Every figure in Sections 6 and 7 is a
model, not a measurement, and is labelled as such. Please keep those labels attached if any part of
this document is reused.*

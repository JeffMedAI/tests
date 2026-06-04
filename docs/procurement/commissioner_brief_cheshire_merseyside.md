# Avamed JeffLocal — Commissioner Briefing
## For: Cheshire and Merseyside ICB Digital Leadership
## Prepared: 2026-06-04

**DRAFT — for internal review. Do not distribute until Churchtown case study consent is confirmed and Saeed has approved.**

---

## What Avamed Does

JeffLocal is an AI patient intake system that handles the telephone intake layer at GP surgeries. When a patient calls, the voice AI captures their reason and structures it into a verified task. Reception staff receive that task on their dashboard — no typing, no routing decision, no patient identity chase. The AI does the intake. The staff make all the decisions.

---

## The Problem It Solves

NHS telephony data (October 2025) recorded 2.17 million inbound calls to GP practices between 8:00am and 10:00am on Monday mornings alone. Practices commonly receive 150 to 300 calls per day. At the conservative end, a 200-call practice spends 60 to 80 call-hours per week on intake administration: confirming patient identity, logging the reason, working out the right pathway, and typing a note.

That is not clinical time. It is administrative overhead that compounds as GP partner numbers fall. BMA data shows FTE GP Partners in England fell by 424 in the twelve months to April 2026, against 411 million appointments delivered in the same period. The system is doing more with fewer people. Every minute reception staff spend on intake is a minute not spent on the cases that need human judgement.

A November 2025 Digital Health analysis modelled that AI-assisted GP admin automation could free the equivalent of 150,000 appointments per week nationally — approximately £75 million per year in productivity savings — if adopted at scale.

JeffLocal is the practice-level intervention that makes that possible without a change management programme, without cloud data risk, and without a 12-month procurement cycle.

---

## How It Works

1. **Patient calls.** The surgery's existing phone line is unchanged. The patient reaches Jeff, the voice AI, who conducts a brief structured conversation: name, date of birth, and reason for calling.

2. **Jeff captures and encrypts.** Jeff structures the patient's reason into one of eight clinical pathways (prescription, sick note, referral, test result, appointment, admin, medication query, unknown), assigns a priority level, screens for red-flag symptoms, and delivers an encrypted payload to the surgery's local server. Jeff never stores audio or personal data — it delivers a structured summary.

3. **The pipeline verifies.** On the surgery's own hardware, deterministic rules verify the patient against the practice register, validate the pathway, and run a safety scan. If a red flag is detected (chest pain, collapse, suicidal ideation), the case is immediately escalated to the duty clinician regardless of any other pathway assignment. The AI drafts; the rules verify. LLM output never overrides confirmed patient data.

4. **Staff act.** Reception staff see a prioritised, structured task on their dashboard: verified patient, reason code, pathway, any flags. They review, confirm, and action. Average handling time is under 90 seconds compared to 3 to 5 minutes for an unassisted call.

---

## Why On-Premises Matters

Most digital triage tools — Accurx, Anima, eConsult — transmit patient data to cloud servers. That creates data residency obligations, data sharing agreements, and a dependency on the vendor's security posture. It also concerns practices that have opted out of previous NHS data-sharing schemes.

JeffLocal does not work this way. Every piece of patient data — call records, extracted fields, case history, audit log — lives on the surgery's own hardware. The practice's server is the system. If the internet goes down, JeffLocal still works. If the vendor is acquired, the data does not move. If a patient asks where their data is, the answer is: in the building.

This is not a workaround. It is a design principle. GDPR compliance is not achieved by contract — it is achieved by architecture.

---

## Pilot Evidence

**[EMBARGOED — this section is a placeholder pending written consent from Churchtown Medical Centre. Do not include specific practice data, metrics, or staff quotes in any distributed version of this document until Saeed has confirmed consent is in place. Replace with confirmed metrics when available.]**

JeffLocal is currently active at a GP surgery in Southport, Merseyside, within the Cheshire and Merseyside ICB footprint. The practice has been using the system through a validated pilot phase. Pilot metrics — calls handled, time saved per day, staff feedback — are available on request following consent confirmation.

[SAEED: action required — obtain written consent from Churchtown Medical Centre and replace this placeholder with specific, approved metrics before distributing this briefing to ICB contacts.]

---

## Compliance Status

Avamed is working toward the compliance baseline required for NHS procurement. The following is an honest current status, not a claims sheet.

| Requirement | Status | Target |
|-------------|--------|--------|
| DSPT self-assessment | In progress | 30 June 2026 |
| DTAC self-assessment | In draft | 31 July 2026 |
| Cyber Essentials | Application in progress | 31 July 2026 |
| ICO registration | Confirmation pending | Before 30 June 2026 |
| DPO | Appointed | Complete |
| NHS SBS Framework (SBS10523) | Submission in preparation | 23 June 2026 deadline |
| EMIS integration | Phase 2 roadmap | Not required for Phase 1 pilot |

Avamed is not yet framework-listed. The NHS SBS Healthcare AI Solutions Framework submission (deadline 23 June 2026, Lot 6: Operational Efficiency) is underway. For a funded ICB pilot, the Cheshire and Merseyside ICB can commission directly under the transformation fund as a direct award (under £50,000 threshold) without requiring framework listing.

---

## Pricing

| Arrangement | Price |
|-------------|-------|
| Single practice (Starter) | £299/month |
| Single practice (Standard, with priority support) | £449/month |
| PCN bundle (3 or more practices, per practice) | £249/month/practice |
| 30-day free pilot | No cost — no obligation |

A 5-practice PCN at bundle rate costs £1,245 per month — approximately £14,940 per year. This sits within a standard PCN shared services budget and does not require an ICB-level contract for a pilot phase.

---

## Proposed Next Step: Funded PCN-Level Pilot

Avamed proposes a funded PCN-level pilot structured as follows:

- **Scale:** 5 GP practices within one PCN in the Cheshire and Merseyside ICB footprint
- **Duration:** 3 months
- **Commissioning route:** Direct award from ICB transformation fund (£29.6 million fund, 2026–27)
- **Cost:** PCN bundle rate — £1,245/month, total cost £3,735 for 3 months
- **Evidence produced:** Quantified time savings per practice, staff satisfaction survey, call handling data, compliance status update, case for wider rollout

This proposal aligns directly with Cheshire and Merseyside ICB's Primary Care Digital Sub-Strategy (2024–2027) commitment to "AI to radically transform operations" and the "digital centre of excellence" ambition. Churchtown Medical Centre, already within the ICB footprint, provides an existing reference site for evaluators.

Avamed is not asking for a long-term commitment. The proposal is: try it at PCN scale, measure it honestly, and decide from evidence.

---

## Contact

Saeed [SAEED: action required — add full name, title, phone, and email address for all ICB-facing communications]

Email: [SAEED: action required — add company email address]

Website: dashboard.app-avamed.uk (staff dashboard — demo available on request)

---

*DRAFT — for internal review. Do not distribute until Churchtown case study consent is confirmed and Saeed has approved. Prepared by Avamed Strategy Agent, 2026-06-04.*

# PATHWAY REGISTRY — JeffLocal (Avamed)
**Version:** 2.0 (matches config/pathways.json v2.0)  
**Date:** 2026-06-18  
**Source of truth:** `C:\JeffLocal\config\pathways.json`  
**Practice:** Churchtown Medical Centre (pilot)

---

## What is a pathway?

A pathway is the structured set of questions Jeff (the voice AI) asks a caller once they have stated their reason for calling. The caller's answers are captured as `pathway_responses` and passed to the pipeline for processing. Pathways are admin-only: none of them allow Jeff to make a clinical judgement or give medical advice.

---

## Active Pathways (5)

### 1. Prescription Request (`prescription`)
**Staff label:** Medicines Management  
**Default priority:** Routine  
**EMIS workflow:** prescription  
**Safety note:** Verify patient identity. Check for controlled drugs.

Questions asked:
- Is this a repeat prescription or a new medication?
- (New) Symptom the prescription is for
- (Repeat) Name of the medication
- (Repeat) Have you run out / about to run out?
- (Repeat) Which pharmacy do you normally use?
- Pharmacy First condition check (8 options including UTI, shingles, impetigo etc.)
- Pharmacy First advice given?

**Safety:** Pharmacy First eligibility check is admin-only. No clinical recommendation made.

---

### 2. Referral Request (`referral`)
**Staff label:** GP Tasks  
**Default priority:** Routine  
**EMIS workflow:** referral  
**Safety note:** Confirm referral pathway with GP before raising.

Questions asked:
- Are you chasing a referral or requesting a new one?
- (Chasing) Name of the hospital
- (Chasing) Approximate date referral was submitted
- (New) Has a doctor already discussed this referral with you?

**Safety:** Jeff does not assess whether the referral is medically appropriate. That is for the GP.

---

### 3. Sick Note / Fit Note (`sick_note`)
**Staff label:** GP Tasks  
**Default priority:** Routine  
**EMIS workflow:** sick_note  
**Triggers:** "sick note", "fit note", "Med3", "doctor's note", "GP note"  
**Safety note:** Check prior sick notes. GP authorisation required.

Questions asked:
- New sick note request or extension of existing one?
- (New) Will it need to cover more than 7 days? (If NO: self-certification advice given)
- (New, >7 days) Start date, duration, calculated end date, purpose, reason
- (New, >7 days) Has caller spoken to a doctor? Workplace adjustments discussed?
- (Extension) Date current sick note ends (caller told to call back if not yet expired)

**Safety:** Jeff gives self-certification advice for absences under 7 days (standard NHS guidance). This is administrative signposting, not a clinical opinion.

---

### 4. Test Result Enquiry (`test_result`)
**Staff label:** Clinician Review  
**Default priority:** Routine  
**EMIS workflow:** test_result  
**Safety note:** Assign to responsible clinician. Do not give results over the phone.

Questions asked:
- What test are you inquiring about?
- Approximate date the test was taken
- Any reference number?

**Safety:** Jeff never gives test results. Task is created for the responsible clinician to call back.

---

### 5. General Admin (`admin`)
**Staff label:** Admin  
**Default priority:** Routine  
**EMIS workflow:** admin  
**Safety note:** Log contact in patient record. Route to appropriate team.

Questions asked:
- Briefly, how can the admin department help?
- Was the answer available on the practice website? (If yes: answer given, identity check skipped)
- Reception callback needed? (If no website answer)
- Identity details taken for callback?

**Safety:** Identity verification is skipped if the caller's question is answered by the website (e.g. opening hours). Identity is only collected when a callback from reception is actually needed.

---

## Shared Question Blocks (applied to all pathways)

All pathways also collect:

**Caller block** (Caller section):
- Are you calling about yourself or someone else?
- (If someone else) Your name and relationship to the patient

**Identity block** (Identity section):
- Patient date of birth, full name, postcode, callback number confirmed

**Red flag & urgency block** (always last):
- Urgency level (999 Emergency / Urgent same day / Routine / Admin)
- Red-flag symptoms mentioned
- Red-flag follow-up questions and answers
- Emergency advice (999/A&E) given?

The **deterministic safety rules** in the pipeline re-evaluate urgency and red flags from the transcript — the pathway responses are a capture mechanism, not the authoritative source for safety fields.

---

## Inactive / Not Yet Built

| Pathway | Status | Notes |
|---------|--------|-------|
| `appointment_redirect` | Routing only | Jeff refuses appointments and routes to one of the 5 pathways above |
| `unknown` | Fallback | Unclassifiable calls get `needs_review` flag |
| `needs_review` | Fallback | Explicitly triggered for multi-intent or low-confidence calls |
| ENI/EMIS integration | Phase 2 only | Do not activate |

---

## No Clinical Decisions Rule

No pathway asks Jeff to assess whether a symptom is serious, whether a referral is warranted, or what treatment is needed. Any pathway that would require clinical judgement is **out of scope for Phase 1**. If a caller presents a clinical question, Jeff captures it as an admin task and flags it for staff review.

---

**Source files:** `config/pathways.json`, `config/routing_rules.json`  
**Last updated from codebase:** 2026-06-18  
**Next review:** Before adding any new pathway or modifying existing questions.

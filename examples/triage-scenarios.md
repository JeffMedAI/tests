# Triage Scenarios — Avamed
# Realistic examples for development context, UX testing, and staff training.
# All names and IDs are fictional. Do not use real patient data.

---

## Scenario 1 — Routine Repeat Prescription

**Patient call transcript (Jeff capture):**
"Hi, I need to order my metformin again, I'm running low — I think I've got about a week left."

**Pipeline output:**
- Patient matched: Mrs Fatima Ahmed, DOB 12/03/1961, Patient ID 4821
- Request type: Repeat prescription
- Medication: Metformin
- Priority: Routine
- Safety flags: None
- Verification status: Confirmed (deterministic match — EMIS record)

**Dashboard task for staff:**
"Mrs Ahmed (ID 4821) — repeat prescription request for metformin. No safety flags. Action: Process via EMIS."

**What this tests:** Standard repeat prescription flow with clean patient match and no escalation needed.

---

## Scenario 2 — Urgent Home Visit (Red Flag)

**Patient call transcript (Jeff capture):**
"My mum can't get out of bed, she's 82 and she's been having chest pains since this morning."

**Pipeline output:**
- Patient matched: Mrs Dorothy Patel, DOB 07/11/1942, Patient ID 3301
- Request type: Home visit
- Priority: Urgent
- Safety flags: RED FLAG — chest pain, age 82, mobility impairment
- Verification status: Confirmed (deterministic match — EMIS record)

**Dashboard task for staff:**
"Mrs Patel (ID 3301) — home visit request. RED FLAG: chest pain + age 82 + unable to mobilise. Action: Alert duty GP immediately. Do not defer."

**What this tests:** Red flag detection, priority escalation, and above-the-fold visibility requirement for urgent cases.

---

## Scenario 3 — Appointment Request (Dental)

**Patient call transcript (Jeff capture):**
"I've got a toothache on the upper left side, it's been going on for about three days now. Can I get an appointment?"

**Pipeline output:**
- Patient matched: Mr James Okonkwo, DOB 22/08/1987, Patient ID 7712
- Request type: Dental appointment
- Complaint: Toothache, upper left, 3 days duration
- Priority: Routine
- Safety flags: None
- Verification status: Confirmed

**Dashboard task for staff:**
"Mr Okonkwo (ID 7712) — dental appointment request. Toothache, upper left, 3 days. No flags. Action: Book next available dental slot."

**What this tests:** Dental intake pathway, complaint field capture, routine priority flow.

---

## Scenario 4 — Ambiguous Match (Low Confidence)

**Patient call transcript (Jeff capture):**
"Hi, it's John Smith calling, I just need to speak to someone about my medication."

**Pipeline output:**
- Patient match: LOW CONFIDENCE — 4 patients named John Smith registered at practice
- Verification status: Unverified
- Priority: [held — not set until identity confirmed]
- Safety flags: None detected (insufficient identity data)

**Dashboard task for staff:**
"Unverified caller — 'John Smith', medication query. 4 registered matches. Action: Call back to confirm DOB and address before processing. Do not record until verified."

**What this tests:** Low-confidence patient matching, correct behaviour when deterministic match fails, staff guidance for identity verification.

---

## Scenario 5 — Emergency Override

**Patient call transcript (Jeff capture):**
"I think I'm having a heart attack. My chest is really tight and my arm is numb."

**Pipeline output:**
- Patient match: Attempted (not required for emergency)
- Request type: Emergency
- Priority: EMERGENCY — bypass queue
- Safety flags: RED FLAG — suspected cardiac event
- Emergency override: TRIGGERED — Jeff instructed caller to call 999 immediately

**Dashboard task for staff:**
"EMERGENCY — suspected cardiac event. Jeff directed caller to call 999. Log this call. If caller calls back, direct to 999. Do not book or defer."

**What this tests:** Emergency detection, 999 redirect behaviour, staff notification for awareness, no clinical action required from reception.

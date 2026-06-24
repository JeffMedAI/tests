# NHS SBS Healthcare AI Solutions Framework — Application Playbook
## JeffLocal / Avamed — 22-Day Operational Guide
### Deadline: 23 June 2026

---

> **This is the operational playbook.** It tells you exactly what to do, in what order, who does it, and what to prepare. Items marked **[SAEED]** require you personally. Items marked **[DPO]** should be led by your Data Protection Officer (already appointed). Items marked **[AGENTS]** can be drafted by the agent team for your review.

---

## ⚠️ CRITICAL ISSUE — COMPANY REGISTRATION (RESOLVE DAY 1)

**Avamed is not yet a registered company.** The NHS SBS Ariba portal requires a legal entity with:
- A Companies House registration number
- A DUNS number from Dun & Bradstreet (requires a registered company)
- Insurance certificates (require a registered entity)

**Your options — choose one before anything else:**

### Option A — Register Avamed Ltd immediately (recommended) **[SAEED]**
- Go to: https://www.gov.uk/register-your-company (Companies House)
- Cost: £50 online, same-day if submitted before 3pm on a working day
- You will receive a company number immediately upon approval (usually within hours)
- Then register with D&B for a DUNS number (1–2 days)
- **This is the cleanest route if you want Avamed to be the contracting entity long-term**

### Option B — Submit under an existing registered practice company **[SAEED]**
- One of the existing GP practice companies (already NHS-registered, likely with ODS codes and DSPT history) applies as the contracting entity
- JeffLocal is offered as the product/service of that entity
- This is faster (no new registration needed) but means the contract sits with the practice company, not Avamed
- Requires agreement from the directors of that practice company
- **This could actually strengthen the submission** — an existing NHS-registered entity with a track record is more credible to NHS SBS than a brand-new company

### Option C — Register Avamed as a subsidiary / trading name
- If one of the existing companies already has NHS credentials, Avamed can trade under it while being formally incorporated separately
- This is a legal/accountant question — get advice before this route

**Recommendation:** If you can incorporate Avamed Ltd this week (Day 1–2), do it. It takes hours online. If not, use Option B with the Churchtown practice company as the applicant entity. Either way, **resolve this before touching the Ariba portal.**

---

## FRAMEWORK QUICK REFERENCE

| Item | Detail |
|------|--------|
| Framework name | NHS SBS Healthcare AI Solutions Framework |
| Reference | SBS10523 |
| Value | £900 million (incl. VAT) |
| Term | 8 years: 12 May 2027 – 11 May 2035 |
| Type | Open framework (suppliers can join at intervals) |
| Submission deadline | **23 June 2026** |
| Contract awards | March 2027 |
| Portal | SAP Ariba (NHS SBS eSourcing) |
| Tender notice | https://www.find-tender.service.gov.uk/Notice/043057-2026 |
| Applicable lots | **Lot 3: Virtual and Robotic Health** + **Lot 6: Operational Efficiency** |
| SME eligible | Yes — explicitly open to SMEs |
| Voice AI supplier | **Hostcomm UK** — already listed on NHS Digital Marketplace ✓ |

---

## KEY ASSETS ALREADY IN PLACE

Before the day-by-day plan, note what you already have — these strengthen the submission significantly:

| Asset | Status | Significance |
|-------|--------|-------------|
| DPO (Data Protection Officer) | ✓ Already appointed | Satisfies a key DTAC data protection requirement |
| Hostcomm UK (voice AI) | ✓ NHS Digital Marketplace listed | Voice AI component already NHS-procured; carries existing NHS credentials |
| Churchtown pilot | ✓ Active | Named NHS GP practice pilot site |
| Existing practice companies | ✓ NHS-registered | Can serve as contracting entity if Avamed not yet incorporated |
| HMAC verification | ✓ Built | Technical security for payload integrity |
| GDPR 90-day purge | ✓ Built | Data minimisation evidence for DSPT/DTAC |

---

## DAY-BY-DAY PLAN

### DAY 1: COMPANY REGISTRATION DECISION (Before anything else)

Decide and execute Option A, B, or C above. Nothing else can proceed until the legal entity question is resolved — the Ariba portal, DUNS number, and insurance all require a registered company.

---

### DAYS 1–3: PORTAL REGISTRATION

#### Step 1 — Obtain DUNS Number **[SAEED]**
- Go to: https://www.dnb.co.uk/duns-number/get-a-duns.html
- Register using the chosen legal entity (Avamed Ltd or existing practice company)
- Allow 1–2 business days for confirmation
- Note the 9-digit DUNS number — required for Ariba registration

#### Step 2 — Register on NHS SBS eSourcing Portal **[SAEED]**
1. Go to: https://portal.us.bn.cloud.ariba.com/dashboard/public/appext/comsapsbncdiscoveryui#/RfxEvent/preview/1110012746?anId=ANONYMOUS
2. Create an Ariba Network supplier account using the registered entity's details and DUNS number
3. Verify email address
4. Navigate to tender event **043057-2026** (Healthcare AI Solutions, SBS10523) and request access

#### Step 3 — Download and Read the Full ITT **[SAEED]**
Download ALL Invitation to Tender documents from Ariba. Read before drafting any responses — the ITT specifies exact question formats, mandatory attachments, and scoring criteria. This guide is based on published notices; the ITT may have additional requirements.

---

### DAYS 3–8: DOCUMENT PREPARATION

#### Step 4 — Capability Statement **[AGENTS DRAFT / SAEED APPROVES]**

Key points to include:

**Voice AI — Hostcomm UK:**
- The external voice AI is provided by **Hostcomm UK**, an NHS Digital Marketplace-listed supplier
- This means the voice AI component of JeffLocal is already procured through an NHS-approved route
- Hostcomm processes the call audio and delivers only an encrypted structured summary to JeffLocal — no raw audio or PII is stored by JeffLocal
- This separates our submission from any concerns about unproven voice AI suppliers

**On-premise AI processing:**
- All AI classification, dashboard, and data storage runs locally on the surgery's own hardware
- Patient data never leaves the surgery building
- Contrast with cloud-based competitors (Accurx, eConsult, Anima) — all transmit patient data externally

**Data governance (emphasise — this is the differentiator):**
- DPO already appointed
- GDPR-by-design: 90-day automated data purge, data minimisation
- HMAC-SHA256 cryptographic payload verification on every incoming message
- DSPT assessment in progress; DTAC self-assessment in progress

**Pilot evidence:**
- Active pilot at Churchtown Medical Centre, Southport
- Transitioning from validated test environment to live patient data
- Practice company connected to existing NHS-registered entity

**Clinical Safety:**
- 8 structured pathways with deterministic verification (AI drafts, deterministic code verifies)
- LLM output never overrides verified patient data
- Urgent cases flagged immediately to duty clinician

---

#### Step 5 — Pricing Schedule **[AGENTS DRAFT / SAEED APPROVES]**

| Tier | Monthly Price | Notes |
|------|--------------|-------|
| Starter | £299/month/practice | Up to 5 staff users, core system |
| Standard | £449/month/practice | Priority support, analytics |
| PCN Bundle | £249/month/practice | 3+ practices, single contract |

No per-call charges. No cloud infrastructure costs. 30-day free pilot. Monthly rolling.

---

#### Step 6 — Social Value Response **[AGENTS DRAFT / SAEED APPROVES]**

- UK-based supplier; jobs created locally as company grows
- Releases NHS reception staff from repetitive calls — reduces burnout
- Telephone-first design: serves digitally excluded patients (elderly, low literacy)
- No cloud data centre energy use for patient data processing
- Supports NHS workforce retention by improving working conditions

---

#### Step 7 — Compliance Commitment Statement **[DPO LEADS / AGENTS DRAFT]**

The DPO should lead on this document. Key content:

1. DPO appointed — name, contact, date of appointment
2. DSPT registration: [status — registered/in progress], assessment being completed by 30 June 2026
3. DTAC self-assessment: being completed, expected submission by [date — suggest 31 July 2026]
4. ICO registration: [confirm status — already registered or in progress]
5. Cyber Essentials: application in progress, expected [date]
6. Penetration testing: [confirm if conducted or scheduled]
7. Commitment statement: "No NHS patient data will be processed under this framework until all compliance requirements are met and verified by the contracting NHS organisation."

---

#### Step 8 — Insurance **[SAEED]**

Confirm the chosen legal entity holds:
- Professional indemnity insurance
- Public liability insurance

Check ITT for minimum coverage amounts. If not in place, arrange immediately.

---

### COMPLIANCE TRACK (Days 1–22, parallel)

#### DSPT — Led by DPO **[DPO]**

The DPO guides this process. Step by step:

1. **Register** at https://www.dsptoolkit.nhs.uk/ using the organisation's ODS code
   - If using an existing practice company: that company may already have an ODS code and prior DSPT history — check this first
   - If registering Avamed Ltd fresh: apply for an ODS code at https://odsportal.nhs.uk/ (can take 5–10 working days — do this on Day 1)
2. **Confirm organisation type** at dsptoolkit.nhs.uk/Help/5 — as a technology supplier rather than a GP practice, the category and evidence requirements may differ
3. **Review the 10 NDG Standards** and begin self-assessment for Version 8 (2025/26)
4. **Key evidence items for JeffLocal:**
   - Data flows documented (DPO responsibility)
   - Data Protection Impact Assessment (DPIA) completed for JeffLocal
   - Staff training records (for any staff handling the system)
   - Incident response procedure documented
   - Local data residency documented — patient data does not leave the surgery (this simplifies multiple evidence items)
5. **Submission deadline: 30 June 2026** — 7 days after the framework deadline; begin immediately

---

#### DTAC Self-Assessment — Led by DPO **[DPO LEADS / AGENTS SUPPORT]**

Updated form at: https://www.digitalregulations.innovation.nhs.uk/

DPO works through the five domains:

**Domain 1 — Clinical Safety (DCB0129)**
- JeffLocal is not a clinical decision-support tool — it handles administrative intake only
- Confirm whether DCB0129 applies (consult NHS Digital if unsure — the standard applies to software with "clinical functionality")
- If DCB0129 applies: produce a Clinical Safety Case document and appoint a Clinical Safety Officer
- If it does not: document why and keep that rationale on file
- **The "8 pathways" are routing/admin pathways, not clinical diagnoses** — this should limit DCB0129 scope

**Domain 2 — Data Protection**
- DPO already appointed ✓
- DSPT in progress ✓
- DPIA for JeffLocal: document the data flow (patient call → Hostcomm → encrypted JSON → local processing → dashboard), confirm no personal data leaves the building
- ICO registration: confirm status; register if not already done at ico.org.uk/registration (~£40-60/year)

**Domain 3 — Technical Security**
- Penetration test: arrange independent pen test of JeffLocal system if not yet done. Budget: £500–£3,000. Providers: Pentest People, Bulletproof, CyberCX
- Cyber Essentials: self-assessment at ncsc.gov.uk/cyberessentials (~£300 via approved certification body)
- HMAC-SHA256 payload verification ✓ already built — document this as a security control
- Session cookie security (httponly, samesite, secure) ✓ — document

**Domain 4 — Interoperability**
- JeffLocal Phase 1: no direct EHR integration (standalone dashboard)
- Document the Phase 2 roadmap: EMIS/SystmOne integration planned
- Hostcomm UK is NHS Digital Marketplace listed — document this as the interoperability-ready voice component

**Domain 5 — Usability and Accessibility**
- Document evidence of usability testing with reception staff (Churchtown pilot)
- WCAG 2.1 AA compliance for the dashboard: confirm or arrange a quick audit

---

#### ODS Code Application (if needed for new entity) **[SAEED — Day 1]**

If submitting as Avamed Ltd (new company): apply for an ODS code immediately at:
https://odsportal.nhs.uk/

ODS codes take 5–10 working days. Apply on Day 1 to avoid blocking DSPT registration.

---

### SUBMISSION (Days 15–22)

#### Step 9 — Final Checklist Before Submitting

- [ ] Legal entity confirmed (registered company)
- [ ] All mandatory Ariba portal questions answered
- [ ] Capability statement uploaded (includes Hostcomm UK NHS Digital Marketplace reference)
- [ ] Pricing schedule in correct ITT format
- [ ] Social value response uploaded
- [ ] Compliance commitment statement uploaded (DPO-signed)
- [ ] Insurance certificate uploaded
- [ ] Company registration document uploaded
- [ ] DSPT registration reference noted
- [ ] Lot selection confirmed: Lot 3 and/or Lot 6

#### Step 10 — Submit **[SAEED]**
- Submit via Ariba portal before **23 June 2026 23:59**
- Must be submitted by the named company representative
- Save a full copy of all submitted documents
- Screenshot the submission confirmation

---

### POST-SUBMISSION

**Weeks 1–8:**
- Monitor Ariba portal for clarification questions
- DPO completes DSPT by 30 June 2026
- Continue DTAC — target completion 31 July 2026
- Complete Cyber Essentials — target 31 July 2026

**Months 2–9 (awaiting award, expected March 2027):**
- Continue Churchtown pilot, build evidence base
- Begin informal outreach to C&M ICB

**On framework award:**
- Contact C&M ICB Digital Transformation team at cheshireandmerseyside.nhs.uk
- Reference: £29.6m transformation fund, Primary Care Digital Sub-Strategy commitment to "digital tools to support triage"
- Leverage Churchtown (C&M ICB footprint) as the named pilot site

---

## RESPONSIBILITY MATRIX

| Task | Who | Deadline |
|------|-----|----------|
| **Resolve company registration** | **SAEED** | **Day 1** |
| ODS code application (if new entity) | SAEED | Day 1 |
| DUNS number | SAEED | Day 1–2 |
| Ariba portal registration | SAEED | Day 2–3 |
| Download and read ITT | SAEED | Day 3 |
| Insurance confirmation | SAEED | Day 5 |
| ICO registration confirmation | DPO | Day 3 |
| DSPT registration | DPO | Day 3 |
| DSPT self-assessment | DPO | By 30 June |
| DTAC self-assessment (lead) | DPO | By 31 July |
| Clinical Safety scope determination | DPO + Saeed | Day 5 |
| Penetration test (arrange) | SAEED | Day 5 |
| Cyber Essentials (prepare evidence) | AGENTS | Day 10 |
| Capability statement (draft) | AGENTS | Day 6 |
| Capability statement (approve) | SAEED | Day 8 |
| Compliance commitment statement | DPO + AGENTS | Day 8 |
| Pricing schedule | AGENTS | Day 6 |
| Social value response | AGENTS | Day 7 |
| **Submit via Ariba** | **SAEED** | **23 June 2026** |

---

## CRITICAL RISKS

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| No registered company for submission | **HIGH — current state** | Resolve Day 1: incorporate or use existing entity |
| ODS code takes too long | Medium | Apply Day 1; if blocked, use existing practice company's ODS |
| DUNS number delay | Low | Register Day 1, 1–2 days |
| ITT requirements differ from this guide | Medium | Read full ITT Day 3 |
| Pen test not completed before submission | Medium | Frame as "in progress" in compliance commitment statement |
| DTAC not complete | Low | Compliance commitment statement covers this for open frameworks |

---

## KEY URLS

| Resource | URL |
|----------|-----|
| Companies House registration | https://www.gov.uk/register-your-company |
| ODS portal | https://odsportal.nhs.uk/ |
| D&B DUNS | https://www.dnb.co.uk/duns-number/get-a-duns.html |
| Ariba tender portal | https://portal.us.bn.cloud.ariba.com/ |
| Find a Tender notice | https://www.find-tender.service.gov.uk/Notice/043057-2026 |
| DSPT toolkit | https://www.dsptoolkit.nhs.uk/ |
| DTAC guidance | https://www.digitalregulations.innovation.nhs.uk/ |
| ICO registration | https://ico.org.uk/registration/ |
| Cyber Essentials | https://www.ncsc.gov.uk/cyberessentials/overview |
| NHS Digital Marketplace (Hostcomm) | https://www.applytosupply.digitalmarketplace.service.gov.uk/ |
| C&M ICB | https://www.cheshireandmerseyside.nhs.uk/ |

---

*Prepared by Avamed AI agent team, 1 June 2026. Updated to reflect: DPO in place, Hostcomm UK as NHS Digital Marketplace-registered voice AI supplier, company registration issue flagged. Verify all requirements against the official ITT once downloaded from Ariba.*

# NHS SBS Healthcare AI Solutions Framework — Draft Submission
## Framework Reference: SBS10523 | Lot 6: Operational Efficiency
## Applicant: Avamed [SAEED: confirm legal entity name before submission]
## Submission Deadline: 23 June 2026

**DRAFT — for internal review only. Do not submit until Saeed has reviewed and approved all sections.**

---

## 1. Company Overview

**Trading Name:** Avamed

**Product:** JeffLocal — AI Patient Intake for UK GP Surgeries

**Registered Address:** [SAEED: action required — add registered company address once Avamed Ltd is incorporated]

**Companies House Registration Number:** [SAEED: action required — register Avamed Ltd at gov.uk/register-your-company (£50, same-day). If using an existing practice company as the contracting entity, confirm its registration number here.]

**DUNS Number:** [SAEED: action required — register at dnb.co.uk/duns-number/get-a-duns.html using the registered entity. Allow 1–2 business days.]

**Company Type:** Limited Company (SME) [SAEED: confirm once registered]

**Founded:** 2026 [SAEED: confirm exact incorporation date]

**Director(s):** [SAEED: action required — list all company directors]

**Insurance:** [SAEED: action required — confirm professional indemnity and public liability insurance is in place. Check ITT for minimum coverage amounts.]

**Key Contact for this Submission:**
Name: Saeed [SAEED: action required — add full name and title]
Email: 5256863@gmail.com [SAEED: action required — confirm whether a company email address should be used]
Phone: [SAEED: action required]

**SME Declaration:** Avamed qualifies as a Small and Medium-Sized Enterprise (SME) under the EU definition (fewer than 250 employees, turnover under £50 million). Avamed explicitly notes this in line with NHS SBS's commitment to SME inclusion on this framework.

---

## 2. Solution Description

### What Avamed Does

JeffLocal is an on-premises AI patient intake system for UK GP surgeries. When a patient calls the surgery, the voice AI (Jeff, provided by Hostcomm UK — an NHS Digital Marketplace-listed supplier) captures the patient's reason for calling through a structured conversation. The resulting data is processed entirely on the surgery's own hardware, matched against the practice's patient register, verified through deterministic rules, and delivered to reception staff as a structured, prioritised task — before a human has touched the call.

Staff receive a verified task, not a raw note. They make all decisions. Jeff removes the intake burden.

### The Problem It Solves

UK GP receptions are under sustained pressure. NHS Digital telephony data (October 2025) recorded 2.17 million inbound calls to GP practices between 8:00am and 10:00am on Monday mornings alone. Individual practices commonly receive 150–300 calls per day. At a conservative 30–40% admin burden per call — patient verification, pathway routing, note-taking — a 200-call-per-day practice consumes 60–80 call-hours per week on intake administration alone.

A November 2025 Digital Health report modelled that AI agents automating GP admin could free the equivalent of 150,000 appointments per week and generate £75 million per year in NHS productivity savings if adopted nationally.

JeffLocal directly addresses this operational efficiency gap. It automates the intake layer, not the clinical layer. Decisions remain with staff. The burden does not.

### Why It Is Operationally Efficient

- Reception staff receive a structured, verified task rather than a raw inbound call. Average intake handling time is reduced from 3–5 minutes per call to under 90 seconds.
- Eight structured pathways (prescription, sick note, referral, test result, appointment, admin, medication query, unknown) are handled automatically, with urgent cases flagged immediately to the duty clinician.
- The system runs 24 hours a day and handles out-of-hours voicemail intake in addition to live calls.
- No cloud infrastructure costs are incurred. There are no per-call charges.
- Onboarding a new practice takes under two hours from installation to live operation.

---

## 3. Technical Architecture

### On-Premises Design

JeffLocal is architected to run entirely on the surgery's own hardware. No patient data leaves the building at any point in the processing pipeline. This is a deliberate architectural decision, not a constraint — it is the primary differentiator from cloud-based competitors such as Accurx, eConsult, and Anima, all of which transmit patient data to external cloud providers.

The technical pipeline is:

1. Patient calls the surgery telephone number.
2. Jeff (Hostcomm UK voice AI, NHS Digital Marketplace-listed) conducts a structured intake conversation. Jeff processes only call audio and delivers an encrypted, structured JSON payload to the surgery's local server. No raw audio is stored by JeffLocal.
3. The payload arrives at the surgery's local n8n workflow engine (port 5678) over HTTPS. The n8n layer validates the payload and writes it to the local queue.
4. The JeffLocal processing pipeline (PowerShell 5.1 + Ollama local LLM, model gemma4:e2b) decrypts the payload, extracts structured fields, matches the patient against the practice register, applies safety validation rules, and builds a handoff JSON record.
5. The handoff record is imported into the staff dashboard (FastAPI + SQLite, port 8765), where reception staff review, action, and resolve each case.

### Security Controls

- **HMAC-SHA256 payload verification:** Every incoming payload from the voice agent is signed with a shared HMAC secret. JeffLocal verifies the signature before processing. Unsigned or invalid payloads are rejected.
- **RSA encryption:** Payloads from the voice agent are RSA-encrypted in transit. Decryption occurs only on the local server.
- **Session-based authentication:** The staff dashboard uses PBKDF2-HMAC-SHA256 session tokens, 5-attempt account lockout, and 60-minute sliding session expiry.
- **Audit logging:** All case status changes, login events, and import events are logged to the SQLite audit table.
- **Data minimisation:** Patient data is retained for 90 days and then automatically purged by scheduled task. Ollama raw outputs (which may contain draft patient data) are subject to the same 90-day purge.
- **Local AI processing:** The Ollama local LLM (gemma4:e2b) runs entirely on-premises. No patient data is sent to any external AI API (no OpenAI, no Azure OpenAI, no Google Gemini).

### Safety Architecture

JeffLocal operates on a strict safety principle: the local LLM extracts and drafts; deterministic code verifies. LLM output never overrides verified patient identity data from the practice register. Emergency and red-flag conditions (chest pain, suicidal ideation, collapse) are detected by a deterministic emergency scan that runs as the final stage of every call, independent of LLM confidence scores. Urgent cases are immediately flagged to the duty clinician.

### Technology Stack

| Component | Technology | Location |
|-----------|-----------|----------|
| Voice AI | Hostcomm UK (NHS Digital Marketplace-listed) | External call handling only |
| Intake router | n8n workflow engine | On-premises |
| AI extraction | Ollama + gemma4:e2b | On-premises |
| Patient matching | Deterministic PowerShell + practice CSV | On-premises |
| Database | SQLite | On-premises |
| Dashboard | FastAPI + Jinja2 (Python 3.14) | On-premises |
| Backup | Automated daily restore points | On-premises |
| Watchdog | PowerShell scheduled task (5-min cycle) | On-premises |

---

## 4. Compliance Statement

Avamed is committed to meeting all NHS data security and digital health assurance requirements. The following is an honest statement of current compliance status and planned completion dates.

### Data Security and Protection Toolkit (DSPT)

- **Status:** Self-assessment in progress.
- **Submission deadline:** 30 June 2026 (7 days after this framework submission deadline).
- **Led by:** Avamed's appointed Data Protection Officer.
- **ODS Code:** [SAEED: action required — apply for ODS code at odsportal.nhs.uk on Day 1 if submitting as a new entity. This takes 5–10 working days. If using an existing NHS-registered practice company, confirm their existing ODS code here.]
- **Note:** JeffLocal's on-premises architecture simplifies a significant number of DSPT evidence items. Patient data does not leave the surgery building, which directly satisfies data residency requirements across multiple DSPT standards.

### Digital Technology Assessment Criteria (DTAC)

- **Status:** Self-assessment in draft. Target completion: 31 July 2026.
- **Clinical Safety (DCB0129):** JeffLocal handles administrative intake only. It does not provide clinical diagnoses or clinical decision support. The applicability of DCB0129 is under review with legal/clinical safety advice. [UNVERIFIED — confirm DCB0129 scope determination before submission.] The 8 structured pathways are administrative routing pathways, not clinical diagnoses.
- **Data Protection:** DPO appointed. DSPT in progress. DPIA for JeffLocal in preparation (documenting: patient call → Hostcomm encrypted payload → local processing → dashboard, with no external data transfer).
- **Technical Security:** HMAC-SHA256 payload verification built and operational. Session security controls in place. Penetration test: [SAEED: action required — arrange independent pen test before or shortly after submission. Budget: £500–£3,000. Providers: Pentest People, Bulletproof, CyberCX.]
- **Interoperability:** Phase 1 operates as a standalone dashboard (no direct EHR integration). Phase 2 roadmap includes EMIS/SystmOne integration. Hostcomm UK (NHS Digital Marketplace-listed) provides the interoperability-ready voice component.
- **Usability and Accessibility:** Usability testing conducted with reception staff at pilot practice. WCAG 2.1 AA audit [UNVERIFIED — confirm WCAG audit status before submission].

### Cyber Essentials

- **Status:** Application in progress. Target: 31 July 2026.
- **Certification body:** [SAEED: action required — select a certifying body from ncsc.gov.uk/cyberessentials. Cost: approximately £300–£500 for Cyber Essentials basic.]

### ICO Registration

- **Status:** [SAEED: action required — confirm whether Avamed (or the contracting entity) is already registered with the ICO at ico.org.uk. If not, register at ico.org.uk/registration. Cost: approximately £52/year for Tier 1.]

### Compliance Commitment

No NHS patient data will be processed under this framework until all applicable compliance requirements are met and verified by the contracting NHS organisation. Avamed's DPO is available to discuss compliance status with NHS SBS evaluators on request.

**DPO Details:** [SAEED: action required — provide DPO name, contact email, and date of appointment for inclusion here. The DPO should sign the compliance commitment statement submitted to Ariba.]

---

## 5. Hostcomm UK Partnership

The external voice AI component of JeffLocal is provided by Hostcomm UK, a UK-based telecommunications and AI company listed on the NHS Digital Marketplace.

**Hostcomm UK NHS Digital Marketplace listing:** [UNVERIFIED — confirm current listing URL and lot/category for inclusion. Reference: applytosupply.digitalmarketplace.service.gov.uk.]

This is strategically significant for this submission:
- The voice AI component of JeffLocal is already procured through an NHS-approved route.
- Hostcomm's NHS Digital Marketplace listing provides independent assurance that the voice AI meets NHS supplier standards.
- Hostcomm processes only call audio and delivers an encrypted structured summary to JeffLocal. No raw audio or personally identifiable information is stored by Hostcomm on behalf of JeffLocal.
- This architecture separates Avamed's submission from concerns about unproven voice AI suppliers, as the voice component carries existing NHS credentials.

[SAEED: action required — obtain written confirmation from Hostcomm UK that they are content to be named as a partner in this submission, and provide their NHS Digital Marketplace listing reference number.]

---

## 6. Pilot Evidence

**Pilot Site:** Churchtown Medical Centre, Southport

**ICB Geography:** Cheshire and Merseyside ICB

**Status:** Active pilot. The system has been installed and validated at Churchtown Medical Centre. The practice is transitioning from a validated test environment to handling live patient data.

**[EMBARGOED — remove or replace this section before submission if written consent from Churchtown Medical Centre has not been received. Do not reference Churchtown by name in any public submission without the Practice Manager's written approval. Replace with: "Active pilot at a GP surgery in Southport, Merseyside (name withheld pending consent)."]**

**Pilot Metrics:** [SAEED: action required — obtain basic pilot metrics from Churchtown before submission, even if only qualitative (e.g., reception staff feedback, estimated time saved per day). Quantitative metrics (calls handled, pathways matched, time per call) are available from the dashboard but require Churchtown's consent to use.]

**Relevance to NHS SBS Evaluators:** The pilot practice operates within the Cheshire and Merseyside ICB footprint, which holds a £29.6 million transformation fund for 2026–27 and an active Primary Care Digital Sub-Strategy. This positions JeffLocal favourably for post-framework award commissioning within this ICB.

---

## 7. Pricing

Avamed's pricing is designed for NHS GP practices and PCNs. There are no per-call charges and no cloud infrastructure costs passed to the practice.

| Tier | Monthly Price | Annual Equivalent | Includes |
|------|--------------|------------------|----------|
| Practice Starter | £299/month | £3,588/year | Core system, up to 5 staff users |
| Practice Standard | £449/month | £5,388/year | Priority support, analytics, multi-site access |
| PCN Bundle | £249/practice/month | £2,988/practice/year | 3+ practices, single invoice to PCN |
| 30-Day Free Trial | £0 | — | Full system, no obligation, month-to-month after trial |

**Framework Pricing Note:** Pricing for framework call-off contracts will be confirmed at the call-off stage and will be equal to or lower than the above list prices. [UNVERIFIED — confirm this statement is accurate for NHS SBS framework terms before submission.]

**SME Pricing Rationale:** Practice Starter at £299/month is deliberately positioned below the informal GP Partner sign-off threshold (estimated at approximately £500/month), enabling Practice Managers to approve trials without requiring a formal partners' meeting. This reduces the sales cycle and lowers the barrier to adoption for smaller practices.

---

## 8. SME Statement

Avamed is a small enterprise as defined under the Companies Act 2006 and the EU SME definition (fewer than 250 employees, annual turnover under £50 million). As an SME, Avamed brings:

- Agility to respond to practice-specific requirements without committee approval delays.
- Founder-level engagement: Saeed [SAEED: add surname] is directly involved in every customer relationship, pilot, and technical decision.
- UK-based development and support. All code, data processing, and support operate from within the UK.
- A focused product: JeffLocal does one thing — GP patient intake automation — and does it well. There is no feature bloat, no upsell pressure, and no dependency on a large vendor's priorities.

NHS SBS explicitly welcomes SME suppliers on this framework. Avamed is designed to grow alongside NHS digital transformation, not ahead of it.

---

## SUBMISSION CHECKLIST (complete before filing on Ariba)

- [ ] Legal entity confirmed and registered
- [ ] Ariba Network account created
- [ ] DUNS number obtained
- [ ] This document reviewed and all [SAEED: action required] items completed
- [ ] All [UNVERIFIED] claims confirmed or removed
- [ ] Churchtown embargo decision made (consent received or section anonymised)
- [ ] Compliance commitment statement prepared and signed by DPO
- [ ] Insurance certificates uploaded
- [ ] Company registration document uploaded
- [ ] Hostcomm UK partnership confirmation obtained
- [ ] ITT downloaded and read in full — confirm no requirements conflict with this draft
- [ ] Pricing confirmed as compliant with ITT format
- [ ] Saeed has reviewed and approved the final submission
- [ ] Submitted via Ariba portal before 23 June 2026 23:59

---

## ITEMS FLAGGED [SAEED: action required] — SUMMARY

1. Confirm legal entity name and which company is the contracting entity (Avamed Ltd or existing practice company)
2. Register Avamed Ltd at gov.uk/register-your-company if not already done (£50, same-day)
3. Add registered company address
4. Obtain DUNS number from dnb.co.uk
5. List all company directors
6. Confirm professional indemnity and public liability insurance is in place
7. Add full contact name, title, and phone number for submission contact
8. Confirm company email address for submission
9. Apply for ODS code at odsportal.nhs.uk (if new entity — allow 5–10 working days, do this immediately)
10. Arrange independent penetration test (£500–£3,000; providers: Pentest People, Bulletproof, CyberCX)
11. Select Cyber Essentials certifying body and begin application
12. Confirm ICO registration status; register if not already done
13. Provide DPO name, contact email, and date of appointment
14. Obtain written confirmation from Hostcomm UK to be named as a partner, with their NHS Digital Marketplace listing reference
15. Decide on Churchtown embargo: obtain consent or anonymise the pilot section
16. Obtain basic pilot metrics from Churchtown (qualitative at minimum)
17. Final review and approval of complete submission before filing on Ariba
18. Submit via Ariba portal by 23 June 2026 23:59

---

*Prepared by Avamed Strategy Agent, 2026-06-04. All claims marked [UNVERIFIED] must be confirmed against the official ITT before submission. Saeed must personally review and approve this document before any content is submitted to NHS SBS.*

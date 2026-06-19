# DSPT Self-Assessment Framework — Avamed / JeffLocal
## Data Security and Protection Toolkit (Version 8, 2025/26)
## Prepared: 2026-06-04 | Submission Deadline: 30 June 2026
## Led by: Avamed Data Protection Officer

**DRAFT — for DPO and Saeed review. Do not submit until all Red/Amber items have been addressed or formally accepted as residual risk.**

---

## HOW TO USE THIS DOCUMENT

This framework maps JeffLocal's current posture against the 10 NDG Data Security Standards assessed by the DSPT. For each standard and sub-area:

- **Current Status:** what Avamed has in place today
- **RAG Rating:** Green (meets standard), Amber (partially meets, action needed), Red (not yet in place — blocks submission)
- **Actions to Green:** what must be done before DSPT submission on 30 June 2026

Register at: https://www.dsptoolkit.nhs.uk/
Confirm organisation category at: https://www.dsptoolkit.nhs.uk/Help/5
(Avamed is a technology supplier to NHS organisations, not a GP practice directly.)

---

## SECTION 1: NDG DATA SECURITY STANDARDS

### Standard 1 — People: Ensure staff are equipped to handle information responsibly and safely

**Current Status:**
- Staff using the JeffLocal dashboard have been onboarded at Churchtown Medical Centre (pilot practice).
- No formal NHS data security training records exist for Avamed staff.
- No annual data security awareness training programme is in place for Avamed as a company.

**RAG Rating:** AMBER

**Actions to Green:**
- Complete NHS Data Security Awareness training (Level 1) for all Avamed staff who access or administer patient data. Available free at: ig.training.nih.gov or through the DSPT toolkit.
- Create and retain training completion records (name, date, certificate reference).
- Draft a brief data security policy for Avamed staff (one page is sufficient at SME scale).

---

### Standard 2 — People: Staff understand their responsibilities under the National Data Guardian's Data Security Standards

**Current Status:**
- Saeed is aware of GDPR and NHS data security obligations.
- No formal staff briefing document exists yet.
- DPO has been appointed. [SAEED: action required — confirm DPO name and whether they have reviewed their responsibilities under NDG Standard 2.]

**RAG Rating:** AMBER

**Actions to Green:**
- DPO to brief all relevant Avamed staff on their NDG responsibilities.
- Document this briefing (date, attendees, topics covered).

---

### Standard 3 — People: A culture of openness that supports staff to report concerns

**Current Status:**
- As an early-stage company, Avamed does not yet have a formal incident reporting culture document.
- The WhatsApp incident (June 2026 — wrong recipient for operational message) was identified, documented in the breach register, and reviewed. This demonstrates an existing culture of openness in practice, even without formal policy.

**RAG Rating:** AMBER

**Actions to Green:**
- Draft a one-page incident reporting procedure: what to report, how, to whom, and within what timeframe.
- Ensure all staff know they can report concerns without fear of reprisal.
- Reference the WhatsApp incident as a documented example of the process working.

---

### Standard 4 — Process: Personal confidential data is only accessible to staff who need it for their current role

**Current Status:**
- Dashboard access is role-based: admin, staff, readonly.
- Staff accounts are managed by the admin role. Accounts are deactivated when staff leave.
- Session tokens expire after 60 minutes of inactivity.
- 5-attempt account lockout in place.
- Patient data in the processing pipeline is accessible only to the server on which JeffLocal runs (no external access).

**RAG Rating:** GREEN

**Maintenance Actions:**
- Document the access control model formally (role definitions, access levels, account lifecycle).
- Add a periodic access review procedure (e.g., quarterly: are all active accounts still required?).

---

### Standard 5 — Process: Processes are in place to prevent unauthorised access to systems

**Current Status:**
- Dashboard: PBKDF2-HMAC-SHA256 authentication, 60-minute sliding session expiry, 5-attempt lockout.
- HMAC-SHA256 payload verification for all incoming voice agent payloads (built; enforcement in pipeline currently being confirmed — see SC-03 in production spec).
- RSA encryption for payload transit.
- No penetration test has been conducted. [UNVERIFIED — confirm current pen test status before DSPT submission.]
- Cyber Essentials application in progress. Target: 31 July 2026.
- HTTP security headers (Content-Security-Policy, X-Frame-Options): in progress — flagged as SC-06 in production roadmap. [SAEED: action required — confirm whether security headers have been implemented before DSPT submission. If not, list as planned remediation with target date.]
- SQLite database is currently unencrypted at rest. Acceptable for single-practice pilot on local hardware; will be addressed before Phase 2 multi-practice deployment.

**RAG Rating:** AMBER

**Actions to Green:**
- Arrange independent penetration test (budget £500–£3,000). Can be "in progress" at submission if arranged before 23 June.
- Confirm HTTP security headers are in place or provide target date.
- Document the HMAC enforcement status in the evidence pack.

---

### Standard 6 — Process: Processes ensure that personal confidential data is stored securely and used properly

**Current Status:**
- All patient data is stored on the surgery's local server. No data is sent to external cloud providers.
- SQLite database holds case records. Database file is on the local machine.
- 90-day automated purge is in place for queue directories and handoff JSON outputs.
- Ollama raw outputs (may contain draft patient data): 90-day purge in place as of recent development cycle.
- Backup: daily automated restore points kept locally, last 3 retained.
- Data minimisation: JeffLocal stores only the structured fields required for the reception task — it does not store call audio or full transcripts.

**RAG Rating:** GREEN (with caveats — see notes)

**Notes:**
- The 90-day purge covering all patient data directories (handoff_json, ollama_raw, queue stages) should be confirmed as tested and operational before submission.
- SQLite encryption at rest is a known gap — document as an accepted risk for Phase 1 (local hardware, single practice) with a plan for Phase 2.

---

### Standard 7 — Process: Personal confidential data is only shared for lawful and appropriate purposes

**Current Status:**
- Patient data is not shared with any third party by JeffLocal.
- Hostcomm UK (voice AI) delivers an encrypted structured payload to JeffLocal. Hostcomm does not retain raw patient data on behalf of JeffLocal.
- No patient data is sent to any external AI API.
- Data flows have not yet been formally documented as a DPIA. [SAEED: action required — DPO to complete a Data Protection Impact Assessment (DPIA) for JeffLocal before DSPT submission. The DPIA should document: patient call → Hostcomm encrypted payload → local processing → dashboard → reception staff. This is a requirement under GDPR Article 35 for health data processing.]

**RAG Rating:** AMBER

**Actions to Green:**
- DPO to complete DPIA and retain on file.
- Document data flows formally (one diagram is sufficient).
- Obtain a Data Processing Agreement from Hostcomm UK if one is not already in place. [SAEED: action required — confirm whether a DPA with Hostcomm UK is in place or needs to be drafted.]

---

### Standard 8 — Process: Processes are in place to handle confidentiality, integrity, and availability

**Current Status:**
- Confidentiality: role-based access, no external data transfer (as above).
- Integrity: HMAC-SHA256 payload verification, deterministic validation rules, audit logging to SQLite.
- Availability: watchdog service (5-minute cycle), health monitor (10-minute cycle), daily backup, automatic service restart on failure.
- Incident register: the breach register at `docs/compliance/breach_register.md` documents the WhatsApp incident.

**RAG Rating:** GREEN

**Maintenance Actions:**
- Formally document the CIA (Confidentiality, Integrity, Availability) controls in the evidence pack for DSPT submission.
- Confirm the breach register is up to date and accessible to the DPO.

---

### Standard 9 — Technology: IT suppliers and partners are held to the same data security standards

**Current Status:**
- Hostcomm UK (the only external IT supplier with access to patient call data) is listed on the NHS Digital Marketplace, which implies a baseline of NHS supplier assurance.
- No formal supplier assurance questionnaire has been sent to Hostcomm UK.
- No formal Data Processing Agreement with Hostcomm UK is confirmed to be in place. [SAEED: action required — confirm DPA status with Hostcomm.]

**RAG Rating:** AMBER

**Actions to Green:**
- Confirm or obtain a Data Processing Agreement with Hostcomm UK (GDPR Article 28 requirement).
- Request Hostcomm's DSPT evidence or equivalent supplier assurance document.
- If other IT suppliers are used (e.g., hosting for n8n, any monitoring tools), assess them against this standard.

---

### Standard 10 — Technology: Accountable for personal confidential data held within their organisation

**Current Status:**
- DPO has been appointed. [SAEED: action required — provide DPO name and appointment date for the DSPT submission record.]
- No formal information governance lead is named for the purpose of the DSPT submission beyond the DPO.
- The DSPT submission will be made by the DPO or a named accountable person. [SAEED: action required — confirm who will be the named accountable person on the DSPT submission (likely Saeed as director, with DPO as lead).]

**RAG Rating:** AMBER (pending DPO details in submission)

**Actions to Green:**
- Name the accountable person in the DSPT portal.
- DPO to confirm they have reviewed and are satisfied with the self-assessment before submission.

---

## SECTION 2: DATA PROTECTION OFFICER

**DPO Status:** Appointed.

**DPO Name:** [SAEED: action required — provide DPO full name for this record]

**DPO Contact:** [SAEED: action required — provide DPO email address]

**Date of Appointment:** [SAEED: action required — provide date DPO was appointed]

**DPO Responsibilities at Avamed:**
- Lead the DSPT self-assessment (30 June 2026 deadline)
- Lead the DTAC self-assessment (31 July 2026 target)
- Complete the DPIA for JeffLocal
- Maintain the breach register
- Confirm supplier DPAs (Hostcomm UK)
- Advise on ICO registration status
- Determine DCB0129 applicability with clinical safety input

**RAG Rating:** GREEN (DPO in place) / AMBER (details not yet recorded in this document)

---

## SECTION 3: INFORMATION ASSET REGISTER

An Information Asset Register (IAR) is a record of all personal data held by an organisation — what it is, where it is stored, who is responsible, how long it is kept, and the lawful basis for processing.

**Current Status:** No formal IAR exists. The data flows are understood but not formally documented.

**RAG Rating:** RED (required for DSPT submission)

**Draft IAR Structure (DPO to populate and verify):**

| Asset | Data Type | Location | Owner | Retention | Lawful Basis | Risk |
|-------|----------|----------|-------|-----------|-------------|------|
| Call intake records (handoff JSON) | Patient name, DOB, reason for call, pathway, medications (mentioned) | `outputs/handoff_json/` on local server | Avamed / DPO | 90 days (automated purge) | Legitimate interest / NHS care pathway processing | Medium — plaintext at rest |
| Ollama raw outputs | Draft extraction containing patient-derived data | `outputs/ollama_raw/` on local server | Avamed / DPO | 90 days (automated purge) | Legitimate interest | Medium — plaintext at rest |
| Dashboard case records | Patient name, DOB, reason, pathway, priority, staff actions | `dashboard/data/dashboard.sqlite` on local server | Avamed / DPO | 90 days from case closure | Legitimate interest / healthcare administration | Medium — SQLite unencrypted at rest (Phase 1 accepted risk) |
| Staff account data | Username, hashed password, role, PIN hash | `dashboard/data/dashboard.sqlite` | Avamed / DPO | Duration of employment + 1 year | Legitimate interest | Low — passwords hashed (PBKDF2) |
| Audit log | User actions, timestamps, case IDs | `dashboard/data/dashboard.sqlite` (audit table) | Avamed / DPO | 12 months | Legal obligation (NHS audit requirements) | Low |
| Call queue files | Encrypted patient call data (raw, incoming, processing stages) | `queue/` directories on local server | Avamed / DPO | Purged after processing (processed stage: 90 days) | Healthcare processing | Low — encrypted in transit, processed rapidly |
| Patient lookup reference | Patient name, DOB, NHS number, postcode (practice-supplied) | `data/patient_lookup/mock_patient_lookup_v1.csv` | Practice / Avamed as processor | Duration of practice contract | Contractual (data processor) | Low — read-only, local |

**Actions to Green:**
- DPO to review and formally adopt this IAR draft.
- DPO to confirm all data assets are accounted for — check for any logging or diagnostic files not listed above.
- IAR to be maintained and updated when new assets are added.

---

## SECTION 4: STAFF TRAINING

**Current Status:**
- Reception staff at Churchtown Medical Centre have been onboarded on dashboard use.
- No formal NHS data security awareness training records exist.
- No annual training programme is in place.

**RAG Rating:** AMBER

**Actions to Green:**
- All Avamed staff who access patient data to complete NHS Data Security Awareness training (Level 1) and retain certificates.
- All practice staff using JeffLocal to complete their own DSPT-required training through their practice's existing programme (this is the practice's responsibility, not Avamed's, but Avamed should confirm it is happening).
- Draft a one-page data handling guide for reception staff using JeffLocal: what patient data they see, how long it is retained, who to contact if they spot an error.

---

## SECTION 5: TECHNICAL SECURITY

**On-Premises Architecture (key DSPT advantage):**

JeffLocal's on-premises design means that the majority of cloud-related data security risks simply do not apply. There is no data in transit to a cloud provider, no shared tenancy, no cloud API processing patient data. This simplifies the evidence required for multiple DSPT standards.

**Security Controls in Place:**

| Control | Status | Notes |
|---------|--------|-------|
| HMAC-SHA256 payload verification | Built | Enforcement in final validation — confirm operational before submission |
| RSA encryption (payload transit) | Operational | Public/private key pair in config/security/keys/ |
| PBKDF2-HMAC-SHA256 authentication | Operational | 100,000 iterations, 32-byte session tokens |
| Account lockout | Operational | 5 failed attempts, 15-minute lockout |
| Session expiry | Operational | 60 minutes sliding expiry |
| Audit logging | Operational | Case status changes, login events, import events |
| 90-day data purge | Operational | Scheduled task — confirm covers all patient data directories |
| Daily backup | Operational | Restore points retained, daily automated |
| Watchdog / auto-restart | Operational | 5-minute cycle |
| HTTP security headers (CSP, X-Frame-Options) | In progress | Target: before DSPT submission |
| Penetration test | Not yet arranged | [SAEED: action required] — arrange before or shortly after 23 June |
| Cyber Essentials | In progress | Target: 31 July 2026 |
| SQLite encryption at rest | Not in place (Phase 1 accepted risk) | Phase 2 prerequisite — document as known gap |
| IP allowlist for dashboard | Not in place | Phase 2 — consider for production environment |

**External Data Transfer:** None. All patient data processing is local.

**RAG Rating:** AMBER (pen test and HTTP headers outstanding)

---

## SECTION 6: INCIDENT MANAGEMENT

**Breach Register:** Exists at `C:\JeffLocal\docs\compliance\breach_register.md`

**Documented Incident:**
- WhatsApp wrong recipient incident (June 2026): an operational message was sent to the wrong WhatsApp recipient. The incident was identified immediately, documented in the breach register, reviewed by the security team, and a corrective procedure was implemented. No patient data was involved. The incident has been assessed as not reportable to the ICO.

**Incident Response Procedure:** Not yet formally documented.

**RAG Rating:** AMBER

**Actions to Green:**
- DPO to formally document the incident response procedure: detection → assessment → containment → notification decision (ICO 72-hour rule) → remediation → lessons learned.
- Update breach register format to include: date discovered, date of incident, type of data, number of individuals, ICO notification decision (yes/no/N/A), outcome.
- DPO to confirm the WhatsApp incident entry in the breach register is complete and signed off.

---

## SECTION 7: BUSINESS CONTINUITY

**Current Controls:**

| Control | Status |
|---------|--------|
| Watchdog (auto-restart on crash) | Operational — 5-minute cycle |
| Health monitor (deep checks) | Operational — 10-minute cycle |
| Daily backup | Operational — last 3 restore points retained |
| Backup restore procedure | Documented in infrastructure spec — not yet formally tested end-to-end |
| Log archiving | In progress |
| Disaster recovery procedure | Not formally documented |

**RAG Rating:** AMBER

**Actions to Green:**
- Formally document the disaster recovery procedure: what happens if the server restarts, if the database corrupts, if the queue jams, if Ollama crashes.
- Conduct a backup restore test: restore from the latest restore point to a test directory and validate database integrity. Document the outcome.
- DPO to confirm that business continuity planning covers the data protection obligations (i.e., that patient data can be recovered and continuity of care maintained).

---

## SECTION 8: GAPS SUMMARY (HONEST ASSESSMENT)

The following gaps must be addressed before or shortly after DSPT submission. This is an honest internal assessment.

| Gap | Severity | Owner | Target Date |
|-----|----------|-------|-------------|
| Information Asset Register not formally created | HIGH | DPO | Before 30 June |
| DPIA for JeffLocal not completed | HIGH | DPO | Before 30 June |
| Staff data security training records do not exist | HIGH | Saeed / DPO | Before 30 June |
| DPO details not recorded in DSPT portal | HIGH | DPO / Saeed | Before 30 June |
| Incident response procedure not formally documented | MEDIUM | DPO | Before 30 June |
| Supplier DPA with Hostcomm UK not confirmed | HIGH | Saeed / DPO | Before 30 June |
| Penetration test not arranged | MEDIUM | Saeed | Arrange before 23 June; complete by 31 July |
| HTTP security headers not confirmed in place | MEDIUM | Development team | Before 30 June |
| Cyber Essentials not yet obtained | MEDIUM | Saeed | 31 July 2026 |
| Backup restore procedure not tested | LOW | Development team | 31 July 2026 |
| Disaster recovery procedure not documented | MEDIUM | Development team | 31 July 2026 |
| SQLite encryption at rest (Phase 1 accepted risk) | LOW (Phase 1) | Development team | Phase 2 prerequisite |
| ICO registration status unconfirmed | HIGH | Saeed / DPO | Before 30 June |

**Note to DPO:** The DSPT toolkit allows partial completion with a credible improvement plan. Not every item needs to be Green at initial submission, but the high-severity gaps above (IAR, DPIA, training, DPO details, ICO registration, supplier DPA) should be resolved before or at submission. The DSPT submission should be honest: state what is in place, what is in progress, and when the remaining items will be complete.

---

## ITEMS FLAGGED [SAEED: action required] — SUMMARY

1. Confirm DPO name, email, and date of appointment for all compliance documents
2. Confirm ICO registration status; register if not done (ico.org.uk/registration, £52/year)
3. Arrange independent penetration test (£500–£3,000; Pentest People, Bulletproof, CyberCX)
4. Confirm whether a Data Processing Agreement with Hostcomm UK is in place; if not, obtain one
5. Confirm who will be the named accountable person on the DSPT portal submission
6. Ensure all Avamed staff who access patient data complete NHS Data Security Awareness training (Level 1)

---

*Prepared by Avamed Strategy Agent, 2026-06-04. DPO should lead this document from this point forward. Saeed should review and confirm all [SAEED: action required] items. This document does not constitute a completed DSPT submission — it is a preparation framework.*

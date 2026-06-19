# WhatsApp Channel — GDPR Compliance Addendum
**Project:** JeffLocal — Avamed  
**Date:** 2026-06-02  
**Author:** Claude (Security + Strategy Agent)  
**Status:** DRAFT — Requires DPO/Saeed sign-off before pilot go-live  

---

## 1. SCOPE

This addendum covers the data protection obligations arising from adding WhatsApp Business as a patient intake channel to JeffLocal. It supplements the existing JeffLocal Governance Framework (`GOVERNANCE_FRAMEWORK.md`).

---

## 2. DATA FLOW ANALYSIS

### Existing voice channel
```
Patient phone call → Jeff voice AI → JeffLocal server (on-premises) → dashboard
[ALL data stays on-premises / within NHS-grade network]
```

### New WhatsApp channel
```
Patient WhatsApp message → Meta servers (EU/US) → JeffLocal webhook → on-premises processing
[Message content transits Meta's infrastructure before reaching JeffLocal]
```

**Key difference:** Patient message content (name, date of birth, symptom/reason) passes through Meta's servers before arriving at your system. This requires explicit compliance steps.

---

## 3. DATA CONTROLLER / PROCESSOR RELATIONSHIPS

| Entity | Role | Basis |
|--------|------|-------|
| Avamed / Churchtown Medical Centre | Data Controller | Operates the service, determines purpose |
| Meta Platforms Ireland Ltd | Data Processor | Processes messages in transit on behalf of the Controller |
| Anthropic / Ollama | Sub-processor (local) | On-premises AI extraction — no data leaves building |

---

## 4. LEGAL BASIS FOR PROCESSING

**Lawful basis:** Article 6(1)(b) — Processing necessary for performance of a contract (providing healthcare administrative services to the patient).

**Special category data (Article 9):** Patient symptom/reason data is health data. Lawful basis: Article 9(2)(h) — Healthcare provision and management.

**Condition for special category:** The surgery is a registered healthcare provider. Reception intake is a legitimate healthcare management activity.

---

## 5. META DATA PROCESSING AGREEMENT (DPA)

**Action required before go-live.**

Meta provides a standard DPA for WhatsApp Business API customers. This must be formally accepted.

Steps:
1. Log in to Meta Business Suite → Settings → Data Use Checkup
2. Review and accept Meta's Data Processing Terms
3. Download and retain a copy in `governance/external_dpas/`
4. Record acceptance date in change log

**Meta's data handling commitments (summary):**
- Message content used only to deliver the message (not for advertising targeting)
- EU customers: data processing under EU Standard Contractual Clauses
- Retention: messages not retained by Meta beyond delivery
- Full DPA: https://www.facebook.com/legal/terms/dataprocessing

---

## 6. PATIENT CONSENT (OPT-IN)

WhatsApp patient intake is **opt-in only**. No patient can be processed via WhatsApp without explicit consent.

### Consent mechanism (technical)
1. Patient sends any first message to the surgery WhatsApp number
2. Jeff responds BEFORE any intake:
   > "Hello! Before I can help you, I need your consent to process your message.  
   > Your message will be handled by Avamed's JeffLocal system and will transit WhatsApp's servers.  
   > Our full Privacy Notice is at: [URL]  
   > **Reply YES to continue, or call the surgery on [number] if you prefer not to use WhatsApp.**"
3. Patient must reply "YES" (case-insensitive) to proceed
4. Consent is recorded in `whatsapp_consents` table with:
   - Hashed phone number (SHA-256 — never plain text)
   - Timestamp
   - Version of consent text shown (to handle future updates)
5. If patient replies anything other than YES, session is closed with:
   > "No problem. Please call us on [number]. Goodbye."

### Consent validity
- Consent valid for 12 months from last contact
- After 12 months: consent prompt shown again
- Consent can be withdrawn at any time by texting "STOP" — session terminated, consent record flagged

### Records
- Consent records retained for minimum 3 years (healthcare records retention requirement)
- Separate from the 90-day message purge cycle

---

## 7. PRIVACY NOTICE UPDATES REQUIRED

The surgery's Privacy Notice must be updated to include:

**New section to add:**

> **WhatsApp Intake Service**  
> We offer an optional WhatsApp service allowing you to submit appointment requests via WhatsApp instead of calling. If you use this service, your messages will be processed by WhatsApp (Meta Platforms Ireland Ltd) as a data processor before reaching our secure on-premises system. Meta's Privacy Policy applies to message transit. We do not share your health information with Meta for any advertising purpose. Your consent is required before using this service and can be withdrawn at any time by texting STOP to our WhatsApp number.

**Where to update:** Surgery website Privacy Notice page + printed copies in waiting room.

---

## 8. DATA MINIMISATION

Jeff only collects what is necessary for admin intake:
- Full name
- Date of birth (for patient matching)
- Reason for contact (symptom/concern — kept brief)
- Duration of symptom (optional clarification)

Jeff does NOT ask for:
- NHS number (matched from name/DOB against EMIS)
- Medications, past history, diagnoses
- Anything not required for routing the appointment request

---

## 9. TECHNICAL DATA PROTECTION MEASURES

| Measure | Implementation |
|---------|---------------|
| Phone number hashing | SHA-256 hash stored, never plain text |
| Message content purge | Included in existing 90-day GDPR purge |
| HMAC webhook verification | Validates messages are genuinely from Meta |
| Consent records | Retained separately, 3-year minimum |
| `.env` credentials | Never committed to git, stored locally only |
| Audit logging | All WhatsApp intake events logged to audit table |
| Emergency override | Red-flag messages trigger immediate safe reply before any storage |

---

## 10. INTERNATIONAL TRANSFERS

Meta is a US company. Message data may transit US servers.

**Safeguard:** Meta relies on EU Standard Contractual Clauses (SCCs) for EU→US transfers, accepted as part of Meta's DPA (Section 5 above). This is the standard GDPR-compliant transfer mechanism used by the NHS and most UK healthcare providers with Meta products.

---

## 11. DATA SUBJECT RIGHTS

Patients can exercise their rights by contacting the surgery directly. For WhatsApp-specific requests:

- **Right of access:** Conversation logs purged after 90 days; retained data (consent record) available on request (hashed phone, timestamp only)
- **Right to erasure:** Patient texts "DELETE MY DATA" → consent record flagged for deletion; processed within 72 hours
- **Right to withdraw consent:** Patient texts "STOP" → immediate cessation of WhatsApp intake

---

## 12. SIGN-OFF REQUIRED

Before WhatsApp channel goes live, the following must be completed:

| Item | Owner | Status |
|------|-------|--------|
| Meta DPA accepted | Saeed | ⬜ Pending |
| Privacy Notice updated | Saeed / Practice Manager | ⬜ Pending |
| Consent mechanism tested | Claude / Saeed | ⬜ Pending |
| Governance Framework updated (WhatsApp section) | Claude | ⬜ Pending |
| DPIA completed (if required) | Saeed / DPO | ⬜ Pending |

**DPIA note:** A Data Protection Impact Assessment (DPIA) may be required under UK GDPR Article 35 as this involves large-scale processing of health data via a new channel. Recommended to complete a brief DPIA — Claude can draft this.

---

*WHATSAPP_GDPR_ADDENDUM.md | Created: 2026-06-02 | Status: DRAFT*  
*This document does not constitute legal advice. Review with your DPO before go-live.*

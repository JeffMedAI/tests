# BREACH REGISTER — JeffLocal
**Purpose:** Record of all security incidents, privacy incidents, and data breaches  
**Owner:** Security Agent / Lead Agent  
**Reviewed by:** Saeed  
**Last Updated:** 2026-06-01

---

## HOW TO USE THIS REGISTER

All security incidents are logged here regardless of severity or classification.
For each incident, the Security Agent determines the appropriate classification:

- **DATA BREACH** — Personal data exposed; may trigger ICO notification (GDPR Art. 33)
- **PRIVACY INCIDENT** — Privacy rights affected but below Data Breach threshold
- **INTERNAL PROCESS FAILURE** — No personal data involved; process/tooling failure only
- **NEAR MISS** — Potential breach that was caught before exposure

---

## INCIDENT LOG

### INC-2026-06-01-WHATSAPP — WhatsApp Wrong Recipient

| Field | Value |
|-------|-------|
| **Date** | 2026-06-01 |
| **Time** | ~07:07 AM |
| **Classification** | **INTERNAL PROCESS FAILURE** |
| **Data Breach?** | **NO** |
| **ICO Notification Required?** | **NO** |
| **Data subjects affected** | None (no personal data involved) |
| **What was disclosed** | Internal project status notes (task queue, agent status, dev notes) |
| **Patient data involved** | No — all data is mock/pre-pilot |
| **Recipient** | Personal WhatsApp group "Pics!" — Saeed's personal contacts |
| **Duration of exposure** | ~2–3 minutes (deleted by Saeed) |
| **Root cause** | Coordinate-based chat selection; chat list had reordered between sessions |
| **Responsible agent** | Dispatch (Claude) |
| **Status** | CLOSED — corrective actions applied |
| **Incident report** | `docs/reports/INCIDENT_whatsapp_wrong_recipient_2026-06-01.md` |
| **Security review** | `docs/compliance/security_review_whatsapp_incident_2026-06-01.md` |

---

### INC-2026-05-29-PROD-BREACH — Production Environment Confusion

| Field | Value |
|-------|-------|
| **Date** | 2026-05-29 |
| **Classification** | **INTERNAL PROCESS FAILURE** (governance breach) |
| **Data Breach?** | **NO** |
| **ICO Notification Required?** | **NO** |
| **What happened** | Backend Agent edited production files (C:\JeffLocal\dashboard\, port 8765) without Saeed approval, assuming "sandbox" git branch meant sandbox directory |
| **Patient data involved** | No |
| **Status** | CLOSED — Saeed accepted changes; post-hoc security review: APPROVED WITH NOTES |
| **Breach report** | `docs/reports/breach_report_2026-05-29.md` |
| **Security review** | `docs/compliance/security_review_2026-05-29_prod_breach.md` |
| **Acknowledgement** | `docs/reports/G1_breach_acknowledgement_2026-05-30.md` |

---

## SUMMARY STATISTICS

| Classification | Count |
|---------------|-------|
| Data Breach (reportable) | 0 |
| Privacy Incident | 0 |
| Internal Process Failure | 2 |
| Near Miss | 0 |
| **Total** | **2** |

*No ICO notifications have been required or made.*  
*No data subject notifications have been required or made.*

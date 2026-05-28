# Pathway Registry
**Version:** 1.0
**Author:** TechLead
**Created:** 2026-05-23
**Status:** Approved and deployed

---

## Purpose

This registry defines all request pathways handled by the JeffLocal system at Churchtown Medical Centre. Each pathway describes a category of patient/caller request that reception staff process as an admin task. The LLM suggests a pathway — deterministic code in `Jeff.RequestType.ps1` makes the final routing decision.

**Core rule:** All pathways produce admin tasks for human staff. The system does not make clinical decisions.

---

## Pathway: `prescription`

**Description:** Patient or caller requests a repeat or new prescription, or queries a medication-related admin issue.

**Triggered by (keywords in transcript):**
prescription, repeat, medication, medicine, inhaler, pharmacy, drug, tablet, cream, gel, capsule, dose

**Required fields:**
| Field | Type | Description |
|-------|------|-------------|
| `prescription_type` | string | "repeat" or "new" |
| `medications_requested` | array | List of medication names |
| `pharmacy` | string | Preferred pharmacy if stated |
| `run_out_status` | string | Whether patient has run out ("yes", "no", "soon") |

**Optional fields:** callback number, urgency flag

**Routing queue:** `normal` (standard) / `review` (if identity incomplete) / `urgent` (if run_out_status = "yes" and safety flag)

**Handoff output language:** "Patient requests repeat prescription for [medication]. Please process via [pharmacy]."

**Clinical boundary:** System does not assess clinical appropriateness of prescriptions. Staff decide.

---

## Pathway: `sick_note`

**Description:** Patient or representative requests a sick note (fit note / Med3 certificate).

**Triggered by (keywords):**
sick note, fit note, fitnote, med3, med 3, doctor's note, GP note, certificate, signed off, sign off

**Required fields:**
| Field | Type | Description |
|-------|------|-------------|
| `request_type` | string | "new" or "extension" |
| `purpose` | string | Employer / self-certification purpose if stated |
| `start_date` | string | Start date of illness if provided |
| `duration_requested` | string | Duration requested if stated |

**Optional fields:** employer name, return to work date

**Routing queue:** `normal` (standard) / `review` (if dates unclear or identity incomplete)

**Handoff output language:** "Patient requests sick note from [start_date]. Please process and contact patient."

**Clinical boundary:** System does not assess fitness for work. GP decides.

---

## Pathway: `referral`

**Description:** Patient queries the status of a referral, requests information about a referral, or needs a referral initiated.

**Triggered by (keywords):**
referral, hospital, consultant, clinic, chase referral, referred, choose and book, e-RS, ERS

**Required fields:**
| Field | Type | Description |
|-------|------|-------------|
| `referral_type` | string | "chase", "query", "new_request" |
| `hospital_name` | string | Hospital or clinic name if stated |
| `approx_submission_date` | string | When referral was submitted if known |
| `specialty` | string | Specialty if stated |

**Optional fields:** reference number, consultant name

**Routing queue:** `normal` (standard) / `review` (if referral cannot be located)

**Handoff output language:** "Patient chasing referral to [hospital/specialty]. Please check e-RS and contact patient."

**Clinical boundary:** System does not assess clinical priority of referrals. GP/staff decide.

---

## Pathway: `test_result`

**Description:** Patient queries a test result (blood, scan, biopsy, urine, swab, etc.) or requests a copy.

**Triggered by (keywords):**
test, result, blood, xray, x-ray, scan, MRI, CT, urine, swab, sample, specimen, ultrasound

**Required fields:**
| Field | Type | Description |
|-------|------|-------------|
| `test_type` | string | Type of test (blood, scan, etc.) |
| `approx_test_date` | string | Approximate date of test if stated |
| `reference_number` | string | Reference number if patient has one |

**Optional fields:** requesting doctor, hospital name

**Routing queue:** `normal` (standard) / `review` (if result flagged as urgent by caller)

**Handoff output language:** "Patient querying [test_type] result from approx [date]. Please check records and contact patient."

**Clinical boundary:** System does not interpret test results. Clinician/staff decide on disclosure.

---

## Pathway: `appointment_redirect`

**Description:** Patient or caller wishes to book, cancel, or reschedule an appointment, or is directed to a booking service.

**Triggered by (keywords):**
appointment, book, booking, see a doctor, see GP, see nurse, same day appointment

**Required fields:**
| Field | Type | Description |
|-------|------|-------------|
| `appointment_type` | string | "book", "cancel", "reschedule", "query" |
| `urgency` | string | "routine" or "same_day" if stated |
| `preferred_clinician` | string | Preferred GP/nurse if stated |

**Optional fields:** preferred time, callback number

**Routing queue:** `normal` (routine booking) / `urgent` (same-day request) / `review` (complex or unclear)

**Handoff output language:** "Patient requests [appointment_type] appointment. Please contact patient to arrange."

**Clinical boundary:** System does not assess clinical urgency. Triage staff decide priority.

---

## Pathway: `admin`

**Description:** Admin or general enquiry — records, registration, letters, complaints, online access, address changes.

**Triggered by (keywords):**
admin, reception, letter, records, address, registration, register, form, email, online access, medical record, copy of, complaint

**Also the default:** Any call that does not match another pathway routes here.

**Required fields:**
| Field | Type | Description |
|-------|------|-------------|
| `admin_type` | string | "records", "registration", "letter", "complaint", "other" |
| `detail` | string | Brief description of the request |

**Optional fields:** urgency, reference number

**Routing queue:** `normal` (standard) / `review` (complaints or sensitive requests)

**Handoff output language:** "Patient requests [admin_type]. Please action and contact patient if needed."

**Clinical boundary:** None — this is a purely administrative pathway.

---

## Emergency Detection (Overlay)

The `Jeff.Emergency.ps1` module runs on every call regardless of pathway. It detects language indicating a potential emergency and can override routing to flag the call for immediate staff attention.

**This is not a separate pathway.** It is a safety overlay that applies to all pathways.

**Emergency detection is deterministic** — it uses keyword matching, not LLM assessment. The system never tells a caller to call 999 or makes any clinical recommendation. Staff are alerted to review the call immediately.

---

## Routing Summary

| Pathway | Normal Queue | Review Queue | Urgent Queue |
|---------|-------------|-------------|-------------|
| prescription | ✅ | Identity incomplete | Run out, safety flag |
| sick_note | ✅ | Dates/identity unclear | — |
| referral | ✅ | Cannot locate referral | — |
| test_result | ✅ | Urgent flag from caller | — |
| appointment_redirect | ✅ | Complex/unclear | Same-day request |
| admin | ✅ | Complaint/sensitive | — |

All routing decisions are made by deterministic code (`Jeff.Handoff.ps1`, `Jeff.RequestType.ps1`). The LLM does not make routing decisions.

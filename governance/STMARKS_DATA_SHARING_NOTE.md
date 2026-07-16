# St Marks Pharmacy Intake — Data Controller & Retention Note
**Project:** JeffLocal — Avamed
**Date:** 2026-07-16
**Author:** Claude (Security Agent finding, written up by Strategy Agent per Saeed's approval)
**Status:** DRAFT — unresolved, flagged for Saeed's decision. Not a go-live blocker (endpoint not yet in live use — `STMARKS_INTAKE_SECRET` unset in production).

---

## 1. WHAT CHANGED

Commit da24bb2 (merged 2026-07-16) added `POST /api/intake/stmarks-contact` — a new endpoint in the
Avamed/JeffLocal dashboard that receives contact-form submissions from St Marks Pharmacy's public
website (stmarkspharmacy.co.uk, a separate business, separate Cloudflare Workers site, separate git
repo at `C:\JeffLocal\SMCPHARMA`). Submissions land in the **same SQLite case queue** as GP triage
cases from Churchtown Medical Centre, tagged with `call_id` prefix `STMARKS-`.

Code: [dashboard/app/routers/stmarks.py](../dashboard/app/routers/stmarks.py)

## 2. THE ISSUE

JeffLocal's database was built and governed as a **GP surgery patient triage system**. Its data
protection posture (90-day GDPR purge, audit logging, on-premises-only, DCB0129 review) was designed
around Churchtown Medical Centre being the data controller for patient admin-intake data.

St Marks Pharmacy is a **different business** with its own customers, own privacy policy (draft,
not yet pharmacist/DPO-reviewed), and — for the pharmacy's purposes — is presumably its own data
controller for its customer contact-form data.

Mixing St Marks' customer PII (name, phone/email, free-text message) into Avamed's GP case database
raises a question neither project's governance docs currently answer:

- **Who is the data controller for the St Marks records once they land in JeffLocal's database?**
  Avamed (as operator of the system the data physically sits in) or St Marks (as the business that
  collected it from its own customer)?
- Does JeffLocal's 90-day purge cycle apply to St Marks records the same way it applies to GP cases?
- Does storing pharmacy-customer PII inside a system built for patient health-admin data change
  JeffLocal's own data protection classification (e.g. does it complicate the DCB0129/ICO picture)?
- St Marks' own draft privacy policy does not yet mention this data flow (see open question below).

## 3. CURRENT STATE (as of 2026-07-16)

- Endpoint is deployed to production but **inert** — `STMARKS_INTAKE_SECRET` is not set in the
  production environment, so every request fails closed with `503`. No real customer data has
  flowed through it yet.
- Saeed decided (2026-07-16): **no** privacy-policy disclosure line will be added to St Marks'
  draft policy at this time. This note exists so the underlying data-controller/retention question
  is not lost, not to force an immediate change.
- St Marks-side forwarding code (`SMCPHARMA/src/index.js`) is still being built and tested locally
  — nothing live end-to-end yet.

## 4. WHAT THIS NOTE DOES NOT DO

This is not a DPIA and not legal advice. It records the open question for Saeed/DPO review before
the St Marks → JeffLocal flow goes live with real customer data. Recommend treating this the same
way as `WHATSAPP_GDPR_ADDENDUM.md` — a pre-go-live gate, not a blocker on current dev/test work.

## 5. OPEN QUESTIONS FOR SAEED / DPO

1. Should St Marks records be stored in a logically separate table/store from GP cases, rather than
   the same `cases` table distinguished only by `call_id` prefix?
2. Does the 90-day purge need a distinct (possibly shorter) retention rule for `STMARKS-*` records,
   given they are general pharmacy enquiries, not clinical admin intake?
3. Confirm data-controller position in writing before real customer data flows — this affects who is
   accountable for a subject access request, breach notification, etc.

---

*STMARKS_DATA_SHARING_NOTE.md | Created: 2026-07-16 | Status: DRAFT — unresolved*
*This document does not constitute legal advice. Review with DPO before live customer data flows.*

# St Marks Pharmacy Intake — Multi-Controller Data Segregation Note
**Project:** JeffLocal — Avamed
**Date:** 2026-07-16 (v2 — supersedes the v1 draft written earlier the same day)
**Author:** Claude (Security Agent finding; corrected after Saeed's clarification)
**Status:** OPEN — technical gap identified, not yet fixed. Not currently exploitable (see §4).

---

## 0. CORRECTION TO v1 — READ THIS FIRST

The first version of this note treated "who is the data controller?" as the open question, and
described the St Marks records as landing in *"Avamed's GP database"*. **That framing was wrong.**

Saeed confirmed 2026-07-16: **Avamed is the data _processor_ for both JeffLocal and St Marks.**
It is one company providing a service to two separate controllers.

| Entity | Role |
|--------|------|
| Churchtown Medical Centre | Data controller (its patients) |
| St Marks Pharmacy | Data controller (its customers) |
| **Avamed** | **Data processor for both** — processes on each controller's instructions |

This is a cleaner position than v1 assumed, and it resolves the "who is the controller" question.
But it does **not** dissolve the problem — it changes it into a sharper, more concrete one (§2).

**Conflict to resolve:** `WHATSAPP_GDPR_ADDENDUM.md` §3 currently lists
*"Avamed / Churchtown Medical Centre — Data Controller"*. That contradicts the above and should be
corrected to match, or one of the two documents is wrong. [UNVERIFIED — Saeed/DPO to confirm which.]

## 1. WHAT CHANGED

Commit da24bb2 (merged and deployed 2026-07-16) added `POST /api/intake/stmarks-contact`, which
receives contact-form submissions from St Marks Pharmacy's website and lands them in the **same
SQLite `cases` table** as Churchtown GP triage cases, distinguished only by a `STMARKS-` prefix on
`call_id`.

Code: [dashboard/app/routers/stmarks.py](../dashboard/app/routers/stmarks.py)

## 2. THE REAL ISSUE — NO SEGREGATION BETWEEN TWO CONTROLLERS

As processor for two controllers, Avamed's Article 28/32 obligation includes keeping each
controller's data from being disclosed to the other. **The system currently cannot do that.**

Verified 2026-07-16:
- The `cases` table has **no tenant/controller column**. (`PRAGMA table_info(cases)` — the only
  vaguely related columns are `source_path` and `source_file_mtime`, which are file-ingest
  metadata, not a tenant identifier.)
- The worklist query filters on **status / priority / red-flag only** — there is no per-tenant or
  per-controller scoping. See `active_case_clause()` / `worklist_order_clause()` in
  [dashboard/app/case_domain.py](../dashboard/app/case_domain.py) (L245, L368).
- Therefore **any logged-in staff user sees every case.**

**Consequence:** once Churchtown reception staff accounts exist, those staff would see St Marks
Pharmacy customers' enquiries — names, phone numbers, and free-text messages that may contain
health information — in their worklist. That is an unauthorised disclosure of St Marks' customers'
data to a different controller's staff, and as processor it is Avamed's failure, not the
pharmacy's.

The reverse is equally true: St Marks staff with dashboard access would see Churchtown patients.

Multi-tenancy (`tenant_id`, "Item #4") is on the backlog as **Phase 2, unbuilt** — see
PROJECT_MEMORY.md. This note is the compliance argument for why that item is no longer merely a
scaling nicety.

## 3. OTHER OPEN POINTS

- **Article 28 processor agreement.** A written contract between each controller and Avamed is
  required. [UNVERIFIED — is one in place with St Marks? With Churchtown?] Avamed is also not yet
  a registered company (PROJECT_MEMORY.md), which complicates signing one.
- **Retention.** JeffLocal runs a 90-day purge designed around GP admin-intake records. St Marks
  enquiries are general pharmacy enquiries with a different natural lifespan. Each controller
  should set its own retention instruction; right now both inherit one rule by accident.
- **Privacy notice.** Added 2026-07-16 to St Marks' draft policy: a paragraph naming Avamed as a
  processor for the enquiry task list (`site/privacy-policy.html`, "How your booking is sent to
  us"). Still requires superintendent pharmacist + DPO review, like the rest of that draft policy.

## 4. CURRENT EXPOSURE — WHY THIS IS NOT AN INCIDENT TODAY

- The endpoint is deployed but **inert**: `STMARKS_INTAKE_SECRET` is unset in production, so every
  request fails closed with `503`. No real St Marks customer data has ever flowed through it.
- Churchtown has **no real staff accounts** and is **not live with patients** (PROJECT_MEMORY.md).
  There is currently nobody who could see the other controller's data.

So the gap is real but **not yet exploitable**. It becomes live the moment either side is switched
on. That ordering is the whole point of this note.

## 5. RECOMMENDATION

Do not enable the St Marks flow (i.e. do not set `STMARKS_INTAKE_SECRET` on both sides) into a
database that Churchtown staff will later be given accounts on, until at least one of:

1. **Tenant scoping is implemented** — a `tenant_id` on `cases`, set deterministically at ingest,
   with every case-listing query scoped to the logged-in user's tenant (fail-closed default). This
   is the correct fix and also unblocks Item #4.
2. **Separate instances** — St Marks gets its own dashboard instance and its own database. Heavier
   operationally, but total segregation and no shared-query risk.

Interim option if the flow must go live sooner: keep it live only while Churchtown has no staff
accounts, and treat "first Churchtown staff account created" as a hard gate that requires (1) or
(2) first. This is a schedule dependency, not a technical control — it relies on nobody forgetting.

---

*STMARKS_DATA_SHARING_NOTE.md | v2 2026-07-16 | Status: OPEN — segregation gap unfixed*
*Not legal advice. Review with DPO before any real customer data flows.*

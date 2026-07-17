# Multi-Tenant Data Segregation Note (St Marks + GP practices)
**Project:** JeffLocal — Avamed
**Date:** 2026-07-16 (v3 — 2026-07-17, corrected twice; read §0 and §0b before trusting anything here)
**Author:** Claude (Security Agent finding; corrected after Saeed's clarifications)
**Status:** OPEN — technical gap identified, not yet fixed. Not exploitable: nothing is live and
all patient data is fake (see §4). Fix designed in [MULTI_TENANCY_PROPOSAL.md](MULTI_TENANCY_PROPOSAL.md).

---

## 0b. CORRECTION TO v2 (2026-07-17) — SCOPE WAS WRONG

v2 framed this as a "St Marks problem": a separate business's data intruding into a GP database.
**That was wrong.** Saeed clarified:

- **Multi-tenancy is for GP practices under JeffLocal** — Churchtown plus 4 more planned.
- **St Marks is simply one tenant**, a stand-alone pharmacy. It will never have "tenant pharmacies"
  beneath it. It is tenant #2, not a special case.
- So the segregation problem is **generic multi-tenant isolation**, which JeffLocal needs regardless
  of whether St Marks exists at all. Churchtown vs Practice #3 is the same problem.
- **Nothing is live and all patient data is currently FAKE.** Neither business goes live until
  compliant, tested, and approved by the partners.

This note is kept for the analysis in §2 (which is still accurate and still matters), but it should
be read as "why JeffLocal needs multi-tenancy", not "why St Marks is a problem".

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

**And this is not about St Marks.** The same failure exists between any two tenants — Churchtown vs
Practice #3 is identical. JeffLocal is planned for 5 GP practices; the moment there are two, one
practice's reception staff can see the other's patients. St Marks merely made it visible first.

Multi-tenancy was on the backlog as `tenant_id`, "Item #4", **Phase 2, unbuilt**. It is now
promoted and decided: **separate database per tenant**
([MULTI_TENANCY_PROPOSAL.md](MULTI_TENANCY_PROPOSAL.md)). This note is the compliance argument for
why it was never merely a scaling nicety.

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

## 4. CURRENT EXPOSURE — NOT AN INCIDENT, AND NOT CLOSE TO ONE

- **All patient data in the system is FAKE** (Saeed, 2026-07-17). Neither Churchtown nor St Marks
  is live. Neither goes live until compliant, tested, and approved by the partners.
- The St Marks endpoint is deployed but **inert**: `STMARKS_INTAKE_SECRET` is unset, so every
  request fails closed with `503`. No St Marks customer data has ever flowed through it.
- Churchtown has **no real staff accounts**.

So there is **nobody who could see another tenant's data, and no real data to see**. The gap is a
design debt to clear before go-live, not a live exposure. Earlier drafts of this note leaned toward
incident language; that was overstated.

## 5. RECOMMENDATION

**Decided (Saeed, 2026-07-16): separate database per tenant.** See
[MULTI_TENANCY_PROPOSAL.md](MULTI_TENANCY_PROPOSAL.md) — §6 (Avamed tenant switcher) settled
2026-07-17.

Do not set `STMARKS_INTAKE_SECRET` on either side until that lands. Same applies to standing up a
second GP practice: no tenant's intake goes on into a shared database.

Rejected: a shared DB with a `tenant_id` column. It works, and it is the standard SaaS answer, but
it means every one of ~50 case queries must remember its `WHERE tenant_id = ?` — and one forgotten
clause is a cross-controller disclosure of health data. Separate databases make that mistake
unreachable rather than merely unlikely.

Also rejected: "go live now, treat the first staff account as a gate". That is a schedule
dependency, not a technical control — it relies on nobody forgetting. There is no time pressure
here (nothing is live), so there is no reason to take it.

---

*STMARKS_DATA_SHARING_NOTE.md | v3 2026-07-17 | Status: OPEN — segregation gap unfixed, fix designed and decided*
*Not legal advice. Review with DPO before any real patient or customer data flows.*

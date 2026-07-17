# Multi-Tenancy Design Proposal — Separate Database Per Tenant
**Project:** JeffLocal — Avamed
**Date:** 2026-07-16
**Author:** Claude (Lead) — design proposal, NOT built
**Status:** AWAITING SAEED'S APPROVAL + SECURITY AGENT REVIEW. No code written. No data migrated.

---

## 1. WHY THIS EXISTS

Avamed is the **data processor** for two separate **data controllers** — Churchtown Medical Centre
(its patients) and St Marks Pharmacy (its customers) — with more practices planned. Today all their
data would share one SQLite database with no separation, and every logged-in staff user can see
every case. Full analysis: [STMARKS_DATA_SHARING_NOTE.md](STMARKS_DATA_SHARING_NOTE.md).

Saeed's decision, 2026-07-16: **separate database per tenant.** Data must be separate and not
shared.

**This is a gate.** No tenant's flow may be switched on into a shared database.

## 2. DECISIONS TAKEN (Saeed, 2026-07-16, clarified 2026-07-17)

| Decision | Choice |
|----------|--------|
| Isolation model | **Separate database per tenant** |
| What a tenant IS | **A GP practice** (Churchtown + 4 more planned) **or St Marks**. St Marks is simply one tenant — a stand-alone pharmacy. There will be no "tenant pharmacies" beneath it. It is not a special case; it is tenant #2. |
| Tenant staff logins | **Each tenant's staff get their own logins**, scoped to their own tenant |
| Avamed super-admin | **SETTLED — a tenant switcher.** Avamed switches tenant on the dashboard and views each tenant's data **individually**, to provide support. NOT a merged cross-tenant view. NOT for practice staff — Avamed only. See §6. |

**Nothing is live.** All patient data in the system today is FAKE. Neither Churchtown nor St Marks
goes live until compliant, tested, and approved by the partners. This design must land before
either does — but there is no live patient data at risk while it is being built.

## 3. WHY SEPARATE DATABASES FIT THIS CODEBASE WELL

This is far less invasive than it sounds. Two facts make it cheap:

- **`dashboard/app/paths.py:7` already reads config from an environment variable**
  (`JEFFLOCAL_ROOT_DIR`). Env-var-driven config is an established pattern here, not a new idea.
- **`dashboard/app/db.py:9` funnels every database access through one `DB_PATH` constant**, and
  `connect()` (db.py:12) already accepts an optional path override.

So "point this instance at that tenant's database" is close to a two-line change. Everything else
is ops plumbing that the watchdog already knows how to do (it manages 4 services today).

**Auth isolates for free.** `staff_users` lives *inside* each tenant's database. St Marks staff
physically cannot log into Churchtown's instance — there is no account there to authenticate
against. No code enforces this; the topology does.

**This is the key advantage over a shared database with a `tenant_id` column.** In a shared design,
every one of the ~50 case queries must remember its `WHERE tenant_id = ?`, and a single forgotten
one is a cross-controller health-data breach. Here, a query that forgets its scoping simply cannot
reach another tenant's data — the data is not in the database it is connected to.

## 4. PROPOSED ARCHITECTURE

One uvicorn process per tenant. Each has its own port, own database, own users, own hostname.

```
TENANT      PORT   DATABASE                              HOSTNAME
churchtown  8765   dashboard/data/churchtown.sqlite      churchtown.app-avamed.uk
stmarks     8766   dashboard/data/stmarks.sqlite         stmarks.app-avamed.uk
(practice3) 8767   dashboard/data/practice3.sqlite       ...
```

**Code change (small):**
- `db.py`: `DB_PATH` reads `JEFFLOCAL_DB_PATH` env var, falling back to today's default so nothing
  breaks if unset.
- Per-tenant config file (`config/tenants/<tenant>.env`) holding `JEFFLOCAL_DB_PATH`, the port, and
  that tenant's secrets. **Loaded by the secrets loader built this session**
  (`scripts/service_control/_load_secrets.ps1`, branch `feature/secrets-loader`) — that work turns
  out to be the delivery vehicle for this.
- `_launch_dashboard.ps1` takes a `-Tenant <name>` parameter, loads that tenant's env file, starts
  uvicorn on that tenant's port.

**Ops change (the real work):**
- Watchdog: one entry per tenant instead of one dashboard entry.
- Cloudflare tunnel: one hostname per tenant.
- Backups (`scripts/backup/backup_db.py`): loop over tenant databases.
- GDPR 90-day purge: runs per database — which is a *bonus*, since each controller can then set its
  own retention rule rather than both inheriting one by accident.

**Ingest routing falls out naturally:**
- Churchtown: pipeline writes handoff JSON → that instance's importer → churchtown.sqlite. Unchanged.
- St Marks: the Worker already posts to a URL. Point it at `stmarks.app-avamed.uk` and its data
  lands in stmarks.sqlite. The `JEFF_INTAKE_URL` var for this already exists in the Worker.

## 5. MIGRATION OF EXISTING DATA

**All 78 existing cases are FAKE** — test data, no real patients (Saeed confirmed 2026-07-17;
neither business is live). So this migration carries no real-patient risk. It still needs care,
because losing the test corpus would cost the pipeline's regression evidence. All 78 are
Churchtown-side; **zero St Marks** (verified 2026-07-16 — its intake endpoint has never been live).

1. Full backup first (`scripts/backup/backup_db.py` exists and is scheduled daily at 02:15).
2. Copy `dashboard.sqlite` → `churchtown.sqlite`. All 78 cases, all 5 staff users, all audit history
   go with it. Nothing is deleted.
3. Create `stmarks.sqlite` empty, schema-initialised, with its own staff accounts.
4. Keep the original `dashboard.sqlite` untouched as a rollback point until churchtown is verified.

This is a **database migration on the production database** and therefore needs Saeed's explicit
approval on the day, separately from approving this design. The data is fake, but the database is
the live one the dashboard serves from.

## 6. AVAMED SUPER-ADMIN — SETTLED (Saeed, 2026-07-17)

**A tenant switcher. One tenant on screen at a time. Avamed only.**

Saeed clarified: the super-admin switches tenant on the dashboard and views each tenant's data
**individually**, in order to provide support. Practice staff never get this — Avamed only.

That is exactly the shape this design wants, so the "tension" flagged in the first draft of this
document does not exist. It was a misreading: "see across tenants" was taken to mean one merged
screen showing every tenant at once. It means *reach* any tenant, one at a time. Recorded here
because the earlier draft argued against a position Saeed never held.

**Design:**
- Avamed has an admin account **inside each tenant's database** (`staff_users` is per-tenant, so
  this is just a row in each).
- A picker page lists the tenants and links to each one's hostname. One click to enter.
- Full access once inside that tenant; **no screen ever joins two tenants' data**.
- Every Avamed login lands in *that tenant's own audit log* — so each controller can see exactly
  when their processor accessed their data. That is precisely what an Article 28 processor should
  be able to evidence, and it is a benefit of this shape, not a cost.
- Practice/pharmacy staff accounts are scoped to their own tenant and cannot switch.

**Explicitly NOT built:** any component holding connections to several tenant databases at once, or
any view that merges tenants. That would rebuild the single "can read everything" risk that
separate databases exist to remove, and would be the first thing a DPO or NHS assessor asks about.
If a genuine merged view is ever wanted (e.g. cross-practice reporting), it needs its own security
review and a much stronger justification than support convenience.

## 7. WHAT THIS DOES NOT SOLVE

- **`alert_events`, `audit_events`, `call_recordings` all carry patient data** (`first_patient` is a
  patient *name*; `old_values`/`new_values` hold full field contents). Under this design they are
  per-database and therefore isolated automatically — but this is worth stating explicitly, because
  under a shared-database design each of these would have needed its own scoping and each was an
  easy one to miss. The Operational Alert modal shipped 2026-07-16 renders `first_patient`; in a
  shared database it would have popped one controller's patient name onto another's screen.
- **Article 28 processor agreements** with each controller — a legal instrument, not code.
  [UNVERIFIED — in place with either controller?] Complicated by Avamed not yet being a registered
  company.
- **Memory/resource cost** of N uvicorn processes. Fine at 2–6 tenants; revisit if it grows.
- **Schema migrations must run N times.** Needs a migration runner that loops tenants. Worth
  building before tenant count grows.

## 8. PROPOSED SEQUENCE

Realistically **2–3 sessions**, not one. Each step ends green and deployable.

| # | Step | Gate |
|---|------|------|
| 1 | Merge the secrets loader (`feature/secrets-loader`) — it carries the per-tenant config | Security: APPROVE-WITH-CHANGES, strike the overclaims first + Saeed |
| 2 | `JEFFLOCAL_DB_PATH` env var + `-Tenant` launcher param; full suite green | Security review |
| 3 | Backup, then migrate `dashboard.sqlite` → `churchtown.sqlite`; verify | **Saeed, on the day** (production DB, though the data is fake) |
| 4 | Stand up the stmarks tenant instance + hostname + its staff accounts | Saeed |
| 5 | Tenant picker page + Avamed admin account per tenant (§6) | Saeed |
| 6 | Per-tenant backup + purge; migration runner (schema changes must run N times) | Security review |
| 7 | Only then: set `STMARKS_INTAKE_SECRET` on both sides | Saeed + pharmacist/DPO |
| 8 | Go-live of either tenant | Partners' compliance sign-off — separate from all of the above |

## 9. RECOMMENDATION

Approve §4 (architecture) and §8 (sequence). §6 is settled. Do not enable any tenant's intake flow
until step 7.

**No time pressure from live data.** Nothing is live and every patient record is fake, so this can
be built properly rather than rushed. The constraint is ordering, not the clock: multi-tenancy must
land before either business goes live, because retrofitting segregation after real patient data
exists is far harder than building it now.

---

*MULTI_TENANCY_PROPOSAL.md | v2 2026-07-17 | Status: §6 settled; architecture awaiting approval — nothing built*
*Supersedes "Item #4 / tenant_id / Phase 2" in PROJECT_MEMORY.md's backlog.*

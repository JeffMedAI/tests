# Tenant Registry

**ZERO patient data in this file, ever.** Config pointers only. Practice/pharmacy details and
patient data live inside each tenant's own database, never here. See MULTI_TENANCY_PROPOSAL.md §8.

---

## Naming convention (DECIDED by Saeed 2026-07-21)

Two separate things - do not conflate them:

- **Slug (internal ID):** `tenant1`, `tenant2`, ... - STABLE FOREVER. Used for the database
  filename, the `config/tenants/<slug>.env` file, the `-Tenant <slug>` launcher arg, and the
  watchdog service entry. **A slug never changes, not even at go-live.** This keeps the system
  internally consistent and avoids rename churn across DB files / hostnames / accounts.
- **Display name (human-facing):** the real practice/pharmacy name, e.g. "Churchtown Medical
  Centre", "St Marks Pharmacy". Stored as `JEFFLOCAL_TENANT_NAME` in the tenant's `.env` (and shown
  in the dashboard). Set/changed freely whenever the real name is known. Placeholder ("Tenant 2")
  until then.

Rationale: pure numeric names at scale become their own hazard ("which practice is tenant4?"),
dangerous in a patient-data system - so the display name carries the real name. But the slug stays
a stable number so nothing internal has to be renamed at go-live. Hostname is mapped per row
(hostname != slug).

---

## Registry

| Slug | Display name | Port | Database file | Hostname (target) | Status |
|------|--------------|------|---------------|-------------------|--------|
| _(default / legacy)_ | JeffLocal | 8765 | `dashboard/data/dashboard.sqlite` | `dashboard.app-avamed.uk` (live today) | LIVE-ish (fake data). The original single-instance production. Becomes slug `tenant1` at step 5. |
| `tenant1` _(planned, not yet wired)_ | Churchtown Medical Centre | 8765 | `dashboard/data/tenant1.sqlite` | `churchtown.app-avamed.uk` (not yet set) | PLANNED. `churchtown.sqlite` (an unused step-3 migrated copy) becomes `tenant1.sqlite` when step 5 wires up the first real tenant and repoints 8765. |
| `tenant2` | Tenant 2 _(placeholder - real name at go-live)_ | 8766 | `dashboard/data/tenants/tenant2.sqlite` | `tenant2.app-avamed.uk` (not set - localhost only) | LIVE on localhost:8766, watchdog-managed (2026-07-21). Placeholder identity; likely St Marks, not yet confirmed. |

## Notes

- **Today's reality (be precise):** the live dashboard on 8765 is still the ORIGINAL default
  instance serving `dashboard.sqlite` - it is NOT yet a named/numbered tenant. `churchtown.sqlite`
  is an unused migrated copy from step 3. The `tenant1` slug + Churchtown display name get applied
  when step 5 stands the first tenant up properly (Saeed's call 2026-07-21: defer the rename to step 5).
- Renaming `tenant2`'s DISPLAY name to a real business later is just editing `JEFFLOCAL_TENANT_NAME`
  in `config/tenants/tenant2.env` + adding a hostname - the SLUG `tenant2` and its DB filename stay put.
- No public hostname is configured for tenant2 this round (localhost:8766 only). Cloudflare hostname
  setup is a separate, Saeed-driven step.
- Every tenant's intake flow stays inert (no intake secret) until its own go-live sign-off.

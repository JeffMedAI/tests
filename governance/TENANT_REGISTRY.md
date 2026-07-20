# Tenant Registry

**ZERO patient data in this file, ever.** Config pointers only — name, target hostname,
port, database path, status. Practice/pharmacy details and patient data live inside each
tenant's own database, never here. See `governance/MULTI_TENANCY_PROPOSAL.md` §8.

| Tenant slug  | Display name | Hostname (target — not all live yet) | Port | Database path | Status |
|--------------|--------------|----------------------------------------|------|----------------|--------|
| `churchtown` | Churchtown Medical Centre | `churchtown.app-avamed.uk` (currently answers on `dashboard.app-avamed.uk` — rename not yet done) | 8765 | `dashboard/data/churchtown.sqlite` | Live-ish — real (fake) test data, not yet go-live approved |
| `tenant2`    | Tenant 2 (placeholder — real business name assigned at go-live) | `tenant2.app-avamed.uk` (not configured — localhost:8766 only for now) | 8766 | `dashboard/data/tenants/tenant2.sqlite` | Build/test only |

## Notes

- `tenant2` is a deliberately generic placeholder identity for this build phase.
  Renaming it to a real business name (e.g. when St Marks or another practice is ready to
  go live) means: rename this row, rename `config/tenants/tenant2.env` and its
  `JEFFLOCAL_TENANT_NAME`/`JEFFLOCAL_DB_PATH` values, add the real Cloudflare hostname, and
  update the `watchdog.ps1` service entry's name/comment — no other code should need to
  change.
- No public hostname is configured for `tenant2` in this round. That is a separate,
  Saeed-driven Cloudflare Zero Trust action for whenever this tenant is renamed and ready
  to go live.
- Every tenant's intake flow stays inert (no intake secret set) until its own go-live
  sign-off, independent of this registry.

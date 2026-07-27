# Step 5 Design Note — Tenant Picker + Roles + Naming Convention

**Project:** JeffLocal — Avamed
**Date:** 2026-07-22
**Author:** Backend Agent (Claude), built in worktree `feature/step5-tenant-picker-roles`
**Status:** DESIGN — written before implementation, per MULTI_TENANCY_PROPOSAL.md §8 step 5 process.
**Not built/run against production:** nothing here touches C:\JeffLocal's live checkout, dashboard.sqlite,
or churchtown.sqlite. All DB work is proven against throwaway copies in tests.

---

## 1. Role model — decision and reasoning

**Question the brief asked me to resolve:** does `tenant-admin` need to be a distinct role from
`admin`, or is `admin` already tenant-admin?

**Answer: `admin` already IS tenant-admin. No rename, no new role value for it.**

Evidence:
- MULTI_TENANCY_PROPOSAL.md §6b states this explicitly and was already decided by Saeed
  (2026-07-17): *"Tenant admin (practice manager) — Manages their own tenant's staff accounts.
  Today's `admin` role becomes this."*
- Structurally, `admin` is already scoped to one tenant, because `staff_users` lives inside that
  tenant's own database (separate-DB-per-tenant model, settled in step 1-4). There is no code path
  where an `admin` row can act on another tenant's data — the isolation is the database boundary,
  not a role check. Renaming the string to `"tenant-admin"` would not change any behaviour, would
  require a data migration across every existing tenant DB (churchtown's 5 rows, tenant2's 2 rows),
  and would touch every existing test/template that hardcodes `"admin"` — real risk for zero
  behavioural gain.

**Decision: keep the stored role value `"admin"`, document that it means "tenant admin" under this
architecture.** `STAFF_ROLES` (dashboard/app/consts.py:118, the *assignable-via-UI* set) is
unchanged: `{"admin", "staff", "readonly"}`.

## 2. `avamed-super-admin` — IS a new, distinct role

Unlike tenant-admin, this needs new behaviour that no existing role has: cross-tenant *reach* (via
the picker) while staying single-tenant *per session* (§6/§6b). It cannot be modelled as "admin
with a flag" because the picker must be gated to it specifically, and — this is the part I want to
flag clearly — **it must NOT be grantable through the ordinary staff-management UI.**

### The privilege-escalation risk I found and closed

`dashboard/app/routers/staff.py` validates role assignment against `STAFF_ROLES`
(dashboard/app/consts.py:118) in three places: `staff_create` (line 84), `staff_edit` (line 131),
and `staff_invitation_create` (line 220). All three are gated only by `require_staff_admin`, i.e.
any `admin`/tenant-admin can call them.

If I had simply added `"avamed-super-admin"` to `STAFF_ROLES`, any practice manager (tenant-admin)
could create an Avamed super-admin account **inside their own tenant's database**, via the normal
"Add staff" form — a full privilege escalation to Avamed's own support role, entirely inside a
single practice with no Avamed involvement. That defeats the entire point of the role.

**Fix:** `STAFF_ROLES` (assignable via the staff-management HTTP routes) stays exactly as it is
today. A new, separate constant `ALL_VALID_ROLES = STAFF_ROLES | {AVAMED_SUPER_ADMIN_ROLE}` exists
only for the DB CHECK constraint (a role value that can legitimately exist in the table) and for
permission checks (`staff_can_edit`/`staff_can_manage`/`is_avamed_super_admin`). It is never used
to validate an incoming role assignment from the staff UI. `avamed-super-admin` rows can only be
created by a provisioning script run outside the web app (`scripts/tenant/seed_super_admin.py`,
same trust model as `create_tenant_db.py`'s placeholder seeding) — never through `/staff/create`,
`/staff/{id}/edit`, or `/staff/invitations/create`.

### Permissions granted to avamed-super-admin (within the one tenant it's logged into)

Per §6: "Full access once inside that tenant." So:
- `staff_can_edit`: `{"admin", "staff", "avamed-super-admin"}` (can work cases)
- `staff_can_manage`: `{"admin", "avamed-super-admin"}` (can manage that tenant's staff — needed
  for support scenarios, e.g. unlocking a locked-out practice manager)
- New: `is_avamed_super_admin` / `require_avamed_super_admin` — gates the tenant picker page only.

## 3. Schema change — CHECK constraint migration

`dashboard/app/db.py` has `role TEXT NOT NULL CHECK(role IN ('admin', 'staff', 'readonly'))` on
both `staff_users` and `staff_invitations`. This is created with `CREATE TABLE IF NOT EXISTS`, so
existing tenant DBs (churchtown.sqlite, tenant2.sqlite, and any future ones) will silently keep the
OLD constraint even after `init_db()` is re-run — SQLite does not support widening a CHECK via
`ALTER TABLE`. Inserting a row with `role='avamed-super-admin'` into an unmigrated DB fails at the
SQLite layer with an `IntegrityError`, not at the app layer — this would have been a confusing
failure to debug in production if missed.

**Fix:** `init_db()` gained an idempotent migration step that runs on every call (matching the
existing additive-migration style used elsewhere in this function): it inspects
`sqlite_master.sql` for `staff_users` and `staff_invitations`; if the CHECK clause does not already
contain `avamed-super-admin`, it recreates the table (rename → create with the new CHECK → copy
rows across explicit column names → drop the renamed old table) and preserves all existing data
and IDs. Proven with a test that builds a DB under the OLD schema, calls `init_db()`, and asserts
old rows survive and new-role inserts now succeed.

**CORRECTION (2026-07-22, Security review — reproduced empirically, not just theorised):** my
original claim here was **wrong**. I wrote that the `sessions` foreign key (references
`staff_users(id)`) was "unaffected by the swap since the final table name and id values are
unchanged." That's false. On modern SQLite (`legacy_alter_table` OFF, the default since 3.25),
`ALTER TABLE staff_users RENAME` doesn't just rename the table — it also rewrites *other* tables'
foreign-key definitions that reference it. So `sessions.user_id` and `auth_reset_tokens.user_id`
(both FK → `staff_users`) got silently repointed at the temporary renamed table during the RENAME
step, which was then DROPped a few statements later — corrupting both FKs. Security proved this
with `PRAGMA foreign_key_check` and a session INSERT under `PRAGMA foreign_keys=ON`, which failed
with "no such table". I had reasoned about *data* (same table name, same row ids after the swap
completes) and missed that SQLite mutates *other tables' schema text* mid-RENAME — a different
mechanism entirely, and one my original test didn't check for (it only asserted a JOIN returned a
row, which passes even with a corrupted FK definition, since SQLite doesn't enforce FKs by default
unless `PRAGMA foreign_keys=ON` is set on that connection).

**Actual fix:** wrap the `RENAME` statement in `PRAGMA legacy_alter_table=ON` / restore-to-previous
afterwards — this disables SQLite's dependent-FK-rewrite behaviour for the duration of the rename,
so `sessions`/`auth_reset_tokens` keep pointing at plain `staff_users` once it's recreated under
that name. The whole per-table migration (rename → create → copy → drop) now also runs as one
explicit transaction (`BEGIN IMMEDIATE` / `COMMIT`, `ROLLBACK` on any exception) instead of relying
on sqlite3's implicit transaction handling, so an interruption mid-migration can't strand rows in
the renamed table. The regression test
(`test_sessions_fk_still_resolves_after_migration`) was hardened to actually assert the FK survives
— under `PRAGMA foreign_keys=ON`, insert a session and confirm it succeeds, and separately confirm
`PRAGMA foreign_key_check` returns no violations — rather than only checking a JOIN, which the
original version of the test did and which passed regardless of whether the FK definition itself
was intact.

This migration runs automatically the next time any tenant DB is opened via `connect()` +
`init_db()` (i.e. `ensure_ready()`, already called on every request) — no separate migration script
needed, consistent with how every other schema change in this file has been handled to date.

## 4. Avamed super-admin account seeding

**One identity per admin person, replicated as a row in every tenant DB** (there is no shared
cross-tenant table — same structural isolation as every other login, per the brief). Today that's
one person (Saeed).

New script: `scripts/tenant/seed_super_admin.py`, modelled directly on `create_tenant_db.py`'s
seeding pattern (calls `db_module.init_db()` first — which also runs the CHECK-constraint migration
above — then inserts via `auth_module.hash_password()`, audit-logs via `audit_module`).

**Design choices and why:**
- `--display-name`, `--username`, `--email` are **required CLI args, not hardcoded** — the script
  itself is committed to git, and hardcoding a real person's email into a committed script felt
  wrong even though it's Saeed's own account information already on file elsewhere. Whoever runs
  the script supplies it at run time, same pattern `create_tenant_db.py` already uses for tenant
  names.
- **UPDATED 2026-07-27 — Saeed's decision, matching Security's recommendation: a SEPARATE
  one-time password per tenant, not one shared across every target DB.** My original design here
  argued for one shared password on UX grounds (one person authenticating separately per tenant per
  §6b, so remembering one password felt like less friction than N). Security's counter, which Saeed
  accepted: the security cost outweighs that convenience — a single shared password means a leak or
  intercept of it exposes the super-admin row in *every* tenant DB at once, not just one. A separate
  `secrets.token_urlsafe(12)` call now runs per tenant, inside the loop (not before it), so each
  tenant's row gets its own distinct one-time password from the start. `must_change_password=1`
  still forces a real password to be set at first login to each instance, same as before — this
  only changes what the *initial* seeded credential looks like. The script's return value changed
  from `(password, {db_path: outcome})` to `{db_path: {"outcome": ..., "password": ...}}`, and the
  CLI output now prints each tenant's password labelled next to a slug (derived from the DB
  filename stem, e.g. `tenant2.sqlite` → `tenant2`) so they're never presented as interchangeable.
- Targets are passed as explicit `--db-path` args (repeatable) rather than the script scanning
  `config/tenants/*.env` itself — keeps the script pure/testable (no filesystem-scanning side
  effects to mock) and matches `migrate_to_tenant_db.py`'s style of explicit source/dest paths.
  The operator (Saeed/DevOps) is expected to pass every current tenant DB path; a future
  enhancement could read `config/registry.json` (see §6) to build this list automatically,
  intentionally left undone here to keep the script's blast radius reviewable.
- Reuses `create_tenant_db.py`'s audit pattern: `action="staff_created"`, `edited_by` set to a
  fixed marker string (`"super_admin_provisioning_script"`) so these rows are traceable in each
  tenant's own audit log — directly satisfies §6d's "every Avamed login lands in that tenant's own
  audit log" requirement, extended here to cover *provisioning*, not just login.

## 5. Tenant picker page

New router `dashboard/app/routers/tenants.py`, route `GET /tenants`, gated by
`require_avamed_super_admin` (403 for every other role, same HTTPException pattern as
`require_staff_admin`).

**What it renders:** a static list of tenant links — display name, a login link (hostname if set,
else `http://localhost:<port>` for today's pre-hostname reality), and status. **Nothing else.** No
case counts, no patient data, no per-tenant metrics — per §6/§6b this page's whole job is to be a
link list, never a merged data view. It reads from a new **machine-readable** config file,
`config/registry.json` (see §6) — it does not connect to any tenant database to build the
list, so there is no code path here that could accidentally hold two tenant DB connections open at
once (the exact component §6 forbids).

**Known duplication I'm flagging, not solving:** `governance/TENANT_REGISTRY.md` (human-readable,
existing) and `config/registry.json` (new, machine-readable) now both describe the tenant
list, and nothing keeps them in sync automatically. I judged writing a markdown parser to derive
one from the other to be more fragile than it's worth for 2-3 tenants. Whoever runs tenant
onboarding scripts in future must update both. Worth automating if the tenant count grows past a
handful — noted as follow-up, not fixed here.

## 6. `config/registry.json` — new file

Pure config, matches TENANT_REGISTRY.md's naming convention (slug is stable, display_name is
human-facing). Zero patient data, per the existing rule for this directory. Contains slug,
display_name, hostname (nullable — not all tenants have one yet), port, status. This is what the
picker page reads.

**RELOCATED 2026-07-27 — this file was originally designed to live at `config/tenants/registry.json`,
inside the same folder as the per-tenant `.env` files.** That was a mistake I only found out about
at merge time, not at design time: `config/tenants/` was deliberately ACL-locked in an *earlier* and
*separate* piece of work (Saeed's step-4 fix, `scripts/service_control/fix_tenant_config_acl.ps1` —
see PROJECT_MEMORY.md's step-4 history), which strips ordinary-user write access from that folder so
only admin-elevated processes can touch it. That lockdown is correct and intentional for the `.env`
files it protects (they hold real per-tenant config, written by elevated onboarding scripts). It was
never designed with this file in mind, because this file didn't exist yet — `registry.json` is the
first thing step 5 needed to write into `config/` at all, and it's read by the live dashboard process
at request time, not written by an elevated admin script. A normal `git merge` running as an ordinary
user therefore could not create it inside `config/tenants/` — confirmed as a real Permission Denied at
merge time, not a merge-state artefact. **Fix: moved to `config/registry.json` — one level up, out of
the locked subfolder.** `config/` itself carries no such restriction; only `config/tenants/` does. No
other design or behaviour changed — this is a location fix, not a scope or logic change. See
`dashboard/app/routers/tenants.py`'s `REGISTRY_PATH` comment for the same note at the code level.

## 7. Churchtown → `tenant1` naming/repoint script

New script: `scripts/tenant/rename_tenant_slug.py`. Scope, per TENANT_REGISTRY.md's already-decided
convention: `churchtown.sqlite` (the unused step-3 migrated copy, already verified 78
cases/5 staff_users/1251 audit_events/integrity OK) becomes the tenant1 slug's database, and the
live 8765 instance repoints from `dashboard.sqlite` onto it.

**This script takes source/dest paths as parameters — never hardcodes `C:\JeffLocal`'s real
production paths as the only option** — so it can be proven against throwaway copies in tests
(the brief is explicit: prove the repoint script works against a throwaway copy, not the real
file). It has a `--dry-run` mode (reports what it would do, touches nothing) and an apply mode.

**What it does (apply mode):**
1. Refuses to run if dest already exists, unless `--force` (same guard as `migrate_to_tenant_db.py`).
2. Copies source DB (churchtown.sqlite) → dest path (tenant1.sqlite) using the same
   `sqlite3.Connection.backup()` approach as `migrate_to_tenant_db.py` (safe against a live writer).
3. Verifies row counts + `PRAGMA integrity_check` on both sides (reuses
   `migrate_to_tenant_db.verify_migration`, same `VERIFY_TABLES` list, rather than
   reimplementing it).
4. Writes `config/tenants/tenant1.env` (`JEFFLOCAL_TENANT_NAME=Churchtown Medical Centre`,
   `JEFFLOCAL_DB_PATH=<dest>`, `JEFFLOCAL_PORT=8765`) — same format as `tenant2.env`.
5. Does **not** touch `dashboard.sqlite`, does **not** restart or repoint the live watchdog/uvicorn
   process, does **not** delete anything. The actual cutover (pointing the running 8765 process at
   the new tenant1 config and restarting the service) is an ops action explicitly left for
   DevOps/Saeed to run deliberately, the same way step 4's `apply_tenant2_ops.ps1` was a
   reviewable script that Saeed ran himself in an elevated session — this script only prepares the
   database and config file, it is not itself the cutover.

**What I did NOT do:** run this script against the real `C:\JeffLocal\dashboard\data\churchtown.sqlite`
or touch the live `dashboard.sqlite`. Tests exercise it exclusively against `tmp_path` copies.

## 8. Access matrix — before / after

| Route | Before (this session) | After | Notes |
|---|---|---|---|
| `/case/*`, `/api/cases/*` writes | `staff_can_edit`: admin, staff | admin, staff, avamed-super-admin | avamed-super-admin can work cases while logged into a tenant |
| `/staff/create`, `/staff/{id}/edit`, `/staff/{id}/(de)activate`, `/staff/invitations/*` | `staff_can_manage`: admin only | admin, avamed-super-admin | avamed-super-admin can support a locked-out practice |
| `/staff/create` etc. **assignable role values** | `{admin, staff, readonly}` | **unchanged** — `{admin, staff, readonly}` | deliberate: avamed-super-admin is never grantable via this UI (see §2) |
| `/tenants` (new) | did not exist | avamed-super-admin only, 403 for everyone else | new picker page |
| `/staff` page (view) | any logged-in user, no role gate (pre-existing) | unchanged | flagged as a pre-existing gap, not introduced by this work, not in scope to fix here — readonly staff can currently view (not edit) the staff list |
| Login itself | any row in `staff_users`/`sessions` regardless of role value | unchanged | `auth.py`/`get_session_user` never inspected role; only the CHECK constraint blocked new role values before §3's migration |

## 9. What is explicitly out of scope for this step (left for later phases)

- Adding a "Tenants" link to the nav (`base.html`) — templates/UX polish is Frontend Agent's
  domain; the route works via direct URL, nav wiring left for a follow-up so this stays reviewable
  as a backend change.
- Per-tenant branded login pages (STAFF_ACCESS_MODEL.md) — separate, later piece of work, needs the
  real hostnames first.
- Cloudflare hostname setup for tenant1/tenant2 — Saeed-driven, deferred per existing notes.
- Actually executing the churchtown→tenant1 repoint against production, or restarting the live
  8765 service onto the new config — script is built and tested against throwaway copies only.
- Security review and Saeed approval — next phase, not done by this agent.

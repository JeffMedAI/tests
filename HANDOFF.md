# HANDOFF - Avamed (JeffLocal)

> **What this file is:** the single, always-current handoff note for the project.
> It holds **only the most recent session's** handoff - not a history.
> Read it at session start, right after PROJECT_MEMORY.md (see SESSION START PROTOCOL).
> Rewrite it in full at session end. If it disagrees with PROJECT_MEMORY.md on *state*,
> PROJECT_MEMORY.md wins; this file is the plain-English "where we left off" story.
>
> **Rolling latest-only:** overwrite the whole file each close. Do NOT append. Keep it short.

---

**Last session:** 2026-07-21 (long session, spanned 07-20 evening into the 21st)
**Closed by:** Claude (Sonnet 5)
**Branch:** main. C:\JeffLocal IS the production directory, checked out on main.
**Latest commit:** 513ce36 (docs: tenant naming convention). Local == origin/main, pushed.
**Restore tag:** restore/2026-07-21-1343 (a fresh one is created at this close).
**Production:** dashboard.app-avamed.uk (tunnel -> localhost:8765). case_count 78, healthy, untouched
all session. A SECOND instance (tenant2) now also runs on localhost:8766, watchdog-managed.

> **NOTHING IS LIVE. ALL PATIENT DATA IS FAKE.** No tenant goes live until compliant, tested, and
> partner-approved. Blockers below are pre-go-live debt, not active incidents.

---

## WORK SCOPE

Multi-tenancy step 4: stand up a second tenant instance (own DB, port, logins). DONE and verified
live. Next up: step 5.

## WHAT WORKED / WHAT DIDN'T

**Worked:**
- **Plan mode + explore/plan subagents, worktree isolation, TDD, Security review** - same disciplined
  loop as steps 1-3. Security review (APPROVE) added 2 real polish items. Full LIVE browser E2E before
  claiming done, not tests alone.
- **Verifying each admin-script run independently** (Get-ScheduledTask, icacls, /api/health, watchdog
  log) instead of trusting the screenshot - caught that "it printed success" hid three real problems.

**Didn't work / gotchas - READ THESE (all cost a round-trip this session):**
- **PowerShell SWITCH params need the colon form for a value:** `-Switch:$false`, never `-Switch $false`
  (space form throws "positional parameter ... 'False'"). Bit register_scheduled_tasks.ps1.
- **`icacls /remove:g` only strips EXPLICIT ACEs, not INHERITED ones.** config\tenants (and C:\JeffLocal,
  config) inherit `Authenticated Users:Modify` from the C:\ drive root, so the 07-20 fix never cleared
  it. To remove an inherited ACE you must break inheritance (`icacls <dir> /inheritance:d`) first.
- **The watchdog survives a naive restart.** Stop/Start-ScheduledTask left a days-old elevated
  watchdog.ps1 running OLD in-memory code. Must force-kill lingering watchdog.ps1 processes by PID.
- **The dashboard's ONLY write access to its DB/logs is via that broad `Authenticated Users:Modify`
  grant** (the app runs as a normal user; BUILTIN\Users is read-only). So you CANNOT strip Authenticated
  Users tree-wide without first granting the service account explicit write - it would break production.
- **.ps1 files here must be plain ASCII** - PowerShell 5.1 mangles em-dashes/smart quotes into a bogus
  "missing string terminator".
- Stale `.git/index.lock` recurs (0-byte, no git running) - remove it if a merge/stash dies.
- Run dashboard tests with cwd=C:\JeffLocal\dashboard; scripts/ tests from repo root. Pass `--basetemp=`.

## HOW THE SESSION CLOSED

- **Step 4 DONE + verified live:** tenant2 on 8766 (own isolated DB, case_count 0), watchdog-managed
  ("Tenant 2 Dashboard OK" in the log); churchtown 8765 unchanged at 78 throughout.
- Along the way fixed 3 real bugs (scheduled-task switch syntax + found GDPR purge was never scheduled;
  watchdog orphan; config\tenants inherited ACL) and flagged the 07-20 ACL fix as incomplete.
- Two design decisions recorded + pushed: staff access model (STAFF_ACCESS_MODEL.md) and tenant naming
  convention (TENANT_REGISTRY.md).
- Everything committed and pushed to main. Memory files + restore tag updated.

## NEXT + BLOCKERS

**NEXT: START STEP 5** (governance/MULTI_TENANCY_PROPOSAL.md §8 step 5). Brainstorm/plan first, then
build in a worktree, TDD, Security review, Saeed approval - same loop as step 4. Step 5 scope:
1. **Tenant picker page + Avamed super-admin account per tenant.** Picker = LINKS to each tenant's own
   hostname/login, never a screen that merges tenant data (per §6/6b). Avamed admin has an account
   inside each tenant DB.
2. **Roles:** add `tenant-admin` (practice manager, manages own tenant's staff) and `avamed-super-admin`
   - these were deliberately kept OUT of step 4 (code still only has admin/staff/readonly at consts.py:118).
3. **Apply the naming convention:** rename churchtown -> slug `tenant1` (display "Churchtown Medical
   Centre"), stand it up as a proper tenant, and repoint 8765 off the default `dashboard.sqlite`.
   (Today 8765 is still the original default instance; churchtown.sqlite is an unused step-3 copy.)

**Blockers needing Saeed (none block starting step 5):**
1. Broader C:\JeffLocal + config ACL fix - 07-20 fix incomplete (AU write via inheritance). Careful
   redesign needed (explicit service-account write grant first). Own task.
2. Cloudflare hostnames (tenant2 public hostname; churchtown hostname). Deferred; wants guidance when ready.
3. Replace placeholder logins (tenant2 admin/staff + churchtown's 5) with real names/emails before go-live.
4. Standing items: unauth intake endpoint (/api/n8n/test-intake-batch), HMAC secret rotation, gates 1-7.
5. Orphan SID `S-1-5-21-...-2510526684` still has write on config\tenants (didn't block anything; folds
   into the broader ACL fix).

**Durable gotchas (carried forward, still true):**
- PRODUCTION is C:\JeffLocal\dashboard\ (8765) but the git branch of C:\JeffLocal decides what runs.
- Never switch C:\JeffLocal's own branch for WIP - use a worktree.
- LLM output must NEVER set verification_status, safe_to_queue, priority, or identity fields.
- Session cookies expire after 1 hour.
- Windows security/ACL/scheduled-task changes are run by Saeed in admin PowerShell, not by Claude.
- Tenant model: each tenant = own DB + own staff_users (login isolated structurally) + own instance/port;
  SAME shared codebase. Slug = stable tenantN; display name = real practice name. Avamed super-admin
  reaches any tenant one at a time via LINKS, never a merged view.
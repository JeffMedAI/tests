# HANDOFF - Avamed (JeffLocal)

> **What this file is:** the single, always-current handoff note for the project.
> It holds **only the most recent session's** handoff - not a history.
> Read it at session start, right after PROJECT_MEMORY.md (see SESSION START PROTOCOL).
> Rewrite it in full at session end. If it disagrees with PROJECT_MEMORY.md on *state*,
> PROJECT_MEMORY.md wins; this file is the plain-English "where we left off" story.
>
> **Rolling latest-only:** overwrite the whole file each close. Do NOT append. Keep it short.

---

**Last session:** 2026-07-28 (long session, ran via /loop, spanned usage-limit resets)
**Closed by:** Claude (Sonnet 5, then Opus 4.8 for the merge/cutover)
**Branch:** main. C:\JeffLocal IS the production directory, checked out on main.
**Latest commit:** addd6e0 (step5 cutover: security robustness fixes). Local == origin/main, pushed.
**Restore tag:** restore/2026-07-28-1108 (created at this close).
**Production:** dashboard.app-avamed.uk (tunnel -> localhost:8765). NOW serves tenant1 (Churchtown's
78 cases). tenant2 on localhost:8766 (case_count 0), untouched. Both healthy, watchdog-managed.

> **NOTHING IS LIVE. ALL PATIENT DATA IS FAKE.** No tenant goes live until compliant, tested, and
> partner-approved. Blockers below are pre-go-live debt, not active incidents.

---

## WORK SCOPE

Multi-tenancy step 5: tenant picker page + avamed-super-admin role + apply the tenant1 naming
convention to Churchtown and repoint 8765 onto its own database. DONE, merged, cutover run by Saeed,
verified live. This was the last step in the multi-tenancy sequence (§8).

## WHAT WORKED / WHAT DIDN'T

**Worked:**
- Same disciplined loop as steps 1-4: worktree isolation, design note first, TDD, Security review
  before merge, live verification after. TWO security rounds here (code, then cutover tooling) — both
  caught real things.
- Reading the cutover scripts IN FULL before running them against real data — surfaced that the .env
  write lands in the ACL-locked config\tenants dir (needs elevation) BEFORE trying it.
- Checking the full branch diff before merge — caught 199k lines of accidental graphify/junk cruft.
  Merged selective files only (byte-identical to reviewed tip) instead of the polluted branch.
- The Test-Path guard on the watchdog repoint = zero pre-cutover risk (8765 stays on default until
  tenant1.env exists).

**Didn't work / gotchas - READ THESE:**
- **First merge attempt hit Permission Denied** creating config/tenants/registry.json — that dir is
  Saeed's step-4 ACL lockdown (Users read-only). Fix: relocated registry.json to config/ (outside the
  lock). Lesson: anything that WRITES a new file into config\tenants needs elevation; keep app-read
  config out of that locked subfolder.
- **The physical cutover needs elevation Claude doesn't have** (locked-dir env write + elevated
  watchdog restart). Same handoff as step 4: Claude builds the reviewable apply script, Saeed runs it
  elevated. Do NOT try to run it from a normal session.
- **Evening-brief automation (19:00) collides on the git lock mid-session** — left stale .git/index.lock
  AND .git/HEAD.lock (0-byte, old timestamp, no git process). Same as documented rule #12. Remove the
  stale lock(s), re-commit. Don't delete a ref lock if a real git process IS running — check ps first.
- **Usage limits hit twice** — background agents just resume from transcript via SendMessage, no work
  lost. Don't restart from scratch.
- **.ps1 must be plain ASCII** (PS 5.1). New cutover script is ASCII-clean; watchdog.ps1 has
  pre-existing non-ASCII in comments elsewhere (parses fine, left alone).

## HOW THE SESSION CLOSED

- Step 5 DONE + verified live. 8765 serves tenant1 (churchtown 78 cases) via its own DB; 8766
  untouched; /tenants picker gated; avamed-saeed super-admin seeded in both tenants.
- Shipped to main: 82b7ba2 (code), d368529 (cutover tooling), addd6e0 (security fixes). 482 tests green.
- Saeed ran apply_step5_cutover.ps1 elevated; Claude verified the result live.
- Memory files + session log + restore tag updated.

## NEXT + BLOCKERS

**NEXT (none blocking):**
1. Saeed can log into /tenants as avamed-saeed with his OTP to visually confirm per-tenant isolation
   (Claude won't enter passwords; isolation is structurally guaranteed + tested regardless).
2. Cloudflare hostnames (tenant2 public; churchtown -> churchtown.app-avamed.uk). Saeed wants guidance.
3. Replace placeholder logins with real staff names/emails before go-live.
4. Cosmetic: registry.json tenant1 status still "planned" though now running.

**Standing pre-go-live debt (not blocking, all data fake):**
- Unauth intake endpoint (/api/n8n/test-intake-batch), HMAC secret rotation, gates 1-7.
- Broader C:\JeffLocal + config ACL fix - 07-20 fix incomplete (Authenticated Users write via
  inheritance). Careful redesign needed (grant service account explicit write first). Own task.
- Orphan SID still has write on config\tenants (doesn't block anything; folds into the broader ACL fix).

**Durable gotchas (carried forward, still true):**
- PRODUCTION is C:\JeffLocal\dashboard\ (8765) but the git branch of C:\JeffLocal decides what runs.
- Never switch C:\JeffLocal's own branch for WIP - use a worktree.
- LLM output must NEVER set verification_status, safe_to_queue, priority, or identity fields.
- Windows security/ACL/scheduled-task/watchdog changes are run by Saeed in admin PowerShell, not Claude.
- Session cookies expire after 1 hour.
- Tenant model: each tenant = own DB + own staff_users + own instance/port; SAME shared codebase.
  Slug = stable tenantN; display name = real practice name. avamed-super-admin reaches any tenant one
  at a time via the /tenants picker (LINKS), never a merged view.
- The 19:00 evening-brief automation can commit to main mid-session and leave stale git locks.

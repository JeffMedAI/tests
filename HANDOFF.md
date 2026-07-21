# HANDOFF - Avamed (JeffLocal)

> **What this file is:** the single, always-current handoff note for the project.
> It holds **only the most recent session's** handoff - not a history.
> Read it at session start, right after PROJECT_MEMORY.md (see SESSION START PROTOCOL).
> Rewrite it in full at session end (SESSION END PROTOCOL step 2). If it disagrees with
> PROJECT_MEMORY.md on *state*, PROJECT_MEMORY.md wins; this file is the plain-English
> "where we left off" story so the next agent knows what to repeat and what to avoid.
>
> **Rolling latest-only:** overwrite the whole file each close. Do NOT append. Keep it short.

---

**Last session:** 2026-07-21 (work spanned 2026-07-20 evening into the 21st)
**Closed by:** Claude (Sonnet 5)
**Branch:** main. C:\JeffLocal IS the production directory, checked out on main.
**Latest commit:** 037dd63 (chore: add apply_tenant2_ops.ps1). Local == origin/main, pushed.
**Production:** dashboard.app-avamed.uk (tunnel -> localhost:8765). Health-checked repeatedly
throughout the session including after the merge - still up, case_count 78, untouched.

> **NOTHING IS LIVE. ALL PATIENT DATA IS FAKE.** Neither Churchtown nor "Tenant 2" goes live until
> compliant, tested, and approved by the partners. Read blockers below as pre-go-live debt, not
> active incidents.

---

## WORK SCOPE

Multi-tenancy step 4 (governance/MULTI_TENANCY_PROPOSAL.md §8): stand up a SECOND tenant instance
with its own database, port, and staff logins. Saeed's steer: use a generic placeholder identity
("Tenant 2"), not a real business name, until a tenant is actually ready to go live; seed BOTH a
placeholder admin AND a placeholder staff login per tenant; localhost:8766 only, no Cloudflare
this round. Built, tested, merged, pushed. One elevated step left for Saeed to run.

## WHAT WORKED / WHAT DIDN'T

**Worked:**
- **Plan mode + explore/plan subagents before building.** 3 Explore agents mapped the codebase
  (config scaffolding / ops plumbing / staff bootstrap) and a Plan agent designed the sequence
  before a line was written. Caught the real shape early: db.py's demo-seed was a bug, not just an
  inconvenience, and the ops scripts were single-tenant-hardcoded.
- **Worktree isolation again (C:\JeffLocal_tenant2).** All WIP on a feature branch in a separate
  worktree; C:\JeffLocal's own branch never switched. Cleaned up (worktree + branch removed) right
  after merge.
- **TDD caught the shape; Security review caught polish.** Wrote failing tests first for the db.py
  fix and create_tenant_db.py. Security Agent (APPROVE) added 2 optional improvements that were
  worth applying: seed pin_hash=NULL rather than a discarded non-numeric PIN, and write audit
  events for script-seeded accounts. Fourth time across steps 1-4 that Security added real value.
- **Live E2E before claiming done.** Actually launched tenant2 on 8766, logged in as BOTH
  placeholder accounts via the browser, confirmed forced password-change, confirmed case-list and
  audit-log isolation from churchtown, and health-checked churchtown (78) before/during/after. Did
  not trust the tests alone.

**Didn't work / gotchas - READ THESE:**
- **_launch_dashboard.ps1 hardcodes $python/$workDir to C:\JeffLocal\dashboard** regardless of which
  checkout runs it. So launching it FROM a worktree would start PRODUCTION's code, not your WIP. To
  test worktree code, launch uvicorn directly with explicit JEFFLOCAL_DB_PATH / JEFFLOCAL_TENANT_NAME
  env vars (that's what I did). Not a bug for step 4 - watchdog only ever runs it against production.
- **Stale .git/index.lock blocked the merge** ("could not write index / stash failed"). Recurring
  repo issue - there's fix_git_lock.ps1 for it. No git process was running; removed the 0-byte lock
  and the merge went through. Check for this if a git op dies with a lock/stash error.
- **PowerShell 5.1 mangles em-dashes.** First write of apply_tenant2_ops.ps1 used "-" em-dashes;
  PS 5.1 read the UTF-8 bytes wrong and the parser reported a bogus "missing string terminator".
  Rewrote ASCII-only. For any .ps1 in this repo meant to run under Windows PowerShell, stick to
  plain ASCII punctuation. (Same mojibake family as the brief-title bug fixed 07-17.)
- **Two auto-mode classifier denials mid-session** (the watchdog.ps1 edit, and one git push). The
  watchdog one correctly matched my own plan's "pause for Saeed" gate; the push denial was flagged
  transient and succeeded on retry. Expect these on sensitive ops - retry / get explicit OK.
- **Running the dashboard test suite from repo root fails** (conftest can't import `app.helpers`).
  Run dashboard tests with cwd=C:\JeffLocal\dashboard; run scripts/ tests from repo root.
- **Fresh worktree lacks outputs/handoff_json/** - 2 health tests fail until you `mkdir` it. Not a
  code failure.

## HOW THE SESSION CLOSED

- Step 4 merged to main (85815a1) and pushed. Worktree + feature branch removed.
- Real tenant2.sqlite created in production data path (2 placeholder logins, case_count 0, integrity ok).
- CHANGELOG.md entry written. apply_tenant2_ops.ps1 written, ASCII-clean, committed + pushed (037dd63).
- Full verification re-run at close: git clean + pushed, churchtown 78, 19 targeted tests green on
  top of the earlier 393-test post-merge run.
- Session log, this file, PROJECT_MEMORY.md updated. Restore tag pushed.

## NEXT + BLOCKERS

**Next action, in order:**
1. **Saeed RE-runs `C:\JeffLocal\scripts\service_control\apply_tenant2_ops.ps1` in an ADMIN PowerShell.**
   First run (2026-07-21) hit a bug in register_scheduled_tasks.ps1 (`-RunOnlyIfNetworkAvailable $false`
   — a switch param needs the colon form). FIXED (commit f88edef) and pushed. Re-run to finish:
   registers BOTH GDPR-purge tasks + restarts the watchdog so it manages tenant2 on 8766. Non-elevated
   sessions get "Access denied". After it runs, `Get-ScheduledTask -TaskPath \JeffLocal\` should show
   `JeffLocal - GDPR Weekly Purge`, `... (tenant2)`, and the watchdog; churchtown (8765) still 78,
   tenant2 (8766) case_count 0.
   **COMPLIANCE NOTE:** that switch bug meant `JeffLocal - GDPR Weekly Purge` was NEVER registered at
   all — churchtown's 90-day purge is currently unscheduled (pre-go-live debt, all data fake). The
   re-run fixes it; confirm it lands.
2. After that: confirm tenant2 (8766) is watchdog-managed (case_count 0) and churchtown (8765) still 78.
3. Step 5 (§8): tenant picker page + Avamed super-admin account per tenant. The tenant-admin /
   avamed-super-admin ROLE rename lives here, deliberately kept OUT of step 4.

**Blockers needing Saeed (all pre-go-live debt, none an active incident):**
1. apply_tenant2_ops.ps1 - needs elevation (above). Only remaining step-4 item.
2. Cloudflare hostname for tenant2 + churchtown rename (dashboard -> churchtown.app-avamed.uk) -
   deferred by Saeed; wants Claude's guidance when ready.
3. Replace ALL placeholder logins (tenant2's 2 + churchtown's existing 5) with real named
   people/emails before go-live.
4. Standing items unchanged: unauth intake endpoint (/api/n8n/test-intake-batch), HMAC secret
   rotation, governance gates 1-7.

**Durable gotchas (carried forward, still true):**
- PRODUCTION is C:\JeffLocal\dashboard\ (8765) but the git branch of C:\JeffLocal decides what runs.
  Check it every session.
- Never switch C:\JeffLocal's own branch for WIP - use a worktree.
- LLM output must NEVER set verification_status, safe_to_queue, priority, or identity fields.
- Session cookies expire after 1 hour.
- .ps1 files here must be plain ASCII - PowerShell 5.1 mangles em-dashes / smart quotes.
- PowerShell SWITCH params take the colon form for a value: `-Switch:$false`, never `-Switch $false`
  (the space form passes $false as a stray positional arg and throws). Bit register_scheduled_tasks.ps1.
- Windows security/ACL/scheduled-task changes are run by Saeed in admin PowerShell, not by Claude.
- Stale .git/index.lock recurs - remove the 0-byte lock (no git running) if a merge/stash dies.
- pytest: pass --basetemp to somewhere writable; default temp folder can be permission-locked here.
- Before assuming table/column names in a real DB, check the real schema first.

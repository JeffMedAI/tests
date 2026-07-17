# HANDOFF — Avamed (JeffLocal)

> **What this file is:** the single, always-current handoff note for the project.
> It holds **only the most recent session's** handoff — not a history.
> Read it at session start, right after PROJECT_MEMORY.md (see SESSION START PROTOCOL).
> Rewrite it in full at session end (SESSION END PROTOCOL step 2). If it disagrees with
> PROJECT_MEMORY.md on *state*, PROJECT_MEMORY.md wins; this file is the plain-English
> "where we left off" story so the next agent knows what to repeat and what to avoid.
>
> **Rolling latest-only:** overwrite the whole file each close. Do NOT append. Keep it short.

---

**Last session:** 2026-07-17 (evening, continued)
**Closed by:** Claude (Sonnet 5)
**Branch:** main. C:\JeffLocal IS the production directory, checked out on main.
**Latest commit:** 5413466 (memory: multi-tenancy step 3 done — churchtown.sqlite created and verified)
**Production:** dashboard.app-avamed.uk (tunnel → localhost:8765). Health-checked after this
session's DB migration work — still up, still shows 78 cases, untouched. Dashboard process itself
was not restarted this session (no code path it serves changed).

> **NOTHING IS LIVE. ALL PATIENT DATA IS FAKE.** Neither Churchtown nor St Marks goes live until
> compliant, tested, and approved by the partners. Read blockers below as pre-go-live debt, not
> active incidents.

---

## WORK SCOPE

Started as: fewer-permission-prompts cleanup + write up (not run) the folder-permission fix +
multi-tenancy step 3. All three done. Also updated CLAUDE.md per Saeed's direct instruction
(honesty rule, confidence tags, always-on caveman/superpowers, fourth-grade plain English).

## WHAT WORKED / WHAT DIDN'T

**Worked:**
- **Security review caught a real bug again, before merge — third time this happened across
  steps 1/2/3.** The DB migration script had no check stopping source and dest from being the
  same file. With `force=True` (a flag the script itself supports) that would have deleted the
  live database. Fixed before merge, not after. Keep sending new scripts through Security even
  when they feel "small and obviously safe."
- **TDD caught nothing itself this time, but running against REAL data did.** The 15 tests all
  passed against synthetic tables, but the script's assumed table names (`staff`, `audit_log`)
  were wrong for the real schema (`staff_users`, `audit_events`). Lesson: synthetic-fixture tests
  can't catch a wrong assumption baked into both the fixture AND the code — only a real dry-run
  against real data can. The actual file copy was never at risk (SQLite's backup API copies the
  whole file regardless of table names) — only the "did it work" verification step crashed. Worth
  remembering: a crash in verification is not the same as a crash in the operation itself — check
  which one actually failed before panicking.
- Worktree pattern again for the script build (`C:\JeffLocal_dbmigrate`), never touched
  C:\JeffLocal's own branch for WIP. Cleaned up (worktree + branch removed) immediately after merge
  this time, no stragglers left behind.
- Refusing to run the folder-permission (ACL) fix myself, even with Saeed's "write for later" and
  earlier "go ahead" — that's a Windows security-settings change, outside what gets executed
  directly. Wrote the exact commands to a script file instead, for Saeed/an admin to run by hand.

**Didn't work / gotchas — READ THESE:**
- **Don't assume table names — check the real schema first.** Would have saved one crash-and-fix
  cycle. `SELECT name FROM sqlite_master WHERE type='table'` takes two seconds; guessing from
  memory of "cases/staff/audit_log"-style naming from other projects doesn't hold up.
- **pytest's temp folder was locked (`PermissionError` on `AppData\Local\Temp\pytest-of-s5256`)** —
  unrelated to this session's code, looks environmental (possibly related to the same
  overly-open/locked-down folder mess as open item #3, not confirmed). Workaround: always pass
  `--basetemp=<somewhere in the scratchpad>` when running pytest on this machine until the root
  cause is found.
- **Fresh worktrees have no `.venv`.** Running the full 391-test dashboard suite needs
  `dashboard\.venv\Scripts\python.exe`, which only exists in the real `C:\JeffLocal` tree (gitignored,
  not copied into worktrees). For an isolated new script with zero coupling to `app/` modules,
  running just its own test file is enough — don't force a full-suite run that can't actually work
  in a bare worktree.
- `.pyc` files under `tests/__pycache__/` get touched by running pytest in a worktree — `git
  checkout --` them before committing, same as previous sessions.

## HOW THE SESSION CLOSED

- Merged and pushed: `feature/multitenancy-db-migrate` (migration script, Security APPROVE WITH
  CHANGES, fix applied pre-merge) + a same-day post-merge fix (wrong table names, non-security).
- Real migration run against production, Saeed-approved on the day: `churchtown.sqlite` created,
  verified matching (78 cases / 5 staff_users / 1,251 audit_events, integrity OK both sides).
  `dashboard.sqlite` untouched. Live dashboard NOT yet repointed at the new database.
- `.claude/settings.json` updated with a short read-only permission allowlist (fewer-permission-prompts run).
- `scripts/service_control/fix_directory_acl.ps1` written, not run — Saeed to run manually, and
  asked to be reminded.
- CLAUDE.md updated per Saeed's direct instruction — see next session's read of it for full detail.
- CHANGELOG.md, PROJECT_MEMORY.md, this file, and today's session log all written/updated and
  committed.

## NEXT + BLOCKERS

**Next action, in order:**
1. **REMINDER for Saeed:** run `scripts/service_control/fix_directory_acl.ps1` (admin PowerShell) —
   fixes the folder-permission issue blocking tenant onboarding. Carry this reminder forward every
   session until it's done.
2. Step 4 (governance/MULTI_TENANCY_PROPOSAL.md §8): stand up the St Marks tenant instance,
   hostname, and staff accounts. Still blocked by item 1 above.
3. Steps 5-8 unstarted: tenant picker UI + Avamed admin accounts, per-tenant backup/purge +
   migration runner, `STMARKS_INTAKE_SECRET`, go-live sign-off.

**Blockers needing Saeed (priority order) — all pre-go-live debt, none an active incident:**
1. **Folder-permission fix — script written, waiting on Saeed to run it (admin PowerShell).**
   `scripts\service_control\fix_directory_acl.ps1`. Blocks step 4 the same way it blocked step 3
   setup.
2. Real staff accounts (names, roles, emails) — still open, blocks pilot go-live.
3. Governance gates 1-7 — still open, cannot be delegated.
4. `JEFF_WEBHOOK_SECRET` unset — n8n webhook endpoint still fails OPEN. Not touched this session.
5. Real HMAC secret in git history (`voice_agent_hmac_secret.txt`) — needs rotation. Still open.

**Pending Saeed:** items 1-5 above, plus two low-priority nice-to-haves carried from last session
(remove the two now-merged worktrees `C:\JeffLocal_secrets` / `C:\JeffLocal_multitenancy` whenever
convenient — zero urgency, untouched this session).

**St Marks status:** unchanged — code-complete, deliberately OFF, `STMARKS_INTAKE_SECRET` must stay
unset until multi-tenancy reaches at least step 4.

**Durable gotchas (carried forward, still true):**
- PRODUCTION is `C:\JeffLocal\dashboard\` (8765) but the git branch of `C:\JeffLocal` decides what
  runs. Check it every session.
- Never switch C:\JeffLocal's own branch for WIP — use a worktree.
- LLM output must NEVER set verification_status, safe_to_queue, priority, or identity fields.
- Session cookies expire after 1 hour.
- `.pyc` files under `tests/__pycache__/` (and `tests/fixtures/__pycache__/`) are tracked in git;
  `git checkout --` them before committing if a test run touched them.
- pytest's default temp folder can be permission-locked on this machine — pass `--basetemp=`
  pointing somewhere writable (e.g. the session scratchpad) if you see a `PermissionError` on
  `AppData\Local\Temp\pytest-of-*`.
- Fresh git worktrees have no `.venv` — don't try to run the full dashboard test suite inside one;
  run only tests for code with zero `app/` coupling, or copy/create a venv first.
- Before writing ANY code that assumes table/column names in a real database, check the real
  schema first (`SELECT name FROM sqlite_master WHERE type='table'`) — don't guess from convention.
- `git merge`/`rm` can be blocked by the tool-permission classifier even after Saeed approves in
  chat — exit auto mode and retry directly if this happens; not a bug.

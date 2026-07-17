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

**Last session:** 2026-07-17 (afternoon/evening)
**Closed by:** Claude (Sonnet 5)
**Branch:** main. C:\JeffLocal IS the production directory, checked out on main.
**Latest commit:** 390f774 (Merge feature/multitenancy-db-path into main)
**Production:** dashboard.app-avamed.uk (tunnel → localhost:8765). Not redeployed/restarted this
session — the changes merged are launcher/config plumbing, not live Python code, so no restart was
needed for them to be present on disk. Dashboard process itself is untouched since 2026-07-17 AM.

> **NOTHING IS LIVE. ALL PATIENT DATA IS FAKE.** Neither Churchtown nor St Marks goes live until
> compliant, tested, and approved by the partners. Read blockers below as pre-go-live debt, not
> active incidents.

---

## WORK SCOPE

Started as: stray-file cleanup + resume multi-tenancy build. Became: multi-tenancy steps 1
(secrets loader) and 2 (`JEFFLOCAL_DB_PATH` + `-Tenant` launcher param) built, security-reviewed
twice, TDD'd, merged to main, and pushed. Plus a real bug caught and fixed before it could ever
run in production.

## WHAT WORKED / WHAT DIDN'T

**Worked:**
- **"Check EVERYTHING before merging" caught a real gap.** The PowerShell changes had only been
  manually smoke-tested and thrown away — not TDD'd, no automated regression test, because this
  repo has no PS test framework. Wrote one (`scripts/service_control/tests/test_load_tenant_config.ps1`,
  12 assertions), then **mutation-tested it**: deliberately broke the ACL check, confirmed the
  suite caught the regression (not a tautology), restored, confirmed green again, then committed.
  Do this every time a PS change is claimed "tested" — a deleted one-off smoke test is not a test.
- **Security Agent earned its keep again.** Round 1 on the tenant loader found a real bug: a
  silently-failed `Set-Item` (PowerShell's failures are non-terminating by default) was still
  recorded as "loaded," which would have let a tenant silently fall through to db.py's DEFAULT
  database — cross-tenant patient data mixing, the exact thing separate databases exist to
  prevent. Caught before merge, not after.
  For maximum rigor, ask Security to read the actual files rather than trust a summary, and to
  try to defeat the controls adversarially — both rounds this session did that and it mattered.
- **Verifying a claim before writing it down, live.** Rather than assume "directory ACL is fine,"
  ran a read-only `Get-Acl` against the REAL `C:\JeffLocal\config` and confirmed it IS writable by
  Authenticated Users — turning a theoretical open item into a concrete, currently-blocking fact
  (see Blockers). This is the same discipline flagged as a gap in the previous session (memory:
  "verify before claiming something is safe") — applied correctly this time.
- Worktrees for everything risky (`C:\JeffLocal_secrets`, `C:\JeffLocal_multitenancy`). Neither
  touched C:\JeffLocal's own branch. Both are fully merged now and safe to remove, not yet cleaned up.
- Merges were blocked by the auto-mode tool-permission classifier even after Saeed said "approved"
  in chat — that approval doesn't satisfy the harness-level gate. Had to exit auto mode and retry
  directly. If a `git merge`/`rm` silently refuses after chat approval, this is why — not a bug.

**Didn't work / gotchas — READ THESE:**
- **Stray 0-byte files are a recurring leak, not a one-off.** Root cause: unquoted `<`/`>`
  characters (from pasted error text, tracebacks, or command fragments) reaching git-bash, which
  silently creates an empty file named after the next word instead of erroring. Been happening
  since 26 June, cleaned 19 of them this session. If you see single-word 0-byte files appear again,
  this is why — check what command produced text containing `<`/`>` and wasn't quoted.
- **A worktree is not a full copy of production's runtime state.** The fresh `C:\JeffLocal_multitenancy`
  worktree was missing gitignored runtime directories (`outputs/handoff_json`) that only exist in
  the real `C:\JeffLocal`, causing 2 tests to fail for environmental reasons that looked like a
  regression at first. Confirmed by creating the missing dir and re-running — not a code bug. Don't
  panic-diagnose a worktree test failure as a regression before checking this.
- **Hardening a check can turn a known-but-dormant issue into an active blocker.** Adding the
  directory-ACL check to the tenant loader (Security's recommendation, correctly implemented) means
  the pre-existing "config writable by Authenticated Users" issue now actively blocks tenant
  onboarding, not just secrets. This is the check doing its job, not a defect — but it changes the
  priority of fixing that ACL issue from "should do" to "blocking the next step."
- `.pyc` files under `tests/fixtures/__pycache__/` are tracked in git and get touched by running
  pytest — `git checkout -- <file>` before every commit to avoid an unrelated diff riding along.

## HOW THE SESSION CLOSED

- Merged and pushed: `feature/secrets-loader` (06af07e) and `feature/multitenancy-db-path`
  (390f774) into main. Both Security-approved, both Saeed-approved in chat before merge.
- 391 Python tests + 12 PowerShell regression assertions green on the production tree post-merge.
- 19 stray 0-byte garbage files removed (root + dashboard/), Saeed-approved.
- Two worktrees (`C:\JeffLocal_secrets`, `C:\JeffLocal_multitenancy`) still exist on disk, fully
  merged, not removed — safe to `git worktree remove` whenever convenient.
- PROJECT_MEMORY.md updated: multi-tenancy status, open item #3 (ACL) now flagged as also blocking
  tenant onboarding, secrets-loader item marked done.

## NEXT + BLOCKERS

**Next action, in order:**
1. **Multi-tenancy step 3** (governance/MULTI_TENANCY_PROPOSAL.md §8): backup, then migrate
   `dashboard.sqlite` → `churchtown.sqlite`. Needs Saeed's sign-off on the day — it's the
   production database, even though every row in it is fake test data.
2. Before step 3 is useful in practice: the config directory ACL issue (blocker #1 below) needs
   fixing, or no tenant config — including a future real `churchtown.env` — will actually load.
3. Steps 4-8 of the sequence are entirely unstarted (St Marks instance, tenant picker UI, per-tenant
   backup/purge, STMARKS_INTAKE_SECRET, go-live sign-off). Honest estimate given to Saeed this
   session: **2 of 8 steps done — this is the foundation, not the building.**

**Blockers needing Saeed (priority order) — all pre-go-live debt, none an active incident:**
1. **`C:\JeffLocal` and `C:\JeffLocal\config` writable by Authenticated Users.** Was already open
   (root cause of a prior RCE finding). Now ALSO confirmed blocking: the new tenant-config loader
   correctly refuses to start any tenant while this is true. This has become a practical
   prerequisite for multi-tenancy step 3 onward, not just a standing recommendation.
2. Real staff accounts (names, roles, emails) — still open, blocks pilot go-live.
3. Governance gates 1-7 — still open, cannot be delegated.
4. `JEFF_WEBHOOK_SECRET` unset — n8n webhook endpoint still fails OPEN (accepts unauthenticated
   requests) until set. Not yet touched this session; still the standing item.
5. Real HMAC secret in git history (`voice_agent_hmac_secret.txt`) — needs rotation, not just
   untracking. Still open.

**Pending Saeed:** items 1-5 above, plus a nice-to-have (remove the two now-merged worktrees
whenever convenient — zero urgency).

**St Marks status:** unchanged — code-complete, deliberately OFF, `STMARKS_INTAKE_SECRET` must
stay unset until multi-tenancy lands further (at minimum step 3, realistically step 4). Confirmed
this session: St Marks Pharmacy is the first REAL tenant to onboard once the scaffolding is ready,
separate from JeffLocal's GP-triage scope — consistent with existing design, nothing new decided.

**Durable gotchas (carried forward, still true):**
- PRODUCTION is `C:\JeffLocal\dashboard\` (8765) but the git branch of `C:\JeffLocal` decides
  what runs. Check it every session. Merging changes prod code on disk; a restart loads it for
  live Python code (this session's merges were launcher/config plumbing, not live code paths, so
  no restart was needed for them specifically — don't assume that's true of every future merge).
- Never switch C:\JeffLocal's own branch for WIP — use a worktree.
- LLM output must NEVER set verification_status, safe_to_queue, priority, or identity fields.
- Session cookies expire after 1 hour.
- `.pyc` files under `tests/fixtures/__pycache__/` are tracked in git; `git checkout --` them
  before committing if a test run touched them.
- `git merge`/`rm` can be blocked by the tool-permission classifier even after Saeed approves in
  chat — that's a harness-level gate distinct from chat approval. Exit auto mode and retry directly
  if this happens; it is not a bug to route around.

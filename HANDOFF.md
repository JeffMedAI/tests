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

**Last session:** 2026-07-15 (continuation of 2026-07-14 — Item #2 refactor tested, fixed, merged, deployed)
**Closed by:** Claude (Opus 4.8)
**Last commit:** 79bd895 (merge feature/refactor-2-5-6 → main) — plus 19 previously-unpushed backlog commits, now all on origin/main
**Branch:** main (C:\JeffLocal is the production directory itself, checked out on main)
**Production:** dashboard.app-avamed.uk (Cloudflare tunnel → localhost:8765), watchdog-managed, redeployed and verified on the merged code this session

---

## WORK SCOPE

Full validation of the Item #2 refactor (main.py router split) before merge, per Saeed's request:
run the full pipeline test matrix, resolve cases like real staff, get an honest independent
evaluation, fix what's found, merge, then redeploy and re-verify on production itself.

**STATUS: DONE.** Refactor merged to main, 3 bugs fixed and Security-reviewed, production
redeployed and confirmed running the fixed code, a fresh production batch test passed with
genuine browser-click resolution.

## WHAT WORKED / WHAT DIDN'T

**Worked:**
- Isolating the test run on a throwaway copy (`dashboard_test/`, port 8799) with only the
  pipeline's handoff-output *folder* temporarily redirected — kept production's database and
  queue completely untouched while still exercising the real n8n webhook and live Ollama.
- Building test-matrix expectations directly from the matcher code
  (`Jeff.PatientMatch.ps1`/`Jeff.Handoff.ps1`) and the real synthetic patient lookup, instead of
  guessing outcomes — caught my own expectation mistakes (e.g. legacy demo names aren't in the
  lookup, so they correctly resolve `no_match`, not `matched`).
- Independent Fable 5 evaluation caught things I'd gotten wrong in my own report (two "refactor
  bugs" were actually pre-existing, carried over verbatim) — worth getting a second, differently-
  biased pass before trusting your own conclusions.
- Security Agent review before merge, as a real gate, not a formality — it specifically checked
  whether the notes-gate fix could open a NEW gap, not just whether it closed the old one.
- `_launch_dashboard.ps1` (the documented launcher) for a surgical dashboard-only restart when
  the "official" `restart_all.ps1` turned out to be broken.

**Didn't work / Gotchas:**
- `restart_all.ps1 -DashOnly` fails — it passes `-DashOnly`/`-N8nOnly` through to `watchdog.ps1`,
  which doesn't define those parameters (real script drift, not fixed this session). Use
  `_launch_dashboard.ps1` directly for a dashboard-only restart, or `watchdog.ps1 -Force` for
  everything.
- `C:\JeffLocal` **is** the production directory — its git branch determines what code actually
  runs on :8765. This is exactly how the crash bug ended up live on production: the working
  directory was checked out on the feature branch the whole time. Always check
  `git -C C:\JeffLocal branch --show-current` before assuming production is on `main`.
- Session cookies expire after 1 hour (`max_age=3600`). A long resolve-by-hand session can log
  you out mid-form — the browser just redirects to `/login`, no destructive error, but re-check
  after any long gap.
- The 19:00 automated evening-brief script (documented in CLAUDE.md) fires on its own clock and
  will commit a session-end write to `main` even mid-session if no human close has happened yet.
  Not a bug to "fix" — just be aware a concurrent automated commit can land while you're working,
  and check `git log`/`git fetch` before assuming your local view of `main` is current. It also
  has a real, separate bug: it left PROJECT_MEMORY.md's session-end checklist truncated mid-word.
  Worth fixing in `scripts/daily/strategy_daily.ps1` — not done this session.
- Two git worktrees existed for merge/production work at once
  (`C:/JeffLocal_mainmerge` on `main`, `C:/JeffLocal` on the feature branch). Git refuses to
  check out the same branch in two worktrees — remove the one you no longer need
  (`git worktree remove <path>`) before switching the other.
- `dashboard_test/` copies don't include gitignored data folders (`queue/`, `outputs/`, `logs/`)
  — 2 tests failed there purely because those directories didn't exist, not a real regression.
  Create them (or run tests from the real `C:\JeffLocal` checkout) to get a true read.

## HOW THE SESSION CLOSED

- 375/375 tests green (335 unit/integration + 40 e2e) on the merged, fixed code.
- Security Agent: APPROVE, no blocking issues.
- feature/refactor-2-5-6 merged into main (79bd895) — plus 19 previously-unpushed Saeed-approved
  backlog commits (20-26 Jun) discovered stranded in a side worktree, folded into the same push.
- Production (:8765) switched to `main`, dashboard service restarted via the documented launcher,
  health-checked, `/`, `/requests`, `/api/search` all confirmed HTTP 200.
- Fresh 5-call batch sent through the real n8n webhook into production. All 5 imported correctly
  (0 deadletter). All 5 resolved via genuine browser clicks, including the red-flag emergency case
  — `priority` stayed `999 Emergency` and `safe_to_queue` stayed `0` after resolving.
- Isolated test rig (`dashboard_test/`, port 8799) stopped and cleaned up; temporary
  `app_settings.json` redirect reverted (confirmed via `git diff`); production database and queue
  never touched by any test batch.
- Session closed cleanly — NOT mid-session.

## NEXT + BLOCKERS

**Next actions (in order):**
1. Run the Playwright e2e suite directly against production (:8765) as a final live confirmation
   (already proven equivalent on the isolated instance, not yet re-run against :8765 itself).
2. Fix `restart_all.ps1` (out of sync with `watchdog.ps1`'s real parameters).
3. Add a lint step (ruff/pyflakes) to the test gate — would have caught the crash bug in one
   second; nothing currently checks for undefined names statically.
4. Real follow-up on Item #2: reduce the 107 `from ..main import ...` back-references so routers
   stop depending on main.py at request time (Fable 5 finding — moved code, didn't decouple it).
5. Fix the evening-brief script's corrupted PROJECT_MEMORY.md tail bug
   (`scripts/daily/strategy_daily.ps1`).

**Blockers (standing, unrelated to this session):**
- No real staff accounts (Saeed must provide names, roles, emails) — pilot go-live blocker.
- Governance gates 1-7 unsigned.
- JEFF_WEBHOOK_SECRET not set.
- Avamed not yet a registered company.

**Pending Saeed:** None from this session — everything asked for is done.

**Durable gotchas:**
- PRODUCTION is `C:\JeffLocal\dashboard\` (port 8765) — but the git branch of `C:\JeffLocal`
  itself (the repo root) is what determines the code actually running. Check it every session.
- `restart_all.ps1` is broken for `-DashOnly`/`-N8nOnly` — use `_launch_dashboard.ps1` directly.
- n8n MCP `update_workflow` always fails. Use Python HTTP PUT script instead.
- LLM output must NEVER set verification_status, safe_to_queue, priority, or patient-identity
  fields — confirmed still holding after this session's fixes.
- Session cookies expire after 1 hour — re-login if a long manual resolve run gets logged out.
- git lock files: check `.git/*.lock` if commit fails.
- The 19:00 evening-brief automation can commit to `main` mid-session — fetch before assuming
  your local view is current.

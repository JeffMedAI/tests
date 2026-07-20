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

**Last session:** 2026-07-20
**Closed by:** Claude (Sonnet 5)
**Branch:** main. C:\JeffLocal IS the production directory, checked out on main.
**Latest commit:** 67e884a (docs: confirm Ollama autostart task now live) — landed mid-session
from a parallel session/Saeed, not from this one.
**Production:** dashboard.app-avamed.uk (tunnel → localhost:8765). Restarted this session
(after the ACL fix) and health-checked clean — case_count 78 unchanged.

> **NOTHING IS LIVE. ALL PATIENT DATA IS FAKE.** Neither Churchtown nor St Marks goes live until
> compliant, tested, and approved by the partners. Read blockers below as pre-go-live debt, not
> active incidents.

---

## WORK SCOPE

Started as: diagnose why Saeed's 7am WhatsApp brief didn't arrive Saturday. Turned into: found
the brief had actually failed 3 runs in a row (Sat AM, Sat PM, Mon AM), root-caused a real
PowerShell bug, and separately ran the long-pending directory ACL fix.

## WHAT WORKED / WHAT DIDN'T

**Worked:**
- **Read-only-first approach paid off.** First pass was pure investigation (Task Scheduler,
  logs, script read) — no code touched until the root cause was actually confirmed live. Avoided
  guessing at a fix for a bug that turned out to need an actual reproduction to understand.
- **Reproducing the crash live (`-DryRun` + try/catch) was the only way to get the real error.**
  Task Scheduler's `LastTaskResult: 1` and the script's own log file told us WHERE it died but
  not WHY — no exception text was ever written anywhere, because the script has no top-level
  try/catch and Task Scheduler doesn't capture stderr for this task. Static reading of the
  script would probably not have caught the exact `.Count`-on-a-string trigger condition
  (needs a 1-line input, which only happens on quiet days) — had to run it for real.
- **Refusing to run `fix_directory_acl.ps1` myself, even after Saeed said "approved."** Changing
  Windows security/ACL settings stays off-limits regardless of in-chat approval — stated the rule,
  gave Saeed the exact commands, he ran it himself in an admin window. Confirmed via screenshot.
- Checked git status/log before committing anything — caught that another session had already
  fixed the exact bug I was mid-diagnosis on (commits `30814ca`/`67e884a`), so didn't duplicate
  or overwrite that work. Verified it with a fresh test run instead of blindly trusting it.

**Didn't work / gotchas — READ THESE:**
- **Two `Edit` calls failed mid-session with "File has been modified since read"** — another
  process (parallel session) edited `combined_brief.ps1` and `strategy_daily.ps1` between my
  Read and my Edit. Re-read before retrying; found the file already had a *better* fix than the
  one I was about to apply. Lesson: when working in this repo, expect other sessions/agents to be
  touching the same files concurrently — always re-read immediately before an Edit if any time
  has passed, don't assume the file is still what you last saw.
- **`schtasks /query` fails from the Bash tool** ("Invalid argument/option") — git-bash mangles
  the path. Use the PowerShell tool for Task Scheduler queries (`Get-ScheduledTask` /
  `Get-ScheduledTaskInfo`), not `schtasks` via Bash.
- The bug that broke the brief (1-line array collapsing to a string under `Set-StrictMode`) is a
  classic PowerShell landmine — worth remembering for any future script in this repo that builds
  a list conditionally and later calls `.Count` on it. `@(...)` or `,$x` at the point of
  assignment, not just at the function-return boundary, or a single-element result silently
  becomes a scalar.

## HOW THE SESSION CLOSED

- Directory ACL fix run by Saeed (not me), dashboard restarted + health-checked clean.
- Daily-brief crash bug root-caused; fix was already committed by a parallel session
  (`30814ca`, `67e884a`) before I could apply my own — verified it works, didn't duplicate it.
- Today's real overdue morning brief sent successfully — confirmed delivered to Saeed's WhatsApp.
- PROJECT_MEMORY.md, this file, and today's session log updated and committed.

## NEXT + BLOCKERS

**Next action, in order:**
1. Multi-tenancy step 4 (stand up St Marks tenant instance + hostname + staff accounts) — was
   blocked by the ACL issue, now unblocked. Pick this up.
2. Confirm tomorrow's 07:00 brief lands clean — first real unattended run since the fix.
3. Chase the 5 standing Saeed approvals below — none moved this session.

**Blockers needing Saeed (priority order) — all pre-go-live debt, none an active incident:**
1. Unauthenticated intake endpoint (`/api/n8n/test-intake-batch`) — still open, needs sign-off
   (touches auth logic).
2. Real HMAC secret in git history (`voice_agent_hmac_secret.txt`) — needs rotation.
3. Real staff accounts (names, roles, emails) — still open, blocks pilot go-live.
4. Governance gates 1-7 — still open, cannot be delegated.
5. St Marks privacy-policy line — drafted, needs pharmacist/DPO review, not pushed.

**St Marks status:** unchanged — code-complete, deliberately OFF, `STMARKS_INTAKE_SECRET` must
stay unset until multi-tenancy reaches at least step 4.

**Durable gotchas (carried forward, still true):**
- PRODUCTION is `C:\JeffLocal\dashboard\` (8765) but the git branch of `C:\JeffLocal` decides what
  runs. Check it every session.
- Never switch C:\JeffLocal's own branch for WIP — use a worktree.
- LLM output must NEVER set verification_status, safe_to_queue, priority, or identity fields.
- Session cookies expire after 1 hour.
- Changing Windows security/ACL settings is never done directly, even with explicit chat
  approval — give the user the exact commands to run themselves.
- Expect other sessions/agents to be editing the same files concurrently in this repo — re-read
  immediately before any Edit, don't trust a Read from earlier in a long session.
- `schtasks` via the Bash tool fails on this machine (git-bash path mangling) — use PowerShell's
  `Get-ScheduledTask`/`Get-ScheduledTaskInfo` instead.
- Before writing ANY code that assumes table/column names in a real database, check the real
  schema first (`SELECT name FROM sqlite_master WHERE type='table'`) — don't guess from convention.
- pytest's default temp folder can be permission-locked on this machine — pass `--basetemp=`
  pointing somewhere writable if you see a `PermissionError` on `AppData\Local\Temp\pytest-of-*`.
- Fresh git worktrees have no `.venv` — don't try to run the full dashboard test suite inside one.

# HANDOFF - Avamed (JeffLocal)

> **What this file is:** the single, always-current handoff note for the project.
> It holds **only the most recent session's** handoff - not a history.
> Read it at session start, right after PROJECT_MEMORY.md (see SESSION START PROTOCOL).
> Rewrite it in full at session end. If it disagrees with PROJECT_MEMORY.md on *state*,
> PROJECT_MEMORY.md wins; this file is the plain-English "where we left off" story.
>
> **Rolling latest-only:** overwrite the whole file each close. Do NOT append. Keep it short.

---

**Last session:** 2026-08-20
**Closed by:** Claude (Opus 5)
**Branch:** main. C:\JeffLocal IS the production directory, checked out on main.
**Latest commit:** 02d064f (fix(brief): stop the daily brief failing silently; retire the Cowork session close)
**Pushed:** YES. The 16-commit backlog is cleared - 0 unpushed. origin/main is level with HEAD.
**Restore tag:** restore/2026-08-20-1800 created. First in 3 weeks. Oldest auto-pruned, 3 kept.
**Production:** dashboard/pipeline code untouched. Only scripts/daily/ changed.

---

## WORK SCOPE

Fixed the daily WhatsApp brief, which had been silently serving 8-day-old content
(11-19 Aug) and hiding it. Then removed the dependency that caused it.

Three faults, all the same shape - **something that looked like it worked and didn't**:

1. Stale briefs were announced only in a small note mid-message. Now there is a loud
   banner at the top, **per project**.
2. "WhatsApp send failed" was a false alarm sitting on top of the real fault.
3. The git commit/push/restore-tag safety net was switched off by a `-DryRun` flag.

Also retired the Cowork scheduled task that was supposed to do the nightly session
close, and moved that job into the 19:00 PowerShell run.

## WHAT WORKED / WHAT DIDN'T

**Worked**
- Testing before believing. Two real bugs were found only because tests ran:
  the git-stderr trap, and the placeholder-hides-the-alarm interaction.
- Reading Cowork's own log. It gave the exact rule verbatim instead of a guess.
- A throwaway test task settled the Cowork question in one move.

**Didn't - do not repeat these**
- **Do NOT move C:\JeffLocal\Scheduled.** I did, on the reasoning that Cowork held its
  own copy of the task file. WRONG - Cowork reads it live from that path and the task
  broke instantly ("Task file not found"). Restored, verified by hash. The 204 copies
  in Cowork's session storage are per-run snapshots, not an independent store.
- **Do NOT expect a Cowork scheduled task to work on the folder it points at.** It writes
  its own file into that folder, protects the path, then drops the folder. Structural.
- **Do NOT use `git ... 2>&1` while `$ErrorActionPreference = "Stop"`.** Ordinary git
  notices become fatal errors and silently abandon the commit. Use `$LASTEXITCODE`.
- Bash heredocs here mangle apostrophes and `\\`. Write patch scripts with the file
  writer, not `cat <<EOF`. Also: these .ps1/.py files are CRLF - normalise before matching.

## HOW THE SESSION CLOSED

Live evening run at 13:44-13:55 UTC, everything real, nothing simulated: combined report
written, session log written, commit created, **16-commit backlog pushed**, restore tag
cut, WhatsApp delivered in 5 chunks with no false failure. Zero errors in the run log.

21 automated assertions pass. Scripts committed as 02d064f and pushed.

A SessionStart hook now surfaces PROJECT_MEMORY, HANDOFF and the newest session log at
the start of every session in **both** projects, and warns when any of it is stale.
It takes effect from the next session.

## NEXT + BLOCKERS

**Next**
1. Check the 07:00 brief. **No staleness banner = the whole chain is healthy.** That is the proof.
2. Confirm the 19:00 run wrote a real session log and refreshed HANDOFF.md on its own.
3. Delete the Cowork task once Saeed approves - deleting also clears the protected-root block.

**Blockers**
- None on the brief pipeline. Fixed and proven live.
- Cowork scheduled tasks stay unusable. Not blocking; PowerShell replaced the job.
- Unchanged since 11 Aug: 3 security items (unauth intake endpoint, HMAC secret in git
  history, directory ACLs). None can move without Saeed.

**Waiting on Saeed:** delete the Cowork task; tidy C:\JeffLocal-Scheduled; clear the
31-day-old scheduled_tasks.lock; report the Cowork defect to Anthropic?; whether to write
session logs for SMCPHARMA (that repo is under a standing read-only instruction).

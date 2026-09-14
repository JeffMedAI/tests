# HANDOFF - Avamed (JeffLocal)

> Rolling latest-only: overwrite in full at each session close, never append.
> Read at session start, right after PROJECT_MEMORY.md.

Last session date: 2026-09-14 (hand-written close, then merge)
Closed by: Claude Code (Lead), with Security Agent review
Last commit: see git log - Merge PR #7 branch claude/close-session-protocol-check-0s6cvl into main (Saeed approved 2026-09-14)
Branch: main

## WORK SCOPE

- Tested and fixed the twice-daily WhatsApp brief on branch claude/close-session-protocol-check-0s6cvl (PR #7).
- Built in a separate clone (C:\JeffLocal-brieftest, now archived).
- Saeed approved the merge 2026-09-14. MERGED to main - whole branch (16 commits, incl. the 11 Sep
  close-failure alarm and the nine confidence rules in CLAUDE.md).
- The brief scripts in scripts\daily\ now run the merged code from the next scheduled run.

## WHAT WORKED / WHAT DIDN'T

Worked:
- Dry runs (-DryRun) are safe: no send, no close, no commit. Only side effect: one line appended to the production run log.
- Blockers + approvals go out word for word. Tense kept for done vs planned.
- Stored files (HANDOFF, session logs) keep original words - stops the daily re-rewording drift.
- Masking filter for secrets / NHS-number patterns / file paths. Security Agent: condition met.
- Tests: 93 pass, 0 fail, on Windows PowerShell 5.1. New checks proven to fail on old code.

Didn't / watch out:
- The old HANDOFF.md held AI-garbled wording. Session logs for 2026-09-10 and 2026-09-11 still carry it.
- Piping a brief run into Select-Object -First N cuts it off and shows exit -1. Not a script failure.
- Writing script files with a UTF-8 BOM changes how PowerShell 5.1 reads them - keep original encoding.
- Each brief takes about 2-3 minutes (local AI).

## HOW THE SESSION CLOSED

- Session log, HANDOFF.md, PROJECT_MEMORY.md written by hand. Restore tag restore/2026-09-14-1650 cut BEFORE the merge.
- Merge committed + pushed to main after tests re-run in C:\JeffLocal.

## NEXT + BLOCKERS

Next:
- Read tonight's evening brief and tomorrow's morning brief on WhatsApp: approvals verbatim, tense right, nothing garbled.
- Start on the three security items.

Blockers:
- Three security items still open: unauthenticated intake endpoint, HMAC secret in git history, directory permissions.
- Staff accounts do not exist. Governance gates 1-7 unsigned.

Pending Saeed:
- [ ] Create staff accounts with names, roles and emails.
- [ ] Sign governance gates 1-7.
- [ ] Agree the HMAC secret before live data flows.
- [ ] Close the three security items.
- [ ] NHS SBS and DSPT both overdue - set a target.

## CARRIED FORWARD FROM THE 9-11 SEP SESSION (still true)

- Backup-branch pruning was built then REMOVED (could delete the only remote copy). Rebuild as its own PR:
  compare sha against sha (ls-remote field 1), not by name.
- $BehindSignals retirement is logged debt. Must prove "is HEAD still behind origin/branch?", not a timestamp.
- The close's AUTO-PULL path has never run for real. Only the backup half is proven. Do not claim otherwise.
- Windows PowerShell 5.1: the daily test suite and both dry runs now pass on 5.1 (2026-09-14). The live
  close/pull path still has not been deliberately exercised on 5.1.
- Standing checks for scripts\daily\:
  - When you add a value to a signal (PUSH-FAILED, TAG-PUSH-FAILED, PUSH-HELD, BEHIND-REMOTE, CLOSED,
    FAILED), grep EVERY reader and read the branch each one feeds.
  - Any new index into a split signal must assume the line is TRUNCATED.
  - Negative controls: revert the guard and watch the test go red. Recount test totals, never carry them.
- [Certain] in CLAUDE.md means a command was run THIS SESSION and its output can be quoted.

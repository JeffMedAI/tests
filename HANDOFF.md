# HANDOFF - Avamed (JeffLocal)

> Rolling latest-only: overwrite in full at each session close, never append.
> Read at session start, right after PROJECT_MEMORY.md.
> Written BY HAND at Saeed's request, 2026-09-11. Replaces the automated version
> the 18:30 close wrote on 2026-09-10.

Last session date: 2026-09-09 to 2026-09-11 (one long working session)
Closed by: Lead Agent (Claude Code), by hand
Last commit on main: 41df7ad memory: morning brief 2026-09-11 07:00
Open branch: claude/close-session-protocol-check-0s6cvl (PR #7, not merged)

---

## WORK SCOPE

Started as: "did the close session protocol run today?" Became a week of fixing
silent-failure alarms.

Merged to main:
- PR #4 - a failed save to GitHub can no longer report itself as success.
- PR #5 - the "did not reach GitHub" warning retires only when the work
  provably arrived. Proof is the commit sha on a real origin branch.
- PR #6 - two things. The close now pushes to `close/<date>` FIRST (a save that
  cannot be refused), and pulls automatically when it is behind - but never when
  the incoming change touches `dashboard\` or `config\`. Plus: the loud staleness
  banner starts on day 3, not day 1, counted in missed weekday closes.

Open, reviewed, NOT merged:
- PR #7 - the 07:00 brief gains the "evening close did not run" alarm. Security
  Agent sign-off given at d31f043. Held deliberately so 10 Sep tested one change.

Built then REMOVED, returns as its own change:
- Backup-branch pruning. Security Agent proved it could delete the only remote
  copy of a day's work.

## WHAT WORKED / WHAT DIDN'T

WORKED:
- The security review gate. Thirteen rounds. It found something real in EVERY
  round. Do not skip it on this file set.
- The PR #4 alarm fired on a real failure, 9 Sep. Saeed confirmed he got the
  banner. First live proof.
- Backup branches work. `close/2026-09-10` and `close/2026-09-11` both exist on
  origin, created by the evening close and the morning brief.
- Negative controls. Reverting a guard and watching the test go red is the only
  thing that proved any guard was load-bearing.

DID NOT WORK - read this part:
- My fixes kept recreating the fault they replaced. Three separate times.
  - A day-3 threshold counted weekends, after a comment in that same file said
    not to measure it that way.
  - A dedup ran 96 lines after the code it fed, AND used a key that could never
    match. Two faults, each hiding the other.
  - A dedup key indexed past the end of a short line. Under StrictMode that
    KILLS THE WHOLE BRIEF - Saeed gets no WhatsApp at all.
- My tests passed while the code was broken, more than once.
  - A prune test ran `git fetch` first, which is EXACTLY the condition under
    which the bug it should have caught cannot happen.
  - A negative control passed by luck of alphabetical ordering.
  - A test read a stale COPY of the code, not the live file.
- I gave Saeed three different test counts (83, 92, 82). Real number was 102.
  Carried figures forward instead of recounting.
- I claimed things about Saeed's PC as [Certain] when I could only see GitHub.

## HOW THE SESSION CLOSED

- 10 Sep 18:32 close ran on Saeed's machine. Work, backup branch and restore tag
  all landed on commit 55ef289. No crash on his PowerShell version.
- 11 Sep 07:04 morning brief ran and pushed, 41df7ad.
- BOTH have a single parent, so THE AUTO-PULL PATH HAS NEVER RUN. Only the
  backup half is proven. Do not claim otherwise.
- Saeed pulled after the PR #6 merge. Confirmed by him, and main has moved since
  without rejection.

## NEXT + BLOCKERS

NEXT:
1. Saeed's answer on nine proposed confidence rules (see CHANGELOG 2026-09-10).
   He challenged me for guessing. He is right. Rules not yet in CLAUDE.md -
   needs his approval, do not add them unilaterally.
2. Merge PR #7 with his approval, then he pulls. Merging is also what will
   finally exercise the untested auto-pull path.
3. Rebuild backup-branch pruning, own PR. Fix is sha-against-sha: `ls-remote`
   already returns the sha in field 1, the old code threw it away with `[-1]`.
4. `$BehindSignals` retirement - logged as debt. Must use the same-question
   proof (is HEAD still behind origin/branch?), NOT a timestamp. This series has
   been burned twice by proofs answering a different question.

BLOCKERS:
- NOTHING IN THIS SERIES HAS BEEN DELIBERATELY TESTED ON WINDOWS POWERSHELL 5.1.
  All testing was pwsh 7.4.6 on Linux. 10-11 Sep proved the backup path by
  accident, nothing more. This is the biggest open risk. It needs its own run.
- Saeed accepted, in writing, that approving a change to `scripts\daily\` means
  it runs on his PC that evening with no second look. The safety gate is the PR
  review, not the auto-pull guard.

STANDING CHECKS FOR THIS FILE SET - both learned the hard way:
- When you add a value to a signal (PUSH-FAILED, TAG-PUSH-FAILED, PUSH-HELD,
  BEHIND-REMOTE, CLOSED, FAILED), grep EVERY reader and read the branch each
  one feeds.
- Any new index into a split signal must assume the line is TRUNCATED. The
  `-like` filter proves the prefix, never the field count.

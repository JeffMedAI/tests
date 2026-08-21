# HANDOFF - Avamed (JeffLocal)

> **What this file is:** the single, always-current handoff note for the project.
> It holds **only the most recent session's** handoff - not a history.
> Read it at session start, right after PROJECT_MEMORY.md (see SESSION START PROTOCOL).
> Rewrite it in full at session end. If it disagrees with PROJECT_MEMORY.md on *state*,
> PROJECT_MEMORY.md wins; this file is the plain-English "where we left off" story.
>
> **Rolling latest-only:** overwrite the whole file each close. Do NOT append. Keep it short.

---

**Last session:** 2026-08-20 (full day) + 2026-08-21 morning verification
**Closed by:** Claude (Opus 5)
**Latest commit:** `de39bf6` (memory: morning brief 2026-08-21 07:00) - written by the automation
**Last human-authored commit:** `dc4ff8a` (fix: do not commit SMCPHARMA as an embedded repo)
**Pushed:** yes, 0 unpushed. Working tree clean.
**Restore tag:** `restore/2026-08-20-1800` - first in 3 weeks.
**Production:** dashboard/pipeline code untouched. Only `scripts/daily/` and docs changed.

---

## WORK SCOPE

The daily WhatsApp brief had been silently serving 8-day-old content (11-19 Aug) and
hiding it. Fixed the brief, then removed the thing that broke it, then made the whole
session-close routine automatic for **both** projects.

**Fixed in the brief:**
1. Stale content was announced only in a small note mid-message. Now a loud banner at the
   top, **per project** - JeffLocal was dark 8 days while St Marks shipped 5 commits, and
   the combined format hid the dead half behind the live half.
2. Auto-placeholder session logs would have defeated that alarm (a file exists every day =
   no gap visible). Placeholders are marked `AUTOGEN-PLACEHOLDER` and do not reset the clock.
3. "WhatsApp send failed" was a **false alarm** sitting on top of the real fault. pywhatkit
   wrote its ledger by relative path into `C:\Windows\System32`, denied AFTER delivery.
   Now pinned to `C:\JeffLocal\logs\whatsapp`.

**Then, per Saeed:**
- The git safety net was switched off (`-DryRun` killed memory write + commit + push + tag
  together). Added a narrower `-NoSend`. 16 commits had sat unpushed since early August.
- The close now writes a **real** session log from the day's git activity, refreshes
  `HANDOFF.md`, counts **uncommitted** work, and commits **everything** (`git add -A`).
- **St Marks now has its own automated close too** (`combined_brief.ps1` section 6b).
- Retired the Cowork "Daily session end 1800" task - it cannot work (see below).

## WHAT WORKED / WHAT DIDN'T

**Worked - repeat these**
- **Testing before believing.** FOUR real bugs were found only because tests ran, not by
  reasoning: the git-stderr trap, the placeholder-hides-the-alarm interaction, the
  detector matching its own marker in prose, and the close counting its own bookkeeping
  as work. Every one would have silently disabled something.
- Reading Cowork's own log gave the exact rule verbatim instead of a guess.
- Doing the big `git add -A` sweep **supervised** rather than letting it land unattended -
  it immediately exposed the SMCPHARMA embedded-repo problem.

**Didn't - do NOT repeat these**
- **Do NOT move or delete `C:\JeffLocal\Scheduled` while the Cowork task exists.** I did,
  reasoning Cowork held its own copy. WRONG - it reads the file live from that path and the
  task broke instantly ("Task file not found"). Restored, verified by hash. Deleting the
  TASK in Cowork removes the folder cleanly; that is the safe order.
- **Do NOT expect a Cowork scheduled task to work on the folder it points at.** It writes
  its own file into that folder, protects the path, then drops the folder. Structural.
  Applies to SMCPHARMA equally.
- **Do NOT use `git ... 2>&1` while `$ErrorActionPreference = "Stop"`.** Ordinary git
  notices ("LF will be replaced by CRLF") become fatal and silently abandon the commit.
  Judge git on `$LASTEXITCODE`.
- **Do NOT weaken `.gitignore`.** `git add -A` is only safe because .gitignore excludes
  `.env`, `*.sqlite`, `*.db`, `logs/`, `*.log`, `*.jsonl`, `queue/`, `outputs/`, `data/`.
  That is what keeps secrets and patient data out of the repo.
- Bracket patterns in `.gitignore` must be escaped (`dict\[str`) or git treats them as
  globs and silently fails to match.
- Bash heredocs in this environment mangle apostrophes and `\\`. Write patch scripts with
  the file writer, not `cat <<EOF`. These `.ps1`/`.py` files are CRLF - normalise before
  matching.

## HOW THE SESSION CLOSED

Live evening run on 20 Aug: report, session log, commit, **16-commit backlog pushed**,
restore tag cut, WhatsApp delivered clean. Then the untracked backlog (324 files, ~4 MB,
checked for secrets first) swept in a supervised commit, and the SMCPHARMA gitlink undone.

**Verified in production on 21 Aug:** both scheduled runs fired unattended -
19:00 (`ff47dfa`) and 07:00 (`de39bf6`). Log shows *"Staleness check: both projects have a
real session log within 24h"* - no false banner. The St Marks close ran both times
(`362404b`, `00d4e04`). WhatsApp delivered 6 then 5 chunks with **no "send failed"**.
Everything built yesterday is now proven live, not just tested.

29 automated assertions pass (`scratchpad/test-sessionlog.ps1`, `test-staleness.ps1`).

A **SessionStart hook** (`~/.claude/hooks/session_start_memory.py`, wired in
`~/.claude/settings.json`) now surfaces PROJECT_MEMORY, HANDOFF and the newest session log
at the start of every session in both projects, and warns on staleness or placeholder logs.
Confirmed firing.

## NEXT + BLOCKERS

**Next**
1. **Delete the Cowork task "Daily session end 1800"** - Saeed approved, but it can only be
   done from the Cowork UI. Deleting also removes `C:\JeffLocal\Scheduled` and clears the
   protected-root block. Instructions are archived at
   `docs/archive/cowork-daily-session-end-1800-SKILL.md`, so nothing is lost.
2. Resume the security items - none can move without Saeed.

**Blockers**
- None on the brief pipeline. Fixed, tested, and proven live over two scheduled runs.
- Unchanged since 11 Aug: 3 security items (unauthenticated intake endpoint, HMAC secret in
  git history, directory ACLs).

**Waiting on Saeed - ONE OF THESE IS A REAL RISK**
- **SMCPHARMA deploys live on push, and the close now pushes everything.** Anything left
  uncommitted under `site\` goes live to patients at 19:00 without review. Offered a guard:
  commit everything as normal but skip the auto-push for SMCPHARMA when `site\` is dirty.
  **Not yet answered.**
- `graphify-out/` is now committed nightly in both repos - small but churns. Keep or ignore?
- Delete the Cowork task (above).

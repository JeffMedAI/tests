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

**Waiting on Saeed**
- Nothing outstanding. The Cowork task is deleted and graphify is settled (both below).

**Closed 2026-08-21**
- **Cowork task deleted.** `C:\JeffLocal\Scheduled` no longer exists, so the protected-root
  block is cleared - Cowork can mount this folder again for ordinary *interactive* sessions.
  Never for a *scheduled* task pointed at it. Instructions archived in `docs\archive\`.
- **graphify sorted.** `graphify-out\` is gitignored in both repos (generated index, not
  source). JeffLocal refreshes it at every close and prunes snapshots to the 3 newest;
  St Marks dropped it entirely. **The "duplicate" graph folders were graphify's own dated
  backups — it writes one on every run (~2.5MB), so a nightly refresh would have added
  ~900MB/year.** That is why ignoring only `cache\` would not have stopped the churn.

---

## ADDED 2026-08-21 — LIVE-DEPLOY GUARD (the risk above is now CLOSED)

The close pushes everything, and SMCPHARMA is git-connected to Cloudflare — so unfinished
work in `site\` would have published itself to patients at 19:00, unreviewed. Fixed:

- New `-ProtectPath` parameter on `strategy_daily.ps1`. If the named folder has unfinished
  work at close: **the commit still happens (nothing is lost), the push is held**, and the
  restore tag is skipped.
- Watches **`site\`** on St Marks and **`dashboard\`** on JeffLocal.
- **Be honest about JeffLocal:** a push here deploys nothing — `dashboard\` is already live
  from disk on port 8765 — so holding protects nothing *live*. Saeed chose the same shape
  anyway, for one consistent rule. On this project the **warning** is the valuable half.
- Same-evening warning: the close emits `PUSH-HELD|...`; `combined_brief.ps1` catches it and
  prepends a loud banner to the report file *before* the send reads it. One message, no
  second browser session, no dedup problem.
- **36 assertions pass.** Fixtures now get a real bare remote, so "held" is provably distinct
  from "push failed" — the test is simply whether `origin/main` advanced.
- Detection verified against both real repos; both clean, so tonight pushes normally.

**Test-harness trap worth remembering:** assertions on log text were silently passing
nothing, because `Write-Log` uses `Write-Host`, which lands on the Information stream.
`2>&1` misses it; use `*>&1`.

**Also answered 2026-08-21:** should the dashboard be rebuilt as a Cloudflare Worker like
St Marks, for uniformity? **No** — it holds patient data, and a Worker runs on Cloudflare's
machines, so the data would leave the building (CLAUDE.md line 58). Also a full
Python→JavaScript rewrite that would sever it from the local pipeline. Uniformity is served
instead by `docs\SHIPPING.md`, now in both repos: same template, project-specific content,
one cross-reference line so the two ship models are never confused again.

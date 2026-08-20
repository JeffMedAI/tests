# ARCHIVE - Cowork scheduled task "Daily session end 1800" (RETIRED 2026-08-20)

This is the verbatim instruction file that drove the Cowork scheduled task which used to
perform the nightly session close. It is kept here **only as a record**. The task is
retired and must not be rebuilt in Cowork.

**Why it was retired:** Cowork writes each scheduled task's own file into the folder the
task points at (`C:\JeffLocal\Scheduled\<task>\SKILL.md`), marks that path a *protected
root*, then drops any folder overlapping it. The task therefore started every night with
no access to `C:\JeffLocal` at all, and failed silently. Cowork's own log:

```
[Lifecycle] Dropping folder overlapping protected root from session
local_...: C:\JeffLocal (root: C:\JeffLocal\Scheduled)
```

Confirmed by experiment on 2026-08-20: creating a second test task produced the same
folder inside the project again. It is structural, not a settings problem, and it applies
to `C:\JeffLocal\SMCPHARMA` equally.

**What replaced it:** the 19:00 PowerShell run (`scripts\daily\combined_brief.ps1` ->
`strategy_daily.ps1 -NoSend`) now writes the session log from the day's git activity,
refreshes `HANDOFF.md`, updates `PROJECT_MEMORY.md`, commits, pushes and cuts the restore
tag. See the session log for 2026-08-20.

Two errors in the instructions below, preserved as written: it says `REPO BRANCH: sandbox`
when the repo is on `main`, and the header says 18:00 while the task actually ran at 19:00.

---

## Original SKILL.md, verbatim

```markdown
---
name: daily-session-end-1800
description: Daily session end protocol — writes session log, updates PROJECT_MEMORY, commits at 18:00
---

You are running the Avamed (JeffLocal) daily session end protocol. Execute every step in order. No confirmation needed — this is automated.

PROJECT: C:\JeffLocal
REPO BRANCH: sandbox
PRODUCTION: C:\JeffLocal\dashboard\ (port 8765)

## STEP 1 — Read today's git activity
Run: git -C C:\JeffLocal log --oneline --since="midnight" --until="now"
This gives you what was done today. If nothing — note "No commits today."

## STEP 2 — Check for existing session log
Check C:\JeffLocal\docs\sessions\ for any file starting with today's date (YYYY-MM-DD).
If one already exists AND it looks complete, skip to Step 5.
If none exists, or the existing one is a placeholder, write/overwrite it now.

## STEP 3 — Write today's session log
File path: C:\JeffLocal\docs\sessions\YYYY-MM-DD-1800.md (use today's actual date)

Use this template exactly:
    # SESSION SUMMARY — [YYYY-MM-DD 18:00]
    # Tool: Cowork (automated session end)
    # Written by: Claude scheduled task at 18:00

    ---

    ## WHAT WE DID TODAY

    [List each git commit from Step 1 as a plain-English bullet.
    If a commit message is technical, translate it for Saeed.
    If no commits: "No work committed today."]

    ---

    ## PENDING SAEED APPROVALS (from PROJECT_MEMORY)

    [Read C:\JeffLocal\PROJECT_MEMORY.md section "Pending Saeed approvals" and copy the list here as-is]

    ---

    ## OPEN TASKS (from PROJECT_MEMORY)

    [Read C:\JeffLocal\PROJECT_MEMORY.md section "Open technical tasks" and copy the top 3 items]

    ---

    ## WHAT TO DO TOMORROW

    [Based on open tasks and pending approvals, list the top 2-3 most urgent actions for next session]

    ---

    ## GIT STATE

    Latest commit: [hash from git log]
    Branch: sandbox

## STEP 4 — Update PROJECT_MEMORY.md
Open C:\JeffLocal\PROJECT_MEMORY.md.
- Update the "Last updated" date at the top to today's date.
- Under "GIT STATE", update "Latest:" to the most recent commit hash and message.
- Under "CURRENT STATUS", update the date heading to today.
- Do NOT change any other content unless something is clearly wrong or stale.

## STEP 5 — Commit
Run these commands in order:
    cd C:\JeffLocal
    git add docs\sessions\ PROJECT_MEMORY.md
    git commit -m "memory: session end protocol YYYY-MM-DD 18:00"
    git push origin HEAD
Replace YYYY-MM-DD with today's actual date.

## STEP 6 — Done
Output a 3-line plain English summary:
Line 1: "Session log written: [filename]"
Line 2: "PROJECT_MEMORY updated."
Line 3: "Git committed and pushed." (or "Git push failed — will retry on next launch." if push errors)

Rules:
- UK English
- No jargon
- If any step fails, note the failure clearly but continue to the remaining steps
- Never delete files — only write and update
- Never touch auth.py, enforce_auth.py, or patient_matcher.py
- Never change production logic — this task is documentation only
```

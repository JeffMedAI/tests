# JEFFLOCAL — SESSION START INSTRUCTIONS
# This file is read automatically by Claude at every session start.
# Do NOT skip any step. Do NOT start work until Step 4 is complete.

---

## STEP 1 — READ PROJECT MEMORY (mandatory, every session)

Read this file in full: C:\JeffLocal\PROJECT_MEMORY.md

It contains:
- Current project status
- All pending Saeed approvals
- Open tasks by priority
- Key file paths
- Known process rules
- Last session summary

---

## STEP 2 — READ TODAY'S SESSION LOGS (if any exist)

Check: C:\JeffLocal\docs\sessions\
Read any file dated today (YYYY-MM-DD format).
These are summaries of what happened in earlier sessions today (Cowork, Code, chat).

Also read: C:\JeffLocal\docs\reports\{yesterday's date}.md
This is the Strategy Agent's overnight daily report — compiled at 07:00 automatically.
It tells you: what was done yesterday, what is planned today, what is blocking.

---

## STEP 3 — UPDATE PROJECT_MEMORY.md

After reading the above, update the "CURRENT STATUS" section of PROJECT_MEMORY.md:
- Tick off anything that was completed since the last update
- Add any new pending approvals
- Update the git state section with latest commit
- Update the "last updated" date at the top

Keep it accurate. This is the source of truth for all future sessions.

---

## STEP 4 — REPORT TO SAEED BEFORE DOING ANYTHING ELSE

Produce this report in chat, then WAIT for Saeed's go-ahead:

```
SESSION START — [date] [time]
Source: [Cowork / Claude Code / Claude.ai]

WHAT WE DID LAST SESSION:
[2-4 bullet points from session logs or PROJECT_MEMORY.md]

WHAT IS PLANNED TODAY:
[top 2-3 tasks from open task queue]

WHAT IS BLOCKING US:
[list blockers or "None"]

PENDING YOUR APPROVAL:
[list items needing Saeed sign-off, or "None"]

RECOMMENDED FIRST ACTION:
[one sentence]
```

Then WAIT. Do not assign tasks or make changes until Saeed responds.

---

## STEP 5 — SESSION END (before closing)

At end of every session, do ALL of the following:

1. Write a session summary to: C:\JeffLocal\docs\sessions\YYYY-MM-DD-HHMM.md
   Use the template at: C:\JeffLocal\docs\sessions\SESSION_TEMPLATE.md

2. Update PROJECT_MEMORY.md:
   - Current status section
   - Pending approvals
   - Open tasks
   - Git state (latest commit hash)

3. Commit and push:
   cd C:\JeffLocal
   git add PROJECT_MEMORY.md docs\sessions\
   git commit -m "memory: session summary YYYY-MM-DD"
   git push origin HEAD

4. Tell Saeed: "Session saved. Memory updated. Ready to pick up tomorrow."

---

## ABOUT THE MEMORY SYSTEM

Three layers keep memory alive across reinstalls, crashes, and tool changes:

1. PROJECT_MEMORY.md (this repo, always on disk) — full project state
2. docs\sessions\ (this repo) — per-session summaries from all tools
3. docs\reports\YYYY-MM-DD.md (generated 07:00 daily) — overnight compiled briefing

The daily 07:00 script (scripts\daily\strategy_daily.ps1) automatically:
- Reads all session logs from the last 24 hours
- Updates the "Current Status" section of PROJECT_MEMORY.md
- Writes the daily briefing report to docs\reports\{today}.md

Even if a session ends without a clean save, the 07:00 script catches up.

---

## CHAT HISTORY FROM OTHER TOOLS

Claude.ai web chat, Claude Cowork, and Claude Code do not share session memory
natively. To bridge this:

- At end of every Cowork session: write summary to docs\sessions\
- At end of every Claude Code session: write summary to docs\sessions\
- For claude.ai web chat: paste key decisions into docs\sessions\ manually,
  or ask Claude to "save this conversation to session log"

The Strategy Agent compiles all of these at 07:00 into the daily briefing.

---

## KEY FACTS (always true)

- Owner: Saeed (5256863@gmail.com)
- Product: JeffLocal — AI patient triage for UK GP surgeries (Avamed)
- Pilot: Churchtown Medical Centre, Southport
- Production dashboard: https://dashboard.app-avamed.uk
- PRODUCTION path: C:\JeffLocal\dashboard\ (port 8765) — never edit without Saeed approval
- SANDBOX path: C:\JeffLocal\sandbox\dashboard\ (port 5000) — safe to edit
- Git branch "sandbox" does NOT mean sandbox directory — always verify path
- Saeed's approval is required every session — approvals do not carry over

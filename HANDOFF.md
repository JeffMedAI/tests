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

**Last session:** 2026-07-08 (continuation session)
**Closed by:** Claude (Sonnet 4.6)
**Last commit:** a168af8 feat: SQLite hot backup — TDD tests, script, Task Scheduler entry
**Production:** dashboard.app-avamed.uk (Cloudflare tunnel → localhost:8765), watchdog-managed, LIVE

---

## WORK SCOPE

Production-readiness sprint: 3 tasks approved by Saeed — install gemma4:e4b fallback, SQLite backup script, split main.py into modules. First two complete this session. Third documented but NOT started (Saeed's instruction).

## WHAT WORKED / WHAT DIDN'T

**Worked:**
- gemma4:e4b (9.6 GB) pulled and confirmed in ollama list
- TDD backup script: 22/22 tests GREEN. Failure on first run was Windows temp dir permissions — fix: use `--basetemp` flag pointing to scratchpad directory
- SQLite hot backup confirmed on real DB (568 KB, integrity OK, pruned 0)
- JeffLocal-SQLiteBackup Task Scheduler entry registered (daily 02:15) without admin rights — key: do NOT use `-RunLevel Highest` flag
- `.gitignore` needed `!scripts/backup/` exception — `backup/` rule was blocking the new script files

**Didn't work / Gotchas:**
- `Register-ScheduledTask -RunLevel Highest` → Access Denied (not admin). Remove that flag to register as current user
- pytest `tmp_path` fixture crashes on Windows if `C:\Users\s5256\AppData\Local\Temp\pytest-of-s5256` has a permissions lock — use `--basetemp=<scratchpad>` to work around
- PowerShell `git commit -m "$(cat <<'EOF'..."` heredoc syntax does NOT work in PowerShell — use `$msg = @'...'@; git commit -m $msg` instead
- `2>&1` redirect on native executables in PowerShell triggers cosmetic NativeCommandError even on exit code 0 — not a real error, just ignore it

**Files changed this session:**
- `scripts/backup/backup_db.py` — new: SQLite hot backup with 30-day rolling retention
- `scripts/backup/test_backup.py` — new: 22 TDD tests
- `scripts/service_control/install_scheduled_tasks.ps1` — added JeffLocal-SQLiteBackup entry
- `.gitignore` — added `!scripts/backup/` exception

## HOW THE SESSION CLOSED

- Task 1 (gemma4:e4b): DONE
- Task 2 (SQLite backup): DONE — tests GREEN, script runs, scheduled
- Task 3 (main.py split): PLAN WRITTEN, NOT STARTED — Saeed said "add to pending list"
- PROJECT_MEMORY, HANDOFF, graphify updated
- Commit a168af8 on sandbox branch

## NEXT + BLOCKERS

**Next actions:**
1. **Task 3: Split main.py** — branch `refactor/split-main-py`, extraction order in PROJECT_MEMORY task list. Multi-session. Do NOT start without Saeed's go-ahead each session.
2. Remove legacy static-salt task from PROJECT_MEMORY (already done in auth.py — verify first)
3. Saeed to provide real staff accounts → pilot go-live unblocked

**Blockers:**
- No real staff accounts (Saeed must provide names, roles, emails)
- Governance gates 1-7 unsigned
- JEFF_WEBHOOK_SECRET not set (required before any live Jeff traffic)

**Pending Saeed:**
- Staff account details
- Governance gates 1-7 sign-off
- JEFF_WEBHOOK_SECRET in Windows env
- n8n API key rotation ("later")
- Go-ahead to start Task 3 (main.py split) each session

**Durable gotchas:**
- PRODUCTION is always `C:\JeffLocal\dashboard\` (port 8765). Git branch named "sandbox" — irrelevant to paths.
- n8n MCP `update_workflow` always fails. Use Python HTTP PUT script instead.
- Audit ALL HTTP nodes in ALL workflows when fixing n8n auth — not just the ones currently failing.
- LLM output must NEVER set verification_status, safe_to_queue, priority, or patient-identity fields.
- Git lock files can pile up — check `.git/*.lock` if commit fails.
- pytest `tmp_path` on Windows: use `--basetemp=<scratchpad>` if access denied on default temp dir.
- Task Scheduler registration: do NOT use `-RunLevel Highest`, it requires admin. Omit it to register as current user.

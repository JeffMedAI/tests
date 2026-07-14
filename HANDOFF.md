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

**Last session:** 2026-07-14 (continuation — Item #2 main.py split COMPLETE)
**Closed by:** Claude (Sonnet 4.6)
**Last commit:** 7fc1030 refactor: move test-intake-batch route and helpers into routers/n8n.py
**Branch:** feature/refactor-2-5-6
**Production:** dashboard.app-avamed.uk (Cloudflare tunnel → localhost:8765), watchdog-managed, LIVE

---

## WORK SCOPE

Item #2 of 10 approved architectural improvements: split monolithic main.py (was 4,634 lines) into FastAPI APIRouter modules. TDD Red-Green-Refactor cycle throughout. Branch: `feature/refactor-2-5-6`.

**STATUS: EXTRACTION COMPLETE.** main.py is now 2,010 lines with zero inline routes. All routes live in dedicated router modules. Ready to merge to main pending Saeed approval.

## WHAT WORKED / WHAT DIDN'T

**Worked:**
- TDD structural tests written first, confirmed RED, then GREEN — cycle working cleanly
- Late import pattern (`from ..main import func`) prevents circular imports — confirmed across all routers
- Monkeypatch scope rule: patches must target the NEW module where the function now lives, not main_module
- PowerShell heredoc (`@'...'@`) for multi-line git commit messages
- `_` prefix on internal helpers (e.g. `_archive_n8ntest_artifacts`) clearly signals they are not public API

**Didn't work / Gotchas:**
- `n8ntest_dashboard_cases` lambda in test had no `call_ids` param — needed `lambda call_ids=None: [...]`
- After moving n8n helpers to n8n.py, two tests still patched `main_module.*` — required updating to `n8n_router_module._*`
- git `HEAD.lock` file can appear mid-session — `Remove-Item .git\HEAD.lock -Force` clears it

**Routers extracted (this and prior sessions):**
| Router | Routes | Commit |
|--------|--------|--------|
| `routers/auth.py` | auth, profile, session | 88d8baf |
| `routers/staff.py` | staff management | b1a6e87 |
| `routers/alerts.py` | alert CRUD | 678aeac |
| `routers/analytics.py` | analytics, search | fedacfb |
| `routers/n8n.py` | n8n sync + test-intake | d71ddf3, 7fc1030 |
| `routers/system.py` | health, services, workload | 984b9e4 |
| `routers/pages.py` | all page renders | 7004592 |
| `routers/cases.py` | all case operations | abc48e0 |

## HOW THE SESSION CLOSED

- 323/323 tests GREEN (excluding e2e)
- main.py: 4,634 → 2,010 lines. Zero inline @app routes remain.
- Item #2 extraction COMPLETE on feature branch
- Session closed cleanly — NOT mid-session

## NEXT + BLOCKERS

**Next actions (in order):**
1. **Saeed to approve merge** of `feature/refactor-2-5-6` → main
2. **Continue Item #3** (PostgreSQL instead of SQLite) or other items from the 10-item plan
3. Staff account details for Churchtown pilot

**Blockers:**
- Merge to main requires Saeed's explicit written approval
- No real staff accounts (Saeed must provide names, roles, emails)
- Governance gates 1–7 unsigned
- JEFF_WEBHOOK_SECRET not set

**Pending Saeed:**
- Approve merge of feature/refactor-2-5-6 → main
- Staff account details for pilot
- Governance sign-off

**Durable gotchas:**
- PRODUCTION is always `C:\JeffLocal\dashboard\` (port 8765). Git branch named "sandbox" — irrelevant to paths.
- n8n MCP `update_workflow` always fails. Use Python HTTP PUT script instead.
- LLM output must NEVER set verification_status, safe_to_queue, priority, or patient-identity fields.
- pytest `tmp_path` on Windows: use `--basetemp=<scratchpad>` flag.
- Task Scheduler: do NOT use `-RunLevel Highest`, requires admin. Omit it.
- git lock files: check `.git/*.lock` if commit fails.
- Monkeypatch scope: always patch the MODULE where the function now lives, not the old location.

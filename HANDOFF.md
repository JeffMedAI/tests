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

**Last session:** 2026-07-14 (continuation — Item #2 main.py split)
**Closed by:** Claude (Sonnet 4.6)
**Last commit:** 984b9e4 refactor: extract system/infrastructure routes into routers/system.py
**Branch:** feature/refactor-2-5-6
**Production:** dashboard.app-avamed.uk (Cloudflare tunnel → localhost:8765), watchdog-managed, LIVE

---

## WORK SCOPE

Item #2 of 10 approved architectural improvements: split monolithic main.py (was 4,634 lines) into FastAPI APIRouter modules. TDD Red-Green-Refactor cycle throughout. Branch: `feature/refactor-2-5-6`.

## WHAT WORKED / WHAT DIDN'T

**Worked:**
- TDD structural tests written first, confirmed RED (collection error), then GREEN after router created — cycle working cleanly
- Late import pattern for main.py functions (e.g. `from ..main import active_red_flag_clause`) prevents circular imports — confirmed working across all 6 routers
- Monkeypatch scope rule: when a function moves to a new module, ALL tests must patch BOTH `main_module.X` AND `new_module.X` if both paths exist, OR just `new_module.X` if main.py no longer has it
- `--basetemp` flag required for pytest on Windows (temp dir permission issue)
- PowerShell heredoc: use `@'...'@` not `$(cat <<'EOF'...)` — bash heredoc syntax fails in PowerShell

**Didn't work / Gotchas:**
- `fallback_service_statuses` and `get_service_statuses` were called directly in main.py's `index` route AND `get_system_workload` — removing them without updating those call sites caused NameError. Fixed with late imports (`from .routers.system import _get_service_statuses, _service_status`).
- `subprocess` patch for `api_services_refresh` test must target `system_router_module.subprocess`, not `main_module.subprocess` — the route is now in system.py
- git `HEAD.lock` file appeared mid-session (pre-compact hook left it) — `Remove-Item .git\HEAD.lock -Force` clears it

**Routers extracted this session:**
- `app/routers/n8n.py` — 4 routes (commit d71ddf3)
- `app/routers/system.py` — 7 routes + 3 helpers (commit 984b9e4)

**Routers extracted in prior sessions:**
- `app/helpers.py`, `app/consts.py`, `app/templates_config.py`
- `app/routers/auth.py`, `app/routers/staff.py`, `app/routers/alerts.py`, `app/routers/analytics.py`

## HOW THE SESSION CLOSED

- 314/314 tests GREEN (excluding e2e and intentional RED `test_routers_cases.py`)
- main.py: 4,634 → 3,292 lines
- Compacting mid-session at Saeed's request to free context window
- Session NOT fully closed — work continues after compact

## NEXT + BLOCKERS

**Next actions (in order):**
1. **`routers/pages.py`** — extract page-rendering routes: `/`, `/requests`, `/patients`, `/reports`, `/settings`, `/import`, `/api/import`. These render Jinja2 templates and call many helper functions in main.py. Use late imports for all of them.
2. **`routers/cases.py`** — DEFERRED. Too many entangled helper functions (`prepare_case`, `update_staff_fields`, `batch_resolve_cases`, etc.). Extract `case_queries.py` first, then move routes. Do not attempt until pages.py is done.
3. After all routers done: merge `feature/refactor-2-5-6` → main (Saeed approval required)

**Blockers:**
- No real staff accounts (Saeed must provide names, roles, emails) — pilot blocked
- Governance gates 1-7 unsigned
- JEFF_WEBHOOK_SECRET not set

**Pending Saeed:**
- Staff account details for pilot
- Governance sign-off
- Go-ahead to continue pages.py extraction (already given implicitly — "continue")

**Durable gotchas:**
- PRODUCTION is always `C:\JeffLocal\dashboard\` (port 8765). Git branch named "sandbox" — irrelevant to paths.
- n8n MCP `update_workflow` always fails. Use Python HTTP PUT script instead.
- LLM output must NEVER set verification_status, safe_to_queue, priority, or patient-identity fields.
- pytest `tmp_path` on Windows: use `--basetemp=<scratchpad>` flag.
- Task Scheduler: do NOT use `-RunLevel Highest`, requires admin. Omit it.
- git lock files: check `.git/*.lock` if commit fails.
- `test_routers_cases.py` is intentional RED — always `--ignore` it until cases router is built.

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

**Last session:** 2026-07-08 09:51
**Closed by:** Claude (Sonnet 4.6)
**Last commit:** (run `git log --oneline -1`)
**Production:** dashboard.app-avamed.uk (Cloudflare tunnel → localhost:8765), watchdog-managed, LIVE

---

## WORK SCOPE

Fix n8n workflow execution failures. Both WF03 (Red Flag Scan) and WF04 (Overdue Scan) were failing with `status=error, finished=false` because n8n HTTP nodes were hitting login-protected endpoints that returned 302 HTML redirects instead of JSON.

## WHAT WORKED / WHAT DIDN'T

**Worked:**
- Route rename pattern (`/api/xxx` → `/api/n8n/xxx`) — the `/api/n8n/` prefix is already in `AUTH_PUBLIC_PREFIXES` at main.py:101, so renamed routes bypass auth without any new allowlist changes
- Python script (`fix_n8n_auth_urls.py`) to update n8n workflow nodes via API — bypassed the n8n MCP tool which always fails with "additional properties" schema errors
- WF03 confirmed success at 08:50 UTC after all 3 routes were renamed

**Didn't work / Gotchas:**
- n8n MCP `update_workflow` tool: always fails — do NOT use it. Use direct HTTP PUT via Python (pattern in `fix_n8n_auth_urls.py`)
- Initial fix only renamed 2 routes (`/api/red-flags` and `/api/overdue`). WF03 then failed on a SECOND node — `Log Red Flag Alert` calling `/api/alerts/log`. Had to fix that too. Lesson: when fixing auth on a workflow, audit ALL HTTP nodes in that workflow, not just the first failing one
- WF04 had same `Log Overdue Alert` node calling `/api/alerts/log` — fixed in same pass

**Files changed:**
- `dashboard/app/main.py` — 3 route decorators renamed (lines 2497, 2520, 3390)
- `scripts/service_control/fix_n8n_auth_urls.py` — new file, ran once to update n8n

## HOW THE SESSION CLOSED

- WF03 verified SUCCESS (08:50 UTC execution, `status=success finished=True`)
- WF04 fix applied but not yet confirmed (next run ~09:00 UTC, same fix pattern)
- Dashboard up, all 3 new routes returning 200
- Session log written, HANDOFF written, PROJECT_MEMORY updated
- Restore tag and commit to follow

## NEXT + BLOCKERS

**Next actions:**
1. Confirm WF04 success on next scheduled run (09:00 UTC)
2. Remove legacy static-salt password fallback (Backend Task #1)
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

**Durable gotchas (keep until proven otherwise):**
- PRODUCTION is always `C:\JeffLocal\dashboard\` (port 8765). Git branch named "sandbox" — irrelevant to paths.
- n8n MCP `update_workflow` always fails. Use Python HTTP PUT script instead.
- When fixing n8n auth, audit ALL HTTP nodes in a workflow — not just the first failing one.
- LLM output must NEVER set verification_status, safe_to_queue, priority, or patient-identity fields.
- 5 items in deadletter queue; no replay tooling yet.

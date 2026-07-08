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

**Last session:** 2026-07-08 10:15
**Closed by:** Claude (Sonnet 4.6)
**Last commit:** cfb24d0 chore: add gstack skill routing rules to CLAUDE.md
**Production:** dashboard.app-avamed.uk (Cloudflare tunnel → localhost:8765), watchdog-managed, LIVE

---

## WORK SCOPE

Fix all n8n workflow execution failures. All 6 workflows audited. Install and configure gstack.

## WHAT WORKED / WHAT DIDN'T

**Worked:**
- Route rename pattern (`/api/xxx` → `/api/n8n/xxx`) — the `/api/n8n/` prefix is already in `AUTH_PUBLIC_PREFIXES` at main.py:101, so renamed routes bypass auth without any new allowlist changes
- Python script (`fix_n8n_auth_urls.py`) to update n8n workflow nodes via API — works reliably
- WF03 confirmed success at 08:50 UTC after fix
- WF05 (Daily Summary) was also broken — failing every day since 5 July, now fixed
- WF02 (Dashboard Sync, inactive) pre-fixed so it won't break when activated
- Full audit: all 9 dashboard HTTP nodes across all 6 workflows now on `/api/n8n/` prefix

**Didn't work / Gotchas:**
- n8n MCP `update_workflow` tool: always fails — do NOT use it. Use direct HTTP PUT via Python (pattern in `fix_n8n_auth_urls.py`)
- When fixing n8n auth, audit ALL HTTP nodes in every workflow, not just the first failing one — WF05 would have kept failing if Saeed hadn't asked about workflows 1, 2, 6
- Multiple git lock files appeared during this session — `index.lock`, `HEAD.lock`, `sandbox.lock`, `maintenance.lock`. Clear with `rm -f .git/*.lock .git/refs/heads/*.lock .git/objects/maintenance.lock` if git commits fail

**Files changed this session:**
- `dashboard/app/main.py` — 5 route decorators renamed total (lines 2497, 2520, 2483, 2556, 3390)
- `scripts/service_control/fix_n8n_auth_urls.py` — new file, reusable URL fix script
- `CLAUDE.md` — gstack routing rules appended

## HOW THE SESSION CLOSED

- All 9 n8n dashboard HTTP nodes confirmed clean (audit printed, all OK)
- WF03 verified SUCCESS. WF04 fix applied. WF05 fix applied. WF02 pre-fixed.
- gstack installed: telemetry off, proactive on, routing rules in CLAUDE.md
- Commits: 4d8b127 → 60fd606 → cfb24d0. Pushed. Restore tag restore/2026-07-08-0951.

## NEXT + BLOCKERS

**Next actions:**
1. Confirm WF04 (next 30-min tick) and WF05 (tomorrow 11:00 UTC) succeed
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

**Durable gotchas:**
- PRODUCTION is always `C:\JeffLocal\dashboard\` (port 8765). Git branch named "sandbox" — irrelevant to paths.
- n8n MCP `update_workflow` always fails. Use Python HTTP PUT script instead.
- Audit ALL HTTP nodes in ALL workflows when fixing n8n auth — not just the ones that are currently failing.
- LLM output must NEVER set verification_status, safe_to_queue, priority, or patient-identity fields.
- 5 items in deadletter queue; no replay tooling yet.
- Git lock files can pile up — check for `*.lock` in `.git/` and subdirs if commit fails.

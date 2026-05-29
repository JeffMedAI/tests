# RESTORE POINT — 2026-05-29
Created: 2026-05-29 after Claude Desktop reinstall
State: All tools verified working (computer use + Claude in Chrome)

## What is included
- agents/ — all 8 agent CLAUDE.md files (lead, backend, frontend, database, test, security, devops, strategy)
- dashboard/ — production Flask dashboard (port 8765, Cloudflare tunnel)
- governance/ — full governance framework, approval workflow, change log
- docs/ — project docs, reports, marketing
- config/ — app settings, security config
- scripts/ — daily task scripts including strategy_daily.ps1

## Key status at this restore point
- Issue #1 (sidebar toggle): DEPLOYED
- Cookie fix (session expiry): written, tested, AWAITING SAEED APPROVAL
- Sandbox "Status Degraded" fix: 1-line change, AWAITING SAEED APPROVAL
- Issue #2 (mobile urgent banner): investigation complete, ready to implement
- All 8 agents: CLAUDE.md files present and current
- Strategy Agent: fully onboarded, daily script at scripts/daily/strategy_daily.ps1
- Production dashboard live at dashboard.app-avamed.uk

## To restore
git checkout RESTORE_20260529
or manually copy these folders back to C:\JeffLocal\

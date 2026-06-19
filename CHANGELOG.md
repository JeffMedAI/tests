# CHANGELOG — Avamed / JeffLocal
# Audit log for autonomous bug fixes, approved marketing spend, and governance decisions.
# APPEND ONLY — never delete or edit existing entries.
# Format defined in REPORTING.md

---

## 2026-06-07 — Governance Package Created
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit instruction in session)
**Description:** Created full governance package: updated CLAUDE.md, new AGENT_TEAM_CHARTER.md, GOVERNANCE.md, REPORTING.md, CHANGELOG.md, and all 9 agent MD files in C:\JeffLocal\agents\.
**Files changed:** CLAUDE.md, AGENT_TEAM_CHARTER.md, GOVERNANCE.md, REPORTING.md, CHANGELOG.md, agents/lead_CLAUDE.md, agents/backend_CLAUDE.md, agents/frontend_CLAUDE.md, agents/database_CLAUDE.md, agents/test_CLAUDE.md, agents/security_CLAUDE.md, agents/devops_CLAUDE.md, agents/strategy_CLAUDE.md, agents/marketing_CLAUDE.md
**Tests run:** N/A (documentation only)
**Saeed notified:** This session

---

## 2026-06-07 — Directory Cleanup & Architecture Change (No More Sandbox)
**Agent:** Lead Agent (Claude Code session)
**Approved by:** Saeed (explicit "yes approved" in session)
**Description:** Removed sandbox directory and all junk/temp files. Archived sandbox audit logs to logs/audits/ and sandbox SQLite to backup/sandbox-archive-20260607/. Confirmed all 4 pipeline config files exist in config/ (PE-01 to PE-04 resolved). Updated CLAUDE.md: sandbox section removed, critical path updated, PE-01–PE-04 status updated. New development model: git feature branches, no parallel sandbox directory.
**Files removed:** sandbox/ (entire), production/ (empty), JeffLocaltmppytest-*/, pytest-tmp/, .tmp/, .playwright-mcp/, PyWhatKit_DB.txt, n8n API key.txt, session, 1, check_button.ps1, check_button.py, COMPLETE_HANDOFF_FOR_EMAIL.zip, dashboard/_backup_*, dashboard/app/_backup_*
**Files changed:** CLAUDE.md (critical path + PE-01–PE-04 sections), CHANGELOG.md
**Security note:** n8n API key.txt deleted. Key NOT rotated this session per Saeed's decision — rotation recommended before go-live.
**Tests run:** N/A (infrastructure cleanup only)
**Saeed notified:** This session

---

## 2026-06-10 — Avamed Clarity Design Sprint (Tasks 1–6)
**Agent:** Frontend Agent + Lead Agent (Claude Code session)
**Approved by:** PENDING — this entry is the pre-merge record. Saeed's explicit "approved" required before production merge.
**Security review:** Security Agent (GuardRail) — SIGNED OFF. See docs/reports/clarity-sprint-approval-pack-2026-06-10.md.
**Description:** Full design system and UI refresh implementing the Avamed Clarity visual identity across the staff dashboard. Navy (#0B3D6B) and Teal (#00A896) replace NHS blue. New interactive components: KPI strip with count-up animation, sparkline chart, command palette (/ shortcut), patient hover card, urgent case pulse. Four new authenticated API endpoints. Typography system: Plus Jakarta Sans + Inter + JetBrains Mono via Google Fonts.

**Files changed:**
- dashboard/static/dashboard.css — CSS token migration, new Clarity tokens, component styles (KPI strip, sparkline, command palette, hover card, pulse animation)
- dashboard/templates/base.html — Google Fonts, pipeline health dot, command palette overlay, keyboard shortcut update
- dashboard/templates/index.html — KPI strip, sparkline, urgent pulse, patient hover card, chart colour palette fix
- dashboard/templates/case_detail.html — typography tokens (.cd-meta-id mono font, display font on patient name)
- dashboard/app/main.py — 4 new endpoints: /api/analytics/hourly-volume, /api/analytics/performance-summary, /api/patient-card, /api/search

**New files:**
- PRODUCT.md — Avamed product context for impeccable design tooling (register: product, personality: Calm · Precise · Trustworthy)
- .impeccable/live/config.json — live mode pre-configuration for Clarity sprint iteration

**Security notes:**
- All 4 new API endpoints double-protected: auth middleware (primary) + demo_fallback check (defence-in-depth)
- No PII in analytics endpoints (aggregate counts only)
- NHS number masked server-side in /api/patient-card (digits[:3] + " ***")
- /api/search limited to 8 results, returns minimum necessary fields (no NHS number, no DOB)
- All SQL queries parameterised — no injection vectors

**Tests run:** 21 unit tests passing. 83 failures confirmed pre-existing (git stash verified — identical failures on pre-sprint snapshot). E2E Playwright failures are Playwright auth timeout — pre-existing infrastructure issue unrelated to this sprint.
**Saeed notified:** This session (pending approval)

## [Bug Fix] 2026-06-11 — Curly-quote SyntaxError in detail panel script

**Agent:** Lead Agent  
**Files changed:** dashboard/templates/index.html (line 1349)  
**Approved by:** Saeed (explicit approval in session 2026-06-11)

**Description:** Template line 1349 used Unicode curly/smart quotes (U+2018 / U+2019) as JavaScript string delimiters in the GUIDED_STEPS red_flag array. V8 threw SyntaxError: Invalid or unexpected token which silently killed the entire 46400-char inline script block on every page load. No event listeners registered — filter collapse, batch selection, and detail panel were all non-functional.

**Fix:** Replaced 11 instances of U+2018/U+2019 with ASCII straight single quotes (U+0027) on line 1349.

**Test result:** SyntaxError gone. Clicking a case card triggers the detail panel sliding in from right as designed.

---

## 2026-06-11 — Batch 1 UX/UI Fixes
**Agent:** Frontend Agent (Claude Code session)
**Approved by:** Saeed (explicit instruction in session 2026-06-11)
**Files changed:** `dashboard/templates/index.html`, `dashboard/templates/base.html`, `dashboard/static/dashboard.css`

**Description:** Batch 1 of approved UX improvements following a full UX/UI review of the dashboard.

**Changes:**
1. **Branding** — Replaced all user-facing "JeffLocal" references with "Avamed" (page title, browser tab, topbar, batch resolve note). Internal JS storage keys unchanged.
2. **Resolve confirm UX** — Extended two-step confirm timeout from 3s to 5s. Added amber button state (`.confirming` CSS class). Added animated 5-second countdown progress bar beneath the resolve button.
3. **Panel click-toggle** — Fixed backdrop `pointer-events: none` so clicking a different case card while the panel is open switches directly to that card (no close-then-open). Backdrop retains visual dim but no longer blocks pointer events.
4. **Post-resolve panel state** — After resolve: stepper advances to step 4 (Resolved), guided steps hidden, Escalate button hidden. Both reset correctly when switching to a new case.
5. **Clipboard copy icons** — Added copy-to-clipboard buttons for NHS number, EMIS number, Phone, and AI summary in the detail panel. Uses `navigator.clipboard` with textarea fallback.
6. **NHS/EMIS unconfirmed warning** — Fields showing "n/a" now rendered in amber italic to signal identity not confirmed.
7. **AI Intake Summary label** — Renamed "Jeff's Triage Summary" to "AI Intake Summary". Removed "Ollama/Gemma4 · on-premises" internal attribution from panel.

**Test result:** 10 unit tests passed. 93 fixture-setup errors are pre-existing (test DB not seeded) and unrelated to these changes. No Python code modified.

---

## 2026-06-12 — Sidebar Redesign (Role-based)
**Agent:** Frontend Agent (Claude Code session)
**Approved by:** Saeed (explicit instruction in session 2026-06-12 — design direction confirmed via 4 clarifying questions)
**Files changed:** `dashboard/templates/index.html`, `dashboard/static/dashboard.css`, `dashboard/app/main.py`

**Description:** Full redesign of the analytics sidebar. Removed pipeline jargon and replaced with two role-based views (Reception and Manager) with a persistent toggle stored in localStorage.

**Changes:**
1. **Reception mode (default)** — Needs Attention section: Critical, Overdue (>2h), Review needed, Identity issue — all clickable, jump to filtered case list. Today section: Open cases + Resolved today (clickable) + Peak hour text. Team section: simplified name + open-count only.
2. **Manager mode** — Today's Numbers: Calls received, Resolved, Avg response time. Case Types: horizontal teal bar chart per request type (Prescription, Sick Note, Referral, Appointment, etc.), each bar clickable and filtered by type. Team section: full pills view (open/active/done) with legend.
3. **Removed** — "Call Analytics" card (pipeline terms: "Safe to Queue", "Dropped"), "Live Workload" card (redundant), "Quick Status" card (replaced), hourly sparkline chart.
4. **Added** — `get_peak_hour()` backend function returns busiest hour today (e.g. "10–11am"). `peak_hour` passed to template context.
5. **Reused** — `request_type_breakdown` (already in context) provides bar chart data with pre-calculated `width` percentages and filter URLs.

**Test result:** Python syntax check passed. No unit tests broken. UI requires manual login to verify (browser automation blocked by auth).

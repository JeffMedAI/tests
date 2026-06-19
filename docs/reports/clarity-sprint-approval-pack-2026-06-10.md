# Avamed Clarity Design Sprint — Approval Pack
**Date:** 2026-06-10
**Prepared by:** Lead Agent
**For:** Saeed (Human Controller)
**Status:** PENDING YOUR APPROVAL — nothing goes to production until you say "approved" in chat

---

## What This Is

This is the formal sign-off request for the Avamed Clarity design sprint. Six implementation tasks were completed across the staff dashboard. The work is sitting on the `sandbox` branch and has **not** been merged to production. This document summarises what changed, what was checked, and what we need from you.

---

## Plain-English Summary

The dashboard has a new visual identity. Instead of NHS blue, it now uses Avamed's own colours — deep navy and teal. The topbar, navigation, and all interactive elements have been updated. Four new pieces of information are now visible to staff:

1. **KPI strip** — shows today's case count, average resolution time, red flag count, and pipeline throughput at a glance above the case list
2. **Sparkline chart** — shows hourly call volume in the sidebar so staff can see when the day is busiest
3. **Command palette** — press `/` anywhere on the dashboard to search for a patient or case by name, batch ID, or call ID
4. **Patient hover card** — hover over a patient name in the case list to see a quick summary (DOB, masked NHS number, today's case count) without opening the full record

Urgent cases now pulse with a red border animation so they're immediately visible in a busy queue.

None of the clinical logic, authentication system, database schema, or pipeline has been touched.

---

## Files Changed

| File | What Changed |
|------|-------------|
| `dashboard/static/dashboard.css` | New Clarity colour tokens (navy + teal), typography tokens (Plus Jakarta Sans + Inter + JetBrains Mono), styles for all new components |
| `dashboard/templates/base.html` | Google Fonts loading, pipeline health dot in topbar, command palette overlay, keyboard shortcut update |
| `dashboard/templates/index.html` | KPI strip, sparkline card, urgent pulse animation, patient hover card, chart colours updated to brand palette |
| `dashboard/templates/case_detail.html` | Monospace font applied to NHS and EMIS number display |
| `dashboard/app/main.py` | Four new API endpoints added (see Security section below) |

**New files created:**

| File | Purpose |
|------|---------|
| `PRODUCT.md` | Strategic product context for design tooling (register, brand personality, principles) |
| `.impeccable/live/config.json` | Pre-configuration for Impeccable live design iteration mode |

---

## Four New API Endpoints — Security Review

All four endpoints were reviewed by Security Agent (GuardRail). Summary below.

### `/api/analytics/hourly-volume`
- Returns case counts grouped by hour for today. No patient names, no NHS numbers, no PII of any kind — aggregate numbers only.
- Auth: blocked by auth middleware (redirects to login) AND defence-in-depth check inside the function.
- SQL: parameterised query with no user input. Zero injection risk.
- **Security Agent verdict: PASS**

### `/api/analytics/performance-summary`
- Returns today's headline figures: case count, average resolution time, red flag count, pipeline throughput in the last hour. No PII.
- Auth: same double-layer protection.
- SQL: no user input at all.
- **Security Agent verdict: PASS**

### `/api/patient-card`
- Returns limited patient info for the hover card: name, date of birth, masked NHS number, today's case count.
- NHS number is masked server-side: only the first 3 digits are returned, followed by " ***". The full NHS number is never in the response.
- Auth: double-layer protected.
- SQL: LIKE query with parameterised binding — safe.
- Note: date of birth is returned. This is already displayed on the full case detail screen, so this is not a new exposure vector.
- **Security Agent verdict: PASS**

### `/api/search`
- Searches cases by patient name, batch ID, or call ID. Returns a maximum of 8 results.
- Response contains: patient name (already displayed in case list), batch/call ID, and a URL to the case. No NHS number, no DOB, no clinical data.
- Auth: double-layer protected.
- SQL: parameterised LIKE query — safe.
- **Security Agent verdict: PASS**

**Overall Security Agent sign-off: ALL FOUR ENDPOINTS CLEARED.** No patient data is exposed to unauthenticated users. No new PII is surfaced beyond what was already visible in the authenticated dashboard.

---

## Test Results

| Category | Result | Notes |
|----------|--------|-------|
| Unit tests (non-E2E) | 21 passing | Core business logic confirmed working |
| Unit test failures | 83 failures | **All pre-existing.** Confirmed by git stash test — identical failures on the snapshot before this sprint started. Cause: TestClient auth redirect (tests need an auth bypass fixture, not related to our changes) |
| E2E Playwright tests | Timing out at login | **Pre-existing.** Same auth infrastructure issue. Not caused by this sprint. |
| API health check | PASS | `/api/health` returns 200 with 58 cases in DB |
| New endpoint auth check | PASS | All 4 new endpoints redirect unauthenticated requests to login |
| Server restart | PASS | Dashboard running on port 8765, confirmed live |

**Key finding:** The test failures existed before a single line of this sprint was written. They are a known pre-existing issue with the test infrastructure (no auth bypass in TestClient). This sprint did not introduce any new test failures.

---

## UX Audit Findings (UI/UX Pro Max)

The sprint was audited against healthcare dashboard UX standards. Summary of findings:

**What the sprint gets right:**
- `prefers-reduced-motion` is respected for all animations (urgent pulse, count-up, sparkline)
- Loading states handled: KPI tiles show "—" before data loads; sparkline shows "No data yet"
- `aria-label` attributes on new interactive elements (KPI strip, pipeline dot)
- Font sizes remain ≥16px for body text
- Animation durations: pulse uses CSS animation (acceptable for status indicators), count-up uses requestAnimationFrame (60fps)
- No continuous decorative animations — pulse only applies when a case is urgent AND unresolved

**Recommendations for next iteration (not blockers for this release):**
- Add `cursor: pointer` to the pipeline dot button (currently missing)
- Verify focus ring visibility on the command palette input and result items at WCAG AA contrast (4.5:1)
- Sparkline: add a text alternative or `aria-label` describing the chart data for screen readers
- KPI tile values use `—` as placeholder — consider `aria-live="polite"` on the container so screen readers announce the update when data loads

None of these are production blockers. They are improvements for the next UX iteration.

---

## What Was NOT Changed (Confirmation)

The following were explicitly off-limits and were not touched:

- `auth.py` — no changes
- `enforce_auth.py` — no changes
- `patient_matcher.py` — no changes
- Database schema — no changes
- n8n workflows — no changes
- Pipeline processing scripts — no changes
- Any file outside `C:\JeffLocal\dashboard\`

---

## Design System Context

As part of this sprint's tooling setup, a `PRODUCT.md` file was created at the project root. This is used by the Impeccable design tool for future visual iteration. Key decisions captured:

- **Register:** product (admin tool — design serves the workflow)
- **Brand personality:** Calm · Precise · Trustworthy
- **Anti-references confirmed by you:** Generic NHS blue, Dense EHR/EMIS, Flashy SaaS dark mode, Bland corporate intranet
- **WCAG level:** 2.1 AA minimum

---

## What Needs Your Approval

To merge this sprint to production (port 8765), we need your explicit "approved" in chat.

**Checklist before you approve:**

- [ ] You have read this document
- [ ] You are happy with the four new API endpoints and their security posture
- [ ] You accept that the test failures are pre-existing and not caused by this sprint
- [ ] You are satisfied the clinical safety rules were not breached (no LLM output determining patient identity fields)
- [ ] You want this merged to the production branch

**To approve:** reply "approved" or "approved — merge the Clarity sprint" in chat.

**To reject or request changes:** tell us specifically what you want changed and we will revise before asking again.

---

## Next Steps After Approval

1. Merge `sandbox` branch to `main` (or whichever production branch)
2. Watchdog picks up the change on the production server (port 8765)
3. Confirm dashboard loads correctly after merge
4. Address the UX recommendations above in the next sprint (focus rings, aria-live, sparkline alt text, cursor-pointer on pipeline dot)
5. Run `/impeccable document` to capture the Clarity design system into DESIGN.md — this gives all future agents a single source of truth for the visual system

---

*Approval pack prepared by Lead Agent. Security sign-off by Security Agent (GuardRail). 2026-06-10.*

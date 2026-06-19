# Avamed Clarity — Dashboard Design Sprint Prompt v1
# Drafted: 2026-06-10 | Status: APPROVED — execute immediately

---

## RESTORE POINT — DO THIS BEFORE TOUCHING ANYTHING ELSE

Before writing a single line of code, create a restore point so we can roll back instantly:

  cd C:\JeffLocal
  git add -A
  git commit -m "restore: pre-clarity-sprint snapshot 2026-06-10" --allow-empty
  git tag restore/pre-clarity-sprint-2026-06-10

Confirm the tag exists before proceeding:
  git tag | findstr restore

If the tag is not confirmed: STOP and resolve before continuing.

---

## BRIEFING

You are the Frontend Agent on the JeffLocal/Avamed project. Your task is to implement the
Avamed Clarity design system across the three highest-priority dashboard areas:
  1. Dashboard analytics widgets (the sidebar cards + main content area KPIs)
  2. Case queue (the requests list — the screen reception staff look at all day)
  3. Case detail panel (what opens when you click a case)

This is a REAL IMPLEMENTATION into production code at C:\JeffLocal\dashboard\.
Nothing touches production (port 8765) until Saeed gives explicit "approved" in chat.
You write the code, test it, get Security Agent review, then present an approval pack.

---

## READ THESE FIRST (mandatory, in order)

1. C:\JeffLocal\CLAUDE.md — project rules
2. C:\JeffLocal\PROJECT_MEMORY.md — current state
3. C:\JeffLocal\docs\superpowers\specs\2026-06-09-avamed-clarity-design.md — the design spec you are implementing
4. C:\JeffLocal\dashboard\static\dashboard.css — current CSS (3,112 lines)
5. C:\JeffLocal\dashboard\templates\base.html — base layout
6. C:\JeffLocal\dashboard\templates\index.html — dashboard + case queue (1,679 lines, same template)
7. C:\JeffLocal\dashboard\templates\case_detail.html — case detail page (849 lines)
8. C:\JeffLocal\dashboard\app\main.py — Flask routes and data passed to templates

---

## DESIGN FOUNDATION — AVAMED CLARITY SPEC

The design spec (docs/superpowers/specs/2026-06-09-avamed-clarity-design.md) is your
source of truth. Do NOT redesign. Your job is to:

  A. Implement what the spec defines
  B. Polish anything that looks unfinished or inconsistent
  C. Add the missing analytics features listed below

The key changes from the current CSS are:
  - Retire NHS blue (#005EB8) as primary colour → replace with Avamed Deep Navy (#0B3D6B)
  - New accent: Avamed Teal (#00A896) replaces --accent everywhere
  - New typography: Plus Jakarta Sans (headings) + Inter (body) + JetBrains Mono (IDs)
  - Load fonts from Google Fonts in base.html (see spec section 1.3 for import URL)
  - Keep --nhs-blue: #005EB8 available as a token for NHS compliance badges only

---

## WHAT TO BUILD — PRIORITY ORDER

### TASK 1 — Design System CSS Token Migration

In dashboard.css:
  - Update :root tokens to Clarity values (spec section 1.2 + 1.3 + 1.4)
  - Add all new tokens that don't exist yet: --brand-navy, --brand-teal, --brand-teal-soft,
    --brand-teal-mid, --font-display, --font-body, --font-mono, --text-4xl, --text-5xl
  - Retire --accent → --brand-teal; retire --accent-hover → darken of --brand-teal;
    retire --accent-soft → --brand-teal-soft
  - Keep backwards-compat aliases: --accent: var(--brand-teal) so nothing breaks
  - DO NOT delete any existing CSS rules — only add/update tokens in :root and update
    topbar/nav colour references from NHS blue to navy

### TASK 2 — Topbar + Navigation

In base.html and dashboard.css:
  - Topbar background: --brand-navy (#0B3D6B)
  - Active nav link: --brand-teal underline or indicator (not blue)
  - Add the Live Pipeline Dot to the topbar (spec section 3.1):
      - Small circle, right side of topbar, before the user avatar
      - Green (#00A896 teal) = healthy, amber = degraded, red = down
      - Polls GET /api/health every 60 seconds via vanilla JS fetch
      - Tooltip on hover: "Pipeline: healthy / degraded / down"
      - Use the existing /api/health endpoint (already returns JSON)

### TASK 3 — Dashboard Analytics Widgets

The sidebar currently has: Quick Status, Staff Workload, Call Analytics, Live Workload.
These are working but need visual uplift + two new widgets.

Existing sidebar cards — polish only:
  - Apply Clarity typography to sidebar card headers (Plus Jakarta Sans 600)
  - Teal dots and accents instead of NHS blue
  - Count-up animation on all numeric values (vanilla JS, 800ms ease-out, triggers on
    IntersectionObserver — spec section 2.3 Count-up KPI component)

New widget 1 — "Today's Performance" KPI strip (above the case queue, full width):
  Four KPI tiles in a horizontal row:
    [Cases Today] [Avg. Resolve Time] [Red Flags] [Pipeline Throughput]
  - Cases Today: total cases processed today
  - Avg. Resolve Time: average minutes from case created to resolved (today). Show "—"
    if no resolved cases yet. Use existing audit_events table or case timestamps.
  - Red Flags: count of cases with red_flags_present = true today. Red coloured if > 0.
  - Pipeline Throughput: cases imported in last 60 minutes. Source: dashboard_imports count.
  Each tile has a count-up number animation on page load.
  Add a Flask route/query to supply this data (or extend the existing index route).

New widget 2 — "Hourly Call Volume" sparkline (bottom of sidebar, collapsible):
  - Small area sparkline chart showing calls per hour for today (00:00 to now)
  - Use ApexCharts (CDN: https://cdn.jsdelivr.net/npm/apexcharts)
  - Teal area fill (#00A896 at 15% opacity), teal line
  - No Y axis labels — just the shape of the curve
  - Data source: count cases grouped by hour from today. Add /api/analytics/hourly-volume
    endpoint returning JSON array of {hour: 0-23, count: N}
  - Show "No data yet" text if no cases today

### TASK 4 — Case Queue (Requests List)

This is the main list in index.html when show_requests=True. Polish and add:

  Priority Ribbon (spec section 2.1):
    - Each case card has a left border colour strip (already exists as priority colour coding)
    - For URGENT/999 cases: add a subtle CSS pulse animation on the left border
      (keyframe: opacity 1 → 0.4 → 1, 2s infinite). Stop pulse once case is opened.
    - Implementation: add class "is-urgent-pulse" to card if priority contains "999" or
      red_flags_present is true. Add keyframe in CSS.

  Patient Hover Card (spec section 2.4):
    - On hover over a patient name in the queue, show a small floating card with:
        Name, DOB (if available), NHS number (masked: first 3 + ***), case count today
    - Delay: 200ms after hover starts (prevent flicker on mouse-over)
    - Dismiss on mouse-leave
    - Implementation: vanilla JS, position relative to the hovered element
    - Data: add /api/patient-card?name=<name> endpoint returning JSON
      (query cases table for matching patient_name, return dob, nhs_number masked, count)
    - If no data: show just the name with "No prior cases today"
    - IMPORTANT: NHS number must be masked in the UI. Never show full NHS number in hover.

  Queue filtering UX polish:
    - Filter pills (existing) → update active state to teal (not NHS blue)
    - Sort dropdown → teal focus ring
    - Empty state: if no cases match filter, show a centred message with a teal icon
      (not a blank white space)

### TASK 5 — Case Detail Panel

In case_detail.html — polish and add Guided Workflow Steps (spec section 3.3):
  - Add a 4-step progress indicator at the top of the detail panel:
      [1. Review] → [2. Verify Patient] → [3. Action] → [4. Resolve]
  - Current step inferred from case status:
      new/open → step 1 highlighted
      in_progress → step 2 highlighted
      actioned → step 3 highlighted
      resolved → step 4 (all green)
  - Visual: horizontal stepper, teal for completed/active steps, grey for future steps
  - No backend change needed — inferred from existing case status field

  Apply Clarity typography and token updates:
    - Section headers → Plus Jakarta Sans 600
    - NHS number and batch_id fields → JetBrains Mono (font-family: var(--font-mono))
    - Case ID / call_id → JetBrains Mono
    - Status badge → teal for open/in_progress, green for resolved, red for urgent

### TASK 6 — Command Palette (spec section 2.5)

Global keyboard shortcut: press "/" anywhere to open a floating command palette.
  - Modal overlay, centred, max-width 560px
  - Search field at top (autofocused)
  - Results: patients by name, cases by ID, quick actions (Go to Queue, Go to Reports, etc.)
  - Keyboard: arrow keys to navigate, Enter to select, Escape to close
  - Data: search against /api/search?q=<query> — add this endpoint if it doesn't exist
    (searches case patient_name, batch_id, call_id — returns top 8 results)
  - Show "Press / to search" hint in topbar (subtle, grey text, desktop only)
  - Implementation: vanilla JS only, no framework dependency

---

## WHAT NOT TO TOUCH

  - Auth logic (auth.py, enforce_auth.py) — Security Agent must review separately
  - Patient matching pipeline (patient_matcher.py)
  - Database schema — no migrations in this sprint
  - The n8n workflow
  - Any file outside C:\JeffLocal\dashboard\ (no scripts, no config)
  - The login and forgot-password pages (separate sprint)

---

## ANALYTICS — MISSING BACKEND ENDPOINTS

You need to add these Flask routes in main.py (or a new analytics.py blueprint):

  GET /api/analytics/hourly-volume
    Returns: {"hours": [{"hour": 0, "count": 5}, ...]} for today
    Query: SELECT strftime('%H', created_at) as hour, COUNT(*) as count
           FROM cases WHERE date(created_at) = date('now') GROUP BY hour

  GET /api/analytics/performance-summary
    Returns: {
      "cases_today": N,
      "avg_resolve_minutes": N or null,
      "red_flags_today": N,
      "throughput_last_hour": N
    }

  GET /api/patient-card?name=<str>
    Returns: {
      "name": "...",
      "dob": "DD/MM/YYYY" or null,
      "nhs_number_masked": "123 ***" or null,
      "cases_today": N
    }
    SECURITY: nhs_number must be masked server-side before returning. Never return full number.

  GET /api/search?q=<str>
    Returns: {"results": [{"type": "case|patient", "label": "...", "url": "..."}]}
    Searches: patient_name LIKE %q%, batch_id LIKE %q%, call_id LIKE %q%
    Limit: 8 results. Requires auth (use @require_auth decorator).

---

## TESTING REQUIREMENTS

After each task:
  1. Run the existing test suite: cd C:\JeffLocal\dashboard && python -m pytest tests/ -q
     All tests must pass. Do not break existing tests.

After all tasks:
  2. Start the Flask server locally and do a visual check of each changed page.
     Document any rendering issues.
  3. Check /api/health returns 200.
  4. Test the command palette: press /, type a patient name, verify results appear.
  5. Test the live pipeline dot: verify it shows green when Ollama is up.
  6. Test count-up animations on page load.

---

## GOVERNANCE — MANDATORY

1. Security Agent must review the four new API endpoints before the approval pack is sent.
   Focus: /api/patient-card masking logic, /api/search auth check, no PII leakage.

2. Lead Agent compiles the approval pack with:
   - List of every file changed
   - Before/after screenshots of: dashboard overview, case queue, case detail, command palette
   - Test results (pytest output)
   - Security Agent sign-off confirmation
   - Any deviations from the Clarity spec (explain why)

3. Deployment approach: changes go directly to C:\JeffLocal\dashboard\ (live server,
   port 8765). Make ALL file changes first across CSS and templates. Do ONE server restart
   at the very end — never restart mid-sprint to avoid a partially-broken state.

4. After implementation, DO NOT present results yourself. Trigger the independent review
   process described in the INDEPENDENT REVIEW section below, then report back.

5. Log everything in CHANGELOG.md under date 2026-06-10.

---

## QUALITY BAR

  - No hardcoded hex colours in templates. All colours via CSS tokens.
  - No inline styles except for dynamic values (e.g. width percentages in progress bars).
  - All interactive elements (buttons, links, inputs) must have :focus-visible styles.
  - NHS number never appears unmasked in any template or API response.
  - The pulse animation must respect prefers-reduced-motion (skip animation if set).
  - Google Fonts must load with display=swap to prevent flash of invisible text.
  - ApexCharts loaded from CDN with a fallback message if it fails to load.
  - Every new JS function must have a JSDoc comment explaining what it does.
  - No console.log left in production code.

---

## INDEPENDENT REVIEW — MANDATORY BEFORE REPORTING DONE

After completing all tasks and the server has been restarted:

STEP 1 — Functional regression check (you run this yourself):
  - Visit http://localhost:8765 — confirm dashboard loads, no 500 errors
  - Visit http://localhost:8765/requests — confirm case queue loads
  - Click a case → confirm case detail loads with the new stepper
  - Press "/" → confirm command palette opens and search works
  - Check every nav link in the topbar → confirm all pages load (no broken routes)
  - Run: python -m pytest C:\JeffLocal\dashboard\tests\ -q
    All tests must pass.

STEP 2 — Visual comparison against Clarity spec:
  Take screenshots of:
    a. Dashboard overview (KPI strip + sidebar analytics)
    b. Case queue (showing at least one case with priority ribbon)
    c. Case detail panel (showing the workflow stepper)
    d. Command palette open
    e. Topbar close-up showing the pipeline dot
  Save all screenshots to: C:\JeffLocal\docs\design_refs\clarity-sprint-review\

  Compare each screenshot against the Clarity spec (section 3) and note any deviation.

STEP 3 — Run UX UI Pro Max skill:
  Invoke the UX UI Pro Max skill against the updated dashboard.
  The skill should run a comprehensive accessibility and UX audit covering:
    - Colour contrast (WCAG AA minimum)
    - Touch target sizes
    - Keyboard navigation
    - Focus indicators
    - ARIA labels on new components
  Save the skill output to: C:\JeffLocal\docs\reports\ux-review-post-clarity-sprint-2026-06-10.md

STEP 4 — Security Agent sign-off:
  Present the four new API endpoints to Security Agent for review.
  Security Agent must confirm:
    - /api/patient-card: NHS number masked server-side, no full number in response
    - /api/search: @require_auth decorator present, no unauthenticated access
    - /api/analytics/*: auth protected, no PII in response
    - No new SQL injection vectors

Only after STEPS 1-4 are complete, compile the approval pack.

---

## DELIVERABLE FORMAT

Present to Saeed (in plain English — /caveman format):
  1. What changed — one sentence per task, no jargon
  2. Test results: PASS / FAIL + number of tests
  3. UX audit score and top 3 findings (if any issues)
  4. Security verdict: APPROVED / BLOCKED + reason
  5. Screenshots (attach the ones saved in step 2)
  6. One clear recommendation: READY TO GO LIVE or NEEDS FIX FIRST

If anything in steps 1-4 fails: fix it before presenting to Saeed. Do not present
broken work. "It should work" is not done.

---

## RESTORE POINT REMINDER

If at any point the dashboard breaks and you cannot fix it quickly:
  git checkout restore/pre-clarity-sprint-2026-06-10 -- dashboard/static/dashboard.css
  git checkout restore/pre-clarity-sprint-2026-06-10 -- dashboard/templates/
  Restart the server.
This restores only the dashboard files, not the whole repo.

---

*Drafted by: Dispatch / Lead Agent*
*Version: 2 (updated with restore point, live deploy, independent review)*
*Status: APPROVED — execute immediately*

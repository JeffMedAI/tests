# JeffLocal — Live UX Monitoring Report
**Date:** 2026-06-01 | **Method:** Playwright agent observing staff resolve workflow  
**Viewports:** 1280px desktop + 375px mobile

---

## CRITICAL — Fix Before Pilot

| # | Issue | Location | Fix |
|---|-------|----------|-----|
| M1 | `cd-meta-grid` overflows mobile (489px on 375px viewport) — DOB/phone/EMIS off-screen | Case detail mobile | CSS: `max-width:100%; overflow:hidden`, collapse to 1-col at <600px |
| M2 | `cd-content-grid` overflows mobile (537px) — AI Summary, Staff Task, Copy buttons ALL off-screen | Case detail mobile | Same responsive CSS fix |
| M3 | "Copy Staff Task" button off-screen on mobile (right:480) — most-used action completely inaccessible | Case detail mobile | Sticky bottom action bar on mobile |
| M4 | Filter tabs: 4 of 7 cut off on mobile with no scroll indicator | Requests list mobile | Scroll fade gradient on tab bar |
| M5 | Bulk action buttons only 28px tall | Requests list | Raise to 44px |
| M6 | `h3` sidebar headings render at 10px — below WCAG minimum | All pages sidebar | Raise to 13px minimum |
| M7 | Staff Workload numbers (open/active/done pills) at 10px | Sidebar | Raise to 12px |

## HIGH — Fix Soon

| # | Issue | Location |
|---|-------|----------|
| H1 | Nav links 36px, Import 32px, Sign Out icon 30px — below 44px | All pages topbar |
| H2 | Sign Out icon has no label (bare arrow icon) | Topbar |
| H3 | "→ View" on KPI cards at 10.5px (<small>) — invisible CTA | Dashboard |
| H4 | Nav links on mobile: Staff/Reports/Settings off-screen (right:416-586) | Topbar mobile |
| H5 | Alerts bell has no badge count | Topbar |

## MEDIUM — Polish

| # | Issue |
|---|-------|
| P1 | Duration shows "198s" — should be "3m 18s" |
| P2 | Red call-age on resolved cases (misleading urgency) |
| P3 | "Reopen" button has same weight as "View" — should be amber with confirmation |
| P4 | Timestamp in Staff Workload h3 heading (accessibility) |
| P5 | "Avg Response Time: 2d 3h" — no tooltip explaining the metric |
| P6 | Bulk actions enabled on Resolved view (meaningless) |
| P7 | "Status Distribution" shows empty bar area when 0 open cases |
| P8 | Long Call IDs wrap/dominate case cards |

## What Worked Well

- KPI cards scannable at a glance
- "All Clear" green panel gives instant 2-second triage
- Request Mix donut chart with clickable legend — excellent
- Case detail patient name as h1 — immediately clear
- EMIS Workflow Steps numbered list — great for less-experienced staff
- Breadcrumb "Requests › Patient Name" — clear context
- ARIA tab roles on case detail — keyboard accessible
- Filter tabs with counts — fast triage

## Higgsfield Video Models Available (for Avamed promo)

Models: Kling 3.0, Google Veo 3/3.1, Seedance 2.0, Minimax Hailuo, Wan 2.6/2.7
Recommended: **Kling 3.0** (multi-shot, audio sync) or **Google Veo 3.1** (ultra-realistic)
Duration: 3-15s per clip, max 15s
Credit cost: ~10-40 credits per 5-10s clip (estimate — actual cost check was blocked by permissions)
A 30-60 second promo would need 3-6 clips stitched = ~30-150 credits total

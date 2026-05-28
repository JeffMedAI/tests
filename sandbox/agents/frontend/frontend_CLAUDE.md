# FRONTEND AGENT — JeffLocal
# Role: React/TypeScript dashboard, CSS component system, staff UX
# Assigned by: Lead Agent
# Reviews by: Security Agent (all PRs) + Test Agent (Playwright)

---

## SCOPE — OWNS THESE, TOUCHES NOTHING ELSE

```
sandbox\frontend\src\           ← All React components and logic
sandbox\frontend\src\styles\    ← Design tokens, global CSS, component styles
sandbox\frontend\public\        ← Static assets
sandbox\frontend\package.json   ← Frontend dependencies only
```

## NEVER TOUCHES

```
sandbox\backend\          ← Backend Agent owns this
sandbox\db\               ← Database Agent owns this
sandbox\tests\e2e\        ← Test Agent owns Playwright tests
sandbox\voice\            ← Backend Agent owns this
production\               ← Read-only for comparison only
```

---

## DESIGN SYSTEM — THE LAW

JeffLocal uses a strict component system. Every visual element is a component.
Inline styles are banned. No exceptions.

### Design Tokens (sandbox\frontend\src\styles\tokens.css)
```css
:root {
  /* Colours */
  --color-primary:        #2563EB;   /* Action blue */
  --color-primary-hover:  #1D4ED8;
  --color-danger:         #DC2626;   /* Urgent / critical */
  --color-danger-light:   #FEE2E2;
  --color-warning:        #D97706;   /* Pending / at risk */
  --color-warning-light:  #FEF3C7;
  --color-success:        #16A34A;   /* Resolved */
  --color-success-light:  #DCFCE7;
  --color-neutral-50:     #F9FAFB;
  --color-neutral-100:    #F3F4F6;
  --color-neutral-200:    #E5E7EB;
  --color-neutral-700:    #374151;
  --color-neutral-900:    #111827;

  /* Typography */
  --font-sans:    'Inter', system-ui, sans-serif;
  --text-xs:      0.75rem;
  --text-sm:      0.875rem;
  --text-base:    1rem;
  --text-lg:      1.125rem;
  --text-xl:      1.25rem;

  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;

  /* Shadows */
  --shadow-card:  0 1px 3px rgba(0,0,0,0.12);
  --shadow-modal: 0 8px 32px rgba(0,0,0,0.18);

  /* Radius */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
}
```

### Component Rules
- Base components: shadcn/ui (import from @/components/ui/)
- All cards use `<Card>` component — never raw divs with styles
- All buttons use `<Button variant="...">` — never styled divs
- Status colours always use CSS vars — never hardcoded hex in components
- Every new component: one file, one default export forbidden (named exports only)
- Every component has a matching `ComponentName.test.tsx`

---

## ACTIVE TASKS (R3 → R1 → R2 — IN ORDER)

### R3 — Unified Card CSS (DO THIS FIRST)
```
Goal: Remove ALL inline styles from sidebar cards and dashboard cards
      Build consistent Card component that all cards use

Steps:
1. Audit all components for inline styles (grep -r "style={{" src\)
2. Move each style to the component system using CSS vars
3. Create <WorkItemCard>, <StatCard>, <AlertCard> base components
4. Replace all inline-styled cards with these components
5. Verify: zero instances of style={{ in any .tsx file
6. Playwright: visual regression — cards look identical after refactor

Files likely affected:
  Sidebar.tsx, RequestQueue.tsx, DetailPanel.tsx, Dashboard.tsx
```

### R1 — Icon-Only Collapsed Sidebar with Tooltips (DO AFTER R3)
```
Goal: Collapsed sidebar shows meaningful icons + tooltips, not empty space

Behaviour:
- Expanded: icon + label visible
- Collapsed: icon only, tooltip on hover showing full label
- Collapse state: persisted in localStorage
- Collapse button: always visible
- Icons: use lucide-react — match semantically to each section

Implementation:
- useSidebarState() hook for collapse logic
- <Tooltip> wrapper from shadcn/ui
- CSS transition on width: var(--sidebar-expanded) / var(--sidebar-collapsed)
- No JS-based show/hide — CSS-only transition preferred

Files: Sidebar.tsx, hooks\useSidebarState.ts
```

### R2 — Critical Alert Badge on Sidebar Toggle (DO AFTER R1)
```
Goal: When sidebar is collapsed, badge on toggle button shows
      count of unresolved critical items

Behaviour:
- Badge visible when: sidebar collapsed AND critical_count > 0
- Badge count: live, updates with dashboard data
- Badge disappears when: sidebar expanded OR critical_count === 0
- Badge style: red dot with count, uses --color-danger

Implementation:
- DashboardContext provides critical_count
- <AlertBadge count={criticalCount}> component (reusable)
- Placed on sidebar toggle button, not the sidebar itself
- Playwright test: collapse sidebar → badge appears with correct count

Files: Sidebar.tsx, DashboardContext.tsx, components\AlertBadge.tsx
```

---

## WORKFLOW (SUPERPOWERS ENFORCED)

```
1. /superpowers /brainstorm
   - List all files that will change
   - Identify any state management implications
   - Check: does this need a new context? a new hook?

2. Confirm Test Agent has Playwright tests ready before implementing

3. /frontend-design — load before creating any new component
   - Use design tokens, not custom values
   - Follow NHS-friendly accessible design (WCAG AA minimum)
   - Staff will use this on a desktop monitor — optimise for 1280px+

4. Implement with /superpowers /tdd
   - Write component, run unit tests, fix, repeat

5. Run Playwright yourself to verify UI
   - "Open the dashboard, navigate to [feature], verify [expected state]"
   - Check in headed mode if visual debugging needed

6. Self-review: zero inline styles, zero `any` types, all tokens used
7. Message Lead Agent: "Frontend task [X] complete. Tests passing. Ready for Security review."
```

---

## UX PRINCIPLES FOR STAFF

```
This dashboard is used by NHS reception and admin staff:
- They are busy — every click costs time
- They are not technical — no jargon, no ambiguity
- They may be stressed — clear visual hierarchy, calming colours
- Critical items must be unmissable — use --color-danger boldly
- Status must be instantly readable — colour + icon + label (never colour alone)
- Loading states must always be shown — never blank screens
- Errors must say what to do — never "Something went wrong"
- Accessibility: keyboard navigable, ARIA labels on all interactive elements
```

---

## WHAT THIS AGENT NEVER DOES

```
✗ Add inline styles (style={{ ... }}) — ever
✗ Use `any` TypeScript type
✗ Use default exports for components
✗ Hardcode colour values — CSS vars only
✗ Touch backend files
✗ Write Playwright tests (Test Agent owns those)
✗ Make API calls without checking with Backend Agent that the endpoint exists
✗ Use localStorage for patient or session data — state management only
✗ Install npm packages without checking for security advisories first
```

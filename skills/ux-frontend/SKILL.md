# SKILL: UX & Frontend Design — Avamed
# Trigger: any UI complaint, staff feedback, or design/layout request.

---

## When to Use

- A staff complaint or pain point about the dashboard ("the case list is cluttered")
- A feature request affecting the UI ("action CTAs should be above the fold")
- A screenshot or description of an unclear or broken layout
- A specific Jinja2 template or CSS file that needs redesigning

## When NOT to Use

- Backend-only changes with no effect on templates, CSS, or staff-facing UI
- Pipeline or PowerShell module work

---

## Typical Input

- A staff complaint: "We can't tell which cases are urgent at a glance"
- A feature request: "Add a status badge to the case card header"
- A screenshot of the current UI with a marked problem area
- A specific template file: "Redesign the case detail panel in templates/case_detail.html"

---

## Context Before Starting

The dashboard uses:
- **FastAPI + Jinja2** for server-side rendering — templates are in `sandbox/dashboard/app/templates/`
- **Custom CSS** in `sandbox/dashboard/app/static/` — match existing design system before adding new elements
- **Status pills and priority badges** — these must use the same CSS class names as existing `summary_chips` — do not invent new ones
- **No React or client-side framework** — all UI changes are HTML/CSS/minimal JS

Always work in **sandbox only** (`C:\JeffLocal\sandbox\dashboard\`). Never touch production templates without Saeed's explicit approval.

---

## Step-by-Step Process

1. **Read the complaint or request carefully.** Understand what the staff member actually needs — not just what was said. The stated problem and the actual problem are often different.

2. **Read the current template and CSS** in sandbox before proposing anything. Understand the existing structure.

3. **Check for design consistency issues.** Are pill styles, colours, or priority indicators inconsistent? Fix those as part of any change — do not add new inconsistencies.

4. **Propose the change** with a before/after description in plain English. Get Saeed's approval before writing any code.

5. **Apply changes to sandbox only.** Run the sandbox dashboard locally to verify the change visually.

6. **Run the test suite.** Confirm no regressions — pay particular attention to page render tests.

7. **Produce the structured report** (see Output Format below).

---

## Output Format

```
UX CHANGE REPORT — [Feature or Issue Title]
Date: YYYY-MM-DD | Environment: SANDBOX

PROBLEM
  [What the staff experience was before — plain English]

CHANGE MADE
  [What was changed and why — plain English]

VISUAL WALKTHROUGH
  Before: [description of old layout]
  After:  [description of new layout]

FILES CHANGED
  [template or CSS file path — what changed]

DESIGN CONSISTENCY CHECK
  Pill/badge styles consistent: [yes/no — detail if no]
  CSS class reuse vs new classes: [list any new classes introduced]

TEST RESULTS
  Suite: [X/Y passing]
  Page render tests: [pass/fail]

CHECKLIST OF CHANGES
  [ ] [change 1]
  [ ] [change 2]

NEXT STEPS
  [If production deployment needed, flag for Saeed approval]

DECISIONS NEEDED
  [Anything Saeed must approve before production]
```

---

## Common Failure Modes — How to Prevent

- **Inconsistent pill or colour styles** — always check the existing CSS class names before adding new ones. If `summary_chips` handles priority display on cards, it must handle it in the side panel too.
- **Changing production templates without approval** — always sandbox first, always get explicit sign-off before production.
- **Solving the stated problem but creating a new one** — run the full page render test suite, not just the page you changed.

---

## Success Criteria

1. The reported issue is resolved and verifiably better — not just different.
2. The design is consistent with the existing component system — no new pill classes, no one-off colour values.
3. The UX pass confirms the staff workflow is clearer: the right action is visible faster than before.

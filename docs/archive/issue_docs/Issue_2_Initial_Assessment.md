# Issue #2: Urgent Banner Visibility - Initial Assessment

**Issue:** Critical alerts/urgent banners are hidden in narrow viewport (tablet/mobile)
**Severity:** HIGH
**Reported:** 2026-05-22
**Impact:** Staff cannot see urgent notifications on mobile/tablet devices

---

## Problem Statement

The urgent attention banner (`.urgent-panel`) which displays critical alerts and red flags is not visible on narrow viewports (tablets and mobile phones). This is a critical UX issue because urgent notifications are essential for staff awareness during their shifts, particularly when using mobile devices.

---

## Current Implementation Analysis

### HTML Structure
**Location:** `/JeffLocal/dashboard/templates/index.html`

The urgent banner is rendered as:
```html
<section class="urgent-panel" aria-label="Urgent Attention">
  <div>
    <h2>⚠️ Urgent Attention</h2>
    <p>{{ alert message }}</p>
  </div>
  <div class="urgent-counts">
    <!-- Critical issue counts with links -->
  </div>
  <div class="urgent-actions">
    <!-- Action buttons -->
  </div>
</section>
```

### Current CSS
**Location:** `/JeffLocal/dashboard/static/dashboard.css`

The urgent-panel styling:
```css
.urgent-panel {
  background: var(--danger-bg);
  border: 1px solid var(--danger-line);
  border-left: 4px solid var(--danger);
  border-radius: 10px;
  padding: 16px 18px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
```

### Container Context
The urgent-panel is inside `.dashboard-scroll`:
```css
.dashboard-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
```

---

## Root Cause Analysis

### Findings

1. **No media queries for narrow viewports** - The CSS file contains NO `@media` queries at all
2. **Flex container issue** - `.urgent-panel` uses `justify-content: space-between` which may cause layout issues when items don't fit
3. **Large padding on scroll container** - `.dashboard-scroll` has 24px horizontal padding which reduces content width
4. **No responsive rules for children** - `.urgent-counts` and `.urgent-actions` have `flex-wrap: wrap` but may still overflow

### Probable Causes

1. **Sidebar not collapsing on narrow screens** - The analytics sidebar (280px) takes up too much space on mobile, leaving insufficient room for content
2. **Banner might be pushed off-screen** - The flex layout with `justify-content: space-between` may cause elements to exceed viewport width
3. **Horizontal overflow hidden** - Parent containers with `overflow: hidden` (common in flex layouts) may be clipping the banner
4. **No viewport meta tag handling** - Mobile viewport scaling issues may be affecting layout

---

## Related Code Analysis

### Similar Issue (Issue #1 - Now Fixed)
The toggle button issue was also CSS-based:
- Used `border: 1px solid` and `background: var(--panel)` making it invisible
- Fixed by changing to `border: none` and `background: transparent`

Issue #2 appears to have a similar root cause: **CSS display/visibility rules hiding content on narrow screens without proper responsive design**

### Sidebar Width Issue
- Sidebar width: `--sidebar-w: 280px`
- Sidebar collapsed width: `--sidebar-coll-w: 56px`
- No mechanism to auto-collapse on mobile

---

## Expected Behavior

On narrow viewports (< 768px):
1. Sidebar should auto-collapse to collapsed state (56px)
2. Urgent banner should be fully visible
3. All content should be readable without horizontal scroll
4. Touch targets should meet accessibility standards (44px minimum)

---

## Investigation Checklist

- [x] Found urgent-panel HTML markup
- [x] Located CSS for urgent-panel styling
- [x] Checked for media queries (NONE found)
- [x] Analyzed parent container layout
- [x] Identified sidebar width as contributing factor
- [ ] Test on actual mobile viewport
- [ ] Check JavaScript responsiveness code
- [ ] Look for hidden overflow rules in parent containers

---

## Next Steps

1. Add media query for narrow viewports (max-width: 768px)
2. Auto-collapse sidebar on mobile viewports
3. Adjust banner layout for mobile (stack items vertically)
4. Test on multiple device sizes (iPhone, iPad, Android)
5. Verify no horizontal scroll on any viewport

---

## Files to Modify

1. `/JeffLocal/dashboard/static/dashboard.css` - Add responsive styles
2. `/JeffLocal/dashboard/templates/index.html` - Possibly adjust banner structure
3. `/JeffLocal/dashboard/app/` - Check for JavaScript responsiveness code

---

## Estimated Fix Complexity

**Medium** - Similar structure to Issue #1 (CSS-based), but may require:
- Multiple media queries for different breakpoints
- JavaScript changes for sidebar auto-collapse
- Testing on multiple devices

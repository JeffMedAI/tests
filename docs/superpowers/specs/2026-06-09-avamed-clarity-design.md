# Avamed Clarity — Design System & Sprint Spec
**Date:** 2026-06-09  
**Approved approach:** B — Avamed Identity  
**Scope:** Landing page (avamed.uk) + Full dashboard redesign (all pages)  
**Dark mode:** Phase 2  
**Status:** Awaiting Saeed review before implementation

---

## 1. Design System — "Avamed Clarity"

### 1.1 Philosophy

Every second counts at a GP surgery reception desk. The interface must direct attention to what matters, eliminate decision fatigue, and feel like the most premium tool in the practice. The design language is called **Clarity** — calm, purposeful, authoritative. Not corporate-cold. Not NHS-generic. Unmistakably Avamed.

### 1.2 Colour Palette

| Token | Name | Hex | Usage |
|---|---|---|---|
| `--brand-navy` | Avamed Deep Navy | `#0B3D6B` | Primary brand, topbar, CTAs |
| `--brand-teal` | Avamed Teal | `#00A896` | Accent, highlights, active states, CTA hover |
| `--brand-teal-soft` | Teal Soft | `#E6F7F5` | Teal tint backgrounds, selected states |
| `--brand-teal-mid` | Teal Mid | `#7DD3CA` | Borders, dividers on teal surfaces |
| `--bg` | Slate White | `#F7F9FC` | Page background |
| `--panel` | Pure White | `#FFFFFF` | Cards, panels, modals |
| `--ink` | Rich Black | `#111827` | Primary text |
| `--ink-muted` | Slate 600 | `#4B5563` | Secondary text |
| `--ink-subtle` | Slate 400 | `#9CA3AF` | Tertiary, placeholders |
| `--line` | Slate 200 | `#E5E7EB` | Borders, dividers |
| `--line-strong` | Slate 300 | `#D1D5DB` | Stronger dividers |
| `--danger` | NHS Red | `#D5281B` | Urgent, errors |
| `--danger-bg` | Red Tint | `#FDE8E7` | Urgent card backgrounds |
| `--danger-line` | Red Border | `#F3A8A4` | Urgent card borders |
| `--warning` | NHS Amber | `#C45000` | High priority, warnings |
| `--warning-bg` | Amber Tint | `#FFF4E5` | Warning card backgrounds |
| `--warning-line` | Amber Border | `#FFCD6A` | Warning borders |
| `--success` | NHS Green | `#00703C` | Resolved, safe |
| `--success-bg` | Green Tint | `#F0FDF4` | Success card backgrounds |
| `--success-line` | Green Border | `#86EFAC` | Success borders |
| `--purple` | Purple | `#7C3AED` | Identity flags |
| `--purple-bg` | Purple Tint | `#FAF5FF` | Identity card backgrounds |

**NHS blue (`#005EB8`) is retired as the primary brand colour.** It remains available as `--nhs-blue` for compliance badges and NHS integration indicators only.

### 1.3 Typography

| Role | Font | Weights | Usage |
|---|---|---|---|
| Display / Hero | Plus Jakarta Sans | 700, 800 | Landing page hero headlines, page titles |
| Heading | Plus Jakarta Sans | 600, 700 | Section headings, card titles, navigation |
| Body | Inter | 400, 500 | All body copy, labels, descriptions |
| Mono | JetBrains Mono | 400, 500 | Case IDs, NHS numbers, batch IDs |

**Google Fonts import (landing page):**
```css
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');
```

**System stack (dashboard — no external font request for performance):**
```css
--font-display: 'Plus Jakarta Sans', 'Segoe UI', system-ui, sans-serif;
--font-body:    'Inter', 'Segoe UI', system-ui, sans-serif;
--font-mono:    'JetBrains Mono', 'Courier New', monospace;
```

**Font sizes (unchanged from current — already calibrated for clinical density):**
```
--text-xs:   12px
--text-sm:   13px
--text-base: 14px
--text-lg:   16px
--text-xl:   20px
--text-2xl:  24px
--text-3xl:  30px
--text-4xl:  40px   (new — landing page hero)
--text-5xl:  56px   (new — landing page hero)
```

### 1.4 Spacing & Radius

```css
--radius-sm:  4px    /* inputs, small chips */
--radius-md:  8px    /* cards, panels */
--radius-lg:  12px   /* modals, large cards */
--radius-xl:  16px   /* hero sections, landing cards */
--radius-pill: 99px  /* badges, pills */
```

Spacing: 4px base unit. Common values: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64px.

### 1.5 Elevation (Shadows)

```css
--shadow-xs: 0 1px 2px rgb(0 0 0 / .05);
--shadow-sm: 0 1px 3px rgb(0 0 0 / .08), 0 1px 2px -1px rgb(0 0 0 / .08);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / .08), 0 2px 4px -2px rgb(0 0 0 / .08);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / .08), 0 4px 6px -4px rgb(0 0 0 / .08);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / .10), 0 8px 10px -6px rgb(0 0 0 / .10);
--shadow-brand: 0 8px 24px rgb(11 61 107 / .20);   /* brand navy glow */
--shadow-teal:  0 8px 24px rgb(0 168 150 / .20);   /* teal CTA glow */
```

### 1.6 Animation Tokens

```css
--duration-fast:   120ms   /* hover colour changes */
--duration-base:   200ms   /* transitions, panels sliding */
--duration-slow:   300ms   /* page transitions, modals */
--duration-xslow:  600ms   /* count-up animations, hero entrances */
--ease-default:    cubic-bezier(0.4, 0, 0.2, 1)
--ease-spring:     cubic-bezier(0.34, 1.56, 0.64, 1)  /* slight overshoot for buttons */
--ease-out:        cubic-bezier(0, 0, 0.2, 1)
```

All animations respect `@media (prefers-reduced-motion: reduce)` — disable or reduce all transitions.

### 1.7 Component Library Changes

**Topbar:** Background changes from `#005EB8` (NHS blue) to `#0B3D6B` (Avamed navy). All other topbar structure stays the same.

**Active nav link:** Highlight changes from `rgba(255,255,255,.2)` to a teal left-border indicator: `border-left: 3px solid #00A896` on a slightly lighter navy background.

**Primary buttons:** Background → `#0B3D6B`. Hover → `#00A896` (teal). Transition: 200ms.

**CTA buttons (landing page only):** Background → `#00A896` teal. Hover → darken 10% + `--shadow-teal`. Spring easing on press.

**Badges — priority:** Urgent stays NHS red. High → amber. Normal → teal tint (replaces NHS blue tint). Low → grey.

**Focus rings:** 3px solid `#00A896` (teal) replacing NHS blue. Maintains WCAG 2.4.7 compliance.

**Cards:** Slight border-radius increase from 10px → 12px. Shadow upgrade from `--shadow-xs` to `--shadow-sm` on hover.

---

## 2. Landing Page — avamed.uk

### 2.1 Purpose

Public-facing marketing homepage. Three audiences:
1. **GP Practice Managers** — primary buyer
2. **GP Partners / Senior Partners** — sign-off authority
3. **ICB Digital Leads** — procurement influence

### 2.2 Page Sections

#### Section 1: Navigation (sticky, height 64px)
- Left: Avamed logo (wordmark + icon)
- Centre: `How It Works` · `For Practices` · `Pricing` · `Compare`
- Right: `Practice Login` (ghost button, navy border) + `Book a Demo` (teal filled CTA)
- On scroll: subtle white background + shadow appears
- Mobile: hamburger menu

#### Section 2: Hero
- **Headline (H1, 56px, Plus Jakarta Sans 800):** "Every patient request. Captured. Prioritised. Resolved."
- **Sub (18px, Inter 400, ink-muted):** "Jeff is the on-premises AI that answers your phone calls, receives WhatsApp messages, and handles online requests — then delivers a prioritised task to your reception team. No cloud. No data leaving the building."
- **CTAs:** `Book a Free Demo` (teal filled, large) + `See How It Works` (ghost, scrolls to demo section)
- **Hero visual:** Animated SVG/CSS illustration. Three intake icons (phone, WhatsApp, web form) with animated arrows flowing into a single Avamed dashboard inbox preview. The inbox shows 3 cards: one red (URGENT), one amber (HIGH), one green (RESOLVED). Cards animate in one by one on page load.
- Background: White with a subtle radial teal gradient bloom top-right. Not distracting — purely atmospheric.

#### Section 3: Problem Strip (dark navy background)
- Three stat blocks separated by vertical dividers:
  - `68 calls` before 9:30am — "Your reception team is overwhelmed before the day starts"
  - `40 minutes` average hold time — "Patients give up. They call 111. Or worse."
  - `45%` of reception time spent on admin — "Your skilled staff are glorified message-takers"
- Source footnote: [UNVERIFIED — replace with cited NHS/BMA stats before publishing]

#### Section 4: How It Works (3-step interactive)
- Step 1: **Patient calls, texts, or submits online**
  - Animated: phone ringing → waveform → tick
- Step 2: **Jeff processes it on your server**
  - Animated: waveform → AI icon → structured card appearing
  - Small badge: "On your premises. Data never leaves."
- Step 3: **Prioritised task in your staff dashboard**
  - Animated: card appears in dashboard with priority badge + patient name
  - Small text: "Staff guided through resolution in 4 steps"
- Each step has a short paragraph of explanation below the animation.

#### Section 5: WhatsApp Feature Panel
- Background: White with a subtle WhatsApp green left-border accent (`#25D366`)
- Headline: "Patients who won't wait on hold can now text you"
- Body: "A patient texts your practice WhatsApp number with their reason for contact. Jeff reads it, extracts what matters, and adds it to the same priority queue as your phone calls. No new app. No NHS login. Just a text message."
- Mock WhatsApp conversation (static image/SVG): Patient texts "I need a sick note for work" → Response: "Thanks, we've received your request. Your reception team will be in touch shortly."
- Right side: Dashboard card showing the same request, now prioritised.
- Badge chip: `Coming Soon · Join the Pilot`

#### Section 6: On-Premises Trust
- Background: Avamed navy (`#0B3D6B`)
- White text
- Headline: "Your patients' data never leaves your building"
- Body: "Every other AI platform in this market sends patient data to their cloud servers. Avamed runs entirely on your own hardware. The AI processes everything locally. Nothing is transmitted outside your practice."
- Comparison table (white on navy): Three columns — Avamed ✓ | Cloud-based AI ✗ | Traditional | with rows: Data stays on-site / On-premises AI / GDPR by design / No vendor data access / Works offline
- Compliance badges: GDPR · NHS DSPT (in progress) · Cyber Essentials (in progress) · Powered by Hostcomm NHS Digital Marketplace

#### Section 7: Competitor Comparison Table
- Clean, airy table. Avamed column has teal header.
- Rows: Voice call capture / WhatsApp intake / On-premises / Guided staff workflow / Unified queue / Pricing transparency
- Competitors: EMMA · Rapid Health · Anima · Accurx
- No aggressive language — just ticks and crosses.

#### Section 8: Pricing
- Three cards: **Starter** · **Practice** · **Multi-Site**
- Each has: price/month · patient list size · key features list · CTA button
- Below pricing: "Less than one staff hour per month. No per-call charges. Cancel anytime."
- Small print: Annual contract. Setup fee [TBD].
- Prices: [Awaiting Saeed commercial decision — spec uses PLACEHOLDER]

#### Section 9: Case Study
- Background: Soft teal tint (`#E6F7F5`)
- Headline: "A Southport GP Practice reduced reception call time by [X]% in the first month"
- Pull quote from practice manager (anonymised)
- Three stat bubbles: Calls handled automatically / Staff hours saved per week / Patient access score improvement
- All stats: [UNVERIFIED — placeholder until pilot data collected]
- CTA: "See how it works at your practice → Book a Demo"

#### Section 10: Demo Booking Form
- Clean centred card on white background
- Headline: "See Avamed at your practice"
- Fields: Full name · Practice name · Email address · Phone number · Approx patient list size (dropdown: <5k / 5–8k / 8–12k / 12k+) · Best time to call (dropdown)
- Submit button: "Request a callback" (teal)
- Below: "We'll call you within one working day."
- Privacy: "Your information is only used to arrange your demonstration. See our Privacy Policy."

#### Section 11: Footer
- Left: Avamed logo + tagline "On-premises AI for NHS primary care"
- Centre links: Privacy Policy · Contact · How It Works · Pricing
- Right: Compliance badges (small)
- Below divider: "© 2026 Avamed. All rights reserved. | Powered by Hostcomm UK (NHS Digital Marketplace listed)"
- Note: Do not include Churchtown by name until written consent obtained.

### 2.3 Technical Spec (Landing Page)

- **Stack:** Single HTML file + embedded CSS + vanilla JS (no framework dependency — fast load, easy to host on Cloudflare Pages)
- **Animations:** CSS keyframes + IntersectionObserver for scroll-triggered entrance animations. No heavy JS libraries.
- **Fonts:** Google Fonts (Plus Jakarta Sans + Inter) loaded with `display=swap`
- **Performance target:** Lighthouse score 90+ on mobile
- **Responsive breakpoints:** 375px (mobile) · 768px (tablet) · 1280px (desktop) · 1440px (wide)
- **Form submission:** HTML form → Cloudflare Pages Function or simple email via Formspree (no backend needed for v1)
- **Practice login button:** Links to existing dashboard URL (https://dashboard.app-avamed.uk)

---

## 3. Dashboard Redesign — All Pages

### 3.1 Shared Changes (Apply Everywhere)

1. **Topbar:** Navy `#0B3D6B` replaces NHS blue. Teal active indicator on nav links.
2. **Typography:** Plus Jakarta Sans for headings, Inter for body text. Loaded via Google Fonts with fallback to system fonts if blocked.
3. **Favicon:** Update to Avamed mark (navy circle + teal pulse icon — design TBD).
4. **Focus rings:** `#00A896` teal everywhere.
5. **Primary button:** Navy fill, teal hover.
6. **Card border-radius:** 12px throughout.

### 3.2 Login Page (`/login`)

**Current:** Basic white form.

**New:**
- Left panel (60% width): Full-height image/gradient. Avamed navy-to-teal diagonal gradient. White wordmark logo centred. Below: Three animated stat counters (calls handled, tasks resolved, practices live). Bottom: Compliance badges.
- Right panel (40%): White background. Centred login form. "Welcome back" heading (Plus Jakarta Sans 700). Username + password fields with Inter. Teal "Sign in" button. Forgot password link. "New practice? Book a demo →" link at bottom.
- Mobile: Single-column. Left panel collapsed to a thin teal header strip with logo.

### 3.3 Dashboard Overview (`/`)

**New elements:**
1. **Live Priority Ribbon:** Full-width banner below topbar. Shows: `● 3 Urgent  ·  11 Open  ·  2 Red Flag  ·  Pipeline: Healthy ●`. The urgent count has a CSS pulse animation. When queue is empty: green "All Clear" state.
2. **KPI Cards:** Count-up animation on page load (numbers count from 0 over 800ms). Border-left colour coded by status.
3. **System Health dot:** Top-right of topbar. 8px dot: green/amber/red. Tooltip on hover: "Pipeline healthy — last import 2 min ago".
4. **Page font upgrade:** h1/h2 → Plus Jakarta Sans.

### 3.4 Requests / Case Queue (`/requests`)

**New elements:**
1. **Guided Workflow Mode:** When a case card is clicked, the right detail panel shows a 4-step progress indicator at the top:
   - `1 · Confirm Patient` → `2 · Review Request` → `3 · Choose Action` → `4 · Complete`
   - Active step highlighted in teal. Completed steps show a teal tick.
   - Each step has a clear prompt: "Is this the correct patient? Check DOB and NHS number below."
2. **Patient Hover Card:** Hovering over a patient name in the list shows a 200ms-delayed tooltip card with: last case type, DOB, GP name, any red flags. Disappears on mouseout.
3. **Command Palette:** Press `/` anywhere. Spotlight overlay appears. Search patients, cases, team members, or trigger actions ("resolve", "escalate"). Keyboard navigable. Dismiss with Escape.
4. **Card visual upgrade:** Left border colour = priority (red/amber/teal/grey). Subtle `--shadow-sm` on hover. 12px radius.

### 3.5 Case Detail (`/case/<id>`)

**New elements:**
1. **Guided workflow steps** persist as a sticky header below the topbar when scrolling the detail page.
2. **Action buttons** are teal (resolve) / red (escalate) with clearer labels: "Mark Resolved" and "Escalate to GP" — not icon-only.
3. **Patient identity block** uses JetBrains Mono for NHS number, DOB, EMIS number — visually distinct from prose.

### 3.6 Patients Page (`/patients`)

- Same grid layout, updated card styling (12px radius, shadow-sm hover).
- Patient name uses Plus Jakarta Sans 600.
- Search bar upgraded to the rounded pill style from the landing page.

### 3.7 Staff Page (`/staff`)

- Cards updated to new radius/shadow.
- Online/offline presence indicator (green dot / grey dot) added to each staff avatar.
- "Add Staff" CTA button → teal.

### 3.8 Reports Page (`/reports`)

- Chart colours updated to use brand palette (navy primary series, teal secondary, NHS red for urgent).
- Section headings → Plus Jakarta Sans 700.
- ApexCharts integration: replace any Chart.js instances with ApexCharts for premium animated charts.

### 3.9 Settings Page (`/settings`)

- Two-column layout: left nav anchors (System · Security · Notifications · Team · Billing), right content.
- Section headers → Plus Jakarta Sans 600.
- Toggle switches → teal when active (replaces NHS blue).

### 3.10 Alerts Page (`/alerts`)

- Alert cards: left border colour coded (red = critical, amber = warning, teal = info).
- Unread badge → teal.
- Mark-all-read button → ghost style.

### 3.11 Profile Page (`/profile`)

- Avatar background → navy gradient.
- Edit fields styled to new input system (teal focus ring).

### 3.12 Forgot Password Page (`/forgot`)

- Same two-panel layout as login page (reuse the component).

---

## 4. Staff Walk-Through — Onboarding System

### 4.1 First Login Tour (4 steps)

Triggered once, on first login. Overlay backdrop with spotlit element. Skip button always visible.

| Step | Spotlit element | Message |
|---|---|---|
| 1 | Priority ribbon | "These are your cases. Red means urgent — action those first." |
| 2 | First case card | "Click any case to open it. The system guides you through what to do." |
| 3 | Pipeline health dot | "This indicator shows if the system is processing calls. Green means healthy." |
| 4 | Command palette hint | "Press / anywhere to search patients, cases, or trigger actions." |

After step 4: "You're ready. Your first case is waiting." → CTA: "Open first case".

### 4.2 Contextual Tip Badges (Week 1)

Small teal dot on features not yet used. Clicking opens a one-sentence tooltip. Dismissed forever on click. All badges auto-hide after 7 days (stored in localStorage).

Features with tips: Import button · Reports nav link · Bulk-select · Copy NHS number.

### 4.3 After Week 1

All onboarding elements hidden. Clean interface. No visual noise.

---

## 5. New Components Required

| Component | Where used | Notes |
|---|---|---|
| Priority Ribbon | Dashboard overview | CSS animated pulse ring on urgent count |
| Live Pipeline Dot | Topbar (all pages) | Polls `/api/health` every 60s |
| Guided Workflow Steps | Requests detail panel, Case detail | 4-step progress indicator |
| Patient Hover Card | Requests list | IntersectionObserver + 200ms delay |
| Command Palette | All pages | Keyboard: `/` to open, Escape to close, arrow keys to navigate |
| Count-up KPI | Dashboard overview | vanilla JS, 800ms ease-out |
| Onboarding Overlay | First login | Stored in localStorage `avamed.onboarding.v1` |
| Contextual Tip Badges | Multiple pages | localStorage dismissal |
| Two-panel Auth Layout | Login, Forgot password | Reused component |

---

## 6. Out of Scope (Phase 2)

- Dark mode
- WhatsApp integration backend (landing page "coming soon" label only)
- Mobile app / PWA
- Live WebSocket updates (pipeline dot polls REST for now)
- EMIS/SystmOne deep integration
- Billing/subscription management UI

---

## 7. Spec Self-Review

**Placeholder check:** Pricing figures marked as [Awaiting Saeed decision]. Case study stats marked [UNVERIFIED]. Competitor pricing marked [UNVERIFIED]. All other content is concrete.

**Internal consistency:** Design tokens used throughout. No conflicting colour values. Typography scale consistent between landing and dashboard.

**Scope check:** This is large but decomposable. Implementation plan will split into: (1) design system CSS, (2) landing page, (3) dashboard page-by-page.

**Ambiguity check:** "Command palette" scope is clear (search + actions, keyboard nav). "Guided workflow" scope is clear (4-step overlay in detail panel). "On-premises trust" is a content section, not an engineering claim requiring verification — it describes the existing architecture accurately.

---

*Spec written by: Lead Agent / Strategy Agent collaboration*  
*Next step: Saeed reviews this document → approval → implementation plan via writing-plans skill*

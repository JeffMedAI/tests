# Product

## Register

product

## Users

UK GP surgery reception staff. Non-clinical admin role, desktop workstation in a busy front-desk environment — often fielding calls while simultaneously working the dashboard. Sessions are typically 4–8 hours of continuous use. Staff range from digitally confident to digitally cautious; the interface must not demand technical literacy to operate confidently.

## Product Purpose

Avamed (internal name: JeffLocal) is an AI-assisted patient intake triage tool for UK GP and dental surgeries. Patients call the surgery; Jeff (voice AI, Hostcomm UK) captures the reason for contact. The system extracts structured data, matches the caller to NHS/EMIS patient records, applies safety rules, and delivers a prioritised task to reception staff on a web dashboard. Staff action the task — booking, escalation, messaging — without reading a raw transcript. No clinical decisions are made by the AI; admin intake only.

Success: reception staff clear the queue faster, urgent cases surface immediately, nothing falls through the cracks.

## Brand Personality

Calm · Precise · Trustworthy

Clinical confidence without clinical coldness. The interface is quiet when nothing is urgent and unambiguous when something is. Every element earns its place by reducing cognitive load, not adding visual noise.

## Anti-references

- **Generic NHS blue / GOV.UK style**: Sterile, institutional, dated. Avamed is better than the status quo — it should look and feel like it.
- **Dense EHR / EMIS-style screens**: Overcrowded grids, tiny text, no hierarchy. The opposite of what staff need when a call queue is building.
- **Flashy SaaS dark mode**: Neon accents, glassmorphism, dark-first aesthetics. This is a daytime clinical environment under fluorescent light, not a developer tool.
- **Bland corporate intranet**: Grey, lifeless, zero hierarchy. The SharePoint aesthetic kills urgency signals.

## Design Principles

1. **Urgency speaks first.** Red flags and unresolved critical cases must be immediately legible — not discovered. The hierarchy does the shouting; staff shouldn't have to hunt.
2. **Quiet confidence.** When the queue is normal, the interface is calm. Anxiety comes from the job, not from the tool.
3. **One action at a time.** Every screen has a clear primary action. Secondary actions are reachable but never competing.
4. **Clinical-grade trust.** Every displayed value is verifiable, every action is reversible or confirmable. The UI never guesses.
5. **Fast above all else.** Reception staff are interrupted constantly. The dashboard must be scannable in 3 seconds and actionable in 10.

## Accessibility & Inclusion

WCAG 2.1 AA minimum (UK public sector obligation via DSPT / NHS Digital standards). Keyboard navigation required throughout. No colour-only urgency signals — pair with icons and text labels. Minimum 16px body text. `prefers-reduced-motion` respected for all animations. No time-limited interactions.

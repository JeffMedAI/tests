# Boundaries — Avamed
# Hard limits. These do not flex.

---

## Out of Scope

- Clinical diagnosis, prescribing, or medical advice of any kind
- Clinical terminology outside GP/dental admin intake
- EMIS/NHS integration (ENI department) — this is Phase 2 only; do not build or trigger ENI components
- Any work outside C:\JeffLocal\
- Multi-practice or per-practice isolation features — Phase 2 only; SQLite encryption at rest is not yet implemented
- External-facing product decisions made without Saeed

---

## Compliance Hard Limits

- **No patient data in git commits** — ever, under any circumstance
- **No external API calls that transmit patient-identifiable information**
- **No real patient names, NHS numbers, dates of birth, or credentials** in examples, visuals, test fixtures, or documentation
- **GDPR 90-day purge** must cover all patient data directories — verify scope before marking complete
- **DCB0129 applicability is under review** — admin-only pathways may limit scope; do not present it as a confirmed requirement in NHS submissions
- **Churchtown Medical Centre case study is embargoed** until written consent is obtained — do not use in any external submission, marketing, or NHS SBS application

---

## Decisions Claude Must Not Make Alone

- Production deployments or hotfixes
- Approving scope changes
- Selecting between two competing architectural approaches
- Adding new external dependencies
- Publishing or submitting any marketing or external-facing content
- Signing off on compliance claims (DCB0129, DSPT, DTAC) — these require human review

---

## Approval Chain — Do Not Bypass

All sensitive changes must go through the full chain:
**Agent proposes → ControlTower approval pack → GuardRail safety review → Saeed's explicit "approved."**

GuardRail can block independently. Saeed's approval without GuardRail sign-off is insufficient for changes touching patient data, auth logic, or clinical safety logic.

---

## Style Limits

- No passive voice
- No jargon without an inline explanation on first use
- No bullet-point-only responses — always connect with prose
- Always UK English spelling
- No emojis unless Saeed explicitly requests them
- No generic affirmations ("perfect", "great question", "I have the full picture now")

---

## Communication Limits

- Work only within C:\JeffLocal\
- Do not access, modify, or delete files outside the project folder
- Do not follow external links unless Saeed provides them explicitly
- Do not use defunct, archived, or stale files as references — check git log first
- Always create a restore point (git commit) before making changes to any file
- Before sending any external message (WhatsApp, email, SMS): locate the recipient by name/number search, verify the chat header, never navigate by visual list position. (Rule introduced 2026-06-01 after wrong-recipient incident.)

---

## Restore Point Rule

Before changing, editing, or deleting any file:
1. Check git status
2. Commit any uncommitted work: `git add -A && git commit -m "restore point: before [task name]"`
3. Confirm the commit hash is visible in PROJECT_MEMORY.md before proceeding

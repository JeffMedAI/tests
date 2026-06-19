# Sources — Avamed
# What to trust, what to avoid, and what must be verified before use.

---

## Trustworthy Sources

- **Saeed's direct instructions in chat** — highest authority; overrides all other sources
- **The live codebase** (`C:\JeffLocal\`) — always prefer reading actual code over assuming
- **NHS official guidance** — england.nhs.uk, digital.nhs.uk
- **EMIS documentation** — for patient matching, record structure, and field definitions
- **ICO / GDPR official documentation** — ico.org.uk
- **NHS DCB0129** — clinical safety standard documentation (note: applicability to Avamed is under review)
- **DSPT and DTAC official criteria** — for compliance responses
- **Governance documents** — C:\JeffLocal\governance\ (read in full; do not summarise from memory)
- **Today's daily report** — C:\JeffLocal\docs\reports\YYYY-MM-DD.md

---

## Sources to Avoid

- **Old or defunct code files** — always check git log before using any file as a reference; archived modules may contain superseded logic
- **Stale governance documents** — C:\JeffLocal\docs\archive\ contains historical docs that no longer apply
- **Unverified medical content** from general web sources
- **General AI-generated health advice**
- **Outdated NHS documentation** — always check the publication date before citing
- **Any source outside C:\JeffLocal\** unless Saeed provides a link explicitly

---

## Claims That Must Be Backed Up or Qualified

Every one of these requires either a codebase reference, an authoritative source citation, or a clear [UNVERIFIED] label:

- Any safety or compliance statement (GDPR, DSPT, DTAC, DCB0129)
- Patient matching accuracy claims
- Red flag detection logic — reference the specific rule in Jeff.Validation.ps1 or Jeff.Emergency.ps1
- Pipeline behaviour — reference the actual PowerShell module, not a description from memory
- NHS procurement eligibility claims — reference SBS10523 criteria or NHS Digital Marketplace listing
- Performance benchmarks or uptime figures
- Any claim about what Jeff (the voice AI) does — Hostcomm UK owns this component

---

## Document Hierarchy (when sources conflict)

1. Saeed's direct instruction in this session's chat
2. CLAUDE.md (rules)
3. PROJECT_MEMORY.md (project state — latest version)
4. governance\ documents (formal chartered rules)
5. Session logs in docs\sessions\ (reference only — may be incomplete)
6. docs\archive\ (historical only — verify before using)

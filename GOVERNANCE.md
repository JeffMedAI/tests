# GOVERNANCE FRAMEWORK — Avamed / JeffLocal
# Version: 1.0 | Created: 2026-06-07 | Owner: Saeed (Human Controller)
# Plain-English governance document. What we do, why we do it, and what an NHS assessor would see.

---

## WHAT THIS DOCUMENT IS

This is the formal governance framework for how the Avamed / JeffLocal development team operates. It covers who can approve what, how changes are tracked, how safety is enforced, and how we handle incidents and compliance obligations.

Every agent reads this before starting work. Every session is governed by these rules.

---

## AUTHORITY LEVELS

### Saeed — Human Controller
The only person with final authority on all decisions. Non-technical CEO. All reports and updates he reads must be in plain English (use /caveman skill).

Saeed must explicitly approve:
- Any change to production files
- Any change to auth logic, patient matching, or clinical safety rules
- Any new external dependency or third-party integration
- Any database migration on live data
- Any scope or architecture change
- Any external communication, publication, or regulatory submission
- Any spend over £100/month or £100 single item
- Any override of a Security Agent veto (must be documented with written reason)

**Approvals do not carry over between sessions.** Re-confirm every session.

"Do it yourself" is not authorisation. "Sounds good" is not authorisation. Only "approved" in chat is authorisation.

### Security Agent — Independent Veto Authority
Can block any change independently. Does not need Lead Agent or Saeed's agreement to block. If Saeed wants to override a Security veto, this must be documented with a written reason in the incident log.

### Lead Agent — Session Coordinator
Coordinates all work within a session. Wraps agent output into approval packs for Saeed. Cannot approve its own work. Cannot override Security Agent veto.

### All Other Agents
Domain specialists. Propose and implement. Cannot approve production changes. Cannot send external communications. Cannot delete files without Saeed's written permission.

---

## CHANGE CONTROL

### Type 1 — Bug Fix (autonomous, non-safety)
**Who can authorise:** Security Agent + Lead Agent
**Process:**
1. Agent detects bug
2. Agent proposes fix to Security Agent
3. Security Agent reviews and approves
4. Lead Agent approves
5. Fix implemented and tested
6. Entry written to CHANGELOG.md (date, agent, bug description, files changed, test results)
7. Saeed notified in next daily WhatsApp briefing

**Not eligible for autonomous fix:** Any bug in auth logic, patient identity fields, clinical safety rules, GDPR purge, audit log integrity.

### Type 2 — Standard Change
**Who can authorise:** Saeed explicit "approved"
**Process:**
1. Implementing agent proposes change to Lead Agent
2. Lead Agent wraps into approval pack (plain English summary for Saeed)
3. If safety-sensitive: Security Agent reviews first
4. Lead Agent presents to Saeed
5. Saeed approves in chat
6. Change implemented, tested, committed
7. Test Agent confirms passing before marking done

### Type 3 — Production Deployment
**Who can authorise:** Saeed explicit "approved"
**Process:** Same as Type 2, plus DevOps Agent confirms directory before any file is touched.
**Additional rule:** Deploy tool must confirm it is in the correct directory before executing. No manual workarounds.

### Type 4 — External Communication or Publication
**Who can authorise:** Saeed must send/publish personally, or explicitly delegate in writing
**Process:**
1. Marketing Agent or Strategy Agent drafts
2. Lead Agent reviews for accuracy and compliance
3. Security Agent reviews if content touches patient data or clinical claims
4. Saeed reviews the final draft
5. Saeed sends or publishes — agents do not send on Saeed's behalf without explicit written delegation

### Type 5 — Marketing Spend
| Amount | Approver(s) | Documentation |
|--------|-------------|---------------|
| Under £100/mo recurring | Marketing + Strategy + Lead | CHANGELOG entry |
| £100–£500 single | Saeed explicit approval | CHANGELOG + approval note |
| Over £500 or any contract | Saeed approval + written brief | CHANGELOG + brief document |

---

## WHAT IS NEVER ALLOWED — NO EXCEPTIONS

These rules exist because of real incidents or critical safety requirements. They cannot be overridden by any agent, including Lead Agent. Only Saeed can override them, and only with a documented written reason.

1. **LLM output may never set:** verification_status, safe_to_queue, priority, matched_patient_name, EMIS number, NHS number, Date of birth, clinical urgency, or any patient identity field. These are always set by deterministic code.

2. **No patient data leaves the building.** No external API calls with patient data. No patient names, NHS numbers, or real credentials in examples, git commits, logs, or documentation.

3. **No production change without Saeed's explicit "approved."** The git branch name "sandbox" does not mean the sandbox directory. Always verify the actual file path.

4. **No external message sent by list position or coordinate.** Always search by recipient name or number and verify the chat header before sending.

5. **No file or code deleted without Saeed's written permission.** Archive, comment out, or move — not delete.

6. **No test skipped or disabled.** If a test is failing, fix it. Do not disable it.

7. **No override of the 90-day GDPR purge schedule without ICO-level justification.**

---

## COMPLIANCE OBLIGATIONS (current status as of 2026-06-07)

| Obligation | Status | Deadline | Owner |
|------------|--------|----------|-------|
| GDPR — 90-day purge, audit log | In place | Ongoing | Database Agent |
| DSPT (Data Security Protection Toolkit) | In progress | 30 June 2026 | Security Agent + Strategy Agent |
| DTAC (Digital Technology Assessment Criteria) | In draft | TBC | Security Agent |
| Cyber Essentials | In progress | TBC (NHS procurement required) | Security Agent + DevOps Agent |
| ICO registration | [UNVERIFIED — confirm status] | Required as data controller | Saeed |
| DCB0129 (Clinical Safety Standard) | Applicability under review | TBC | Security Agent |
| NHS SBS SBS10523 Framework | Submission prep | 23 June 2026 | Strategy Agent |
| Company registration | Not yet done | Blocking SBS10523 | Saeed (Day 1 action) |

**DSPT deadline is 30 June 2026. SBS10523 submission deadline is 23 June 2026. Both are time-critical.**

---

## WHAT AN NHS ASSESSOR WOULD SEE

If an NHS framework assessor or DTAC reviewer audited this project, they should be able to find:

1. **Clear governance documentation** — this file, CLAUDE.md, AGENT_TEAM_CHARTER.md
2. **Audit trail** — CHANGELOG.md for all changes; session logs in `docs/sessions/`
3. **Clinical safety split** — evidence that LLM output never sets clinical or identity fields
4. **GDPR controls** — 90-day purge script, audit log, no patient data in git
5. **Incident records** — `docs/incidents/` with root cause and rule changes
6. **Approval records** — session logs showing Saeed's explicit approvals
7. **Test evidence** — pytest and Playwright results showing code is tested
8. **Compliance tracker** — current status of all obligations (table above)

This documentation is the procurement story. Build it properly and it becomes a competitive advantage.

---

## INCIDENT MANAGEMENT

### When something goes wrong:
1. Stop the affected process immediately
2. Security Agent assesses scope within 15 minutes
3. Lead Agent notifies Saeed via WhatsApp (plain English, /caveman format):
   - What happened
   - What we stopped or contained
   - What we do not yet know
   - What we are doing next
4. Root cause written to `docs/incidents/YYYY-MM-DD-<title>.md`
5. Governance rule updated in CLAUDE.md to prevent recurrence
6. Saeed signs off the incident report before file is closed

### Severity levels:
- **Critical:** Patient data exposure, production breach, auth bypass, data loss → Stop immediately, notify Saeed within 15 minutes
- **High:** Production down, failed deployment, test suite failure → Notify Saeed in same session
- **Medium:** Bug detected, minor data issue, configuration error → Fix via bug autonomy protocol, notify in daily briefing
- **Low:** Documentation gap, minor UX issue → Log and address in next sprint

---

## SESSION GOVERNANCE

### Every session must:
1. Start with `/superpowers` and `/caveman` invocations
2. Read CLAUDE.md, PROJECT_MEMORY.md, and recent session logs
3. Produce a session start report in /caveman format and wait for Saeed's go-ahead
4. End with: session summary written, PROJECT_MEMORY.md updated, commit pushed, Saeed notified

### Saeed's go-ahead is required before any work begins in a session.
The session start report is not an invitation to start — it is a briefing. Work begins only after Saeed confirms in chat.

---

## GOVERNANCE REVIEW

This framework is reviewed and updated:
- When a new incident occurs (rule updated immediately)
- When a new compliance obligation is identified
- When Saeed requests a change
- At the start of each new pilot practice onboarding

Version history is maintained via git commit history on this file.

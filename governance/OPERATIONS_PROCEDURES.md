# Operations Procedures Manual
**Version:** 2.0
**Purpose:** Day-to-day operational procedures for the 4-agent team — governance, approvals, testing, and deployment
**Owner:** ControlTower
**Last Updated:** 2026-05-23
**Supersedes:** Version 1.0 (2026-05-22) — 9-agent structure

---

## Table of Contents
1. [Team Structure](#team-structure)
2. [Weekly Operations Cycle](#weekly-operations-cycle)
3. [Approval Workflow — Full Procedure](#approval-workflow--full-procedure)
4. [Approval Pack Template](#approval-pack-template)
5. [Escalation Procedures](#escalation-procedures)
6. [Communication Templates](#communication-templates)
7. [Quality Assurance Checkpoints](#quality-assurance-checkpoints)
8. [Emergency & Incident Procedures](#emergency--incident-procedures)

---

## Team Structure

### Agents (4)

| Agent | Title | Primary Responsibility |
|-------|-------|----------------------|
| **TechLead** | Chief Architect | Application source code, UX/UI design, Technical E2E Testing |
| **ControlTower** | Chief Operations Officer | Team coordination, Operational E2E Testing, Approval Pack creation |
| **DevOps** | Infrastructure & Deployment | Infrastructure scripts/config, Deployment E2E Testing, Production deployment |
| **GuardRail** | Chief Compliance Officer | Independent safety & compliance gate — mandatory review of every approval pack |

### Decision Authority

| Person/Agent | Authority |
|-------------|-----------|
| **Saeed** | Executive — final approval on all deployments. Not an agent. |
| **GuardRail** | Can reject any approval pack before it reaches Saeed. Cannot be overruled by other agents. |
| **ControlTower** | Creates approval packs. Coordinates team. Cannot create pack until all 3 tests pass. |
| **TechLead** | Technical decisions on code and UX/UI. |
| **DevOps** | Infrastructure decisions and production execution. |

### Deployment Target
**Churchtown Medical Centre** — on-premises server. All production deployments executed by DevOps after executive approval from Saeed.

---

## Weekly Operations Cycle

### Monday — Sprint Planning (10:00 AM, 30 min)

**Participants:** ControlTower leads, all agents attend, Saeed optional

**Agenda:**
1. Review last week's completion status (5 min)
2. Identify blockers from previous work (5 min)
3. Assign tasks for this week (15 min)
4. Confirm priorities and dependencies (5 min)

**ControlTower Pre-Meeting Checklist (30 min before):**
- [ ] Review `governance/CHANGE_LOG.md` for last week's completed approvals
- [ ] Check which tasks are blocked or pending
- [ ] Update task assignments
- [ ] Identify any agents needing prep time

**Sprint Planning Summary Template (ControlTower posts after meeting):**

```
SPRINT PLANNING SUMMARY — Week [N]
Date: [Monday date]

COMPLETED LAST WEEK:
  ✅ [Task description] — [Agent], approved [date], deployed [date]
  ✅ [Task description] — [Agent], approved [date], deployed [date]

BLOCKED / IN PROGRESS:
  ⏳ [Task] — waiting for [dependency], estimated [date]
  ⚠️ [Task] — test failure, investigating

THIS WEEK'S ASSIGNMENTS:
  → TechLead:     [Task — deliverable by Friday]
  → ControlTower: [Coordination + any specific task]
  → DevOps:       [Infrastructure task — ready for review Tuesday]
  → GuardRail:    [Any pending reviews]

FLAGGED ISSUES:
  🚨 [Issue]: [description], needs [Saeed decision / agent action]

NEXT MILESTONE:
  [e.g., Sprint 1 complete by 2026-05-31 if all tasks on track]

Prepared by: ControlTower | [timestamp]
```

---

### Tuesday–Thursday — Normal Work Cycle

**Agent Working Day:**
```
09:00 — Check CHANGE_LOG.md for context
09:15 — Work on assigned task in sandbox/code/ or devops/
10:00 — Checkpoint: On track? If blocked → notify ControlTower immediately
14:00 — Milestone complete → notify ControlTower: "Ready for E2E testing phase"
14:30 — E2E testing begins (all three phases, see Approval Workflow)
16:00 — Approval pack created (if all tests pass) → sent to GuardRail
```

**ControlTower Daily Checklist:**
- [ ] Check agent blockers by 10:00 AM
- [ ] Monitor E2E test progress
- [ ] Confirm all 3 test phases complete before creating any approval pack
- [ ] Ensure GuardRail review initiated on every pack
- [ ] Flag schedule risks to Saeed

---

### Friday — Weekly Status & Retrospective

**Friday 14:00 — Progress Check-In (30 min), led by ControlTower**

**Weekly Progress Report Template:**

```
═══════════════════════════════════════════════════════════
WEEKLY PROGRESS REPORT — Week [N]
Date: [Friday date]
Prepared by: ControlTower
═══════════════════════════════════════════════════════════

SPRINT PROGRESS:
  Overall: [X%] complete (target: [Y%] for on-track)
  Tasks complete this week: [N]
  Tasks in progress: [N]
  Tasks blocked: [N]

COMPLETED THIS WEEK:
  ✅ [Approval ID] — [Agent], [description]
     Tested by: TechLead ✅ | ControlTower ✅ | DevOps ✅
     GuardRail: ✅ Approved | Saeed: ✅ Approved
     Deployed: [date/time]

IN PROGRESS:
  🔄 [Task] — [Agent], ~[X]% complete
     Next milestone: [target date]

BLOCKED / AT RISK:
  ⚠️ [Task] — BLOCKED by [dependency]
     Mitigation: [action]

METRICS:
  E2E test pass rate: [%]
  Approval turnaround (target <24h): [avg]
  Production incidents: [N]

NEXT WEEK PRIORITIES:
  1. [Task]
  2. [Task]
  3. [Task]

SAEED DECISION REQUIRED:
  ☐ [Issue] — options: A) [option] B) [option]
═══════════════════════════════════════════════════════════
```

**Friday 14:30 — Retrospective (30 min)**

Questions:
1. What went well this week?
2. What should we improve?
3. Any process blockers?
4. Team sentiment: How clear were priorities? How unblocked did you feel? (1–5)

Output: Lessons documented. Process improvement recommendations to Saeed.

---

## Approval Workflow — Full Procedure

### CRITICAL RULE
**ControlTower MUST NOT create an approval pack until all three E2E testing phases have returned PASS. No exceptions. No bypasses.**

```
TechLead:      Technical E2E Testing    → PASS / FAIL
ControlTower:  Operational E2E Testing  → PASS / FAIL
DevOps:        Deployment E2E Testing   → PASS / FAIL
                     ↓ ALL THREE must be PASS
ControlTower:  Creates Approval Pack
                     ↓
GuardRail:     Mandatory Safety Review  → Approve / Reject
                     ↓ Approve only
Saeed:         Executive Decision       → Approve / Reject / Request Changes
                     ↓ Approve only
DevOps:        Deploy to Production (Churchtown Medical Centre)
```

---

### PHASE 1 — TechLead: Technical E2E Testing

**Trigger:** TechLead completes development work.

**Test Areas:**

| Area | What is Verified |
|------|-----------------|
| Code paths | All critical branches execute correctly |
| Data flows | Data moves correctly between UI → API → DB |
| Performance | Response times within acceptable thresholds |
| Error handling | Exceptions caught, logged, surfaced correctly |
| Regression | Existing features not broken by new changes |

**Test Result Report** saved to: `sandbox/audit/test_results/techlead_<YYYYMMDD>.md`

**Template:**
```
TECHLEAD — TECHNICAL E2E TEST REPORT
──────────────────────────────────────
Date: [timestamp]
Task: [Task ID / description]
Files tested: [list]

Code paths:    ✅ PASS / ❌ FAIL — [detail]
Data flows:    ✅ PASS / ❌ FAIL — [detail]
Performance:   ✅ PASS / ❌ FAIL — [detail]
Error handling:✅ PASS / ❌ FAIL — [detail]
Regression:    ✅ PASS / ❌ FAIL — [detail]

OVERALL VERDICT: ✅ PASS / ❌ FAIL

Notes: [Any observations]
Signed: TechLead | [timestamp]
```

**If FAIL:** TechLead fixes the issue and reruns. Does not notify ControlTower until PASS.

---

### PHASE 2 — ControlTower: Operational E2E Testing

**Trigger:** TechLead reports PASS.

**Test Areas:**

| Area | What is Verified |
|------|-----------------|
| Workflow validation | End-to-end user journeys complete without errors |
| User experience | UI behaves correctly for all user roles |
| Business logic | Rules and constraints enforced as designed |
| Integration points | Services communicate correctly |
| Data integrity | Records created, updated, deleted correctly |

**Test Result Report** saved to: `sandbox/audit/test_results/controltower_<YYYYMMDD>.md`

**Template:**
```
CONTROLTOWER — OPERATIONAL E2E TEST REPORT
────────────────────────────────────────────
Date: [timestamp]
Task: [Task ID / description]
TechLead result: ✅ PASS (confirmed)

Workflow validation: ✅ PASS / ❌ FAIL — [detail]
User experience:     ✅ PASS / ❌ FAIL — [detail]
Business logic:      ✅ PASS / ❌ FAIL — [detail]
Integration points:  ✅ PASS / ❌ FAIL — [detail]
Data integrity:      ✅ PASS / ❌ FAIL — [detail]

OVERALL VERDICT: ✅ PASS / ❌ FAIL

Notes: [Any observations]
Signed: ControlTower | [timestamp]
```

**If FAIL:** ControlTower notifies TechLead. Returns to Phase 1.

---

### PHASE 3 — DevOps: Deployment E2E Testing

**Trigger:** ControlTower reports PASS.

**Test Areas:**

| Area | What is Verified |
|------|-----------------|
| Infrastructure readiness | Server resources, dependencies, disk space OK |
| Configuration validation | Config files correct, secrets in place |
| Migration dry-run | DB migration scripts run cleanly on a copy |
| Rollback preparation | Rollback script written, tested, confirmed ready |
| Smoke test readiness | Post-deployment validation plan confirmed |

**Test Result Report** saved to: `sandbox/audit/test_results/devops_<YYYYMMDD>.md`

**Template:**
```
DEVOPS — DEPLOYMENT E2E TEST REPORT
──────────────────────────────────────
Date: [timestamp]
Task: [Task ID / description]
TechLead result:      ✅ PASS (confirmed)
ControlTower result:  ✅ PASS (confirmed)

Infrastructure readiness: ✅ PASS / ❌ FAIL — [detail]
Configuration validation: ✅ PASS / ❌ FAIL — [detail]
Migration dry-run:        ✅ PASS / ❌ FAIL — [detail]
Rollback preparation:     ✅ PASS / ❌ FAIL — [detail]
Smoke test readiness:     ✅ PASS / ❌ FAIL — [detail]

Rollback script location: devops/scripts/rollback_<version>_<date>.sh
Rollback tested: ✅ YES

OVERALL VERDICT: ✅ PASS / ❌ FAIL

Notes: [Any observations]
Signed: DevOps | [timestamp]
```

**If FAIL:** DevOps resolves infrastructure issues and reruns. Does not notify ControlTower until PASS.

---

### PHASE 4 — ControlTower: Creates Approval Pack

**Trigger:** All three phases return PASS.

**Checklist before creating pack:**
- [ ] TechLead Technical E2E: ✅ PASS with timestamp
- [ ] ControlTower Operational E2E: ✅ PASS with timestamp
- [ ] DevOps Deployment E2E: ✅ PASS with timestamp
- [ ] All three test reports saved to `sandbox/audit/test_results/`
- [ ] Code diffs / config changes / schema changes documented
- [ ] Rollback plan confirmed ready by DevOps

**Approval Pack ID format:** `APPROVAL_<YYYYMMDD>_<SHORT_TITLE>_v<N>`
Example: `APPROVAL_20260525_PATHWAY_REGISTRY_v1`

**Saved to:** `sandbox/audit/approval_packs/APPROVAL_<ID>.md`

**Sent to:** GuardRail for mandatory safety review.

---

### PHASE 5 — GuardRail: Mandatory Safety Review

**Trigger:** ControlTower sends completed approval pack.

**GuardRail is mandatory for every deployment. Not optional. Not conditional on sensitivity.**

**Review Checklist:**

| Check | Criterion |
|-------|-----------|
| Test completeness | All 3 phases present with PASS verdicts + timestamps |
| Audit trail integrity | Complete, consistent, tamper-evident |
| Patient data safety | No risk of data loss, corruption, or unauthorised access |
| Regulatory compliance | Changes comply with applicable healthcare/data regulations |
| Rollback readiness | Rollback script documented, tested, and ready |
| Risk assessment | Risks identified, mitigated, residual risk acceptable |
| Clinical decision boundary | System does NOT make clinical decisions |
| Audit logging | Audit logging present and correct |

**GuardRail Verdict Template:**

```
GUARDRAIL — SAFETY REVIEW
──────────────────────────
Approval Pack: [ID]
Date reviewed: [timestamp]

Test completeness:       ✅ / ❌
Audit trail integrity:   ✅ / ❌
Patient data safety:     ✅ / ❌
Regulatory compliance:   ✅ / ❌
Rollback readiness:      ✅ / ❌
Risk assessment:         ✅ / ❌
Clinical boundary:       ✅ / ❌
Audit logging:           ✅ / ❌

VERDICT: ✅ APPROVED / ❌ REJECTED

[If APPROVED]:
  "GuardRail: ✅ APPROVED — forwarding to Saeed for executive decision."

[If REJECTED]:
  "GuardRail: ❌ REJECTED — [specific reason, not vague]"
  "Required remediation: [specific fix]"
  "Next: [Agent] to revise and resubmit."

Signed: GuardRail | [timestamp]
```

**If REJECTED:** Pack returned to ControlTower. Deficiencies corrected. Full approval workflow restarts from Phase 1 if code was changed.

**GuardRail verdict saved to:** `sandbox/audit/approval_packs/GUARDRAIL_<ID>.md`

---

### PHASE 6 — Saeed: Executive Decision

**Trigger:** GuardRail returns ✅ APPROVED verdict.

**Saeed's review process:**
1. Read "WHAT CHANGED" (2 min)
2. Read "WHY" — tied to which business goal (1 min)
3. Review risk level — does it match the change? (1 min)
4. Confirm rollback is ready (30 sec)
5. Decide (30 sec)

**Decision format:**

```
approved
```
```
approved, but [conditions — agent must address before DevOps deploys]
```
```
rejected: [reason]
```

**If approved:** DevOps proceeds to Phase 7.
**If conditions:** Agent addresses conditions, ControlTower updates pack, GuardRail re-reviews conditions, Saeed re-approves.
**If rejected:** Work returns to relevant agent. Full workflow from Phase 1 if code changes required.

---

### PHASE 7 — DevOps: Deploy to Production

**Trigger:** Saeed executive approval received.

**Deployment Steps (Churchtown Medical Centre):**

```
DEPLOYMENT EXECUTION
─────────────────────
Approval: [ID] — Saeed approved [timestamp]

Step 1 — Code deployment
  Action: Move from sandbox/code/ → production server
  Result: ✅ COMPLETE / ❌ FAILED

Step 2 — Database migrations
  Action: Run migration scripts on production SQLite
  Result: ✅ COMPLETE / ❌ FAILED

Step 3 — Configuration deployment
  Action: Update config files on production
  Result: ✅ COMPLETE / ❌ FAILED

Step 4 — Service restart
  Action: Restart all services
  Result: ✅ COMPLETE / ❌ FAILED

Step 5 — Smoke tests
  Action: Quick validation in production
  Result: ✅ PASS / ❌ FAIL

  [If smoke tests FAIL → execute rollback immediately, notify Saeed]

Deployment status: ✅ SUCCESS / ❌ ROLLED BACK
Completed: [timestamp]
Signed: DevOps
```

**Deployment log saved to:** `sandbox/audit/approval_packs/DEPLOYMENT_LOG_<ID>.md`
**Rollback log (if applicable):** `sandbox/audit/approval_packs/ROLLBACK_LOG_<ID>.md`

---

### PHASE 8 — ControlTower: Logs to CHANGE_LOG

**Trigger:** DevOps confirms deployment complete (or rolled back).

**Change Log Entry Format** (`governance/CHANGE_LOG.md`):

```markdown
## [Date]

### [APPROVAL_ID] — [Short Title]
**Status:** ✅ DEPLOYED / ❌ ROLLED BACK
**Tested by:** TechLead ✅ | ControlTower ✅ | DevOps ✅
**GuardRail:** ✅ Approved [timestamp]
**Saeed:** ✅ Approved [timestamp]
**Deployed:** [timestamp]
**What changed:** [Files created/modified]
**Why:** [Business reason, tied to task]
**Risk:** 🟢 Low / 🟡 Medium / 🔴 High
**Rollback:** [Procedure + script location]
**Notes:** [Any issues or observations]
```

---

## Approval Pack Template

Saved to `sandbox/audit/approval_packs/APPROVAL_<ID>.md`

```markdown
═══════════════════════════════════════════════════════════════
APPROVAL PACK
═══════════════════════════════════════════════════════════════

ID: [APPROVAL_YYYYMMDD_SHORT_TITLE_vN]
Created: [timestamp]
Created by: ControlTower
Status: Pending GuardRail Review → Pending Saeed Approval

───────────────────────────────────────────────────────────────
WHAT CHANGED
───────────────────────────────────────────────────────────────
Files created/modified:
  - [file path]: [what changed]
  - [file path]: [what changed]

Database schema changes: [Yes / No — describe if yes]
Configuration changes:   [Yes / No — describe if yes]
Infrastructure changes:  [Yes / No — describe if yes]

───────────────────────────────────────────────────────────────
WHY
───────────────────────────────────────────────────────────────
Business reason: [Tied to which task / goal]
[1–2 sentence explanation]

───────────────────────────────────────────────────────────────
RISK LEVEL
───────────────────────────────────────────────────────────────
🟢 Low / 🟡 Medium / 🔴 High — [explanation]

Sensitive areas:
  ☐ Encryption / secrets
  ☐ Patient data handling
  ☐ Authentication logic
  ☐ Database schema
  ☐ Audit logging
  ☐ Clinical pathway logic

───────────────────────────────────────────────────────────────
E2E TESTING RESULTS (ALL THREE REQUIRED)
───────────────────────────────────────────────────────────────
TechLead — Technical E2E:
  Verdict: ✅ PASS
  Report:  sandbox/audit/test_results/techlead_<date>.md
  Signed:  TechLead | [timestamp]

ControlTower — Operational E2E:
  Verdict: ✅ PASS
  Report:  sandbox/audit/test_results/controltower_<date>.md
  Signed:  ControlTower | [timestamp]

DevOps — Deployment E2E:
  Verdict: ✅ PASS
  Report:  sandbox/audit/test_results/devops_<date>.md
  Signed:  DevOps | [timestamp]

───────────────────────────────────────────────────────────────
ROLLBACK PLAN
───────────────────────────────────────────────────────────────
Script: devops/scripts/rollback_<version>_<date>.sh
Tested: ✅ YES (confirmed by DevOps)

Steps:
  1. [step]
  2. [step]
Estimated recovery time: [X minutes]

───────────────────────────────────────────────────────────────
GUARDRAIL REVIEW
───────────────────────────────────────────────────────────────
Status: ⏳ Pending / ✅ Approved / ❌ Rejected
Review file: sandbox/audit/approval_packs/GUARDRAIL_<ID>.md
Signed: GuardRail | [timestamp]

───────────────────────────────────────────────────────────────
SAEED DECISION
───────────────────────────────────────────────────────────────
[Response: approved / approved, but [conditions] / rejected: [reason]]
Signed: Saeed | [timestamp]

───────────────────────────────────────────────────────────────
DEPLOYMENT RECORD
───────────────────────────────────────────────────────────────
Execution log: sandbox/audit/approval_packs/DEPLOYMENT_LOG_<ID>.md
Status: ⏳ Pending / ✅ Deployed / ❌ Rolled Back
Completed: [timestamp]
═══════════════════════════════════════════════════════════════
```

---

## Escalation Procedures

### Escalation 1 — E2E Test Failure

**Trigger:** Any of the three E2E testing phases returns FAIL.

```
[Agent who failed] → fixes issue → reruns own tests
                  → notifies ControlTower when PASS
```

If the issue requires another agent's involvement:
```
[Agent] → ControlTower → [Other agent if needed] → Saeed (if blocker)
```

**Template:**
```
🚨 E2E TEST FAILURE
Agent: [TechLead / ControlTower / DevOps]
Phase: [Technical / Operational / Deployment]
Failed area: [which test area]
Failure detail: [description]
Impact: Blocks approval pack creation

Action taken: [investigating / fixing]
Timeline: [when fix expected]
Escalation: [if not resolved by X time → notify Saeed]
```

---

### Escalation 2 — GuardRail Rejection

**Trigger:** GuardRail returns ❌ REJECTED verdict.

```
GuardRail → ControlTower → [Relevant agent]
                         → Saeed (notification only, not for override)
```

No agent can override GuardRail. If Saeed believes the rejection is incorrect, Saeed discusses with GuardRail directly.

**Template:**
```
❌ GUARDRAIL REJECTION
Approval Pack: [ID]
Rejected by: GuardRail | [timestamp]

Reason: [Specific — not vague]
Required remediation: [Specific fix]

Next steps:
  [Agent] to address: [specific action]
  ControlTower to update pack and resubmit to GuardRail
  If code changed: E2E testing must restart from Phase 1
```

---

### Escalation 3 — Blocked Task (Dependency Unmet)

**Trigger:** Agent cannot proceed because a dependency is unresolved.

```
[Agent] → ControlTower → Saeed (decision required)
```

**Template:**
```
⏳ BLOCKED TASK — SAEED DECISION REQUIRED

Task: [description]
Agent: [who is blocked]
Blocked by: [unmet dependency]
Impact: [delay estimate]

Options:
  A) Prioritise dependency → unblock by [date]
  B) Workaround: [describe] → proceed in parallel
  C) Defer to next sprint → new target [date]

ControlTower recommendation: [A / B / C + brief reason]
Waiting for: Saeed decision
```

---

### Escalation 4 — Production Incident

**Trigger:** Problem discovered in production after deployment.

```
[Discoverer] → Saeed + GuardRail (immediately, same message)
```

**Immediate notification template:**
```
🚨 PRODUCTION ISSUE — [Churchtown Medical Centre]

Issue: [brief description]
Discovered by: [agent / system]
Time: [timestamp]
Impact: [affected services / users]
Related deployment: [Approval ID that likely caused this]

Initial hypothesis: [root cause guess]

Saeed: Standing by for your decision.
```

**Saeed's response options:**
- `"Rollback [approval ID]"` → DevOps executes rollback immediately
- `"Provide hotfix"` → TechLead works on fix, full workflow applies
- `"Disable feature, investigate later"` → DevOps disables, team investigates

**Post-Incident (hours 1–24):** GuardRail leads investigation.
- Review: approval pack, test results, change log entry
- Identify: which gate missed this, and why
- Document: `sandbox/audit/approval_packs/INCIDENT_<date>_<description>.md`
- Report to Saeed: root cause, remediation, process change recommendation

---

## Communication Templates

### Agent Quality Gate (Before Notifying ControlTower That Work Is Ready)

```
AGENT QUALITY GATE — SELF-CHECK
────────────────────────────────
Before I say "ready for E2E testing":

Code / Config Quality:
  ☐ Syntax validated (JSON, SQL, Python, PowerShell)
  ☐ No hardcoded secrets
  ☐ Naming conventions followed (REPOSITORY_STRUCTURE.md)
  ☐ All files in sandbox/ (not in production/)

Documentation Quality:
  ☐ Change clearly explained (what + why)
  ☐ Tied to task ID / business goal
  ☐ Dependencies listed
  ☐ Risk level assessed
  ☐ Rollback plan drafted

Safety:
  ☐ No clinical decisions by system
  ☐ Audit logging present where required
  ☐ Patient data properly scoped

Ready:
  ☐ No outstanding questions
  ☐ Can explain this in 2–3 minutes
```

**Agent notification to ControlTower:**
```
READY FOR E2E TESTING
──────────────────────
Agent: [TechLead / DevOps]
Task: [Task ID — description]
Files changed: [list]
Risk: 🟢 Low / 🟡 Medium / 🔴 High
Sensitive areas: [None / describe]

Summary:
  What: [1–2 sentences]
  Why: [tied to which goal/task]
  Rollback: [brief description]

Status: Ready for TechLead Technical E2E → then full workflow
```

### Saeed Decision Format

```
approved
```
```
approved, but [conditions]
```
```
rejected: [reason]
```

---

## Quality Assurance Checkpoints

### Before Approval Pack Creation (ControlTower Gate)

```
APPROVAL PACK GATE — CONTROLTOWER
───────────────────────────────────

E2E Testing Complete:
  ☐ TechLead Technical E2E: ✅ PASS + timestamp + report saved
  ☐ ControlTower Operational E2E: ✅ PASS + timestamp + report saved
  ☐ DevOps Deployment E2E: ✅ PASS + timestamp + report saved

Content Quality:
  ☐ "WHAT CHANGED" section clear and complete
  ☐ "WHY" tied to specific task / goal
  ☐ Risk level matches actual changes
  ☐ Rollback confirmed tested and ready by DevOps
  ☐ All file paths correct (sandbox/ not production/)
  ☐ No hardcoded secrets

If any ☐ unchecked: DO NOT CREATE PACK — resolve first.
```

### Before Production Deployment (DevOps Gate)

```
DEPLOYMENT GATE — DEVOPS
──────────────────────────
Approval validation:
  ☐ Approval ID matches current work
  ☐ GuardRail: ✅ APPROVED confirmed
  ☐ Saeed: ✅ APPROVED confirmed
  ☐ No outstanding conditions

Deployment readiness:
  ☐ Rollback script ready and tested
  ☐ Smoke test plan confirmed
  ☐ Server resources checked
  ☐ No secrets being moved in plaintext

If any ☐ unchecked: STOP — contact ControlTower before proceeding.
```

### Post-Deployment (DevOps + ControlTower)

```
POST-DEPLOYMENT CHECK
──────────────────────
DevOps:
  ☐ All smoke tests passed
  ☐ Services running normally
  ☐ Deployment log saved to sandbox/audit/

ControlTower:
  ☐ CHANGE_LOG.md updated with full entry
  ☐ Saeed notified of successful deployment
  ☐ Approval pack status updated to DEPLOYED
```

---

## Emergency & Incident Procedures

### Production Issue — Minutes 0–5

```
IMMEDIATE RESPONSE
───────────────────
1. Discoverer posts immediately to Saeed + GuardRail:
   🚨 PRODUCTION ISSUE — [description, impact, related approval]

2. Saeed assesses:
   🔴 Critical (service down)  → "Rollback [ID]" — immediate
   🟡 Major (significant)      → "Rollback [ID]" or "Provide hotfix"
   🟢 Minor (limited scope)    → "Investigate, plan fix"

3. DevOps executes Saeed's decision.
   All other agents: stand by.

4. Rollback log saved to: sandbox/audit/approval_packs/ROLLBACK_LOG_<ID>.md
```

### Post-Incident Review — Hours 1–24

GuardRail leads. Document in `sandbox/audit/approval_packs/INCIDENT_<date>.md`:

- What happened
- Root cause
- Which gate missed it and why
- Recommended process change

Team meeting within 48 hours. Saeed approves any process changes.

---

**Maintained by:** ControlTower
**Version:** 2.0
**Last Updated:** 2026-05-23
**Next Review:** After first deployment or sprint completion

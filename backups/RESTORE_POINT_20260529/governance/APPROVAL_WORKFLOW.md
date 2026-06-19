# Approval Workflow — How Changes Get Approved & Executed
**For:** Saeed (Human Controller) and Agent Team  
**Purpose:** Clear, transparent process for proposing, approving, and executing changes  
**Scope:** All code changes, schema migrations, config changes, pathway logic, security updates

---

## The Flow (Simplified)

```
AGENT PROPOSES
     │
     ▼
GUARDRAIL REVIEWS (if sensitive)
     │
     ├─ Block? → Rejected & logged
     │
     └─ OK? ─→ Escalate to SAEED
                     │
                     ▼
              SAEED REVIEWS
                     │
                  Approved?
                  ├─ YES → EXECUTE → Report results
                  └─ NO → Rejected & logged
```

---

## Detailed Steps

### STEP 1: Agent Proposes

**Who:** Any specialist agent (PathFinder, DataVault, PipeWorks, etc.)

**How:**
1. Agent completes their work in sandbox (code, schema, config, design doc)
2. Agent summarises: What changed, why, risk level
3. Agent notifies ControlTower: "Ready for approval pack"

**Example (from PathFinder):**
```
PathFinder to ControlTower: 
"I've completed PATHWAY_REGISTRY.md documenting all 8 pathways 
with required fields, routing rules, and validation logic.
File: agents/PathFinder/PATHWAY_REGISTRY.md
Risk level: Low (design doc, no code)
Blocking tasks: PE-01 (pipeline config), QA-03 (test cases)
Ready for review?"
```

---

### STEP 2: ControlTower Creates Approval Pack

**Who:** ControlTower agent (orchestrator)

**What:** Wraps agent's work into a proposal document for you

**Format:**

```markdown
# APPROVAL PACK
[DATE] — [AGENT NAME] — [SHORT TITLE]

## WHAT CHANGED
- [File 1]: [what was added/modified]
- [File 2]: [what was added/modified]
...

## WHY (Tied to Production Spec)
[2-3 sentences explaining the business reason]
References: PE-01, QA-03 (example task IDs)

## BLOCKING THIS WORK
[If "no", just say "None"]
Lists any dependencies this blocks

## BLOCKED BY THIS WORK
[If agent was waiting on something, list it]

## TOUCHES SENSITIVE AREAS?
☐ Encryption keys
☐ HMAC secrets
☐ Production database
☐ Patient data directories
☐ Authentication logic
☐ Pathway activation
☐ Model configuration
☐ Other: [specify]

[If any checked: GuardRail MUST review before Saeed sees this]

## RISK LEVEL
🟢 Low     — Design doc, no code change, fully reversible
🟡 Medium  — Code change, reversible, low blast radius
🔴 High    — Schema change, encryption config, or patient-affecting

## TESTING
[If code change]:
  Test results: [PASS / FAIL / PENDING]
  Coverage: [% if applicable]
  Regression: [Any known breakage?]
  
[If design doc or config]:
  Reviewed for: [Safety, correctness, clarity]
  Ready to implement: [YES / NO]

## ROLLBACK PLAN
[How to undo this if it breaks]

Example:
  - Delete file X from production
  - Restore DB backup from [date]
  - Revert config to [previous version]

## DECISION REQUIRED
Your choice:

☐ **APPROVED** 
   → Agent executes immediately
   → You'll see results report within [X hours]

☐ **APPROVED WITH CONDITIONS**
   → Specify conditions:
   → Agent waits for clarification

☐ **REJECTED**
   → Agent returns to sandbox
   → Reason: [brief explanation]

---
**Approval Pack ID:** [Date]_[Agent]_[Title]_v1  
**Created by:** ControlTower  
**GuardRail review:** [If sensitive: "Reviewed & OK" or "Blocked: reason"]  
**Status:** Pending your decision
```

---

### STEP 3: GuardRail Review (Conditional)

**Trigger:** If approval pack touches ANY sensitive area (encryption, auth, patient data, pathways)

**What GuardRail Does:**

1. **Read** the approval pack
2. **Check** against safety gate:
   ```
   ☐ Does this allow clinical decisions? NO ✓
   ☐ Does this expose patient data? NO ✓
   ☐ Does this override safety rules? NO ✓
   ☐ Does this have audit logging? YES ✓
   ☐ Is the pathway language admin-task only? YES ✓
   ```
3. **Decide:**
   - ✓ **OK, forward to Saeed** — GuardRail endorsement note attached
   - ✗ **BLOCK** — detailed reason provided

**GuardRail Blocking Example:**
```
APPROVAL PACK: [Date]_PipeWorks_PATHWAY_LOGIC_UPDATE_v1

GuardRail Review:
  ❌ BLOCKED — Safety gate failure

Reason:
  The proposed sick_note pathway includes a field "clinical_urgency" 
  with values [low/medium/high]. This is a CLINICAL DECISION.
  
  Per charter: "System must not make clinical decisions."
  
  Fix: Remove clinical_urgency field. Replace with:
       "recommended_priority: [routine/urgent/review_needed]"
       where all values map to ADMIN TASKS, not clinical severity.
       
  Contact: PipeWorks should revise and resubmit.

Status: BLOCKED until revised
```

**GuardRail Endorsement Example:**
```
GuardRail Review:
  ✅ APPROVED (Safety perspective)

  - Pathway logic: Creates admin tasks only
  - Handoff wording: "Forward to reception" (not clinical)
  - Audit logging: Present
  - Patient data: Properly scoped
  
  Safe to proceed.
```

---

### STEP 4: Saeed Reviews & Approves

**Who:** You (Saeed)

**What You See:**
- ControlTower approval pack (formatted nicely)
- If sensitive: GuardRail endorsement or block notice
- Test results (if applicable)
- Rollback plan
- Clear "APPROVED / REJECTED / CONDITIONS?" options

**What You Do:**

Pick one:

**Option A: APPROVED**
```
You type in chat: "approved"

Then:
- ControlTower moves pack to: agents/ControlTower/approval_packs/approved/
- Agent executes the change
- Agent reports results in chat
- Change logged in CHANGE_LOG.md
```

**Option B: APPROVED WITH CONDITIONS**
```
You type: "approved with conditions: [specify]"

Example:
  "approved, but change HMAC verification to reject 
   invalid signatures before writing to queue (not after)"

Then:
- Agent revises proposal
- Resubmits to ControlTower
- Back to Step 2
```

**Option C: REJECTED**
```
You type: "rejected: [reason]"

Example:
  "rejected: the test suite shows 3 failures on medication_query pathway. 
   PipeWorks should investigate before resubmitting."

Then:
- ControlTower moves pack to: approval_packs/rejected/
- Reason logged
- Agent returns to sandbox to fix
```

---

### STEP 5: Agent Executes (If Approved)

**Trigger:** You respond "approved"

**Agent Does:**

1. **Confirm:** "Executing [approval pack ID]..."
2. **Execute:** Make the change (modify production file, run migration, deploy config)
3. **Verify:** Run quick sanity checks
4. **Report:** Post results in chat

**Example (PipeWorks executing config file):**
```
ControlTower: "Approval APPROVED by Saeed. PipeWorks, proceed."

PipeWorks: "Executing 20260525_PipeWorks_CONFIG_FILES_v1...

  ✓ Copied: config/model_settings.json → production
  ✓ Copied: config/pathways.json → production
  ✓ Copied: config/routing_rules.json → production
  ✓ Copied: config/model_monitoring.json → production
  
  Verification:
  ✓ All JSON files valid (no syntax errors)
  ✓ All required keys present
  ✓ process_queue.ps1 can load these files
  ✓ Pipeline tested with new configs (soft restart)
  
  Status: EXECUTED (2026-05-25 14:32 UTC)
  
  Next: TestBench should run regression to confirm no pipeline breakage."
```

---

### STEP 6: Logging & Closeout

**ControlTower Logs Everything:**

In `CHANGE_LOG.md`:
```markdown
## 2026-05-25

### APPROVED & EXECUTED
**Task:** PipeWorks_CONFIG_FILES_v1  
**What:** Created 4 missing config files (model_settings, pathways, routing, monitoring)  
**Why:** PE-01 blocker — pipeline needs externalised config  
**Who:** PipeWorks (proposed) → ControlTower (wrapped) → GuardRail (reviewed) → Saeed (approved)  
**When:** Proposed 2026-05-24, Approved 2026-05-25 09:15, Executed 2026-05-25 14:32  
**Files Changed:**
  - config/model_settings.json (NEW)
  - config/pathways.json (NEW)
  - config/routing_rules.json (NEW)
  - config/model_monitoring.json (NEW)
**Risk:** 🟡 Medium (new config files, pipeline depends on them)  
**Rollback:** Delete 4 files, restart pipeline with old hardcoded defaults  
**Test Results:** Regression pass (TestBench runs full suite)  
**Status:** ✅ COMPLETE — Pipeline operational with new config

---

### REJECTED
**Task:** DataVault_SCHEMA_MIGRATION_V1  
**What:** Initial schema migration script (001_initial_schema.sql)  
**Who:** DataVault (proposed) → ControlTower (wrapped) → Saeed (reviewed)  
**When:** Proposed 2026-05-24, Rejected 2026-05-25 15:00  
**Reason:** "Test suite shows 2 failures when running migration against test DB. 
            DataVault should debug before resubmitting."  
**Status:** ❌ REJECTED — Awaiting resubmission

---

### BLOCKED BY GUARDRAIL
**Task:** PipeWorks_PATHWAY_UPDATE_V1  
**What:** Add "urgency_score" field to sick_note pathway  
**Who:** PipeWorks (proposed) → ControlTower (wrapped) → GuardRail (BLOCKED)  
**When:** Proposed 2026-05-24, Blocked 2026-05-24 17:30  
**GuardRail Reason:** "urgency_score is a clinical decision. System not allowed to make these."  
**Action:** PipeWorks revising to use "staff_review_flag: boolean" instead  
**Status:** ⏸ BLOCKED — Awaiting revision
```

---

## Example Scenarios

### Scenario 1: Simple Config File (Low Risk)

```
TIMELINE:

Day 1, 09:00 — PipeWorks completes model_settings.json
Day 1, 10:30 — ControlTower creates approval pack
Day 1, 11:00 — GuardRail reviews: "Not sensitive area, no gate required"
Day 1, 11:05 — Saeed reviews approval pack in chat
Day 1, 11:06 — Saeed: "approved"
Day 1, 11:07 — PipeWorks executes (copies file to production)
Day 1, 11:08 — PipeWorks: "Executed. File copied, no errors."
Day 1, 11:09 — ControlTower logs in CHANGE_LOG.md
Day 1, 11:10 — TestBench queues regression test

Total time: ~1 hour from completion to live
Risk: Low — config file, fully reversible
```

### Scenario 2: Schema Migration (High Risk)

```
TIMELINE:

Day 1, 08:00 — DataVault completes SCHEMA_V1.sql + migrations/001_initial_schema.sql
Day 1, 10:00 — ControlTower creates approval pack
             — ControlTower flags: "Touches production database, GuardRail required"
Day 1, 10:15 — GuardRail reviews: "Audit table present ✓, retention policy present ✓"
Day 1, 10:20 — GuardRail: "Approved (safety perspective)"
Day 1, 10:25 — ControlTower escalates to Saeed with GuardRail endorsement
Day 1, 10:30 — Saeed reviews, wants more info
Day 1, 10:35 — Saeed: "approved with conditions: test this against backup copy 
                        of production DB before running on live"
Day 1, 11:00 — DataVault creates test env, runs migration against test DB copy
Day 1, 11:30 — DataVault: "Test passed. Ready for live migration on your signal."
Day 1, 14:00 — Saeed: "approved for live execution"
Day 1, 14:05 — DataVault: "Executing migration on production DB..."
Day 1, 14:12 — DataVault: "Migration complete. Audit table created, tested."
Day 1, 14:15 — ControlTower logs
Day 1, 15:00 — TestBench runs full regression

Total time: ~7 hours (most due to testing)
Risk: High — schema change, requires careful rollback plan
```

### Scenario 3: Blocked for Safety

```
TIMELINE:

Day 1, 09:00 — PathFinder proposes new "triage_priority" pathway
Day 1, 10:30 — ControlTower creates approval pack
             — ControlTower flags: "New pathway logic, GuardRail required"
Day 1, 10:45 — GuardRail reviews
             — ❌ BLOCKED: "triage_priority field implies clinical decision"
             — "Recommendation: Remove priority field, use 
                  staff_review_required: boolean instead"
Day 1, 11:00 — ControlTower reports to PathFinder: "Blocked by GuardRail"
Day 1, 13:00 — PathFinder revises proposal, removes triage_priority
Day 1, 13:30 — PathFinder resubmits to ControlTower
Day 1, 14:00 — ControlTower escalates revised proposal
Day 1, 14:15 — GuardRail: "Revised version approved ✓"
Day 1, 14:20 — Saeed: "approved"
Day 1, 14:21 — PathFinder: "Executing..."
Day 1, 14:22 — PathFinder: "Done. Pathway registered."

Total time: ~5 hours (blocked then revised)
Risk: Medium — pathway logic change, but safety-gated
```

---

## Approval Pack Checklist

**Before ControlTower wraps work in approval pack, agent confirms:**

- [ ] Work complete and in sandbox
- [ ] All draft files saved and committed
- [ ] No production files modified (only sandbox files)
- [ ] If code: tested locally without errors
- [ ] If schema: syntax-checked
- [ ] If config: JSON/YAML valid, all required keys present
- [ ] Impact assessed (what does this affect?)
- [ ] Risk level identified (low/medium/high)
- [ ] Rollback plan documented (how to undo)
- [ ] Dependencies listed (what does this block/need?)
- [ ] Sensitive areas identified (encryption, auth, patient data, etc.)

---

## Sensitive Areas That Always Require GuardRail Review

| Area | Examples | Why |
|------|----------|-----|
| **Encryption Keys** | `config/security/keys/` | Exposure = complete breach |
| **HMAC Secrets** | `voice_agent_hmac_secret.txt` | Forgery risk |
| **Auth Logic** | `dashboard/app/auth.py`, login endpoints | Access control |
| **Patient Data** | `outputs/handoff_json/`, `queue/processed/` | Privacy risk |
| **Audit Logging** | Changes to `audit_log` table | Compliance |
| **Pathway Logic** | Any new pathway or field | Must not be clinical |
| **Model Config** | Ollama model, prompts, thresholds | Quality & safety |
| **Database** | Schema changes, migrations | Data integrity |

---

## Approval Turnaround Expectations

**You should expect:**
- 🟢 **Low-risk** (config files, docs): 1-2 hours
- 🟡 **Medium-risk** (code changes): 2-6 hours
- 🔴 **High-risk** (schema, auth): 4-24 hours (needs testing)

**Why the variance:**
- You're busy — reviews happen when you can
- High-risk needs pre-execution testing
- GuardRail review adds time if sensitive

**Agents will not rush you.** Better to get approval right than execute wrong.

---

## Your Role in Approval

**Each time you see an approval pack:**

1. **Read** the "WHAT CHANGED" section (2 min)
2. **Understand** the "WHY" (1 min)
3. **Assess risk** — does the risk level match the change? (1 min)
4. **Check rollback** — if this breaks, can it be undone? (1 min)
5. **Decide** — approved / conditions / rejected (30 sec)

**You DON'T need to:**
- ❌ Review every line of code
- ❌ Validate SQL syntax
- ❌ Test code (agents do that)
- ❌ Make technical decisions (agents make recommendations)

**You DO need to:**
- ✓ Understand WHAT changed and WHY
- ✓ Know the risk level
- ✓ Know how to undo it
- ✓ Have final say on go/no-go

---

## Example Approval Pack (Ready to Present to You)

```
═══════════════════════════════════════════════════════════════
APPROVAL PACK #1
═══════════════════════════════════════════════════════════════

DATE: 2026-05-25
AGENT: PipeWorks (Workflow Engineer)
TITLE: Create Missing Config Files (PE-01 blocker)
STATUS: Ready for Saeed approval
GUARDRAIL: ✅ Reviewed, no safety concerns

───────────────────────────────────────────────────────────────
WHAT CHANGED
───────────────────────────────────────────────────────────────
4 new files created:
  1. config/model_settings.json — Ollama config (model name, temperature, timeout)
  2. config/pathways.json — Active pathway registry
  3. config/routing_rules.json — Staff assignment logic per pathway
  4. config/model_monitoring.json — Confidence thresholds, fallback triggers

No existing files modified.

───────────────────────────────────────────────────────────────
WHY (Production Spec Reference)
───────────────────────────────────────────────────────────────
PE-01 blocks production readiness: "Create config/model_settings.json, 
pathways.json, routing_rules.json, model_monitoring.json".

These 4 files externalise hardcoded values from PowerShell scripts, 
enabling easier maintenance and multi-pathway management. Currently, 
model name, active pathways, and routing are hardcoded in process_queue.ps1.

After these files exist, PipeWorks can update process_queue.ps1 to load 
from config (PE-01 complete).

───────────────────────────────────────────────────────────────
BLOCKING / BLOCKED BY
───────────────────────────────────────────────────────────────
Blocking:
  → PE-01 (process_queue.ps1 update)
  → QA-03 (test suite pathway tracing)

Blocked by:
  ← PathFinder (PATHWAY_REGISTRY.md — defines all 8 pathways)
     [PathFinder approved 2026-05-24, so this unblocked]

───────────────────────────────────────────────────────────────
TOUCHES SENSITIVE AREAS?
───────────────────────────────────────────────────────────────
☐ Encryption keys
☐ HMAC secrets
☐ Production database
☐ Patient data directories
☐ Authentication logic
☐ Pathway activation
☐ Model configuration ← YES, but config file (not live override)
☐ Other: none

GuardRail cleared (config externalisation is safe).

───────────────────────────────────────────────────────────────
RISK LEVEL
───────────────────────────────────────────────────────────────
🟡 MEDIUM

Why medium, not low:
  - Pipeline depends on these config files at startup
  - If files have wrong JSON syntax, pipeline crashes at start
  - Process_queue.ps1 hasn't been updated yet to load them
    (this is separate execution, not in this approval pack)

Mitigation:
  - JSON syntax validated before copied to production
  - Config files include defaults (won't break if missing)
  - Rollback is simple (delete files, restart with old hardcoded values)

───────────────────────────────────────────────────────────────
TESTING
───────────────────────────────────────────────────────────────
TestBench validation:
  ✓ JSON syntax validation: PASS
  ✓ All required keys present: PASS
  ✓ Default values reasonable: PASS
  ✓ Config loader test (dummy): PASS
  ✗ Pipeline integration test: PENDING
    (depends on PE-01 execution — process_queue.ps1 update)

Files ready: YES
Safe to execute: YES
Safe to skip integration test: YES (PE-01 will validate integration)

───────────────────────────────────────────────────────────────
ROLLBACK PLAN
───────────────────────────────────────────────────────────────
If execution breaks the pipeline:

1. Delete 4 new files:
   rm config/model_settings.json
   rm config/pathways.json
   rm config/routing_rules.json
   rm config/model_monitoring.json

2. Restart process_queue.ps1
   → Pipeline reverts to hardcoded defaults (old behavior)

3. Notify Saeed: "Rolled back, investigating issue"

Time to recover: <2 minutes

───────────────────────────────────────────────────────────────
DECISION REQUIRED
───────────────────────────────────────────────────────────────

Choose one:

[A] ✅ APPROVED
    → PipeWorks executes immediately
    → You'll see results report in next message

[B] ⚠️ APPROVED WITH CONDITIONS
    → What conditions? (type your changes)

[C] ❌ REJECTED
    → Why reject? (type reason)

───────────────────────────────────────────────────────────────
APPROVAL PACK ID: 20260525_PipeWorks_CONFIG_FILES_v1
CREATED BY: ControlTower (2026-05-25 10:30)
GUARDRAIL REVIEW: ✅ OK (no safety issues)
STATUS: Pending Saeed decision
───────────────────────────────────────────────────────────────
```

---

## Chat Interaction Example

**ControlTower posts approval pack (above) in chat**

**You respond:**
```
approved
```

**ControlTower immediately:**
```
Approval CONFIRMED. PipeWorks, proceed with execution.
```

**PipeWorks immediately:**
```
Executing 20260525_PipeWorks_CONFIG_FILES_v1...

Copying files:
  ✓ config/model_settings.json
  ✓ config/pathways.json
  ✓ config/routing_rules.json
  ✓ config/model_monitoring.json

Validation:
  ✓ All files in place
  ✓ JSON syntax valid
  ✓ process_queue.ps1 still starts (uses hardcoded defaults for now)

Status: EXECUTED (2026-05-25 10:31)
Next step: Waiting for PE-01 approval (process_queue.ps1 update to load config)
```

**ControlTower logs:**
```
Moved approval pack to: agents/ControlTower/approval_packs/approved/20260525_PipeWorks_CONFIG_FILES_v1_APPROVED.md

Updated CHANGE_LOG.md:
  Date: 2026-05-25
  Task: PipeWorks_CONFIG_FILES_v1
  Status: ✅ EXECUTED
  Approver: Saeed
  Executed: 2026-05-25 10:31
```

---

## What You Approve In Week 1

Plan for this approval pattern in Week 1:

| Approval # | Agent | What | Risk | Est. Time |
|-----------|-------|------|------|-----------|
| 1 | PathFinder | PATHWAY_REGISTRY.md | 🟢 Low | 1-2h |
| 2 | PipeWorks | 4 config files | 🟡 Med | 1-2h |
| 3 | DataVault | SCHEMA_V1.sql (no execution) | 🟢 Low | 2-3h |
| 4 | ModelWatch | Prompt documentation | 🟢 Low | 1-2h |
| 5 | ConfigMaster | practice_settings.json | 🟢 Low | 1-2h |

**Total:** ~8-13 hours of your review time over 2 weeks = ~1-2 hours per week

---

## Go-Live Approval

When all Phase 1 gates are done:

**ControlTower produces:**
```
APPROVAL PACK: PHASE_1_PRODUCTION_READY
- All Priority 1 tasks complete
- All tests passing
- Full regression suite green
- Backup/restore validated
- Security checklist complete
- Zero known critical issues

Status: READY FOR GO-LIVE

Decision required: "Approve production deployment"
```

**You decide:**
- ✅ Go live (deploy everything)
- ⚠️ Go live with caveats (specific restrictions)
- ❌ Hold in staging (more validation needed)

---

**Maintained by:** ControlTower agent  
**Last Updated:** 2026-05-22  
**Next Review:** After first approval

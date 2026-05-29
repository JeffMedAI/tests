# Agent Roles Quick Reference Guide
**Version:** 1.0  
**Purpose:** Quick lookup guide for agent responsibilities, qualifications, and knowledge levels  
**Owner:** ControlTower  
**Last Updated:** 2026-05-22

---

## One-Page Agent Summary

| Role | Title | Reports To | Domain | Key Deliverable | Status |
|------|-------|-----------|--------|-----------------|--------|
| **Saeed** | Executive Sponsor | — | Leadership | Final approvals | ✅ Active |
| **GuardRail** | Safety Gatekeeper | Saeed | Compliance | Safety blocks | ✅ Active |
| **ControlTower** | Chief Coordinator | Saeed | Operations | Approval packs | ✅ Active |
| **PathFinder** | Pathway Architect | ControlTower | Design | Pathway registry | 🟡 Sprint 1 |
| **DataVault** | DB Architect | ControlTower | Schema | SCHEMA_V1.sql | 🟡 Sprint 1 |
| **PipeWorks** | Workflow Engineer | ControlTower | Automation | Config files | 🟡 Sprint 1 |
| **TestBench** | QA Lead | ControlTower | Testing | Test suite | 🟡 Sprint 1 |
| **ModelWatch** | LLM Quality | ControlTower | ML Ops | Prompt docs | 🟡 Sprint 1 |
| **ConfigMaster** | Ops Manager | ControlTower | Operations | Practice config | 🟡 Sprint 1 |

---

## Detailed Role Profiles

### SAEED — Executive Sponsor & Owner

**Quick Facts:**
- 🎯 **Authority:** Final say on ALL production changes
- 📊 **Accountability:** System quality, compliance, go-live decision
- ⏱ **Time:** 2-4 hours/week
- 🚀 **Success Metric:** All high-risk decisions approved within 24h

**What You Do:**
```
Review approval packs (chief)
    ↓
Approve/reject/add conditions
    ↓
Make trade-off decisions (scope vs. speed vs. safety)
    ↓
Escalate governance issues
```

**What You DON'T Do:**
- ❌ Review code line-by-line
- ❌ Validate SQL syntax
- ❌ Make technical architecture decisions (agents do that)
- ❌ Execute changes (agents execute)

**Decision Template:**
```
You see: APPROVAL PACK from [Agent] about [what changed]
You think: Does risk level match the change? Can we undo this?
You decide: "approved" OR "approved with conditions: ..." OR "rejected: ..."
You wait: Agent executes and reports results
You track: ControlTower logs everything in CHANGE_LOG.md
```

---

### GUARDRAIL — Safety & Governance Gatekeeper

**Quick Facts:**
- 🎯 **Authority:** Can BLOCK any sensitive change (safety gate)
- 📊 **Accountability:** Zero compliance violations
- ⏱ **Time:** 3-5 hours/week
- 🚀 **Success Metric:** Zero safety violations + quarterly compliance audit passes

**Domain Expertise Required:**
- 🔴 GDPR, NHS data protection, clinical vs. admin decisions
- 🟡 Auth mechanisms, encryption, database security
- 🟢 Technical architecture (agents brief you)

**What You Do:**
```
Receive approval pack from ControlTower
    ↓
Check: Does this touch encryption, auth, patient data, or pathways?
    ↓
IF SENSITIVE:
    - Review against safety checklist
    - Check: No clinical decisions? ✓
    - Check: Patient data protected? ✓
    - Check: Audit logging present? ✓
    ↓
    Output: "✅ APPROVED (safety)" OR "❌ BLOCKED: reason"
    ↓
    Send to Saeed (or request revision if blocked)
```

**Safety Gate Checklist:**
```
☐ Does this allow system to make clinical decisions? (Must be NO)
☐ Does this expose unencrypted patient data? (Must be NO)
☐ Does this have audit logging? (Must be YES)
☐ Does this comply with GDPR 90-day purge? (Must be YES)
☐ Does LLM output override verified data? (Must be NO)
☐ Is handoff language "admin task only"? (Must be YES)
```

---

### CONTROLTOWER — Chief Coordinator

**Quick Facts:**
- 🎯 **Authority:** Creates approval packs, escalates blockers
- 📊 **Accountability:** 100% on-time approvals, zero missed dependencies
- ⏱ **Time:** 5-7 hours/week
- 🚀 **Success Metric:** Weekly progress reports on time, zero critical path misses

**Primary Workflow:**
```
Agent says: "Ready for approval"
    ↓
You create: Approval pack (what changed, why, risk level, rollback plan)
    ↓
You check: Does this touch sensitive areas?
    → YES: Flag for GuardRail review
    → NO: Direct to Saeed
    ↓
You wait: Saeed approves/rejects
    ↓
If approved: Agent executes
    ↓
You log: CHANGE_LOG.md entry + approval pack archive
```

**Weekly Cadence:**
```
Monday 10:00 — Sprint planning (assign tasks)
Friday 14:00 — Progress check-in (what's done, what's blocked)
Friday 14:30 — Retrospective (lessons learned)
Ongoing — Create approval packs, escalate blockers
```

---

### PATHFINDER — Pathway Architect

**Quick Facts:**
- 🎯 **Authority:** Defines all 8 pathways (prescription, sick_note, referral, test_result, appointment, admin, medication_query, unknown)
- 📊 **Accountability:** 100% pathway documentation, zero clinical decisions
- ⏱ **Time:** 4-6 hours/week
- 🚀 **Success Metric:** All 8 pathways documented + zero clinical-decision fields

**Domain Knowledge Required:**
- 🔴 All 8 pathways, field definitions, routing rules
- 🟡 Backend implementation, LLM extraction quality
- 🟢 Dashboard UI, encryption details

**Deliverables (Sprint 1):**
```
1. PATHWAY_REGISTRY.md
   - All 8 pathways with fields, routing, validation

2. VALIDATION_RULES.json
   - Field formats, required combos, value ranges

3. HANDOFF_TEMPLATES.json
   - Safe output format per pathway (admin task language)

4. TEST_CASES.md
   - Test scenario per pathway (handed to TestBench)
```

**Critical Rule:**
> Pathways must NEVER contain fields that represent clinical decisions.
> ✅ Good: "staff_review_required: boolean"
> ❌ Bad: "clinical_urgency: [low/medium/high]"

---

### DATAVAULT — Database Architect

**Quick Facts:**
- 🎯 **Authority:** Owns SQLite schema v1
- 📊 **Accountability:** Zero schema-related post-deployment issues
- ⏱ **Time:** 5-7 hours/week
- 🚀 **Success Metric:** All migrations pass test DB, zero data loss

**Domain Knowledge Required:**
- 🔴 SQLite, SQL optimization, audit logging, 90-day retention
- 🟡 Pathway definitions, backup/restore procedures
- 🟢 Business requirements

**Deliverables (Sprint 1):**
```
1. SCHEMA_V1.sql
   - Complete schema definition (calls, transcripts, pathway_runs, etc.)

2. migrations/
   - 001_initial_schema.sql
   - 002_audit_table.sql
   - 003_retention_policy.sql

3. AUDIT_TABLE_DEFINITION.sql
   - Captures all changes for compliance

4. RETENTION_POLICY.sql
   - 90-day purge logic
```

**Key Design Principles:**
```
✓ Schema supports 100M+ records (index strategy)
✓ Audit log captures every change (GuardRail requirement)
✓ 90-day purge logic built into schema (GDPR requirement)
✓ Backward compatible with existing queue files
✓ Performance tested against test DB
```

---

### PIPEWORKS — Workflow Engineer

**Quick Facts:**
- 🎯 **Authority:** Owns PowerShell, n8n, config externalisation
- 📊 **Accountability:** 99.5% pipeline uptime
- ⏱ **Time:** 5-8 hours/week
- 🚀 **Success Metric:** All 4 config files created, zero manual pipeline steps

**Domain Knowledge Required:**
- 🔴 PowerShell, n8n, configuration management, API auth
- 🟡 Pathway definitions, queue formats, error states
- 🟢 Database schema

**Deliverables (Sprint 1):**
```
1. config/model_settings.json — Ollama config
2. config/pathways.json — Active pathways
3. config/routing_rules.json — Staff assignment
4. config/model_monitoring.json — Confidence thresholds

Plus:
- Updated process_queue.ps1 (loads from config)
- auto_import_trigger.ps1
- Error handling & recovery scripts
```

**Critical Requirements (Security):**
```
IR-01: HMAC verification before queue write
    - Validate voice_agent_hmac_secret
    - Reject invalid signatures (not log & continue)

IR-02: Replace public prefix exemption with API auth
    - Proper authentication key system
    - No public endpoints
```

---

### TESTBENCH — Quality Assurance Lead

**Quick Facts:**
- 🎯 **Authority:** Can BLOCK releases if tests fail
- 📊 **Accountability:** >95% code coverage, zero production surprises
- ⏱ **Time:** 6-8 hours/week
- 🚀 **Success Metric:** 100% of releases pass full regression suite

**Domain Knowledge Required:**
- 🔴 Test automation, Python pytest, regression design
- 🟡 All pathway definitions, patient matching, auth
- 🟢 Database schema

**Deliverables (Sprint 1):**
```
1. auth_helpers.py
   - Session login helpers for tests

2. test_all_pathways.py
   - End-to-end tests for all 8 pathways

3. test_patient_matching.py
   - Matching accuracy regression suite

4. RELEASE_GATE_CRITERIA.md
   - What must pass before any production release

5. TEST_RESULTS_LOG.md
   - Per-run results and pass rate tracking
```

**Release Gate (Before Saeed Approves Go-Live):**
```
☐ All 8 pathway tests pass (100%)
☐ Patient matching tests pass (>95% accuracy)
☐ Auth tests pass (session security validated)
☐ SQLite write tests pass (data integrity)
☐ Code coverage >95% on critical paths
☐ Zero known critical issues
☐ Regression suite runs in <5 minutes
```

---

### MODELWATCH — LLM Quality Lead

**Quick Facts:**
- 🎯 **Authority:** Owns Ollama prompts and extraction quality
- 📊 **Accountability:** >95% extraction accuracy per pathway
- ⏱ **Time:** 4-6 hours/week
- 🚀 **Success Metric:** Zero extraction quality issues post-deployment

**Domain Knowledge Required:**
- 🔴 LLM prompts, extraction validation, confidence thresholds
- 🟡 All 8 pathways, expected extraction patterns
- 🟢 Database, backend processing

**Deliverables (Sprint 1):**
```
1. config/model_prompts/
   - All 8 pathway prompts documented
   - Expected extraction patterns per prompt

2. EXTRACTION_QUALITY_METRICS.md
   - How to measure accuracy
   - Comparison transcripts vs. JSON output

3. CONFIDENCE_THRESHOLDS.md
   - Safe confidence floors per pathway
   - Fallback triggers

4. extraction_regression_suite.md
   - Labeled test transcripts with expected outputs
```

**Quality Framework:**
```
For each pathway:
  Metric: Extraction accuracy >95%
  Measured: Compare model output vs. expected (labeled data)
  Threshold: If <95%, flag for prompt improvement
  Escalation: GuardRail reviews any hallucinations
```

---

### CONFIGMASTER — Operations Manager

**Quick Facts:**
- 🎯 **Authority:** Owns practice configuration & onboarding
- 📊 **Accountability:** 30-min average onboarding time
- ⏱ **Time:** 3-5 hours/week
- 🚀 **Success Metric:** Zero test data in production reports

**Domain Knowledge Required:**
- 🔴 Configuration management, practice operations, onboarding
- 🟡 Dashboard UI, pathway requirements
- 🟢 Database schema

**Deliverables (Sprint 1):**
```
1. PRACTICE_SETTINGS_TEMPLATE.json
   - Practice name, address, GP list, hours

2. ONBOARDING_RUNBOOK.md
   - Step-by-step setup guide

3. CSV_VALIDATION_SPEC.md
   - Patient data upload validation

4. TEMPLATE_MIGRATION_PLAN.md
   - How to remove hardcoded "Churchtown Medical Centre" strings
```

**Critical Requirements:**
```
Isolation:
  ☐ Demo/test cases never appear in live reports
  ☐ Test patients flagged as such
  ☐ Demo mode settings prevent production output

Externalisation:
  ☐ Remove all hardcoded practice strings
  ☐ Load from practice_settings.json
  ☐ Support multi-practice (Phase 2)
```

---

## Knowledge Levels Explained

### 🔴 Deep Knowledge (Expert Level)
**Definition:** Can make independent decisions, teach others, design new approaches  
**Time to Achieve:** 6+ months of hands-on work  
**Used For:** Primary domain decisions, review of agent work  
**Example:** PathFinder's deep knowledge of all 8 pathways allows them to design new pathway logic

### 🟡 Intermediate Knowledge (Working Knowledge)
**Definition:** Can understand decisions, contribute to implementation, flag issues  
**Time to Achieve:** 2-3 months of focused work  
**Used For:** Code review, testing, cross-functional collaboration  
**Example:** PathFinder's intermediate knowledge of backend implementation helps them design feasible pathways

### 🟢 Awareness Level (Familiar)
**Definition:** Knows enough to understand briefings, ask good questions, escalate appropriately  
**Time to Achieve:** 1-2 weeks of onboarding  
**Used For:** Decision context, escalation paths, team communication  
**Example:** PathFinder knows enough about encryption to understand when GuardRail flags a security concern

---

## Time Commitment Expectations

| Role | Hours/Week | Sprint Pattern | Scalability |
|------|-----------|-----------------|------------|
| **Saeed** | 2-4h | Approvals on demand | Fixed (owner) |
| **GuardRail** | 3-5h | Reviews per proposals | Grows with proposal rate |
| **ControlTower** | 5-7h | Steady (coordination) | Grows with team size |
| **PathFinder** | 4-6h | Tapers post-Sprint 1 | Maintains (design decisions only) |
| **DataVault** | 5-7h | Front-loaded (schema design) | Tapers post-Sprint 1 |
| **PipeWorks** | 5-8h | Steady (script work) | Slightly grows post-Sprint 1 |
| **TestBench** | 6-8h | Crescendos pre-release | Maintains (continuous testing) |
| **ModelWatch** | 4-6h | Tapers post-Sprint 1 | Grows with model improvements |
| **ConfigMaster** | 3-5h | Front-loaded (setup) | Tapers significantly post-Sprint 1 |

**Total Team Capacity:** ~40-50 hours/week (equivalent to 1-1.5 FTE)

---

## Onboarding Checklist

When onboarding a new agent (or replacing current agent):

**Week 1:**
- [ ] Read GOVERNANCE_FRAMEWORK.md (full section on your role)
- [ ] Read AGENT_TEAM_CHARTER.md (understand permissions)
- [ ] Read APPROVAL_WORKFLOW.md (understand how work gets approved)
- [ ] Meet with ControlTower (intro to roadmap, current priorities)
- [ ] Meet with GuardRail (understand safety requirements in your domain)
- [ ] Attend Monday sprint planning

**Week 2:**
- [ ] Read JEFFLOCAL_PRODUCTION_SPEC.md (understand requirements)
- [ ] Read existing deliverables from your domain (understand what's done)
- [ ] Review CHANGE_LOG.md (understand what's already approved)
- [ ] Ask questions in team sync (clarify any confusion)

**Week 3+:**
- [ ] Start contributing to your domain
- [ ] Create first approval pack with ControlTower guidance
- [ ] Participate in weekly retrospectives

---

## Common Scenarios & Decision Points

### Scenario 1: Disagreement Between Agents

**Question:** PathFinder and PipeWorks disagree on how to structure a pathway field.

**Answer:**
1. ControlTower facilitates a discussion (sync call if needed)
2. They try to reach consensus (both explain their position)
3. If still blocked → ControlTower escalates to Saeed (with both positions documented)
4. Saeed makes final decision

### Scenario 2: Safety Concern Mid-Work

**Question:** GuardRail sees a proposed change touches patient data unsafely.

**Answer:**
1. GuardRail BLOCKS the approval pack immediately
2. GuardRail sends blocking message to agent + ControlTower
3. Reason is clear ("This exposes unencrypted patient data")
4. Agent revises and resubmits (or accepts recommendation)

### Scenario 3: Test Failure Before Release

**Question:** TestBench finds a failing test the day before planned go-live.

**Answer:**
1. TestBench escalates to ControlTower + Saeed immediately
2. Saeed decides: Fix now (delay release) or investigate post-launch
3. If delay → agents revise, test again
4. If investigate → go-live with documented risk + post-launch follow-up plan

### Scenario 4: New Requirement Mid-Sprint

**Question:** A new requirement comes in that affects multiple agents' work.

**Answer:**
1. ControlTower assesses impact (which agents affected, how much rework)
2. ControlTower brings to Saeed with 3 options:
   - Add to current sprint (delay something else)
   - Add to next sprint (later timeline)
   - Defer to Phase 2 (not in Phase 1)
3. Saeed decides, ControlTower updates roadmap

---

**Maintained by:** ControlTower  
**Last Updated:** 2026-05-22  
**Next Review:** After first agent onboarding or role change

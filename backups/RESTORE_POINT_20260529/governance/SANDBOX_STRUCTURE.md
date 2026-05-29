# JeffLocal Sandbox Structure
**Purpose:** Isolated workspace for agent development before production merge  
**Root:** `C:\JeffLocal-Sandbox\`  
**Status:** Ready for team onboarding

---

## Directory Layout

```
C:\JeffLocal-Sandbox\
│
├── README.md                          ← Start here: sandbox overview
├── TEAM_CHARTER.md                    ← Agent roles & permissions
├── APPROVAL_WORKFLOW.md               ← How proposals become approved
├── CHANGE_LOG.md                      ← Audit trail of all approvals
│
├── agents/                            ← All agent workspace folders
│   ├── ControlTower/
│   │   ├── roadmap.md                 ← Master task list (synced from spec)
│   │   ├── task_tracking.md           ← Sprint 1, 2, 3 tasks
│   │   ├── dependency_graph.md        ← Task dependencies & critical path
│   │   ├── approval_pack_template.md  ← Template for change proposals
│   │   └── approval_packs/            ← Generated approval packs
│   │       ├── approved/
│   │       │   └── YYYYMMDD_[task]_approved.md
│   │       ├── pending/
│   │       │   └── YYYYMMDD_[task]_pending_review.md
│   │       └── rejected/
│   │           └── YYYYMMDD_[task]_rejected.md
│   │
│   ├── GuardRail/
│   │   ├── safety_review_template.md  ← Checklist for safety reviews
│   │   ├── approved_changes.md        ← Log of approved-by-guardrail changes
│   │   ├── blocked_changes.md         ← Log of blocked proposals + reasons
│   │   └── GDPR_audit.md              ← GDPR compliance tracking
│   │
│   ├── PathFinder/
│   │   ├── PATHWAY_REGISTRY.md        ← All 8 pathways documented
│   │   ├── VALIDATION_RULES.json      ← Field formats, required combos
│   │   ├── HANDOFF_TEMPLATES.json     ← Safe output per pathway
│   │   ├── TEST_CASES.md              ← Test scenario per pathway
│   │   └── pathway_gaps.md            ← Identified gaps/risks
│   │
│   ├── DataVault/
│   │   ├── SCHEMA_V1.sql              ← Full SQLite schema (no execution)
│   │   ├── migrations/
│   │   │   ├── 001_initial_schema.sql
│   │   │   └── migration_notes.md
│   │   ├── AUDIT_TABLE_DEFINITION.sql
│   │   ├── RETENTION_POLICY.sql       ← 90-day purge procedures
│   │   └── schema_review_notes.md
│   │
│   ├── PipeWorks/
│   │   ├── config/
│   │   │   ├── model_settings.json    ← Ollama config (externalised)
│   │   │   ├── pathways.json          ← Active pathways list
│   │   │   ├── routing_rules.json     ← Staff assignment rules
│   │   │   └── model_monitoring.json  ← Confidence thresholds
│   │   ├── scripts/
│   │   │   ├── auto_import_trigger.ps1
│   │   │   ├── hmac_verify.ps1        ← Verification implementation
│   │   │   └── pipeline_updates.md    ← What PS1 scripts need changing
│   │   └── n8n_workflow_design.md     ← HMAC + API key auth changes
│   │
│   ├── TestBench/
│   │   ├── helpers/
│   │   │   └── auth_helpers.py        ← Session login helper (reusable)
│   │   ├── test_all_pathways.py       ← 8 pathway E2E tests
│   │   ├── test_patient_matching.py   ← Matching accuracy suite
│   │   ├── test_auth.py               ← Auth flow tests
│   │   ├── RELEASE_GATE_CRITERIA.md   ← What must pass before go-live
│   │   ├── test_results_log.md        ← Per-run results & pass rate
│   │   └── regression_test_data/
│   │       ├── sample_transcripts.json
│   │       └── expected_outputs.json
│   │
│   ├── ModelWatch/
│   │   ├── config/
│   │   │   └── model_prompts/         ← All 8 pathway prompts
│   │   │       ├── prescription.txt
│   │   │       ├── sick_note.txt
│   │   │       ├── referral.txt
│   │   │       ├── test_result.txt
│   │   │       ├── appointment.txt
│   │   │       ├── admin.txt
│   │   │       ├── medication_query.txt
│   │   │       └── unknown.txt
│   │   ├── EXTRACTION_QUALITY_METRICS.md
│   │   ├── CONFIDENCE_THRESHOLDS.md
│   │   ├── model_performance_log.md
│   │   └── hallucination_tracker.md
│   │
│   └── ConfigMaster/
│       ├── config/
│       │   └── practice_settings.json ← Externalised practice data
│       ├── ONBOARDING_RUNBOOK.md      ← Step-by-step setup guide
│       ├── HARDCODE_MIGRATION.md      ← Plan to remove "Churchtown..." strings
│       ├── app/
│       │   └── validate_patient_csv.ps1
│       └── docs/
│           ├── staff_quick_reference.md
│           └── data_processing_agreement_template.md
│
├── approvals/                         ← Central approval tracking
│   ├── pending/
│   │   └── ← proposals waiting for Saeed
│   ├── approved/
│   │   └── ← approved & executed proposals
│   └── rejected/
│       └── ← rejected proposals + reason
│
├── docs/                              ← Consolidated documentation
│   ├── CONSOLIDATED_SPEC.md           ← All 3 of your docs merged
│   ├── PHASE1_CRITICAL_PATH.md        ← Task dependency order for production
│   ├── PRODUCTION_READINESS_CHECKLIST.md
│   └── FAQ.md                         ← Common questions
│
├── tests/                             ← All test files (executable)
│   ├── fixtures/                      ← Test data, not modified from production
│   └── results/                       ← Test run outputs
│
└── sync-plan/                         ← How to merge from sandbox → production
    ├── SYNC_STRATEGY.md
    ├── file_mapping.json              ← Which sandbox file → production location
    ├── pre_sync_checklist.md
    └── post_sync_validation.md
```

---

## Key Principles

1. **No Production Changes Here**  
   Everything in sandbox is **read-only reference or draft-only**. No execution against production files.

2. **Traceability**  
   Every proposal, approval, and rejection is logged with:
   - What changed
   - Who proposed it
   - Who approved/rejected it
   - Why
   - When it was approved
   - When it was executed (if applicable)

3. **Agent Autonomy Within Guardrails**  
   Agents can:
   - ✓ Draft code, schemas, configs
   - ✓ Run tests on sandbox data
   - ✓ Generate approval packs
   - ✓ Document recommendations
   
   But cannot:
   - ✗ Modify production files
   - ✗ Run migrations
   - ✗ Execute scripts against live data
   - ✗ Change encryption keys

4. **You Approve, Agent Executes**  
   Agents never auto-deploy. Pattern:
   ```
   Agent: "Here's proposal [X], test results show [Y], risk is [Z]"
   You: "Approved"
   Agent: "Executing... done. Results in [file]. Production updated."
   ```

5. **Rollback Plan**  
   Every approval pack includes: "If this breaks, here's how to undo it"

---

## Getting Started

### For You (Saeed)
1. **Read:** `TEAM_CHARTER.md` (defines all roles)
2. **Review:** `APPROVAL_WORKFLOW.md` (how you'll interact)
3. **Understand:** `CHANGE_LOG.md` will track everything
4. **First Action:** Approve one test proposal (even something small) to validate workflow

### For Each Agent
1. **Read:** `TEAM_CHARTER.md` section for your role
2. **Create:** Your agent folder with initial documents
3. **First Task:** Create your first proposal via ControlTower
4. **Example:** PathFinder creates `PATHWAY_REGISTRY.md`, uploads to `agents/PathFinder/`, ControlTower wraps it in approval pack, Saeed reviews

---

## Sandbox Sync to Production

### When You're Ready (probably Week 3-4)

```
1. ControlTower produces: "SYNC_PLAN.md"
   - Lists all changed files
   - Shows mapping: sandbox file → production location
   - Includes test plan

2. You review and approve: "approved"

3. Merge process:
   - Copy approved files from sandbox → production
   - Run full test suite against production (read-only)
   - Log all changes in CHANGE_LOG.md
   - Report results to you

4. You decide:
   - "Go live with these changes"
   - "Hold in staging, need more testing"
   - "Roll back, back to previous state"
```

### File Mapping Example

```json
{
  "syncs": [
    {
      "from": "agents/PipeWorks/config/model_settings.json",
      "to": "C:\\JeffLocal\\config\\model_settings.json",
      "approval_date": "2026-05-25",
      "execution_date": "2026-05-26",
      "status": "executed"
    },
    {
      "from": "agents/DataVault/migrations/001_initial_schema.sql",
      "to": "C:\\JeffLocal\\db\\migrations\\001_initial_schema.sql",
      "approval_date": "pending",
      "execution_date": null,
      "status": "pending_approval"
    }
  ]
}
```

---

## Agent Workflow Example

### Scenario: PathFinder Creates Pathway Registry

**Step 1: PathFinder drafts**
```
PathFinder creates: agents/PathFinder/PATHWAY_REGISTRY.md
- Documents all 8 pathways
- Lists fields, routing, validation rules
- Identifies 3 gaps
- Notifies ControlTower: "Ready for review"
```

**Step 2: ControlTower wraps in approval pack**
```
ControlTower creates: agents/ControlTower/approval_packs/pending/20260523_PathFinder_PATHWAY_REGISTRY_v1.md

Content:
  - WHAT: Pathway registry documenting all 8 pathways
  - WHY: Required to define fields per pathway (tied to PE-02, QA-03)
  - RISK: 🟢 Low (read-only doc, no code change)
  - TESTING: Reviewed for completeness, no test needed (design doc)
  - BLOCKS: PE-01, QA-03 can now proceed
  - DECISION REQUIRED: ☐ Approved
```

**Step 3: GuardRail reviews (optional for low-risk docs)**
```
GuardRail: "Document is safety-compliant. Pathways don't make clinical decisions. 
           All handoff outputs are admin-task language. Approved from safety perspective."
```

**Step 4: You (Saeed) approve**
```
You: "approved"
ControlTower: "Moving to approved/, executing..."
```

**Step 5: ControlTower finalises**
```
ControlTower:
- Moves file to: agents/ControlTower/approval_packs/approved/20260523_PathFinder_PATHWAY_REGISTRY_v1_APPROVED.md
- Logs in CHANGE_LOG.md:
  Date: 2026-05-23
  What: PATHWAY_REGISTRY.md created
  Who: PathFinder
  Approver: Saeed
  Risk: Low
  Status: Approved & Available
  
- Notifies downstream agents:
  DataVault: "Now you can design schema around these pathways"
  PipeWorks: "Now you can route based on these pathway definitions"
  TestBench: "Now you can create test cases for these pathways"
```

---

## Key Metrics to Track

**ControlTower will report weekly:**
- Tasks completed this week (count)
- Tasks blocked on approval (count)
- Average approval turnaround (hours)
- Cumulative approval packs: approved / rejected / pending
- Production readiness % (Phase 1 gates complete)

**Example:** 
```
WEEKLY REPORT — Week 1 (May 20-26)
Completed: 8 approval packs approved
Pending: 2 (waiting on Saeed review)
Rejected: 0
Avg approval time: 4 hours
Phase 1 readiness: 15% (1 of 7 critical sections done)

Priority next week:
- Wait for Saeed approval on DataVault SCHEMA_V1.sql
- PipeWorks can then proceed with migrations
- TestBench can then design schema-aware tests
```

---

## Sensitive Areas Requiring Explicit Approval

These touchpoints always need your approval before ANY agent executes:

```
🔒 Encryption Keys
   Location: config/security/keys/
   Always: Read-only until you say "approve this key rotation"

🔒 HMAC Secrets
   Location: config/security/keys/voice_agent_hmac_secret.txt
   Always: Read-only until approved

🔒 Live Database
   Location: dashboard/data/dashboard.sqlite
   Always: No agent modifies; migrations only after approval

🔒 Patient Data
   Locations: outputs/*, queue/processed/
   Always: Purge policies must be approved before automation

🔒 Authentication
   Locations: dashboard/app/auth.py, config/app_settings.json
   Always: Any auth logic change needs approval

🔒 Pathway Activation
   Any new pathway or pathway logic change = approval
   Even low-risk pathway → "approved from PathFinder, GuardRail, Saeed"

🔒 Model Configuration
   Any Ollama model, prompt, or threshold change = approval
```

**For approval packs touching these areas:** GuardRail always gets a look first.

---

## Success Checklist — End of First Sprint

- [ ] All 8 agent folders populated with Sprint 1 deliverables
- [ ] ControlTower has roadmap, task tracking, 3+ approval packs
- [ ] GuardRail has safety review template, initial risk assessment
- [ ] PathFinder has PATHWAY_REGISTRY.md complete
- [ ] DataVault has SCHEMA_V1.sql (no execution)
- [ ] PipeWorks has 4 config files drafted
- [ ] TestBench has test suite rewritten for session auth
- [ ] ModelWatch has prompts documented
- [ ] ConfigMaster has practice_settings.json drafted
- [ ] CHANGE_LOG.md shows 1-5 approved proposals
- [ ] Zero production files modified
- [ ] Approval workflow tested (at least 1 proposal approved)

---

**Maintained by:** ControlTower agent  
**Last Updated:** 2026-05-22  
**Next Review:** End of Sprint 1

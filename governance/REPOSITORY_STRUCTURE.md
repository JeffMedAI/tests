# JeffLocal Repository Structure & Organization
**Version:** 1.0  
**Owner:** ConfigMaster  
**Last Updated:** 2026-05-22

---

## Overview

The JeffLocal repository is organized to support:
- **Clear separation of concerns** (each agent owns specific directories)
- **Audit trail** (all changes documented and reversible)
- **Production safety** (sandbox isolation until approved)
- **Scalability** (easy to add new pathways, agents, features)

---

## Directory Structure

```
C:\JeffLocal/
├── agents/                           # Agent work products (primary)
│   ├── PathFinder/
│   │   ├── PATHWAY_REGISTRY.md       # All 8 pathways documented
│   │   ├── VALIDATION_RULES.json     # Field formats, required combos
│   │   ├── HANDOFF_TEMPLATES.json    # Safe output per pathway
│   │   ├── TEST_CASES.md             # Test scenarios for all pathways
│   │   └── pathway_flowcharts/       # Decision tree diagrams
│   │
│   ├── DataVault/
│   │   ├── SCHEMA_V1.sql             # Complete schema definition
│   │   ├── SCHEMA_DOCUMENTATION.md   # ER diagrams, table descriptions
│   │   ├── migrations/
│   │   │   ├── 001_initial_schema.sql
│   │   │   ├── 002_audit_table.sql
│   │   │   └── 003_retention_policy.sql
│   │   ├── AUDIT_TABLE_DEFINITION.sql
│   │   ├── RETENTION_POLICY.sql
│   │   └── BACKUP_RESTORE_PROCEDURES.md
│   │
│   ├── PipeWorks/
│   │   ├── scripts/
│   │   │   ├── process_queue.ps1     # Main queue processor (production)
│   │   │   ├── auto_import_trigger.ps1
│   │   │   ├── error_handler.ps1
│   │   │   └── recovery_procedures.ps1
│   │   ├── workflows/
│   │   │   ├── n8n_pipeline_export.json # n8n workflow definition
│   │   │   └── N8N_SETUP_GUIDE.md
│   │   └── CONFIG_DOCUMENTATION.md   # How each config file is used
│   │
│   ├── TestBench/
│   │   ├── tests/
│   │   │   ├── test_all_pathways.py  # E2E tests for all 8 pathways
│   │   │   ├── test_patient_matching.py
│   │   │   ├── test_auth_helpers.py
│   │   │   ├── test_queue_processing.py
│   │   │   └── conftest.py           # Pytest fixtures
│   │   ├── auth_helpers.py           # Session login helpers
│   │   ├── RELEASE_GATE_CRITERIA.md  # What must pass before go-live
│   │   ├── TEST_RESULTS_LOG.md       # Per-run results and trends
│   │   └── TEST_DATA/                # Labeled test data
│   │
│   ├── ModelWatch/
│   │   ├── config/
│   │   │   └── model_prompts/        # All 8 pathway prompts
│   │   │       ├── prescription_prompt.md
│   │   │       ├── sick_note_prompt.md
│   │   │       ├── referral_prompt.md
│   │   │       ├── test_result_prompt.md
│   │   │       ├── appointment_prompt.md
│   │   │       ├── admin_prompt.md
│   │   │       ├── medication_query_prompt.md
│   │   │       └── unknown_prompt.md
│   │   ├── EXTRACTION_QUALITY_METRICS.md
│   │   ├── CONFIDENCE_THRESHOLDS.md  # Safety floors per pathway
│   │   ├── HALLUCINATION_DETECTION.md
│   │   └── extraction_regression_suite.md
│   │
│   ├── ConfigMaster/
│   │   ├── PRACTICE_SETTINGS_TEMPLATE.json
│   │   ├── ONBOARDING_RUNBOOK.md
│   │   ├── CSV_VALIDATION_SPEC.md
│   │   ├── TEMPLATE_MIGRATION_PLAN.md
│   │   └── practice_config_examples/
│   │       └── churchtown_example.json
│   │
│   ├── GuardRail/
│   │   ├── SAFETY_REVIEW_TEMPLATE.md
│   │   ├── INITIAL_RISK_ASSESSMENT.md
│   │   ├── SAFETY_GATE_CHECKLIST.md
│   │   └── compliance_audits/
│   │       └── QUARTERLY_COMPLIANCE_REPORT_2026_Q2.md
│   │
│   ├── ControlTower/
│   │   ├── approval_packs/
│   │   │   ├── pending/
│   │   │   │   ├── 20260525_PathFinder_PATHWAY_REGISTRY_v1.md
│   │   │   │   └── 20260525_DataVault_SCHEMA_V1_v1.md
│   │   │   ├── approved/
│   │   │   │   └── 20260524_PipeWorks_CONFIG_FILES_v1_APPROVED.md
│   │   │   └── rejected/
│   │   │       └── 20260523_PathFinder_EMERGENCY_PATHWAY_v1_REJECTED.md
│   │   ├── roadmap.md                # Master task list
│   │   ├── dependency_graph.md       # Task dependencies & critical path
│   │   └── task_tracking.md          # Status of all Priority 1-5 tasks
│   │
│   └── DX/                           # Developer Experience agent (advisory)
│       ├── Issue_1_Implementation_Log.md
│       ├── Issue_1_Testing_Results.md
│       └── Issue_1_READY_FOR_APPROVAL.md
│
├── config/                           # Externalized configuration (production)
│   ├── model_settings.json           # Ollama config
│   ├── pathways.json                 # Active pathways list
│   ├── routing_rules.json            # Staff assignment rules
│   ├── model_monitoring.json         # Confidence thresholds
│   ├── practice_settings.json        # Practice name, GP list, hours
│   ├── security/
│   │   ├── keys/                     # ENCRYPTION KEYS (restricted access)
│   │   │   ├── .gitignore            # Never commit keys
│   │   │   ├── voice_agent_hmac_secret.txt
│   │   │   └── ENCRYPTION_KEY_MANIFEST.md
│   │   └── nonce_store.json          # Nonce tracking (restricted access)
│   └── demo_mode.json                # Demo/test isolation flags
│
├── docs/                             # Documentation (all agents contribute)
│   ├── architecture/
│   │   ├── llm_vs_rules_responsibility.md
│   │   ├── SYSTEM_ARCHITECTURE.md
│   │   └── DATA_FLOW_DIAGRAMS.md
│   ├── prompts/
│   │   ├── codex_build_prompt.md
│   │   ├── claude_cursor_review_prompt.md
│   │   └── PROMPT_ENGINEERING_GUIDE.md
│   ├── testing/
│   │   └── end_to_end_test_requirements.md
│   ├── procedures/
│   │   ├── DEPLOYMENT_PROCEDURES.md
│   │   ├── INCIDENT_RESPONSE.md
│   │   └── DISASTER_RECOVERY.md
│   └── policies/
│       ├── DATA_RETENTION_POLICY.md
│       ├── SECURITY_POLICY.md
│       └── COMPLIANCE_CHECKLIST.md
│
├── dashboard/                        # Flask application (production)
│   ├── app/
│   │   ├── auth.py                   # Session authentication
│   │   ├── models.py                 # Database models
│   │   ├── routes.py                 # View handlers
│   │   └── utils.py                  # Helper functions
│   ├── templates/
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── queue_view.html
│   │   └── admin_settings.html       # Practice admin section
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── requirements.txt
│   ├── config.py
│   └── run.py
│
├── queue/                            # Call queue management
│   ├── new/                          # Incoming calls
│   ├── processing/                   # Being processed
│   ├── normal/                       # Staff handoff (routine)
│   ├── review/                       # Needs manager review
│   ├── failed/                       # Processing failed
│   ├── deadletter/                   # Unrecoverable errors
│   └── processed/                    # Completed (archive)
│
├── outputs/                          # Generated outputs
│   ├── handoff_json/                 # Staff-facing JSON tasks
│   ├── reports/                      # Analytics & metrics
│   ├── logs/                         # Operational logs
│   └── backups/                      # Database backups (automated)
│
├── backup/                           # Restore points (automated daily)
│   ├── restore_points/
│   │   ├── restore_point_20260521_121309_pre_login_uxfixes_20260521/
│   │   └── restore_point_auto_daily_20260522_110047/
│   └── RESTORE_POINTS_INDEX.md
│
├── C:\JeffLocal-Sandbox/             # Sandbox for pre-approval work
│   └── [Same structure as main repo, but isolated]
│
├── GOVERNANCE_FRAMEWORK.md           # Organizational governance
├── AGENT_TEAM_CHARTER.md             # Agent roles & permissions
├── APPROVAL_WORKFLOW.md              # Approval process
├── REPOSITORY_STRUCTURE.md           # This document
├── JEFFLOCAL_PRODUCTION_SPEC.md      # Requirements (your 3-doc consolidation)
├── CHANGE_LOG.md                     # Audit trail of all changes
├── PROGRESS_REPORT.md                # Weekly status update
├── FIRST_SPRINT_ASSIGNMENTS.md       # Initial task allocations
├── README.md                         # Project overview
└── .gitignore                        # Files to exclude from version control
```

---

## Naming Conventions

### Files

**Governance & Process Documents:**
- Format: `[TYPE]_[SCOPE]_[PURPOSE].md` or `[TYPE]_[SCOPE].md`
- Examples: `GOVERNANCE_FRAMEWORK.md`, `CHANGE_LOG.md`, `PROGRESS_REPORT.md`
- All caps with underscores

**Agent Deliverables:**
- Format: `[CONTENT_TYPE]_[SCOPE].[ext]` or just descriptive name
- Examples: `PATHWAY_REGISTRY.md`, `SCHEMA_V1.sql`, `test_all_pathways.py`
- Clear, descriptive names (not abbreviated)

**Configuration Files:**
- Format: `[domain]_[purpose].json` or `[domain]_[purpose].yaml`
- Examples: `model_settings.json`, `practice_settings.json`, `routing_rules.json`
- Lowercase with underscores

**PowerShell Scripts:**
- Format: `[verb]_[noun].ps1`
- Examples: `process_queue.ps1`, `auto_import_trigger.ps1`, `error_handler.ps1`
- Descriptive verbs (process, generate, validate, import, export)

**Python Modules:**
- Format: `test_[module].py` for tests, `[module].py` for code
- Examples: `test_auth_helpers.py`, `auth_helpers.py`, `models.py`
- Lowercase with underscores

**SQL Scripts:**
- Format: `[seq]_[purpose].sql` for migrations
- Examples: `001_initial_schema.sql`, `002_audit_table.sql`
- Numbered for ordering, descriptive purpose

### Directories

**Agent Directories:**
- Format: `[AgentName]/` (PascalCase to match agent names)
- Examples: `PathFinder/`, `DataVault/`, `TestBench/`

**Functional Directories:**
- Format: `[function]/` (lowercase, plural if appropriate)
- Examples: `scripts/`, `migrations/`, `config/`, `tests/`, `outputs/`

**Date-Based Directories (Backups):**
- Format: `[prefix]_[YYYYMMDD_HHMMSS]_[description]/`
- Example: `restore_point_20260521_121309_pre_login_uxfixes_20260521/`

### Approval Pack IDs

**Format:** `[YYYYMMDD]_[AgentName]_[SHORT_TITLE]_v[N]`

**Examples:**
- `20260525_PipeWorks_CONFIG_FILES_v1`
- `20260525_DataVault_SCHEMA_MIGRATION_v1`
- `20260525_PathFinder_PATHWAY_UPDATE_v2` (resubmitted after revision)

---

## Ownership & Access Control

### Directory Ownership

| Directory | Primary Owner | Secondary Access | Restrictions |
|-----------|---------------|------------------|--------------|
| **agents/PathFinder** | PathFinder | ControlTower (read), GuardRail (read) | Editing: PathFinder only |
| **agents/DataVault** | DataVault | ControlTower, GuardRail (read) | Editing: DataVault only |
| **agents/PipeWorks** | PipeWorks | ControlTower (read) | Editing: PipeWorks + Saeed approval |
| **agents/TestBench** | TestBench | ControlTower (read) | Editing: TestBench only |
| **agents/ModelWatch** | ModelWatch | ControlTower, GuardRail (read) | Editing: ModelWatch only |
| **agents/ConfigMaster** | ConfigMaster | ControlTower (read) | Editing: ConfigMaster only |
| **agents/GuardRail** | GuardRail | ControlTower (read) | Editing: GuardRail only |
| **agents/ControlTower** | ControlTower | All agents (read) | Editing: ControlTower only |
| **config/** | ConfigMaster (primary), PipeWorks | All agents (read) | Editing: Saeed approval required |
| **dashboard/** | PipeWorks | ControlTower (read) | Editing: Saeed approval required |
| **queue/** | PipeWorks | All agents (read) | Editing: Automatic (system) |
| **outputs/** | System | All agents (read) | Editing: Automatic (system) |
| **backup/** | System | ControlTower, GuardRail (read) | Editing: System only |
| **config/security/keys/** | GuardRail + Saeed | None | Editing: Saeed approval required + GuardRail audit |

### Read-Only Files (Production)

These files should never be modified except via approval process:
- `C:\JeffLocal\AGENT_TEAM_CHARTER.md` — approval required
- `C:\JeffLocal\GOVERNANCE_FRAMEWORK.md` — approval required
- `C:\JeffLocal\APPROVAL_WORKFLOW.md` — approval required
- `C:\JeffLocal\JEFFLOCAL_PRODUCTION_SPEC.md` — approval required
- `dashboard/app/*.py` (production) — approval required
- `config/*.json` (production) — approval required

---

## Sandbox Sync to Production

### Workflow

```
Agent completes work in:
  C:\JeffLocal-Sandbox/agents/[Agent]/
         ↓
ControlTower wraps in approval pack
         ↓
GuardRail reviews (if sensitive)
         ↓
Saeed approves
         ↓
Agent copies from sandbox to production:
  C:\JeffLocal-Sandbox/ → C:\JeffLocal/
         ↓
TestBench validates (no errors)
         ↓
ControlTower logs in CHANGE_LOG.md
         ↓
Change is live
```

### Sync Verification

Before copying sandbox → production:
- [ ] ControlTower confirms approval
- [ ] All JSON/YAML files validated (syntax check)
- [ ] All SQL scripts validated (syntax check)
- [ ] All Python scripts validated (import check)
- [ ] All PowerShell scripts validated (syntax check)
- [ ] No sensitive data in files (GuardRail audit)
- [ ] File permissions correct (not executable unless intended)
- [ ] Change log updated with pre-copy info

---

## Git Ignore Policy

**DO NOT COMMIT to version control:**

```
# Secrets & Keys
config/security/keys/*
voice_agent_hmac_secret.txt
config/security/nonce_store.json

# Production Data
queue/
outputs/
backup/

# Python
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

**DO COMMIT:**
- All agent deliverables (design docs, schemas, scripts)
- All configuration templates (with placeholder values)
- All tests and test fixtures
- Documentation and procedures
- Change log
- Governance documents

---

## File Versioning

**For Approval Packs:**
- v1 = initial submission
- v2 = first resubmission (if rejected or revised)
- v3+ = subsequent revisions

**For Major Documents:**
- Update version number in document header
- Add changelog entry explaining what changed
- Keep previous versions in a `_archive/` subdirectory if needed

**For Configuration:**
- Keep current production version active
- Archive previous versions in `config/_archive/` with date stamps
- Document all version changes in CHANGE_LOG.md

---

## Maintenance & Cleanup

### Weekly Cleanup (ControlTower)
- [ ] Move completed approval packs to `_archive/`
- [ ] Validate all pending approval packs are current
- [ ] Check for orphaned sandbox files (>2 weeks old)

### Monthly Cleanup (ConfigMaster)
- [ ] Review and consolidate backup restore points (keep latest 10)
- [ ] Archive old logs (>30 days) to `outputs/logs/_archive/`
- [ ] Validate no sensitive data in outputs

### Quarterly Cleanup (ControlTower + GuardRail)
- [ ] Review full directory for any stray files
- [ ] Validate ownership and access control
- [ ] Audit naming consistency
- [ ] Update this document if structure changes

---

**Maintained by:** ConfigMaster  
**Last Updated:** 2026-05-22  
**Next Review:** 2026-06-22

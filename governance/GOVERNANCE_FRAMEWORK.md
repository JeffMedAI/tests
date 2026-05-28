# JeffLocal Governance Framework
**Version:** 2.0 (Professional Edition)  
**Effective Date:** 2026-05-22  
**Organization:** JeffLocal Agent Team  
**Owner:** Saeed (Executive Sponsor)  

---

## Table of Contents
1. [Organizational Structure](#organizational-structure)
2. [Decision Rights & Authority](#decision-rights--authority)
3. [Agent Roles & Qualifications](#agent-roles--qualifications)
4. [Communication & Escalation](#communication--escalation)
5. [Compliance & Audit](#compliance--audit)

---

## Organizational Structure

### Executive Leadership
```
┌─────────────────────────────────────────┐
│    SAEED (Executive Sponsor / Owner)    │
│  - Final approval authority              │
│  - Strategic direction                   │
│  - Risk acceptance                       │
│  - Go-live decisions                     │
└────────────────────┬────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
   GUARDRAIL    CONTROLTOWER   EXECUTIVE
   (Safety)     (Operations)   STEERING
                               (Advisory)
```

### Full Organization Chart

```
SAEED (Owner)
├── GUARDRAIL (Safety & Governance Keeper)
│   └── Reports: Risk assessments, safety blockers, audit findings
│
├── CONTROLTOWER (Chief Coordinator)
│   ├── Oversees: PathFinder, DataVault, PipeWorks, TestBench, ModelWatch, ConfigMaster
│   └── Reports: Weekly progress, blockers, approval packs
│
└── EXECUTIVE STEERING COMMITTEE (Advisory)
    ├── Purpose: Strategic alignment, release gates, escalations
    ├── Members: Saeed (chair), GuardRail, ControlTower, external advisors as needed
    └── Cadence: Weekly

SPECIALIST AGENTS (Functional Teams)
├── PathFinder (Pathway Architecture)
│   ├── Reports to: ControlTower (day-to-day) & GuardRail (safety review)
│   └── Peer: DataVault, PipeWorks
│
├── DataVault (Database & Schema)
│   ├── Reports to: ControlTower (day-to-day) & GuardRail (GDPR/audit review)
│   └── Peer: PathFinder, PipeWorks
│
├── PipeWorks (Workflow & Pipeline)
│   ├── Reports to: ControlTower (day-to-day) & GuardRail (security review)
│   └── Peer: PathFinder, DataVault, ConfigMaster
│
├── TestBench (Quality Assurance)
│   ├── Reports to: ControlTower
│   ├── Gate: Must approve before any production release
│   └── Peer: All other agents (functional dependency)
│
├── ModelWatch (LLM Quality & Monitoring)
│   ├── Reports to: ControlTower (day-to-day) & GuardRail (safety review)
│   └── Peer: PathFinder, PipeWorks
│
└── ConfigMaster (Operations & Practice Settings)
    ├── Reports to: ControlTower (day-to-day)
    └── Peer: DataVault, PipeWorks
```

---

## Decision Rights & Authority

### Authority Levels

| Decision Type | Authority | Rationale | Timeline |
|---------------|-----------|-----------|----------|
| **Strategic Direction** | Saeed | Owner sets vision | Quarterly review |
| **Production Deployment** | Saeed (final) | Safety-critical system | Per release |
| **Safety Gate (Block)** | GuardRail | Independent safety review | Real-time |
| **Release Approval** | ControlTower + TestBench consensus | Operational readiness | Per release |
| **Agent Priorities** | ControlTower | Task orchestration | Weekly adjustments |
| **Technical Architecture** | Specialist agent (domain) | Deep expertise required | Per proposal |
| **Escalation to Saeed** | GuardRail or ControlTower | Blocking issues only | Real-time |
| **Budget/Resource** | Saeed | System constraints | Quarterly |
| **Governance Changes** | Saeed + ControlTower | Process improvement | As needed |

### Approval Authority Matrix

```
DECISION                         WHO APPROVES                   ESCALATION PATH
────────────────────────────────────────────────────────────────────────────
Configuration Change (low-risk)  ControlTower → Saeed          GuardRail (if sensitive)
Schema Migration                 DataVault → GuardRail → Saeed  —
Pathway Logic                    PathFinder → GuardRail → Saeed —
Security/Auth Change             PipeWorks → GuardRail → Saeed  —
Test Suite Update               TestBench → ControlTower       —
Production Deployment           TestBench + ControlTower → Saeed —
Emergency Fix                   Saeed (direct approval)         GuardRail review post-mortem
Governance Change               Saeed + ControlTower            —
Agent Hiring/Role Change        Saeed (with input from current team) —
```

---

## Agent Roles & Qualifications

### 1. SAEED — Executive Sponsor & Owner

**Role:** Final decision authority, strategic vision keeper, risk acceptor

**Responsibilities:**
- Approve all production changes and releases
- Make trade-off decisions (speed vs. safety, scope vs. timeline)
- Accept or reject risk assessments from GuardRail
- Set strategic priorities and roadmap
- Act as tiebreaker for team disagreements
- Conduct quarterly reviews of governance effectiveness
- Make go-live decisions

**Qualifications Required:**
- Domain authority in medical systems (GP reception workflows)
- Understanding of NHS/EMIS requirements
- Ability to assess technical trade-offs
- Experience with healthcare compliance (GDPR, data protection)
- Authority to make binding commitments

**Knowledge Level:**
- 🔴 **Deep:** JeffLocal requirements, safety constraints, business goals
- 🟡 **Intermediate:** Technical architecture, database concepts, pipeline workflows
- 🟢 **Awareness:** Agent-specific technical details (agents brief you on specifics)

**Time Commitment:** 2-4 hours per week (approval reviews, steering committee)

**Success Metrics:**
- All high-risk decisions approved/rejected within 24 hours
- Zero safety incidents due to approval decisions
- Team reports clarity on strategic direction (quarterly survey)

---

### 2. GUARDRAIL — Safety & Governance Gatekeeper

**Role:** Independent safety reviewer, GDPR/audit gatekeeper, clinical decision blocker

**Domain:** Healthcare safety, data protection, compliance, deterministic logic verification

**Primary Responsibilities:**
- Review all proposals touching: patient data, encryption, auth, pathways, clinical logic
- Block changes that allow LLM to override verified data
- Audit GDPR compliance (90-day retention, audit logging)
- Verify absence of clinical decision-making by system
- Review deterministic logic for safety correctness
- Escalate blocked proposals to Saeed with detailed reasoning
- Maintain safety charter and issue guidance

**Secondary Responsibilities:**
- Quarterly compliance audit of all stored data
- Security briefing to team on new threats
- Recommendation on data retention policies
- Training new agents on safety constraints

**Qualifications Required:**
- ✓ Deep understanding of GDPR and UK healthcare data protection
- ✓ Understanding of clinical decision vs. admin task distinction
- ✓ Ability to review code/logic for safety correctness
- ✓ Experience with healthcare compliance frameworks
- ✓ Independent judgment (not influenced by schedule pressure)

**Knowledge Level:**
- 🔴 **Deep:** Healthcare regulations, patient data protection, clinical vs. admin decisions, NHS requirements
- 🟡 **Intermediate:** Technical architecture, authentication, encryption, database security
- 🟢 **Awareness:** Specific agent implementations

**Time Commitment:** 3-5 hours per week (proposal reviews, compliance checks)

**Success Metrics:**
- Zero safety/compliance violations in approved changes
- All blocked proposals correctly identified pre-production
- Quarterly audit passes with zero high-risk findings
- Team reports safety confidence (quarterly survey) >4/5

**Escalation Authority:** Direct to Saeed (can block any change)

---

### 3. CONTROLTOWER — Chief Operations Officer

**Role:** Orchestrator, coordinator, roadmap keeper, task flow manager

**Domain:** Project management, task dependency tracking, approval workflow coordination

**Primary Responsibilities:**
- Maintain master task list aligned to production spec
- Track task dependencies and critical path
- Create approval packs (wrapping agent work)
- Coordinate between specialist agents
- Weekly progress reporting and blocker identification
- Generate roadmap and timeline forecasts
- Plan sandbox-to-production sync process
- Manage change log (audit trail)

**Secondary Responsibilities:**
- Define workflow standards (task naming, status terminology)
- Monitor agent productivity and identify bottlenecks
- Facilitate technical decisions between agents
- Plan sprint goals and retrospectives
- Recommend process improvements to Saeed
- Brief external stakeholders (if applicable)

**Qualifications Required:**
- ✓ Project management experience (Agile/Waterfall)
- ✓ Ability to identify task dependencies and critical path
- ✓ Clear communication and stakeholder management
- ✓ Comfort synthesizing technical information for non-technical audience
- ✓ Attention to detail (audit trail maintenance)

**Knowledge Level:**
- 🔴 **Deep:** Production spec, task dependencies, approval workflow, JeffLocal requirements
- 🟡 **Intermediate:** Technical details of each specialist domain
- 🟢 **Awareness:** Specific implementation details (delegated to specialist agents)

**Time Commitment:** 5-7 hours per week (coordination, approval packs, reporting)

**Success Metrics:**
- Weekly progress reports on time and accurate (100%)
- All task dependencies correctly identified (validation by agents)
- Approval packs processed within target turnaround (see SLA)
- Zero missed critical path items
- Team reports clarity on priorities (weekly check-in)

**Approval Authority:** Creates approval packs; escalates to Saeed (no direct approval authority)

---

### 4. PATHFINDER — Pathway Architecture Lead

**Role:** Multi-pathway design architect, field schema owner, routing logic designer

**Domain:** Call routing, pathway definition, field validation, handoff template design

**Primary Responsibilities:**
- Document all 8 current pathways (prescription, sick_note, referral, test_result, appointment, admin, medication_query, unknown)
- Define required vs. optional fields per pathway
- Design routing rules (normal queue, review queue, failed queue, deadletter)
- Create handoff output templates (admin task language only)
- Design field validation rules and format constraints
- Prevent pathways from making clinical decisions
- Define test cases for all 8 pathways
- Review pathway-related code changes pre-implementation

**Secondary Responsibilities:**
- Recommend new pathways as business needs evolve
- Design pathway activation/deactivation logic
- Document pathway decision trees (flowcharts)
- Work with ModelWatch on pathway-specific prompts
- Create pathway onboarding guide for new agents

**Qualifications Required:**
- ✓ Understanding of GP reception workflows
- ✓ Experience with decision trees and routing logic
- ✓ Ability to distinguish clinical vs. admin language
- ✓ Field schema design experience
- ✓ Attention to consistency across 8 pathways

**Knowledge Level:**
- 🔴 **Deep:** All 8 pathways, field definitions, routing rules, validation requirements
- 🟡 **Intermediate:** Backend implementation (how routes execute), LLM extraction quality
- 🟢 **Awareness:** Dashboard UI, encryption, database schema specifics

**Time Commitment:** 4-6 hours per week (design, code review, testing prep)

**Success Metrics:**
- Pathway registry 100% complete and reviewed by GuardRail
- Zero pathway changes that allow clinical decisions
- All 8 pathways have test cases approved by TestBench
- Pathway logic documentation >95% complete
- Field definitions consistent across pathways (audit by ControlTower quarterly)

**Approval Authority:** Recommends pathway changes; GuardRail reviews; Saeed approves

---

### 5. DATAVAULT — Database & Schema Architect

**Role:** SQLite schema owner, data integrity guardian, migration script author

**Domain:** Database design, SQL, schema migrations, audit logging, data retention

**Primary Responsibilities:**
- Design complete SQLite schema for Phase 1 (calls, transcripts, pathway_runs, extracted_fields, handoff_tasks, audit_log, deadletter_items, model_outputs)
- Design and implement 90-day data retention and purge logic
- Create migration scripts from file-based to SQLite state
- Design audit logging table and triggers
- Ensure backward compatibility with existing queue files
- Plan backup/restore procedures and test them
- Optimize schema for query performance (especially audit log searches)
- Create SQL documentation and ER diagrams

**Secondary Responsibilities:**
- Recommend data model improvements as features evolve
- Work with GuardRail on GDPR compliance for data handling
- Provide test databases for TestBench regression
- Document schema versioning strategy
- Design monitoring queries for operational health

**Qualifications Required:**
- ✓ Advanced SQL and database design expertise
- ✓ Experience with SQLite or similar embedded databases
- ✓ Data retention and compliance requirements knowledge
- ✓ Ability to design efficient schemas for both transactional and audit use cases
- ✓ Experience with migration scripts and zero-downtime transitions

**Knowledge Level:**
- 🔴 **Deep:** SQLite schema design, SQL optimization, audit logging, data retention
- 🟡 **Intermediate:** Pathway definitions (what data to track), backup/restore procedures
- 🟢 **Awareness:** Business requirements, compliance rules (GuardRail briefs)

**Time Commitment:** 5-7 hours per week (schema design, migrations, testing)

**Success Metrics:**
- Schema v1 complete and approved by GuardRail (GDPR compliance)
- All migration scripts tested against test DB (no data loss)
- Audit log table captures all required events (validated by TestBench)
- 90-day retention policy implemented and testable
- Zero schema-related production issues post-deployment

**Approval Authority:** Recommends schema changes; GuardRail reviews (GDPR); Saeed approves migrations

---

### 6. PIPEWORKS — Workflow Engineer & Pipeline Automation

**Role:** End-to-end pipeline builder, config externalizer, automation architect

**Domain:** PowerShell scripting, n8n workflows, API integration, configuration management

**Primary Responsibilities:**
- Connect n8n → queue → PowerShell → dashboard with zero manual steps
- Create and maintain config files (model_settings.json, pathways.json, routing_rules.json, model_monitoring.json)
- Implement HMAC verification before queue writes (IR-01)
- Replace public prefix exemption with proper API authentication (IR-02)
- Implement error handling, deadletter movement, retry logic
- Create auto-import triggers (queue → dashboard)
- Modernize all PowerShell scripts to production standards (error handling, logging, timeouts)
- Generate test data for regression suites
- Create deployment scripts and rollback procedures

**Secondary Responsibilities:**
- Design n8n workflow logic and error paths
- Recommend pipeline improvements and optimizations
- Document workflow architecture and data flows
- Work with ConfigMaster on practice-specific config values
- Support TestBench with test data generation

**Qualifications Required:**
- ✓ Expert PowerShell/scripting skills
- ✓ n8n workflow design experience
- ✓ REST API integration and authentication experience
- ✓ Configuration management best practices
- ✓ Error handling and resilience patterns
- ✓ JSON/YAML configuration format expertise

**Knowledge Level:**
- 🔴 **Deep:** PowerShell scripting, n8n workflows, configuration externalisation, API auth
- 🟡 **Intermediate:** Pathway definitions, queue formats, error states
- 🟢 **Awareness:** Database schema, dashboard specifics

**Time Commitment:** 5-8 hours per week (script development, testing, maintenance)

**Success Metrics:**
- All 4 config files created and validated (PE-01 complete)
- Zero manual steps in pipeline (n8n → queue → dashboard automated)
- HMAC verification implemented (IR-01 complete)
- API auth replaced public exemption (IR-02 complete)
- All PowerShell scripts have error handling and logging
- Test data generation automated for regression

**Approval Authority:** Recommends pipeline changes; GuardRail reviews (security); Saeed approves production changes

---

### 7. TESTBENCH — Quality Assurance & Release Gatekeeper

**Role:** Test suite owner, regression prevention, release validator

**Domain:** Test automation, quality assurance, release criteria, regression prevention

**Primary Responsibilities:**
- Rewrite test suite for session-based authentication (QA-01)
- Implement unique test data generation per run (QA-02)
- Create end-to-end tests for all 8 pathways (QA-03)
- Build regression test suite covering: request classifier, patient matching, auth, SQLite writes
- Define and enforce release gate criteria (what must pass before go-live)
- Run tests automatically before agent proposals (pre-approval validation)
- Create and maintain test data labeling (expected outputs)
- Document test failure root causes and remediation
- Create test automation pipelines (trigger before production changes)

**Secondary Responsibilities:**
- Recommend improvements to code quality based on test results
- Work with other agents on testability of their designs
- Provide test coverage metrics and trends
- Design automated regression detection
- Create test documentation for new agent onboarding

**Qualifications Required:**
- ✓ Expert test automation and QA experience
- ✓ Python testing frameworks (pytest or equivalent)
- ✓ Ability to design comprehensive test cases
- ✓ Experience with regression test suites
- ✓ Understanding of healthcare system testing needs
- ✓ Zero-tolerance mindset for release quality

**Knowledge Level:**
- 🔴 **Deep:** Test suite design, regression prevention, release gate criteria, Python testing
- 🟡 **Intermediate:** All pathway definitions, patient matching logic, auth mechanisms
- 🟢 **Awareness:** Database schema, pipeline workflows

**Time Commitment:** 6-8 hours per week (test development, execution, analysis)

**Success Metrics:**
- Test suite rewritten for session auth (QA-01 complete)
- All 8 pathways have end-to-end test cases (QA-03 complete)
- >95% code coverage on critical paths (validated per release)
- Zero production issues due to missed test cases
- All releases pass 100% of regression suite before Saeed approval
- Test results reported weekly with trend analysis

**Approval Authority:** Can BLOCK releases if tests fail; recommends quality improvements; escalates test failures to ControlTower

---

### 8. MODELWATCH — LLM Quality & Monitoring Lead

**Role:** Extraction quality guardian, prompt engineer, model monitoring designer

**Domain:** LLM prompt engineering, extraction validation, confidence thresholds, model drift detection

**Primary Responsibilities:**
- Document current Ollama prompts for all 8 pathways
- Design extraction validation metrics (compare transcripts vs. JSON output)
- Set confidence thresholds per pathway (currently 0.72 baseline)
- Design fallback logic (when to switch models or escalate)
- Implement hallucination detection (flag unsupported claims)
- Design model monitoring and drift detection metrics
- Label test transcripts with expected extractions for regression
- Recommend prompt improvements based on extraction quality data

**Secondary Responsibilities:**
- Work with PathFinder on pathway-specific extraction requirements
- Create documentation of expected extraction quality per pathway
- Recommend model upgrades or alternatives based on performance data
- Design A/B testing framework for prompt improvements
- Create extraction quality dashboard for operational monitoring

**Qualifications Required:**
- ✓ Expert LLM prompt engineering experience
- ✓ Extraction quality evaluation methodology
- ✓ Statistical analysis and metrics design
- ✓ Understanding of LLM limitations and hallucination patterns
- ✓ Healthcare domain knowledge (what extractions are clinically critical)

**Knowledge Level:**
- 🔴 **Deep:** LLM prompt design, extraction quality metrics, confidence thresholds, model evaluation
- 🟡 **Intermediate:** All 8 pathways, field definitions, expected extraction patterns
- 🟢 **Awareness:** Database schema, backend processing

**Time Commitment:** 4-6 hours per week (prompt documentation, quality testing, monitoring design)

**Success Metrics:**
- All 8 prompts documented with expected extraction quality (EXTRACTION_QUALITY_METRICS.md complete)
- Confidence thresholds set and validated per pathway
- Extraction regression test suite labeled and validated
- Model monitoring dashboard designed and implemented
- Zero production extraction errors due to undetected model drift

**Approval Authority:** Recommends model/prompt changes; GuardRail reviews (safety); Saeed approves production changes

---

### 9. CONFIGMASTER — Practice Operations & Settings Manager

**Role:** Configuration externalizer, practice settings owner, onboarding runbook keeper

**Domain:** Configuration management, practice operations, staff onboarding, CSV validation

**Primary Responsibilities:**
- Externalize practice configuration (practice_settings.json: name, address, GP list, hours)
- Remove all hardcoded strings (e.g., "Churchtown Medical Centre" templates)
- Design and document staff onboarding procedures
- Create patient CSV upload and validation script
- Ensure demo/test cases never appear in live reports
- Prepare practice admin section of dashboard
- Create configuration migration plan for removing hardcodes
- Design settings UI and configuration update procedures

**Secondary Responsibilities:**
- Work with PipeWorks on config file formats
- Document practice-specific configuration options
- Create multi-practice configuration strategy (future Phase 2)
- Recommend onboarding improvements based on user feedback
- Design configuration version control and rollback procedures

**Qualifications Required:**
- ✓ Configuration management and externalization experience
- ✓ Operational procedures documentation skills
- ✓ Understanding of healthcare practice workflows
- ✓ User onboarding and training material design
- ✓ CSV validation and data integrity expertise

**Knowledge Level:**
- 🔴 **Deep:** Practice operations, onboarding procedures, configuration externalisation, CSV validation
- 🟡 **Intermediate:** Dashboard UI, admin functionality, pathway requirements
- 🟢 **Awareness:** Database schema, pipeline workflows

**Time Commitment:** 3-5 hours per week (config design, onboarding docs, CSV validation)

**Success Metrics:**
- All hardcoded practice strings replaced with config files (100% completion)
- practice_settings.json complete and validated
- Onboarding runbook tested with new user walkthrough
- CSV validation script working (no invalid data enters system)
- Demo/test data isolation working (zero test data in production reports)
- Onboarding time reduced by 30% post-implementation

**Approval Authority:** Recommends config changes; ControlTower coordinates; Saeed approves production changes

---

## Communication & Escalation

### Communication Channels

| Topic | Channel | Frequency | Attendees |
|-------|---------|-----------|-----------|
| **Approval Requests** | Chat (approval pack) | As needed | Proposing agent, ControlTower, GuardRail (if sensitive), Saeed |
| **Weekly Progress** | Chat + PROGRESS_REPORT.md | Every Monday | ControlTower → Saeed, all agents |
| **Blocking Issues** | Chat (direct to Saeed) | Real-time | Blocking agent, GuardRail (if safety), Saeed |
| **Sprint Planning** | Chat + task list | Sprint start (weekly) | ControlTower, all agents |
| **Retrospective** | Chat summary | Sprint end (weekly) | ControlTower, all agents |
| **Steering Committee** | Chat summary | Weekly | Saeed, ControlTower, GuardRail, external advisors |
| **Agent Sync (optional)** | Scheduled as needed | Ad-hoc | ControlTower + 2-3 agents |
| **Emergency Incident** | Chat (escalate to Saeed) | Real-time | All relevant agents, Saeed |

### Escalation Paths

```
ISSUE → WHO ESCALATES → TO WHOM → ACTION
────────────────────────────────────────────────────────
Test failure   → TestBench     → ControlTower → Fix before approval
Safety concern → Any agent     → GuardRail    → Block & analyze
Blocked task   → ControlTower  → Saeed        → Decision required
Production bug → Any agent     → Saeed + GuardRail → Post-mortem
Resource issue → ControlTower  → Saeed        → Reallocate
Schedule slip  → ControlTower  → Saeed        → Adjust roadmap
Agent conflict → ControlTower  → Saeed        → Mediate
```

### Meeting Cadence

| Meeting | Day | Time | Duration | Owner | Attendees |
|---------|-----|------|----------|-------|-----------|
| **Sprint Planning** | Monday | 10:00 AM | 30 min | ControlTower | All agents |
| **Steering Committee** | Monday | 3:00 PM | 30 min | Saeed | Saeed, ControlTower, GuardRail |
| **Weekly Progress Check-in** | Friday | 2:00 PM | 30 min | ControlTower | All agents + Saeed |
| **Retrospective** | Friday | 2:30 PM | 30 min | ControlTower | All agents |
| **Emergency Sync** | As needed | ASAP | 15-30 min | Saeed | Relevant agents |

---

## Compliance & Audit

### Audit Trail Requirements

Every change must be logged in CHANGE_LOG.md with:
- Date and time (UTC)
- Change ID and title
- Proposing agent and ControlTower wrapper
- GuardRail review result (if required)
- Saeed approval decision and date
- Execution date and results
- Test results (if applicable)
- Rollback validation

### Quarterly Compliance Review

**GuardRail conducts quarterly audit covering:**
- ✓ 90-day data retention compliance (sample verification)
- ✓ Audit log completeness (all changes logged)
- ✓ Zero clinical decisions by system (code review)
- ✓ Encryption key management compliance
- ✓ GDPR compliance (data handling, consent, privacy)

**Results reported to Saeed with:**
- Findings (compliant / non-compliant)
- Remediation plan (if issues found)
- Recommendations for governance improvements

### Agent Performance Review (Quarterly)

**ControlTower conducts quarterly reviews:**

| Agent | Success Metrics | Target |
|-------|-----------------|--------|
| **GuardRail** | Safety violations | 0 |
| **ControlTower** | On-time approvals | 100% |
| **PathFinder** | Pathway completeness | 100% documented |
| **DataVault** | Schema issues | 0 post-deployment |
| **PipeWorks** | Pipeline uptime | 99.5% |
| **TestBench** | Test coverage | >95% |
| **ModelWatch** | Extraction quality | >95% accuracy per pathway |
| **ConfigMaster** | Onboarding time | 30 min average |

**Results presented to Saeed with recommendations for improvement**

---

## Governance Document Index

| Document | Purpose | Owner | Review Cadence |
|----------|---------|-------|----------------|
| GOVERNANCE_FRAMEWORK.md | This document | Saeed | Quarterly |
| AGENT_TEAM_CHARTER.md | Agent roles and permissions | ControlTower | As agent changes |
| APPROVAL_WORKFLOW.md | Approval process detailed steps | ControlTower | As process changes |
| REPOSITORY_STRUCTURE.md | File organization and naming | ConfigMaster | As repo evolves |
| CHANGE_LOG.md | Audit trail of all changes | ControlTower | Updated per approval |
| PROGRESS_REPORT.md | Weekly status update | ControlTower | Every Monday |
| FIRST_SPRINT_ASSIGNMENTS.md | Initial task allocations | ControlTower | Sprint-based |

---

**Approved by:** Saeed  
**Effective Date:** 2026-05-22  
**Next Review:** 2026-08-22 (Quarterly)  
**Last Updated:** 2026-05-22

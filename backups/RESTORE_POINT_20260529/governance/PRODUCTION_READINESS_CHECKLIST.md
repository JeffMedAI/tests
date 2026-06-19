# Production Readiness Checklist
**Version:** 1.0  
**For:** Sprint 1 Completion → Phase 1 Go-Live  
**Owner:** Saeed (final approval)  
**Last Updated:** 2026-05-22

---

## Overview

This checklist verifies all prerequisites before moving to production. Complete by Sprint 1 end (2026-05-31).

**Go-Live Decision:**
- ✅ All boxes checked → Ready for production
- ⚠️ Some boxes unchecked → Address before go-live
- ❌ Critical boxes unchecked → Hold, fix, recheck

---

## PHASE 1 READINESS GATES

### GATE 1: Governance & Organization (Saeed)

- [ ] Governance suite complete
  - [x] GOVERNANCE_FRAMEWORK.md written
  - [x] OPERATIONS_PROCEDURES.md written
  - [x] DEVOPS_INFRASTRUCTURE_SETUP.md written
  - [ ] Team briefed and acknowledged
  - [ ] First approval executed successfully

- [ ] Agent team operational
  - [ ] All 9 agents assigned and confirmed
  - [ ] Each agent has completed onboarding checklist
  - [ ] Decision rights matrix understood
  - [ ] Escalation paths tested (at least 1)

- [ ] Documentation complete
  - [ ] GOVERNANCE_INDEX.md current
  - [ ] REPOSITORY_STRUCTURE.md implemented
  - [ ] AGENT_ROLES_QUICK_REFERENCE.md reviewed
  - [ ] No conflicting instructions

**Gate Owner:** Saeed  
**Timeline:** Week 1 (by 2026-05-29)  
**Blocker:** Cannot proceed to Gate 2 if unchecked

---

### GATE 2: Infrastructure & DevOps (ControlTower + ConfigMaster)

- [ ] Directory structure created
  - [ ] devops/ folder with all subdirectories
  - [ ] agents/_shared/ with templates
  - [ ] agents/[Agent]/ structure per agent
  - [ ] Documentation: `find C:\JeffLocal\devops /type d | wc -l` = 25+ dirs

- [ ] Monitoring & alerting configured
  - [ ] Daily health check procedure documented
  - [ ] Alert escalation matrix posted
  - [ ] Baseline metrics recorded (response time, error rate, uptime)
  - [ ] Alert configuration created (alerts/*.json files exist)

- [ ] Backup & recovery tested
  - [ ] Daily backup script: devops/backup_recovery/backup_scripts/daily_backup.ps1
  - [ ] Restore script: devops/backup_recovery/restore_scripts/restore_from_backup.ps1
  - [ ] Test restore completed (successful)
  - [ ] Recovery time documented (target: <1 hour)

- [ ] Deployment pipeline designed
  - [ ] Deployment script: devops/deployment/deploy_production.ps1
  - [ ] Rollback script: devops/deployment/rollback_production.ps1
  - [ ] Smoke test script: devops/deployment/smoke_test.ps1
  - [ ] Deployment window scheduled (Sunday 2-4 AM)

- [ ] Disaster recovery plan complete
  - [ ] DISASTER_RECOVERY_PLAN.md written
  - [ ] RTO/RPO metrics documented
  - [ ] Recovery procedures tested (at least scenario 1)
  - [ ] Off-site backup strategy planned

**Gate Owner:** ControlTower + ConfigMaster  
**Timeline:** Week 1-2 (by 2026-05-31)  
**Blocker:** Cannot deploy without backup/restore verified

---

### GATE 3: Code Quality & Testing (TestBench)

- [ ] Test suite complete
  - [ ] test_all_pathways.py: All 8 pathways have end-to-end tests
  - [ ] test_patient_matching.py: >95% matching accuracy
  - [ ] test_auth_helpers.py: Session authentication working
  - [ ] test_queue_processing.py: Queue operations verified

- [ ] Test results passing
  - [ ] All tests run successfully (0 failures)
  - [ ] Code coverage: >95% on critical paths
  - [ ] Regression suite: <5 minutes execution time
  - [ ] Test data: Unique per run, no conflicts

- [ ] Release gate criteria met
  - [ ] RELEASE_GATE_CRITERIA.md specifies all requirements
  - [ ] All P1 requirements passing
  - [ ] No known critical bugs
  - [ ] Performance within baseline

- [ ] Regression testing
  - [ ] Request classifier: Accuracy >95%
  - [ ] Patient matching: Accuracy >95%
  - [ ] Authentication: All session tests pass
  - [ ] SQLite writes: Data integrity verified

**Gate Owner:** TestBench  
**Timeline:** Week 1-2 (by 2026-05-31)  
**Blocker:** Cannot go live if tests failing

---

### GATE 4: Safety & Compliance (GuardRail)

- [ ] GDPR compliance verified
  - [ ] 90-day data retention implemented in schema
  - [ ] Audit log table captures all changes
  - [ ] Patient data encryption verified
  - [ ] Purge procedures tested

- [ ] Safety gates implemented
  - [ ] No system makes clinical decisions
  - [ ] LLM output never overrides verified data
  - [ ] Handoff language: "Admin task" only (no clinical language)
  - [ ] Validation rules enforce safety constraints

- [ ] Security audit passed
  - [ ] No hardcoded secrets in code/config
  - [ ] Encryption keys: Proper access control
  - [ ] API authentication: No public endpoints
  - [ ] Vulnerability scan: Zero critical issues

- [ ] Deterministic logic verified
  - [ ] Patient matching rules reviewed (no AI fallthrough)
  - [ ] Queue routing rules reviewed (no AI decisions)
  - [ ] Field validation rules reviewed (safety constraints)
  - [ ] Handoff output format reviewed (admin-only language)

- [ ] Compliance checklist
  - [ ] NHS/EMIS integration: Not in Phase 1 (approved skip)
  - [ ] Data export: Disabled (approved restriction)
  - [ ] Clinical recommendations: Blocked (enforced)
  - [ ] Audit trail: Complete and tested

**Gate Owner:** GuardRail  
**Timeline:** Week 2 (by 2026-05-31)  
**Blocker:** Cannot go live if safety gate fails

---

### GATE 5: Configuration & Deployment (PipeWorks + ConfigMaster)

- [ ] Configuration externalised
  - [ ] config/model_settings.json: Ollama model, temp, timeout
  - [ ] config/pathways.json: All 8 pathways registered
  - [ ] config/routing_rules.json: Staff assignment rules
  - [ ] config/model_monitoring.json: Confidence thresholds
  - [ ] config/practice_settings.json: Practice name, GP list, hours

- [ ] Hardcoded values removed
  - [ ] "Churchtown Medical Centre" references: Migrated to config
  - [ ] Model name: Loaded from config/model_settings.json
  - [ ] Pathways: Loaded from config/pathways.json
  - [ ] Staff assignments: Loaded from config/routing_rules.json

- [ ] Pipeline integration complete
  - [ ] n8n → queue: Automated (HMAC verification working)
  - [ ] queue → dashboard: Auto-import trigger working
  - [ ] Error handling: Deadletter logic working
  - [ ] Retry logic: Implemented and tested

- [ ] API security
  - [ ] IR-01: HMAC verification (before queue write) ✅
  - [ ] IR-02: API authentication (no public exemption) ✅
  - [ ] API keys: Secure management confirmed
  - [ ] Rate limiting: Configured if applicable

**Gate Owner:** PipeWorks + ConfigMaster  
**Timeline:** Week 1-2 (by 2026-05-31)  
**Blocker:** Cannot go live with hardcoded values

---

### GATE 6: Architecture & Design (PathFinder + DataVault)

- [ ] Pathway architecture complete
  - [ ] PATHWAY_REGISTRY.md: All 8 pathways documented
  - [ ] VALIDATION_RULES.json: All field formats defined
  - [ ] HANDOFF_TEMPLATES.json: Output format per pathway
  - [ ] TEST_CASES.md: Test scenario per pathway
  - [ ] No pathway allows clinical decisions

- [ ] Database schema complete
  - [ ] SCHEMA_V1.sql: All tables defined
  - [ ] Audit log table: Implemented with triggers
  - [ ] 90-day retention: Implemented in schema
  - [ ] Indexes: Performance optimized
  - [ ] Migrations: 001_initial_schema.sql tested

- [ ] Data integrity verified
  - [ ] Migrations tested against test DB (zero data loss)
  - [ ] Audit logging: All changes captured
  - [ ] Referential integrity: Foreign keys enforced
  - [ ] Query performance: Indexes optimized

**Gate Owner:** PathFinder + DataVault  
**Timeline:** Week 1-2 (by 2026-05-31)  
**Blocker:** Cannot go live with incomplete schema

---

### GATE 7: Operations & Support (ControlTower)

- [ ] Operational procedures documented
  - [ ] OPERATIONS_PROCEDURES.md: All sections complete
  - [ ] Runbooks: incident_response, maintenance, health_check
  - [ ] Checklists: Daily, weekly, monthly, quarterly
  - [ ] Escalation paths: Documented and tested

- [ ] Monitoring dashboard created
  - [ ] PIPELINE_HEALTH.md: Metrics and thresholds
  - [ ] DATABASE_HEALTH.md: Metrics and thresholds
  - [ ] SYSTEM_METRICS.md: Overall system health
  - [ ] Baseline metrics recorded (first week of operations)

- [ ] Team communication established
  - [ ] Weekly Monday planning: Scheduled
  - [ ] Weekly Friday review: Scheduled
  - [ ] Incident notification: Process documented
  - [ ] On-call rotation: Assigned (if applicable)

- [ ] Training completed
  - [ ] All agents: Completed onboarding checklist
  - [ ] Saeed: Understands approval process and decision rights
  - [ ] On-call team: Understands runbooks and escalation
  - [ ] Support staff: Can interpret dashboard metrics

**Gate Owner:** ControlTower  
**Timeline:** Week 2 (by 2026-05-31)  
**Blocker:** Cannot go live without operational readiness

---

## SIGN-OFF MATRIX

| Gate | Owner | Status | Date | Sign-Off |
|------|-------|--------|------|----------|
| 1. Governance | Saeed | Pending | — | [ ] |
| 2. Infrastructure | ControlTower + ConfigMaster | Pending | — | [ ] |
| 3. Code Quality | TestBench | Pending | — | [ ] |
| 4. Safety & Compliance | GuardRail | Pending | — | [ ] |
| 5. Configuration | PipeWorks + ConfigMaster | Pending | — | [ ] |
| 6. Architecture | PathFinder + DataVault | Pending | — | [ ] |
| 7. Operations | ControlTower | Pending | — | [ ] |

**All Gates Sign-Off Required:**
- [ ] Saeed (Executive approval)
- [ ] GuardRail (Safety clearance)
- [ ] ControlTower (Operational readiness)
- [ ] TestBench (Test validation)

---

## GO-LIVE DECISION

**Date:** 2026-05-31 (End of Sprint 1)

**Saeed's Decision (Choose One):**

- [ ] **✅ GO LIVE** 
  - All gates passed
  - All sign-offs obtained
  - Proceed with Phase 1 production deployment
  - Deployment window: Sunday 2026-06-02, 2-4 AM

- [ ] **⚠️ GO LIVE WITH RESTRICTIONS**
  - Specify restrictions:
  - [List any features disabled or limited]
  - Plan full go-live for: [Future date]

- [ ] **❌ HOLD / RESCHEDULE**
  - Reason: [Why not ready]
  - Plan: [What needs to be fixed]
  - Revised timeline: [New go-live date]

---

**Saeed Approval Signature:** ________________ **Date:** _______

---

**Maintained by:** ControlTower  
**Next Review:** Weekly (until all gates pass)  
**Final Review:** 2026-05-30 (day before go-live)

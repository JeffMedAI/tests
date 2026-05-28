# Task 1 — Operational Flow (Week 1)
**Version:** 2.0 (updated for 4-agent structure)
**Tasks:** W1-1 Pathway Registry + W1-2 Config Files
**Owner:** TechLead (delivery) + ControlTower (coordination)
**Status:** Complete — executed 2026-05-23

---

## Overview

Week 1 delivers two sets of foundational work:

| Task | Owner | Deliverables |
|------|-------|-------------|
| **W1-1: Pathway Registry** | TechLead | PATHWAY_REGISTRY.md, VALIDATION_RULES.json, HANDOFF_TEMPLATES.json, TEST_CASES.md |
| **W1-2: Config Files** | TechLead | model_settings.json, pathways.json, routing_rules.json, model_monitoring.json |

Both tasks go through the full 4-agent approval workflow before deployment.

---

## Flow Diagram

```
═══════════════════════════════════════════════════════════════════════════
                   WEEK 1 — TASK 1 OPERATIONAL FLOW
═══════════════════════════════════════════════════════════════════════════

PHASE: DEVELOPMENT
──────────────────

TechLead (sandbox/code/):
┌─────────────────────────────────────────────────────────────────────────┐
│ W1-1: Create Pathway Registry                                           │
│   ✅ PATHWAY_REGISTRY.md — all 6 pathways fully documented              │
│   ✅ VALIDATION_RULES.json — field validation per pathway               │
│   ✅ HANDOFF_TEMPLATES.json — output structure per pathway              │
│   ✅ TEST_CASES.md — test scenarios for all 6 pathways                  │
│                                                                         │
│ W1-2: Create Config Files (sandbox/code/config/)                        │
│   ✅ model_settings.json — Ollama configuration                         │
│   ✅ pathways.json — active pathways + field definitions                │
│   ✅ routing_rules.json — queue routing + staff assignment              │
│   ✅ model_monitoring.json — confidence thresholds per pathway          │
│                                                                         │
│ Self-check passed → notify ControlTower: "Ready for E2E testing"       │
└─────────────────────────────────────────────────────────────────────────┘


PHASE: TECHNICAL E2E TESTING
─────────────────────────────

TechLead:
┌─────────────────────────────────────────────────────────────────────────┐
│ Code paths:      ✅ PASS — All pathway definitions execute correctly     │
│ Data flows:      ✅ PASS — JSON structures valid, fields present         │
│ Performance:     ✅ PASS — Config files load in <100ms                  │
│ Error handling:  ✅ PASS — Missing fields handled gracefully             │
│ Regression:      ✅ PASS — No existing functionality broken              │
│                                                                         │
│ OVERALL: ✅ PASS                                                         │
│ Report: sandbox/audit/test_results/techlead_20260523.md                 │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓

PHASE: OPERATIONAL E2E TESTING
────────────────────────────────

ControlTower:
┌─────────────────────────────────────────────────────────────────────────┐
│ Workflow validation: ✅ PASS — End-to-end queue processing works        │
│ User experience:    ✅ PASS — Dashboard shows correct pathway data       │
│ Business logic:     ✅ PASS — Routing rules match live code behaviour    │
│ Integration points: ✅ PASS — Config loads correctly with pipeline       │
│ Data integrity:     ✅ PASS — All 6 pathways consistent across files     │
│                                                                         │
│ OVERALL: ✅ PASS                                                         │
│ Report: sandbox/audit/test_results/controltower_20260523.md             │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓

PHASE: DEPLOYMENT E2E TESTING
───────────────────────────────

DevOps:
┌─────────────────────────────────────────────────────────────────────────┐
│ Infrastructure:   ✅ PASS — Server resources sufficient                  │
│ Config validation:✅ PASS — All 4 JSON files parse without errors        │
│ Migration dry-run:✅ PASS — No DB changes needed for config files        │
│ Rollback prepared:✅ PASS — rollback_configfiles_20260523.ps1 tested    │
│ Smoke test plan:  ✅ PASS — 5 smoke tests defined and ready             │
│                                                                         │
│ OVERALL: ✅ PASS                                                         │
│ Report: sandbox/audit/test_results/devops_20260523.md                   │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓

PHASE: APPROVAL PACK CREATION
───────────────────────────────

ControlTower:
┌─────────────────────────────────────────────────────────────────────────┐
│ All 3 E2E phases: ✅ PASS (confirmed with timestamps)                   │
│ Pack ID: APPROVAL_20260523_W1_PATHWAY_AND_CONFIG_v1                     │
│ Saved: sandbox/audit/approval_packs/APPROVAL_20260523_W1_...md         │
│ Sent to: GuardRail for mandatory safety review                          │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓

PHASE: GUARDRAIL SAFETY REVIEW
────────────────────────────────

GuardRail:
┌─────────────────────────────────────────────────────────────────────────┐
│ Test completeness:    ✅ All 3 phases PASS, timestamped                  │
│ Audit trail:          ✅ Complete and consistent                         │
│ Clinical boundary:    ✅ No clinical decisions — admin tasks only        │
│ Patient data safety:  ✅ No patient data in config/registry files        │
│ Regulatory compliance:✅ Compliant — no new data handling introduced     │
│ Rollback readiness:   ✅ Script tested and ready                         │
│ Admin-task language:  ✅ All handoff templates use admin-task language   │
│ Audit logging:        ✅ Unaffected by these changes                     │
│                                                                         │
│ VERDICT: ✅ APPROVED — forwarding to Saeed                              │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓

PHASE: SAEED EXECUTIVE DECISION
─────────────────────────────────

Saeed reviews approval pack:
  • What changed: Pathway registry (4 docs) + config files (4 JSON)
  • Why: Foundational documentation and config externalisation
  • Risk: 🟢 Low — no code changes, no DB changes
  • GuardRail: ✅ Approved
  • Rollback: Delete 8 files (trivial, <1 min)

  Decision: ✅ APPROVED
                              ↓

PHASE: PRODUCTION DEPLOYMENT
──────────────────────────────

DevOps:
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 1 — Deploy pathway registry docs:                                  │
│   sandbox/code/PATHWAY_REGISTRY.md   → governance/ (reference doc)     │
│   sandbox/code/VALIDATION_RULES.json → governance/                     │
│   sandbox/code/HANDOFF_TEMPLATES.json → governance/                    │
│   sandbox/code/TEST_CASES.md         → sandbox/tests/                  │
│                                                                         │
│ Step 2 — Deploy config files:                                           │
│   sandbox/code/config/model_settings.json   → config/                  │
│   sandbox/code/config/pathways.json         → config/                  │
│   sandbox/code/config/routing_rules.json    → config/                  │
│   sandbox/code/config/model_monitoring.json → config/                  │
│                                                                         │
│ Step 3 — Smoke tests: ✅ All 5 PASS                                     │
│ Step 4 — Deployment log saved                                           │
│                                                                         │
│ STATUS: ✅ DEPLOYED — 2026-05-23                                         │
└─────────────────────────────────────────────────────────────────────────┘
                              ↓

PHASE: CHANGE LOG
──────────────────

ControlTower logs in governance/CHANGE_LOG.md:
  APPROVAL_20260523_W1_PATHWAY_AND_CONFIG_v1 — ✅ DEPLOYED
```

---

## Agent Participation Map

```
SAEED (Human Executive)
  └─ ✅ Executive approval (~10 min review)

CONTROLTOWER (Chief Operations Officer)
  ├─ Coordinates TechLead's development
  ├─ Runs Operational E2E Testing → ✅ PASS
  ├─ Creates Approval Pack (after all 3 pass)
  └─ Logs deployment in CHANGE_LOG.md

TECHLEAD (Chief Architect)
  ├─ Creates all 8 deliverable files
  └─ Runs Technical E2E Testing → ✅ PASS

DEVOPS (Infrastructure & Deployment)
  ├─ Runs Deployment E2E Testing → ✅ PASS
  ├─ Prepares rollback script
  └─ Executes production deployment + smoke tests

GUARDRAIL (Chief Compliance Officer)
  └─ Mandatory safety review → ✅ APPROVED
```

---

**Created:** 2026-05-22 (v1.0 — 9-agent structure)
**Updated:** 2026-05-23 (v2.0 — 4-agent structure, Week 1 executed)

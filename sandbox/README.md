# Sandbox Environment

This is the working sandbox for the Churchtown Medical Centre agent team. All development, testing, and pre-deployment validation happens here. Code only moves to production after the full approval workflow completes.

## Structure

```
sandbox/
  agents/
    TechLead/        Chief Architect — owns code & technical E2E testing
    ControlTower/    Chief Operations Officer — coordination, operational E2E, approval packs
    DevOps/          Infrastructure & Deployment — deployment E2E, production deployment
    GuardRail/       Chief Compliance Officer — independent safety gate
  code/              Working copies of application source code
  tests/             Test suites (unit, integration, E2E)
  audit/
    approval_packs/  Completed approval packs + GuardRail verdicts
    test_results/    Per-agent test result reports
```

## Approval Workflow

```
TechLead:      Technical E2E Testing    → PASS / FAIL
ControlTower:  Operational E2E Testing  → PASS / FAIL
DevOps:        Deployment E2E Testing   → PASS / FAIL
                     ↓ (ALL THREE must PASS)
ControlTower:  Creates Approval Pack
                     ↓
GuardRail:     Safety & Compliance Review → Approve / Reject
                     ↓ (Approve only)
Saeed:         Executive Decision → Approve / Reject / Request Changes
                     ↓ (Approve only)
DevOps:        Deploy to Production (Churchtown Medical Centre)
```

## Critical Rule
**No agent bypasses any check. All 3 testing phases must PASS before the approval pack is created. No exceptions.**

## Agent Briefs
Each agent's full brief (role, responsibilities, testing scope, outputs) is in their folder:
- `agents/TechLead/AGENT_BRIEF.md`
- `agents/ControlTower/AGENT_BRIEF.md`
- `agents/DevOps/AGENT_BRIEF.md`
- `agents/GuardRail/AGENT_BRIEF.md`

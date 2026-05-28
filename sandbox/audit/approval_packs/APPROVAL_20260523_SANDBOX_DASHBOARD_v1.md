# Approval Pack
**ID:** APPROVAL_20260523_SANDBOX_DASHBOARD_v1
**Created:** 2026-05-23
**Created by:** ControlTower
**Status:** Pending GuardRail Review → Pending Saeed Approval

---

## What Changed

**New files created in `sandbox/dashboard/` (not production):**

| File | Purpose |
|------|---------|
| `sandbox/dashboard/` | Full copy of production dashboard |
| `sandbox/dashboard/sandbox_startup.py` | Loads .env.sandbox, injects practice config into templates, starts uvicorn on port 5000 |
| `sandbox/dashboard/.env.sandbox` | Practice config for Churchtown Medical Centre sandbox instance |
| `sandbox/dashboard/launch_sandbox.ps1` | One-command launch script |
| `sandbox/dashboard/DEPLOY_NEW_PRACTICE.md` | Step-by-step guide for deploying to a new practice |
| `sandbox/dashboard/templates/base.html` | Sandbox copy — sandbox banner added, practice name in topbar |
| `sandbox/dashboard/static/dashboard.css` | Sandbox copy — sandbox banner CSS and --practice-accent var added |

**Production files modified:** None. Zero.

---

## Why

Deliver a practice-configurable sandbox dashboard that:
1. Allows the agent team to test changes without touching the live system
2. Serves as the starting point for deploying to new practices (copy folder, update .env, deploy)
3. Shows a clearly visible SANDBOX banner so no one mistakes it for a live system

---

## Risk Level

🟢 **Low** — No production code was modified. Sandbox is a separate copy on a different port (5000 vs 8765) with its own isolated database. Rollback is deleting the `sandbox/dashboard/` folder.

**Sensitive areas touched:**
- ☐ Encryption / secrets
- ☐ Patient data handling
- ☐ Authentication logic
- ☐ Database schema
- ☐ Audit logging
- ☐ Clinical pathway logic
- ✅ None of the above

---

## E2E Testing Results (All 3 Required — All PASS)

| Phase | Agent | Score | Verdict | Report |
|-------|-------|-------|---------|--------|
| Technical E2E | TechLead | 27/27 | ✅ PASS | `sandbox/audit/test_results/techlead_20260523.md` |
| Operational E2E | ControlTower | 5/5 areas | ✅ PASS | `sandbox/audit/test_results/controltower_20260523.md` |
| Deployment E2E | DevOps | 17/17 | ✅ PASS | `sandbox/audit/test_results/devops_20260523.md` |

---

## Rollback Plan

**Script:** Delete `C:\JeffLocal\sandbox\dashboard\`
**Production affected:** No — production dashboard at `C:\JeffLocal\dashboard\` is completely untouched.
**Estimated recovery time:** < 1 minute.
**Tested:** ✅ Yes — production baseline verified intact in DevOps E2E report.

---

## GuardRail Review

Status: ⏳ Pending
Report: `sandbox/audit/approval_packs/GUARDRAIL_20260523_SANDBOX_DASHBOARD_v1.md`

---

## Saeed Decision

✅ **approved**

Signed: Saeed | 2026-05-23

---

## Deployment Record

Status: ✅ Deployed — 2026-05-23
Log: `sandbox/audit/approval_packs/DEPLOYMENT_LOG_20260523_SANDBOX_DASHBOARD_v1.md`

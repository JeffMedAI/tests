# ControlTower — Operational E2E Test Report
**Date:** 2026-05-23
**Task:** Sandbox Dashboard (W1-3)
**TechLead result:** ✅ PASS (confirmed, report: sandbox/audit/test_results/techlead_20260523.md)
**Signed:** ControlTower

## Operational Test Results

### Workflow Validation
- Sandbox dashboard is a standalone copy of production — not modifying the live system ✅
- launch_sandbox.ps1 → sandbox_startup.py → uvicorn is a clear, linear launch path ✅
- .env.sandbox controls all practice-specific settings in one place ✅
- DEPLOY_NEW_PRACTICE.md gives a complete step-by-step guide for deploying to a new practice ✅

### User Experience
- Sandbox banner renders conditionally: visible when ENVIRONMENT=sandbox, hidden when ENVIRONMENT=production ✅
- Banner is orange and clearly labelled "SANDBOX" with practice name — unmistakable ✅
- Practice name appears in topbar brand and page title — correct for any practice ✅
- All existing navigation, routes, and UI features inherited unchanged from production ✅

### Business Logic
- Per-practice config (name, branding, pathways, DB) is fully isolated via env vars ✅
- Production code (main.py, db.py) is untouched — sandbox changes cannot contaminate production ✅
- Setting ENVIRONMENT=production for a new practice deployment removes sandbox banner automatically ✅
- DB_PATH override in db.py (via env var) allows each practice to have its own isolated database ✅

### Integration Points
- sandbox_startup.py imports directly from app.main — same FastAPI app object, no forking or duplication ✅
- templates.env.globals.update() is the correct Jinja2 injection mechanism — works with all existing routes ✅
- Port 5000 does not conflict with production port (8765) ✅

### Data Integrity
- Sandbox database (sandbox/dashboard/data/dashboard.sqlite) is fully isolated from production ✅
- No patient data shared between sandbox and production instances ✅
- All audit logging, session management, and auth from production code are inherited intact ✅

## Summary

| Area | Result |
|------|--------|
| Workflow validation | ✅ PASS |
| User experience | ✅ PASS |
| Business logic | ✅ PASS |
| Integration points | ✅ PASS |
| Data integrity | ✅ PASS |

**OVERALL VERDICT: ✅ PASS**

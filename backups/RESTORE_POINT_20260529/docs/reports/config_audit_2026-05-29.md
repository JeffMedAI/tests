# CONFIG FILE AUDIT — 2026-05-29
# Lead Agent: JeffLocal
# Triggered by: Playwright test showing 4 of 5 config files as "Missing" on Settings page
# Auditor: Lead Agent (assessment only — no files created, no Python touched)

---

## SCOPE

The Settings page (`/settings`) in `dashboard/app/main.py` (line 3838) displays a
health check for 5 config files. During a Playwright dashboard test, 4 showed as
"Missing". This audit determines:
1. Whether each missing file is actually required by the running system
2. What the correct content structure should be
3. Which agent is responsible for creating it
4. The acceptance criteria for each

---

## METHOD

1. Read `dashboard/app/main.py` in full — searched for every reference to each filename
2. Searched entire `C:\JeffLocal` codebase for filename references (governance docs,
   PowerShell scripts, test files, agent briefs, production spec)
3. Read agent briefs: `backend_CLAUDE.md`, `database_CLAUDE.md`
4. Read `JEFFLOCAL_PRODUCTION_SPEC.md` (PE-01 through PE-06 gap list)
5. Read `FIRST_SPRINT_ASSIGNMENTS.md` (PW-01 through PW-04 task definitions)
6. Read `GOVERNANCE_FRAMEWORK.md`, `AGENT_TEAM_CHARTER.md`, test cases

---

## KEY FINDING: Settings Page vs. Active Loading

The Settings page (`/settings`) uses these files ONLY as existence checks for display:
```python
"state": "configured" if path.exists() else "missing"
```
No content is read. Missing files do NOT crash the dashboard. The app starts without them.

However, the files ARE actively loaded and cause hard failures in these scripts:
- `app/run_intake.ps1`       → loads `model_settings.json` (throws if missing)
- `app/evaluate_model_output.ps1` → loads `model_monitoring.json` (throws if missing)
- `tests/run_safe_universal_smoke.ps1` → loads `pathways.json` (throws if missing)

The PRODUCTION SPEC explicitly labels all 4 as PE-01 through PE-04 priority blockers.

---

## FILE-BY-FILE ASSESSMENT

---

### 1. `C:\JeffLocal\config\model_settings.json`

**Status: NEEDED AND MISSING**

**Evidence of active use:**
- `app/run_intake.ps1` lines 18-28: loads this file with `throw "Missing model settings file"`
  if absent. Pipeline CANNOT run without it.
- `JEFFLOCAL_PRODUCTION_SPEC.md` PE-03: "Ollama model name/temperature currently hardcoded
  in PS1 scripts" — file is the intended externalisation
- `governance/FIRST_SPRINT_ASSIGNMENTS.md` PW-01: assigned as Sprint 1 task with
  acceptance criteria: `model_name, temperature, timeout_seconds, confidence_floor`

**Content structure required:**
```json
{
  "model_name": "gemma4:e2b",
  "fallback_model": "gemma4:e4b",
  "temperature": 0.1,
  "timeout_seconds": 30,
  "confidence_floor": 0.72,
  "ollama_endpoint": "http://localhost:11434",
  "max_retries": 2
}
```

**Responsible agent: Backend Agent**
Pipeline scripts are in `app/` — Backend Agent scope. This is a pure config
externalisation with no schema changes.

**Acceptance criteria:**
- File exists at `C:\JeffLocal\config\model_settings.json`
- Valid JSON (no syntax errors)
- Contains: `model_name`, `temperature`, `timeout_seconds`, `confidence_floor`,
  `ollama_endpoint`, `fallback_model`
- `confidence_floor` set to `0.72` (matches system constant)
- `model_name` is `gemma4:e2b` (matches current runtime)
- `timeout_seconds` is `30` (matches current PS1 default)
- `run_intake.ps1` runs without error after file is created
- Settings page shows "configured" for "Model settings"

---

### 2. `C:\JeffLocal\config\routing_rules.json`

**Status: NEEDED AND MISSING**

**Evidence of active use:**
- `JEFFLOCAL_PRODUCTION_SPEC.md` PE-05: "staff assignment routing logic not externalised"
- `FIRST_SPRINT_ASSIGNMENTS.md` PW-03 (2 hours estimated): "routing_rules.json defines
  staff assignment rules per pathway/priority"
- `PRODUCTION_READINESS_CHECKLIST.md` line 162: "config/routing_rules.json: Staff
  assignment rules" — listed as production gate
- `DEPLOY_NEW_PRACTICE.md` line 34: "config/routing_rules.json — update staff groups
  and queues" — referenced as per-practice onboarding file
- `AGENT_TEAM_CHARTER.md` line 264: listed as a config externalisation requirement

**Current state:** Routing logic is currently hardcoded in `app/process_queue.ps1`
and related pipeline scripts. The file is needed but not yet causing a hard throw —
it is a production readiness blocker, not a crash blocker.

**Content structure required:**
```json
{
  "version": "1.0",
  "practice_id": "churchtown",
  "default_queue": "admin",
  "priority_escalation_threshold": "urgent",
  "routes": {
    "prescription": {
      "queue": "medicines_management",
      "staff_group": "admin",
      "requires_gp": false,
      "priority_override": null
    },
    "sick_note": {
      "queue": "gp_tasks",
      "staff_group": "gp",
      "requires_gp": true,
      "priority_override": null
    },
    "referral": {
      "queue": "gp_tasks",
      "staff_group": "gp",
      "requires_gp": true,
      "priority_override": null
    },
    "test_result": {
      "queue": "clinician_review",
      "staff_group": "gp",
      "requires_gp": true,
      "priority_override": null
    },
    "appointment_redirect": {
      "queue": "reception",
      "staff_group": "admin",
      "requires_gp": false,
      "priority_override": null
    },
    "admin": {
      "queue": "admin",
      "staff_group": "admin",
      "requires_gp": false,
      "priority_override": null
    },
    "unknown": {
      "queue": "staff_review",
      "staff_group": "admin",
      "requires_gp": false,
      "priority_override": "review_required"
    },
    "needs_review": {
      "queue": "staff_review",
      "staff_group": "admin",
      "requires_gp": false,
      "priority_override": "review_required"
    }
  },
  "emergency_override": {
    "applies_to_all_routes": true,
    "queue": "999_escalation",
    "notify_gp": true
  }
}
```

**Responsible agent: Backend Agent**
Routing rules govern the pipeline (app/ scripts). This is Backend Agent territory.
No schema change required.

**Acceptance criteria:**
- File exists at `C:\JeffLocal\config\routing_rules.json`
- Valid JSON
- Contains routing entries for all 8 pathways: prescription, sick_note, referral,
  test_result, appointment_redirect, admin, unknown, needs_review
- Each route has: `queue`, `staff_group`, `requires_gp`
- `emergency_override` block present
- `practice_id` set to `"churchtown"` for sandbox
- Settings page shows "configured" for "Routing rules"

---

### 3. `C:\JeffLocal\config\pathways.json`

**Status: NEEDED AND MISSING**

**Evidence of active use:**
- `tests/run_safe_universal_smoke.ps1` line 83: `Get-Content -LiteralPath "C:\JeffLocal\config\pathways.json"` — test THROWS if file missing
- `sandbox/code/TEST_CASES.md` TC-010: "Load pathways.json, check active_pathways
  contains all 6 IDs" — release gate test
- `FIRST_SPRINT_ASSIGNMENTS.md` PW-02: "pathways.json lists all 8 active pathways
  with routing destinations"
- `JEFFLOCAL_PRODUCTION_SPEC.md` PE-04: "active pathway list hardcoded; needs
  externalised config"
- `DEPLOY_NEW_PRACTICE.md`: referenced as per-practice setup file

**Current state:** Pathway logic is hardcoded in pipeline scripts. The smoke test
will fail (throw) without this file. This is both a test blocker and production
readiness blocker.

**Content structure required (8 pathways as per architecture):**
```json
{
  "version": "1.0",
  "practice_id": "churchtown",
  "pathways": {
    "prescription": {
      "enabled": true,
      "canonical_name": "Prescription Request",
      "staff_routing_label": "Medicines Management",
      "default_priority": "routine",
      "emis_workflow": "prescription",
      "safety_notes": "Verify patient identity. Check for controlled drugs."
    },
    "sick_note": {
      "enabled": true,
      "canonical_name": "Sick Note / Fit Note",
      "staff_routing_label": "GP Tasks",
      "default_priority": "routine",
      "emis_workflow": "sick_note",
      "safety_notes": "Check prior sick notes. GP authorisation required."
    },
    "referral": {
      "enabled": true,
      "canonical_name": "Referral Request",
      "staff_routing_label": "GP Tasks",
      "default_priority": "routine",
      "emis_workflow": "referral",
      "safety_notes": "Confirm referral pathway with GP before raising."
    },
    "test_result": {
      "enabled": true,
      "canonical_name": "Test Result Enquiry",
      "staff_routing_label": "Clinician Review",
      "default_priority": "routine",
      "emis_workflow": "test_result",
      "safety_notes": "Assign to responsible clinician. Do not give results over phone."
    },
    "appointment_redirect": {
      "enabled": true,
      "canonical_name": "Appointment Request",
      "staff_routing_label": "Reception",
      "default_priority": "routine",
      "emis_workflow": "appointment_redirect",
      "safety_notes": "Check appointment availability. Redirect to duty clinician if urgent."
    },
    "admin": {
      "enabled": true,
      "canonical_name": "General Admin",
      "staff_routing_label": "Admin",
      "default_priority": "routine",
      "emis_workflow": "admin",
      "safety_notes": "Log contact in patient record. Route to appropriate team."
    },
    "unknown": {
      "enabled": true,
      "canonical_name": "Unknown / Unclassified",
      "staff_routing_label": "Staff Review",
      "default_priority": "review_required",
      "emis_workflow": "admin",
      "safety_notes": "Manual review required before routing."
    },
    "needs_review": {
      "enabled": true,
      "canonical_name": "Needs Review",
      "staff_routing_label": "Staff Review",
      "default_priority": "review_required",
      "emis_workflow": "admin",
      "safety_notes": "Staff review required. Do not auto-route."
    }
  }
}
```

**Responsible agent: Backend Agent**
Pathways define pipeline behaviour (app/ scripts). Backend Agent scope.
No schema change required. The smoke test in `tests/` is owned by Test Agent but
the config it loads is pipeline config.

**Acceptance criteria:**
- File exists at `C:\JeffLocal\config\pathways.json`
- Valid JSON
- Contains `pathways` object with all 8 keys: prescription, sick_note, referral,
  test_result, appointment_redirect, admin, unknown, needs_review
- Each pathway has: `enabled` (bool), `canonical_name`, `staff_routing_label`,
  `default_priority`, `safety_notes`
- All 8 pathways have `enabled: true`
- `tests/run_safe_universal_smoke.ps1` passes pathway structure checks (TC-010)
- Settings page shows "configured" for "Pathway configuration"

---

### 4. `C:\JeffLocal\config\model_monitoring.json`

**Status: NEEDED AND MISSING**

**Evidence of active use:**
- `app/evaluate_model_output.ps1` lines 5, 35-39: loads this file as parameter
  `$MonitoringConfigPath` — throws `"Monitoring config not found"` if absent.
  The script uses the config data in its scoring logic.
- `FIRST_SPRINT_ASSIGNMENTS.md` PW-04: "model_monitoring.json specifies:
  fallback_threshold (0.72), alert_thresholds"
- `JEFFLOCAL_PRODUCTION_SPEC.md` PE-06: "confidence floor and alert escalation
  rules not externalised"
- `sandbox/code/TEST_CASES.md` TC-012: "Load model_monitoring.json, check each
  pathway confidence value >= 0.70" — release gate test

**Current state:** `evaluate_model_output.ps1` will throw when run without this
file. The script is part of the pipeline's post-processing evaluation. This is
a hard runtime blocker for pipeline evaluation runs.

**Content structure required:**
```json
{
  "version": "1.0",
  "confidence_floor": 0.72,
  "fallback_threshold": 0.72,
  "fallback_model": "gemma4:e4b",
  "alert_thresholds": {
    "low_confidence": 0.70,
    "critical_confidence": 0.50,
    "slow_response_seconds": 25,
    "failure_rate_percent": 10
  },
  "per_pathway_thresholds": {
    "prescription": 0.72,
    "sick_note": 0.72,
    "referral": 0.72,
    "test_result": 0.72,
    "appointment_redirect": 0.70,
    "admin": 0.70,
    "unknown": 0.65,
    "needs_review": 0.65
  },
  "red_flag_keywords": [
    "chest pain",
    "difficulty breathing",
    "999",
    "emergency",
    "collapse",
    "unconscious",
    "stroke",
    "severe bleeding"
  ],
  "alert_escalation": {
    "on_confidence_below_floor": "mark_pending_review",
    "on_hard_failure": "deadletter_and_alert",
    "on_red_flag_keyword": "immediate_staff_alert"
  },
  "monitoring_log_dir": "C:\\JeffLocal\\logs\\model_monitoring"
}
```

**Responsible agent: Backend Agent**
This governs Ollama/Gemma pipeline evaluation — Backend Agent scope.
No schema change required.

**Acceptance criteria:**
- File exists at `C:\JeffLocal\config\model_monitoring.json`
- Valid JSON
- Contains `confidence_floor` (numeric, 0.72 minimum)
- Contains `fallback_threshold` (numeric, 0.72)
- Contains `red_flag_keywords` (array, non-empty)
- Contains `alert_escalation` block
- Per-pathway thresholds all >= 0.70 (TC-012 gate)
- `evaluate_model_output.ps1` loads without throw
- Settings page shows "configured" for "Monitoring thresholds"

---

## SUMMARY TABLE

| File | Status | Crash Risk | Blocker Type | Responsible Agent |
|------|--------|------------|--------------|-------------------|
| `model_settings.json` | Needed and missing | HARD CRASH in run_intake.ps1 | Pipeline cannot run | Backend Agent |
| `routing_rules.json` | Needed and missing | No crash today, production blocker | Production readiness (PE-05) | Backend Agent |
| `pathways.json` | Needed and missing | HARD CRASH in smoke tests | Test + production readiness | Backend Agent |
| `model_monitoring.json` | Needed and missing | HARD CRASH in evaluate_model_output.ps1 | Evaluation pipeline blocked | Backend Agent |

---

## DECISION LOG

**Decision 1:** All 4 files are "needed and missing" — not dead config, not references.
Each has at least one active consumer (PS1 script) that throws a hard error without it,
plus is listed as a production gap in JEFFLOCAL_PRODUCTION_SPEC.md.

**Decision 2:** All 4 files are assigned to the Backend Agent, not Database Agent.
They govern the Ollama/Gemma pipeline and routing logic in `app/` scripts. Database
Agent scope is `sandbox/db/` — schema, migrations, seed data. No database schema
changes are needed to create these config files.

**Decision 3:** Lead Agent is NOT creating these files. Per lead_CLAUDE.md: "You write
nothing yourself unless explicitly asked by the human." Task brief will be dispatched
to Backend Agent after this report is logged and Saeed reviews.

**Decision 4:** The Settings page "Missing" indicator is cosmetic-only (existence check,
no content read). The dashboard does not crash or degrade without these files. The
operational risks are in the intake pipeline and test suite, not the dashboard.

**Decision 5:** No escalation to human required at this stage — this is standard
assessment and task briefing within the Lead Agent remit. The task brief will be
included in the dispatch summary for Saeed's awareness.

---

## TASK BRIEF FOR BACKEND AGENT

**Title:** Create 4 missing pipeline config files
**Priority:** HIGH — blocks intake pipeline and smoke tests
**Files to create:**
1. `C:\JeffLocal\config\model_settings.json`
2. `C:\JeffLocal\config\routing_rules.json`
3. `C:\JeffLocal\config\pathways.json`
4. `C:\JeffLocal\config\model_monitoring.json`

**Content structure for each:** See per-file sections above.

**Rules:**
- Content must reflect sandbox/dev state (churchtown practice, gemma4:e2b model)
- All JSON must be valid (no syntax errors)
- Do NOT modify any Python files
- Do NOT modify any PowerShell scripts — only create the JSON config files
- After creating, verify: `run_intake.ps1` and `evaluate_model_output.ps1` no longer throw on startup
- Security Agent review required before any PR

**Test gates (after creation):**
- `tests/run_safe_universal_smoke.ps1` pathway checks pass (TC-010)
- `sandbox/code/TEST_CASES.md` TC-009, TC-010, TC-011, TC-012 all pass
- Settings page at `/settings` shows all 5 config files as "configured"

**Reference documents:**
- `governance/JEFFLOCAL_PRODUCTION_SPEC.md` PE-01 through PE-04
- `governance/FIRST_SPRINT_ASSIGNMENTS.md` PW-01 through PW-04
- `sandbox/code/TEST_CASES.md` TC-009 through TC-012
- This audit: `docs/reports/config_audit_2026-05-29.md`

---

*Report generated by Lead Agent, 2026-05-29. No code was written or modified.*

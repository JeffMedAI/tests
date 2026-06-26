# Tech-Debt Phases 2 & 3 — Design Spec

**Date:** 2026-06-26
**Author:** Lead Agent (Claude Code) for Saeed
**Status:** PLAN — not implemented. Each item needs Saeed approval + Security review before work starts.
**Predecessor:** Phase 1 (B1/D1/DOC1/I1–I3) complete on `sandbox` — see CHANGELOG 2026-06-26.

---

## Context

The tech-debt audit (2026-06-25) scored 13 items. Phase 1 shipped the quick, safe wins.
Phase 2 = hardening (1 week, post-go-live). Phase 3 = strategic refactor (1–2 weeks, planned window).
Two extra items were discovered during Phase 1 and folded in: the watchdog fallback bugs (Security
Agent review) and the FastAPI `on_event` deprecation (seen in test output).

Guiding rules for both phases: **TDD on every change** (the B1 fix proved its worth — the bug had
no test); **Security Agent review before any production merge**; **nothing touches the LLM/deterministic
safety split**; **one reviewable change at a time**.

---

## PHASE 2 — Hardening (target: ~1 week)

### P2.1 — Versioned, validated handoff-JSON contract  *(audit A1, Priority 21)*
**Problem:** `importer.map_handoff_to_case` reads patient-identity fields through dozens of fallback
paths (`normalized_input.patient_name` vs `patient_name` vs `patient.name`) with no schema validation.
If the upstream pipeline changes a key, identity/priority fields can silently mis-map — and these feed
the safety-critical locked fields.
**Approach:** Define a Pydantic model `HandoffEnvelope` (v1) with an explicit `schema_version` field.
Validate at the importer boundary; on failure, route the file to `failed/` with a logged reason
(do not guess). Keep the existing fallback reader only as a v0 compatibility shim, logging a warning
when it fires so we can see how often legacy shapes still arrive.
**Files:** `dashboard/app/importer.py`, new `dashboard/app/handoff_schema.py`, tests.
**Tests:** valid v1 envelope → mapped; missing/!=version → failed/ with reason; legacy v0 → shim + warning.
**Risk:** Medium — touches the path that populates identity fields. Security review mandatory.
**Effort:** 2–4 days.

### P2.2 — De-duplicate resolve logic + date parsing  *(audit C2, Priority 24)*
**Problem:** The red-flag/identity outcome-notes gate, resolved_by, and turnaround logic are duplicated
across `update_case` and `quick_action` — two safety-relevant paths that must stay in sync. Separately,
`models.py` copy-pastes the ISO-date candidate-parsing block across 3 functions.
**Approach:** Extract one `_apply_resolution(case, submitted, staff)` helper used by both endpoints;
extract `_parse_iso_flexible(value)` in models and route the 3 callers through it. Pure refactor — no
behaviour change.
**Files:** `dashboard/app/main.py`, `dashboard/app/models.py`, tests.
**Tests:** characterisation tests first (lock current resolve behaviour for red-flag/identity/normal),
then refactor and keep green.
**Risk:** Medium (safety logic) — but net safety *gain* by removing drift. Security review.
**Effort:** ~1 day.

### P2.3 — Narrow the silent exception handlers  *(audit C3, Priority 20)*
**Problem:** 41 broad/bare `except` blocks (14 in main.py) swallow errors and return defaults
(e.g. `_nav_alert_count`), hiding failures from logs.
**Approach:** Per block: catch the specific exception, log with `exc_info=True`, keep the safe fallback
where it's deliberate. No blanket rewrite — review each.
**Files:** `dashboard/app/main.py`, `importer.py`, `auth.py`.
**Tests:** where a handler guards a real failure mode, add a test that the failure is logged + handled.
**Risk:** Low. **Effort:** ~1 day.

### P2.4 — Hermetic test lane + coverage number  *(audit T1, Priority 15)*
**Problem:** Much of the suite needs live Ollama/n8n (per TESTING.md); no fast CI lane, no coverage metric,
and test temp dirs leak into the tree.
**Approach:** Add a `unit` marker lane that mocks Ollama (`ollama_clinical_summary`) and the n8n webhook,
runnable with no services. Add `pytest-cov` and record a baseline %. Point pytest basetemp fully outside
the repo.
**Files:** `dashboard/pytest.ini`, `conftest.py`, CI notes in TESTING.md.
**Risk:** Low. **Effort:** 2–4 days.

### P2.5 — Fix the watchdog disaster-recovery fallback  *(Security review N1+N2)*
**Problem:** `watchdog.ps1` fallback launches `uvicorn main:app` from `dashboard\app` — would crash on
main.py's package-relative imports; and its venv bootstrap has an ordering bug. Dead today (primary
launcher exists), but the safety net is broken if the launcher is ever lost.
**Approach:** Change to `uvicorn app.main:app` with WorkingDirectory `$RepoRoot\dashboard`; ensure venv
deps install on an existing-but-empty venv too.
**Files:** `scripts/service_control/watchdog.ps1`.
**Tests:** manual DR drill (rename `_launch_dashboard.ps1`, confirm fallback brings the dashboard up).
**Risk:** Medium (production watchdog) — Security + DevOps review. **Effort:** ~0.5 day.

### P2.6 — FastAPI `on_event` → lifespan  *(found in test warnings)*
**Problem:** `@app.on_event("startup")` (main.py:628) is deprecated; will break on a future FastAPI major.
**Approach:** Migrate to the `lifespan` context-manager API.
**Files:** `dashboard/app/main.py`. **Tests:** existing startup-path tests stay green. **Effort:** ~0.5 day.

---

## PHASE 3 — Strategic refactor (target: 1–2 weeks, dedicated window)

### P3.1 — Split `main.py` into FastAPI routers  *(audit C1 — highest raw harm: Impact 5/Risk 4)*
**Problem:** 4,770 lines, 57 routes, 171 functions in one module. Every change risks this file; safety-
sensitive handlers are buried; merge conflicts are frequent.
**Approach (incremental, low-risk):** Introduce `APIRouter` modules one domain at a time, moving routes
without changing behaviour, keeping the full suite green after each move:
`routers/auth.py`, `routers/cases.py`, `routers/staff.py`, `routers/alerts.py`, `routers/analytics.py`,
`routers/services.py`, `routers/pages.py`; shared helpers → `dependencies.py` / `services/`. `main.py`
shrinks to app construction + `include_router` calls.
**Order:** start with the lowest-risk, self-contained group (analytics) to prove the pattern, then
alerts, staff, pages; do cases/auth last (highest safety sensitivity) with Security review on each.
**Tests:** the existing 106-test suite is the safety net; run it after every router extraction. Add a
route-inventory test asserting the full URL list is unchanged.
**Risk:** Medium per step, low if incremental. Never a big-bang rewrite.
**Effort:** 1–2 weeks (can be paused/resumed between routers).

### P3.2 — Real DB migration framework  *(audit A2, Priority 18)*
**Problem:** `db.init_db()` does ad-hoc `CREATE IF NOT EXISTS` + `PRAGMA table_info` + `ALTER`. No version
table, no down-migrations, no ordering guarantees — schema drift risk across environments. Legacy
`demo_pin_hash` column lingers beside `pin_hash`.
**Approach:** Introduce a lightweight versioned-migration system — a `schema_migrations` table + ordered
migration files, or adopt Alembic. Backfill the current schema as migration 0001; convert each existing
ad-hoc ALTER into a numbered migration. Plan a separate, reviewed migration to drop `demo_pin_hash`.
**Files:** new `dashboard/app/migrations/`, `db.py`.
**Tests:** migrate-from-empty == current schema; idempotent re-run; (if added) down-migration.
**Risk:** Medium-High — runs against live patient DB. Mandatory DB backup + Security/Database review +
Saeed sign-off before running on production data.
**Effort:** 2–4 days.

---

## Sequencing & governance

1. Phase 2 first (hardening), then Phase 3 (refactor) in its own window.
2. Suggested Phase 2 order: P2.6 + P2.5 (quick, isolated) → P2.3 → P2.2 → P2.1 → P2.4.
3. Every item: TDD, Security Agent review, Saeed approval before production merge. Items touching the DB
   (P3.2) or identity mapping (P2.1) additionally require a DB backup and Database-agent review.
4. None of these change the LLM/deterministic safety boundary.

## Open questions for Saeed
- Phase 3 timing: schedule the `main.py` split for after the pilot is stable, or sooner?
- P3.2: prefer a minimal home-grown migration table, or adopt Alembic (new dependency)?
- P2.1: is the handoff-JSON producer (the pipeline) stable enough to pin a v1 schema now, or keep the
  compatibility shim longer?

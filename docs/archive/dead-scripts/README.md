# Archived dead scripts

These scripts were moved here on 2026-06-25 during the Phase 1 tech-debt
remediation. They are **dead/incorrect** and must not be used.

- `restart_flask.ps1`, `restart_flask.bat` — both run `python -m flask run`.
  The dashboard is **FastAPI on uvicorn**, not Flask. These would never have
  started the real service. The correct launcher is
  `dashboard/run_dashboard.ps1` (`uvicorn app.main:app --port 8765`), and the
  watchdog (`scripts/service_control/watchdog.ps1`) manages it in production.

Kept (not deleted) for history per the project's archive-don't-delete rule.

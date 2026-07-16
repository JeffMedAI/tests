from __future__ import annotations

import asyncio
import logging
import os
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .auth import get_session_user, purge_expired_sessions
from .consts import AUTH_PUBLIC_PATHS, AUTH_PUBLIC_PREFIXES, SESSION_COOKIE
from .db import connect, init_db
from .importer import import_handoffs
from .paths import ALERT_DIR, BASE_DIR

# Case/query domain layer (case shaping, SQL clause builders, dashboard cards,
# staff/audit helpers) lives in case_domain.py. Re-exported here (respecting
# case_domain.__all__) so routers and tests that still do `from ..main import X`
# for these names keep working during the coupling-reduction migration — new
# code should import from .case_domain / ..case_domain directly.
from .case_domain import *  # noqa: F401,F403

from .routers import alerts as alerts_router
from .routers import analytics as analytics_router
from .routers import auth as auth_router
from .routers import cases as cases_router
from .routers import n8n as n8n_router
from .routers import pages as pages_router
from .routers import staff as staff_router
from .routers import stmarks as stmarks_router
from .routers import system as system_router
from .templates_config import templates as _templates_singleton

_log = logging.getLogger(__name__)

app = FastAPI(title="JeffLocal Staff Dashboard")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = _templates_singleton
app.include_router(alerts_router.router)
app.include_router(analytics_router.router)
app.include_router(auth_router.router)
app.include_router(cases_router.router)
app.include_router(n8n_router.router)
app.include_router(pages_router.router)
app.include_router(staff_router.router)
app.include_router(stmarks_router.router)
app.include_router(system_router.router)


def _nav_alert_count() -> int:
    try:
        with connect() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM alert_events WHERE acknowledged_at IS NULL"
            ).fetchone()[0]
    except Exception:
        _log.error("_nav_alert_count: failed to query alert_events", exc_info=True)
        return 0


templates.env.globals["nav_alert_count"] = _nav_alert_count



def _is_public_path(path: str) -> bool:
    return path in AUTH_PUBLIC_PATHS or any(path.startswith(p) for p in AUTH_PUBLIC_PREFIXES)


@app.middleware("http")
async def enforce_auth(request: Request, call_next):
    if _is_public_path(request.url.path):
        return await call_next(request)
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return RedirectResponse(url=f"/login?next={quote(str(request.url.path), safe='')}", status_code=302)
    with connect() as conn:
        conn.row_factory = __import__("sqlite3").Row
        user = get_session_user(conn, token)
    if user is None:
        resp = RedirectResponse(url=f"/login?next={quote(str(request.url.path), safe='')}", status_code=302)
        resp.delete_cookie(SESSION_COOKIE)
        return resp
    response = await call_next(request)
    # Refresh cookie on every authenticated request to keep session active
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=3600, secure=True)
    return response






async def _daily_session_purge() -> None:
    """Background task: purge expired sessions once per day."""
    while True:
        try:
            with connect() as conn:
                purge_expired_sessions(conn)
        except Exception:
            pass
        await asyncio.sleep(86400)


async def _warmup_ollama() -> None:
    """Pre-load the Ollama model into RAM on startup."""
    try:
        from .importer import ollama_clinical_summary
        await ollama_clinical_summary("warm-up ping", {"call_id": "warmup", "priority": "routine"})
        logging.getLogger(__name__).info("Ollama warm-up complete")
    except Exception:
        pass  # non-fatal


_IMPORTER_INTERVAL_SECONDS: int = int(os.environ.get("JEFF_IMPORT_INTERVAL", "60"))
_importer_log = logging.getLogger("jefflocal.importer")


async def _background_importer() -> None:
    """Continuously polls outputs/handoff_json/ and imports new cases into the DB.

    Runs every JEFF_IMPORT_INTERVAL seconds (default 60). Errors are logged but
    never crash the loop — the dashboard stays up regardless of pipeline state.
    """
    await asyncio.sleep(5)  # brief delay to let startup complete
    while True:
        try:
            with connect() as conn:
                count = import_handoffs(conn)
            if count:
                _importer_log.info("Auto-importer: imported %d new case(s)", count)
        except Exception as exc:
            _importer_log.warning("Auto-importer error (non-fatal): %s", exc)
        await asyncio.sleep(_IMPORTER_INTERVAL_SECONDS)


@app.on_event("startup")
def startup() -> None:
    with connect() as conn:
        init_db(conn)
        import_handoffs(conn)
    asyncio.create_task(_daily_session_purge())
    asyncio.create_task(_warmup_ollama())
    asyncio.create_task(_background_importer())
    logging.getLogger(__name__).info(
        "Auto-importer started (interval=%ds)", _IMPORTER_INTERVAL_SECONDS
    )


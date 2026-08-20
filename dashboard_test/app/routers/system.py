"""
System / infrastructure routes — extracted from main.py.

Covers: /favicon.ico, /api/health, /api/staff-workload,
        /api/services/status, /api/services/refresh, /api/system/workload
"""
from __future__ import annotations

import http.client
import subprocess
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Body
from fastapi.responses import Response

from ..db import connect, init_db
from ..helpers import ensure_ready
from ..models import utc_now_iso
from ..observability import build_health_response

router = APIRouter()


def _service_status(name: str, status: str, url: str, details: str, checked_at: str) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "url": url,
        "details": details,
        "last_checked": checked_at,
    }


def _check_local_n8n(timeout_seconds: float = 2.0) -> dict[str, Any]:
    from ..main import LOCAL_SERVICE_URLS
    checked_at = utc_now_iso()
    try:
        conn = http.client.HTTPConnection("localhost", 5678, timeout=timeout_seconds)
        conn.request("GET", "/healthz")
        response = conn.getresponse()
        response.read(256)
        conn.close()
        return _service_status(
            "n8n",
            "online" if response.status < 500 else "unknown",
            LOCAL_SERVICE_URLS["n8n"],
            f"HTTP {response.status}",
            checked_at,
        )
    except Exception as exc:
        return _service_status(
            "n8n",
            "offline",
            LOCAL_SERVICE_URLS["n8n"],
            f"Localhost check failed: {type(exc).__name__}",
            checked_at,
        )


def _get_service_statuses() -> dict[str, Any]:
    from ..main import BASE_DIR, LOCAL_SERVICE_URLS, app
    timestamp = utc_now_iso()
    try:
        with connect() as conn:
            init_db(conn)
            conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        handoff_folder_ok = (BASE_DIR.parent / "outputs" / "handoff_json").exists()
        dashboard_ok = handoff_folder_ok
    except Exception as exc:
        dashboard_ok = False
        dashboard_detail = f"Dashboard dependency check failed: {type(exc).__name__}"
    else:
        dashboard_detail = "API healthy" if dashboard_ok else "Handoff folder missing"

    try:
        n8n_status = _check_local_n8n()
    except Exception as exc:
        n8n_status = _service_status(
            "n8n",
            "offline",
            LOCAL_SERVICE_URLS["n8n"],
            f"Localhost check failed: {type(exc).__name__}",
            timestamp,
        )

    try:
        test_endpoint_ready = any(
            getattr(route, "path", "") == "/api/n8n/test-intake-batch"
            for route in app.routes
        )
    except Exception:
        test_endpoint_ready = False

    if n8n_status["status"] == "online" and test_endpoint_ready:
        voice_status = "test_ready"
        voice_details = "Local n8n webhook path can forward to JeffLocal test intake; no live voice provider configured."
    elif test_endpoint_ready:
        voice_status = "not_configured"
        voice_details = "Live voice provider not configured; local test intake endpoint exists but n8n is offline."
    else:
        voice_status = "not_configured"
        voice_details = "Live voice provider not configured."

    return {
        "ok": True,
        "timestamp": timestamp,
        "services": {
            "dashboard": _service_status(
                "JeffLocal Dashboard",
                "online" if dashboard_ok else "unknown",
                LOCAL_SERVICE_URLS["dashboard"],
                dashboard_detail,
                timestamp,
            ),
            "n8n": n8n_status,
            "voice_agent": _service_status(
                "Voice Agent Intake",
                voice_status,
                LOCAL_SERVICE_URLS["voice_agent"],
                voice_details,
                timestamp,
            ),
        },
    }


@router.get("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)


@router.get("/api/health")
def api_health() -> dict[str, Any]:
    from ..main import BASE_DIR
    ensure_ready()
    handoff_folder = BASE_DIR.parent / "outputs" / "handoff_json"
    with connect() as conn:
        case_count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    services = {
        "dashboard": "up",
        "database": "up",
        "handoff_folder": "up" if handoff_folder.exists() else "degraded",
    }
    health = build_health_response(services=services)
    health["ok"] = True
    health["service"] = "JeffLocal"
    health["checks"] = {
        "dashboard": True,
        "database": True,
        "handoff_folder": handoff_folder.exists(),
        "case_count": case_count,
    }
    return health


@router.get("/api/staff-workload")
def api_staff_workload() -> dict[str, Any]:
    ensure_ready()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with connect() as conn:
        staff_rows = conn.execute(
            "SELECT id, display_name, username, role FROM staff_users WHERE active=1 ORDER BY display_name"
        ).fetchall()
        result = []
        for s in staff_rows:
            name = s["display_name"] or s["username"] or "Unknown"
            assigned = s["display_name"] or s["username"] or ""
            open_count = conn.execute(
                "SELECT COUNT(*) FROM cases WHERE assigned_to=? AND status NOT IN ('Resolved','Unable to Complete','Cancelled','Closed')",
                (assigned,),
            ).fetchone()[0]
            inprogress = conn.execute(
                "SELECT COUNT(*) FROM cases WHERE assigned_to=? AND status='In Progress'",
                (assigned,),
            ).fetchone()[0]
            resolved_today = conn.execute(
                "SELECT COUNT(*) FROM cases WHERE resolved_by=? AND resolved_at LIKE ?",
                (assigned, f"{today}%"),
            ).fetchone()[0]
            result.append({
                "name": name,
                "username": s["username"] or "",
                "role": s["role"],
                "open": open_count,
                "in_progress": inprogress,
                "resolved_today": resolved_today,
            })
        totals = conn.execute(
            """SELECT
                SUM(CASE WHEN status NOT IN ('Resolved','Unable to Complete','Cancelled','Closed') THEN 1 ELSE 0 END) AS open,
                SUM(CASE WHEN status='In Progress' THEN 1 ELSE 0 END) AS in_progress,
                SUM(CASE WHEN resolved_at LIKE ? THEN 1 ELSE 0 END) AS resolved_today
            FROM cases""",
            (f"{today}%",),
        ).fetchone()
    return {
        "ok": True,
        "timestamp": utc_now_iso(),
        "staff": result,
        "totals": {
            "open": totals["open"] or 0,
            "in_progress": totals["in_progress"] or 0,
            "resolved_today": totals["resolved_today"] or 0,
        },
    }


@router.get("/api/services/status")
def api_services_status() -> dict[str, Any]:
    return _get_service_statuses()


@router.post("/api/services/refresh")
def api_services_refresh(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    from ..main import ROOT_DIR, SERVICE_START_SCRIPT
    start_missing = payload.get("start_missing") is True
    actions: list[dict[str, Any]] = []
    if start_missing:
        if SERVICE_START_SCRIPT.exists():
            result = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(SERVICE_START_SCRIPT),
                ],
                cwd=str(ROOT_DIR),
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            actions.append(
                {
                    "action": "start_missing_local_services",
                    "status": "ok" if result.returncode == 0 else "failed",
                    "returncode": result.returncode,
                    "details": (result.stdout or result.stderr)[-1000:],
                }
            )
        else:
            actions.append(
                {
                    "action": "start_missing_local_services",
                    "status": "skipped",
                    "details": "Service start script not found.",
                }
            )
    else:
        actions.append(
            {
                "action": "check_only",
                "status": "ok",
                "details": "No service start attempted.",
            }
        )
    status = _get_service_statuses()
    status["actions"] = actions
    return status


@router.get("/api/system/workload")
def api_system_workload() -> dict[str, Any]:
    from ..main import get_system_workload
    ensure_ready()
    return get_system_workload()

"""
Alert routes — extracted from main.py.

Covers: /alerts, /api/alerts/recent|unacknowledged|{alert_id}/acknowledge,
        /api/n8n/alerts/log
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Body, HTTPException, Request
from fastapi.responses import RedirectResponse

from ..alert_queries import (
    alert_dedupe_key,
    alert_row_to_display,
    sanitize_alert_payload,
    write_alert_jsonl,
)
from ..audit import write_audit_event
from ..db import connect, row_to_dict
from ..helpers import (
    current_staff_from_request,
    ensure_ready,
    normalize_staff_name,
    require_staff_edit,
    staff_display,
)
from ..models import utc_now_iso
from ..templates_config import templates

router = APIRouter()


@router.post("/api/n8n/alerts/log")
def api_alert_log(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    ensure_ready()
    alert = sanitize_alert_payload(payload)
    if not alert["alert_type"]:
        raise HTTPException(status_code=400, detail="alert_type is required")
    if not alert["source_workflow"]:
        raise HTTPException(status_code=400, detail="source_workflow is required")

    dedupe_key = alert_dedupe_key(alert)
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    with connect() as conn:
        existing = conn.execute(
            """
            SELECT alert_id
            FROM alert_events
            WHERE dedupe_key = ? AND timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (dedupe_key, cutoff),
        ).fetchone()
        if existing is not None:
            return {"ok": True, "logged": False, "deduped": True, "reason": "duplicate_recent_alert"}

        timestamp = utc_now_iso()
        alert_id = f"alert-{uuid4()}"
        alert.update({"alert_id": alert_id, "timestamp": timestamp, "dedupe_key": dedupe_key})
        conn.execute(
            """
            INSERT INTO alert_events (
                alert_id, timestamp, alert_type, severity, count, message,
                first_call_id, first_patient, first_priority, source_workflow,
                dedupe_key
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert["alert_id"], alert["timestamp"], alert["alert_type"], alert["severity"],
                alert["count"], alert["message"], alert["first_call_id"], alert["first_patient"],
                alert["first_priority"], alert["source_workflow"], alert["dedupe_key"],
            ),
        )
        conn.commit()
    write_alert_jsonl(alert)
    return {"ok": True, "logged": True, "alert_id": alert_id, "timestamp": timestamp}


@router.get("/api/alerts/recent")
def api_alerts_recent(limit: int = 20) -> dict[str, Any]:
    ensure_ready()
    safe_limit = min(max(limit, 1), 100)
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT alert_id, timestamp, alert_type, severity, count, message,
                   first_call_id, first_patient, first_priority, source_workflow,
                   dedupe_key, acknowledged_at, acknowledged_by, acknowledgement_source
            FROM alert_events
            ORDER BY timestamp DESC, id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()
    return {"ok": True, "limit": safe_limit, "count": len(rows), "alerts": [alert_row_to_display(row) for row in rows]}


@router.get("/api/alerts/unacknowledged")
def api_alerts_unacknowledged(modal_only: bool = False, limit: int = 5) -> dict[str, Any]:
    ensure_ready()
    safe_limit = min(max(limit, 1), 50)
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT alert_id, timestamp, alert_type, severity, count, message,
                   first_call_id, first_patient, first_priority, source_workflow,
                   dedupe_key, acknowledged_at, acknowledged_by, acknowledgement_source
            FROM alert_events
            WHERE acknowledged_at IS NULL
            ORDER BY timestamp DESC, id DESC
            LIMIT 100
            """
        ).fetchall()
    alerts = [alert_row_to_display(row) for row in rows]
    if modal_only:
        alerts = [alert for alert in alerts if alert["modal_worthy"]]
    alerts = alerts[:safe_limit]
    return {"ok": True, "modal_only": modal_only, "count": len(alerts), "alerts": alerts}


@router.post("/api/alerts/{alert_id}/acknowledge")
def api_alert_acknowledge(alert_id: str, request: Request, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    ensure_ready()
    with connect() as conn:
        staff = current_staff_from_request(request, conn)
        require_staff_edit(staff)
        row = conn.execute("SELECT * FROM alert_events WHERE alert_id = ?", (alert_id,)).fetchone()
        alert = row_to_dict(row)
        if alert is None:
            raise HTTPException(status_code=404, detail="Alert not found")
        if alert.get("acknowledged_at"):
            return {"ok": True, "acknowledged": False, "reason": "already_acknowledged", "alert_id": alert_id}
        now = utc_now_iso()
        acknowledged_by = normalize_staff_name(payload.get("acknowledged_by") or staff_display(staff))
        conn.execute(
            """
            UPDATE alert_events
            SET acknowledged_at = ?, acknowledged_by = ?, acknowledgement_source = ?
            WHERE alert_id = ?
            """,
            (now, acknowledged_by, "dashboard_modal", alert_id),
        )
        write_audit_event(
            conn,
            call_id=alert.get("first_call_id") or alert_id,
            action="alert_acknowledged",
            edited_by=acknowledged_by,
            changed_fields=["acknowledged_at", "acknowledged_by", "acknowledgement_source"],
            old_values={"acknowledged_at": alert.get("acknowledged_at"), "acknowledged_by": alert.get("acknowledged_by")},
            new_values={"acknowledged_at": now, "acknowledged_by": acknowledged_by, "acknowledgement_source": "dashboard_modal"},
        )
    return {"ok": True, "acknowledged": True, "alert_id": alert_id, "acknowledged_at": now, "acknowledged_by": acknowledged_by}


@router.get("/alerts")
def alerts_page(request: Request, severity: str = "all", limit: int = 50) -> Any:
    ensure_ready()
    safe_limit = min(max(limit, 1), 200)
    allowed_severities = {"all", "critical", "warning", "info"}
    if severity not in allowed_severities:
        severity = "all"
    where = "1=1"
    params: list[Any] = []
    if severity != "all":
        where = "LOWER(COALESCE(severity, '')) = ?"
        params.append(severity)
    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        rows = conn.execute(
            f"""
            SELECT alert_id, timestamp, alert_type, severity, count, message,
                   first_call_id, first_patient, first_priority, source_workflow,
                   dedupe_key, acknowledged_at, acknowledged_by, acknowledgement_source
            FROM alert_events
            WHERE {where}
            ORDER BY timestamp DESC, id DESC
            LIMIT ?
            """,
            (*params, safe_limit),
        ).fetchall()
    return templates.TemplateResponse(
        request,
        "alerts.html",
        {
            "alerts": [alert_row_to_display(row) for row in rows],
            "active_severity": severity,
            "limit": safe_limit,
            "severity_options": ["all", "critical", "warning", "info"],
            "current_staff": current_staff,
            "active_nav": "alerts",
        },
    )

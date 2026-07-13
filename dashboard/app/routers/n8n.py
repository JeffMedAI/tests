"""
n8n workflow integration routes — extracted from main.py.

Covers: /api/n8n/sync, /api/n8n/red-flags, /api/n8n/overdue,
        /api/n8n/daily-summary
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from ..db import connect
from ..helpers import ensure_ready
from ..importer import import_handoffs
from ..models import utc_now_iso

router = APIRouter()


@router.post("/api/n8n/sync")
def api_sync(rawmock_only: bool = False) -> dict[str, Any]:
    ensure_ready()
    pattern = "TC-*_handoff.json" if rawmock_only else "*_handoff.json"
    with connect() as conn:
        imported = import_handoffs(conn, pattern=pattern)
    return {
        "ok": True,
        "imported": imported,
        "pattern": pattern,
        "timestamp": utc_now_iso(),
    }


@router.get("/api/n8n/red-flags")
def api_red_flags() -> dict[str, Any]:
    ensure_ready()
    from ..main import active_red_flag_clause, api_case
    red_flag_sql, red_flag_params = active_red_flag_clause()
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT call_id, patient_name, request_type, priority, red_flags_present,
                   safe_to_queue, status, call_summary
            FROM cases
            WHERE {red_flag_sql}
            ORDER BY COALESCE(call_timestamp_sort, 0) DESC, call_id ASC
            """,
            red_flag_params,
        ).fetchall()
    cases = [api_case(row) for row in rows]
    return {
        "ok": True,
        "count": len(cases),
        "cases": cases,
    }


@router.get("/api/n8n/overdue")
def api_overdue(threshold_hours: float = 24) -> dict[str, Any]:
    ensure_ready()
    from ..main import active_case_clause, api_case
    cutoff = datetime.now(timezone.utc).timestamp() - (threshold_hours * 3600)
    active_sql, active_params = active_case_clause()
    with connect() as conn:
        rows = conn.execute(
            f"""
            SELECT call_id, patient_name, request_type, priority, red_flags_present,
                   safe_to_queue, status, call_summary
            FROM cases
            WHERE ({active_sql})
              AND COALESCE(call_timestamp_sort, 0) > 0
              AND call_timestamp_sort <= ?
            ORDER BY COALESCE(call_timestamp_sort, 0) DESC, call_id ASC
            """,
            (*active_params, cutoff),
        ).fetchall()
    cases = [api_case(row) for row in rows]
    return {
        "ok": True,
        "threshold_hours": threshold_hours,
        "count": len(cases),
        "cases": cases,
    }


@router.get("/api/n8n/daily-summary")
def api_daily_summary() -> dict[str, Any]:
    ensure_ready()
    from ..main import (
        SUMMARY_REQUEST_TYPES,
        active_case_clause,
        active_identity_check_clause,
        active_red_flag_clause,
        resolved_case_clause,
    )
    with connect() as conn:
        active_sql, active_params = active_case_clause()
        resolved_sql, resolved_params = resolved_case_clause()
        red_flag_sql, red_flag_params = active_red_flag_clause()
        identity_sql, identity_params = active_identity_check_clause()
        total = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        unresolved = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE {active_sql}",
            active_params,
        ).fetchone()[0]
        resolved = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE {resolved_sql}",
            resolved_params,
        ).fetchone()[0]
        red_flags = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE {red_flag_sql}",
            red_flag_params,
        ).fetchone()[0]
        identity_issues = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE {identity_sql}",
            identity_params,
        ).fetchone()[0]
        avg_turnaround = conn.execute(
            "SELECT AVG(turnaround_minutes) FROM cases WHERE turnaround_minutes IS NOT NULL"
        ).fetchone()[0]
        request_type_rows = conn.execute(
            """
            SELECT COALESCE(request_type, 'unknown') AS request_type, COUNT(*) AS count
            FROM cases
            GROUP BY COALESCE(request_type, 'unknown')
            """
        ).fetchall()
    request_type_counts = {value: 0 for value, _label in SUMMARY_REQUEST_TYPES}
    for row in request_type_rows:
        request_type_counts[row["request_type"] or "unknown"] = row["count"]
    return {
        "ok": True,
        "timestamp": utc_now_iso(),
        "total": total,
        "unresolved": unresolved,
        "resolved": resolved,
        "red_flags": red_flags,
        "identity_issues": identity_issues,
        "avg_turnaround_minutes": 0 if avg_turnaround is None else int(avg_turnaround),
        "request_type_counts": request_type_counts,
    }

"""
Analytics and search routes — extracted from main.py.

Covers: /api/analytics/hourly-volume, /api/analytics/performance-summary,
        /api/patient-card, /api/search
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from ..db import connect
from ..helpers import current_staff_from_request, ensure_ready

router = APIRouter()


@router.get("/api/analytics/hourly-volume")
def api_hourly_volume(request: Request) -> dict[str, Any]:
    ensure_ready()
    with connect() as conn:
        staff = current_staff_from_request(request, conn)
        if staff.get("demo_fallback"):
            raise HTTPException(status_code=401, detail="Authentication required")
        rows = conn.execute(
            """
            SELECT CAST(strftime('%H', imported_at) AS INTEGER) AS hour,
                   COUNT(*) AS count
            FROM cases
            WHERE date(imported_at) = date('now')
            GROUP BY hour
            ORDER BY hour
            """
        ).fetchall()
    hours_map: dict[int, int] = {row[0]: row[1] for row in rows}
    return {
        "ok": True,
        "hours": [{"hour": h, "count": hours_map.get(h, 0)} for h in range(24)],
    }


@router.get("/api/analytics/performance-summary")
def api_performance_summary(request: Request) -> dict[str, Any]:
    ensure_ready()
    with connect() as conn:
        staff = current_staff_from_request(request, conn)
        if staff.get("demo_fallback"):
            raise HTTPException(status_code=401, detail="Authentication required")

        cases_today: int = conn.execute(
            "SELECT COUNT(*) FROM cases WHERE date(imported_at) = date('now')"
        ).fetchone()[0]

        avg_row = conn.execute(
            """
            SELECT AVG(turnaround_minutes)
            FROM cases
            WHERE date(imported_at) = date('now')
              AND turnaround_minutes IS NOT NULL
              AND turnaround_minutes > 0
            """
        ).fetchone()
        avg_resolve: float | None = round(avg_row[0], 1) if avg_row and avg_row[0] is not None else None

        red_flags_today: int = conn.execute(
            """
            SELECT COUNT(*) FROM cases
            WHERE date(imported_at) = date('now')
              AND red_flags_present = 1
            """
        ).fetchone()[0]

        one_hour_ago = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(microsecond=0).isoformat()
        throughput_row = conn.execute(
            "SELECT COUNT(*) FROM cases WHERE imported_at > ?",
            (one_hour_ago,),
        ).fetchone()
        throughput: int = throughput_row[0] if throughput_row else 0

    return {
        "ok": True,
        "cases_today": cases_today,
        "avg_resolve_minutes": avg_resolve,
        "red_flags_today": red_flags_today,
        "throughput_last_hour": throughput,
    }


@router.get("/api/patient-card")
def api_patient_card(request: Request, name: str = "") -> dict[str, Any]:
    ensure_ready()
    if not name or not name.strip():
        raise HTTPException(status_code=400, detail="name parameter required")
    with connect() as conn:
        staff = current_staff_from_request(request, conn)
        if staff.get("demo_fallback"):
            raise HTTPException(status_code=401, detail="Authentication required")
        row = conn.execute(
            """
            SELECT patient_name, dob, nhs_number,
                   (SELECT COUNT(*) FROM cases c2
                    WHERE c2.patient_name = cases.patient_name
                      AND date(c2.imported_at) = date('now')) AS cases_today
            FROM cases
            WHERE patient_name LIKE ?
            ORDER BY COALESCE(call_timestamp_sort, 0) DESC
            LIMIT 1
            """,
            (f"%{name.strip()}%",),
        ).fetchone()
    if not row:
        return {"ok": True, "name": name, "dob": None, "nhs_number_masked": None, "cases_today": 0}

    raw_nhs = row[2] or ""
    nhs_masked: str | None = None
    if raw_nhs:
        digits = "".join(c for c in raw_nhs if c.isdigit())
        nhs_masked = digits[:3] + " ***" if len(digits) >= 3 else "***"

    return {
        "ok": True,
        "name": row[0] or name,
        "dob": row[1] or None,
        "nhs_number_masked": nhs_masked,
        "cases_today": row[3] or 0,
    }


@router.get("/api/search")
def api_search(request: Request, q: str = "") -> dict[str, Any]:
    ensure_ready()
    if not q or not q.strip():
        return {"ok": True, "results": []}
    with connect() as conn:
        staff = current_staff_from_request(request, conn)
        if staff.get("demo_fallback"):
            raise HTTPException(status_code=401, detail="Authentication required")
        term = f"%{q.strip()}%"
        rows = conn.execute(
            """
            SELECT call_id, patient_name, status, priority
            FROM cases
            WHERE patient_name LIKE ?
               OR call_id       LIKE ?
            ORDER BY COALESCE(call_timestamp_sort, 0) DESC
            LIMIT 8
            """,
            (term, term),
        ).fetchall()

    results = []
    for row in rows:
        call_id, patient_name, status, priority = row
        if patient_name and q.lower() in (patient_name or "").lower():
            results.append({
                "type": "patient",
                "label": patient_name,
                "url": f"/case/{call_id}",
            })
        else:
            results.append({
                "type": "case",
                "label": f"{call_id} — {patient_name or 'Unknown'}",
                "url": f"/case/{call_id}",
            })

    return {"ok": True, "results": results}

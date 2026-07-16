"""
Dashboard page-rendering routes — extracted from main.py.

Covers: /, /requests, /patients, /reports, /settings, /import, /api/import
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Query
from fastapi.requests import Request
from fastapi.responses import RedirectResponse

from ..case_domain import (
    active_case_clause,
    attach_recent_audit_events,
    compact_workload,
    demo_data_present,
    get_call_analytics_card,
    get_kpi_cards,
    get_peak_hour,
    get_queue_status_card,
    get_recording_for_case,
    get_request_type_breakdown,
    get_staff_users,
    get_summary_cards,
    get_system_health_card,
    get_system_workload,
    get_team_activity,
    get_urgent_attention,
    make_query,
    paged_worklist_url,
    prepare_case,
    range_clause,
    resolve_date_range,
    resolved_at_range_clause,
    resolved_case_clause,
    summary_chips_for_case,
    worklist_order_clause,
    worklist_url,
)
from ..consts import DATE_RANGE_OPTIONS, LOCAL_SERVICE_URLS, REQUEST_TYPE_CHIPS, SORT_OPTIONS
from ..db import DB_PATH, connect, row_to_dict
from ..helpers import current_staff_from_request, ensure_ready
from ..importer import import_handoffs
from ..models import format_display_timestamp, format_dob_uk, utc_now_iso
from ..paths import ROOT_DIR
from ..templates_config import templates

router = APIRouter()


@router.get("/")
def index(
    request: Request,
    filter: str = "open",
    sort: str = "newest",
    q: str = "",
    request_type: str = "",
    date_range: str = Query("", alias="range"),
    page: int = 1,
    page_size: int = 20,
    notice: str = "",
    show_requests: bool = False,
) -> Any:

    from ..routers.system import _get_service_statuses, _service_status

    ensure_ready()
    if not show_requests and any(key in request.query_params for key in {"filter", "sort", "q", "request_type", "page", "page_size"}):
        target = "/requests"
        if request.url.query:
            target = f"{target}?{request.url.query}"
        return RedirectResponse(target, status_code=307)
    filters = ["all", "urgent_red_flags", "needs_review", "identity_issues", "open", "resolved", "resolved_today"]
    if filter not in filters:
        filter = "all"
    if sort not in {option["value"] for option in SORT_OPTIONS}:
        sort = "newest"
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    explicit_sort = "sort" in request.query_params
    with connect() as conn:
        date_range = resolve_date_range(date_range.strip(), conn)
        summary_cards = get_summary_cards(conn, date_range)
        kpi_cards = get_kpi_cards(conn, date_range)
        request_type_breakdown = get_request_type_breakdown(conn, date_range)
        visible_request_mix = sorted(
            [item for item in request_type_breakdown if item["count"] > 0],
            key=lambda x: x["count"], reverse=True,
        )[:8]
        current_staff = current_staff_from_request(request, conn)
        staff_users = get_staff_users(conn)
        show_demo_banner = demo_data_present(conn)
        staff_activity = get_team_activity(conn, "today")
        urgent_attention = get_urgent_attention(conn)
        queue_status_card = get_queue_status_card(conn, date_range)
        call_analytics_card = get_call_analytics_card(conn)
        range_where, range_params = range_clause(date_range)
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        staff_workload_rows = conn.execute(
            "SELECT display_name, username FROM staff_users WHERE active=1 ORDER BY display_name"
        ).fetchall()
        staff_workload_list = []
        for sw in staff_workload_rows:
            _name = sw["display_name"] or sw["username"] or "Unknown"
            _open = conn.execute(
                "SELECT COUNT(*) FROM cases WHERE assigned_to=? AND status NOT IN ('Resolved','Unable to Complete','Cancelled','Closed')",
                (_name,),
            ).fetchone()[0]
            _prog = conn.execute(
                "SELECT COUNT(*) FROM cases WHERE assigned_to=? AND status='In Progress'", (_name,)
            ).fetchone()[0]
            _done = conn.execute(
                "SELECT COUNT(*) FROM cases WHERE resolved_by=? AND resolved_at LIKE ?",
                (_name, f"{today_str}%"),
            ).fetchone()[0]
            staff_workload_list.append({"name": _name, "open": _open, "in_progress": _prog, "resolved_today": _done})
    try:
        services_status = _get_service_statuses()
    except Exception as exc:
        _ts = utc_now_iso()
        services_status = {
            "ok": True,
            "timestamp": _ts,
            "services": {
                "dashboard": _service_status("JeffLocal Dashboard", "unknown", LOCAL_SERVICE_URLS["dashboard"], f"Service status unavailable: {type(exc).__name__}", _ts),
                "n8n": _service_status("n8n", "unknown", LOCAL_SERVICE_URLS["n8n"], f"Service status unavailable: {type(exc).__name__}", _ts),
                "voice_agent": _service_status("Voice Agent Intake", "not_configured", LOCAL_SERVICE_URLS["voice_agent"], "Live voice provider not configured.", _ts),
            },
        }
    where, params = make_query(filter, sort, q.strip(), request_type.strip())
    if range_where != "1=1":
        where = f"({range_where}) AND ({where})"
        params = tuple(range_params) + params
    order_by = worklist_order_clause(sort, filter, explicit_sort)
    with connect() as conn:
        total_cases = conn.execute(f"SELECT COUNT(*) FROM cases WHERE {where}", params).fetchone()[0]
        total_pages = max(1, (total_cases + page_size - 1) // page_size)
        page = min(page, total_pages)
        offset = (page - 1) * page_size
        rows = conn.execute(
            f"""
            SELECT *
            FROM cases
            WHERE {where}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
            """,
            (*params, page_size, offset),
        ).fetchall()
        cases = [prepare_case(row_to_dict(row)) for row in rows]
        attach_recent_audit_events(conn, cases)
        for case in cases:
            case["recording"] = get_recording_for_case(conn, case["call_id"])
            case["summary_chips"] = summary_chips_for_case(case)
    try:
        workload = get_system_workload()
    except Exception:
        workload = {
            "ok": False,
            "timestamp": utc_now_iso(),
            "status": "attention_needed",
            "queue_depth": {},
            "active_processing": "not available",
            "throughput": {},
        }
    system_health = get_system_health_card(services_status, show_demo_banner)
    workload_card = compact_workload(workload)
    _filter_counts: dict[str, Any] = {
        "open":             kpi_cards[0]["value"] if kpi_cards else None,
        "urgent_red_flags": urgent_attention.get("red_flags"),
        "needs_review":     urgent_attention.get("staff_review"),
        "identity_issues":  urgent_attention.get("identity_checks"),
        "resolved_today":   kpi_cards[4]["value"] if len(kpi_cards) > 4 else None,
    }
    filter_links = [
        {
            "value": item,
            "label": item.replace("_", " "),
            "url": worklist_url(item, sort, q, request_type, date_range),
            "count": _filter_counts.get(item),
        }
        for item in filters
    ]
    request_type_links = [
        {
            "value": item,
            "label": label,
            "url": worklist_url(filter, sort, q, item, date_range),
        }
        for item, label in REQUEST_TYPE_CHIPS
    ]
    active_date_range_label = next(
        (item["label"] for item in DATE_RANGE_OPTIONS if item["value"] == date_range),
        date_range,
    )
    pagination = {
        "page": page,
        "page_size": page_size,
        "total": total_cases,
        "total_pages": total_pages,
        "start": 0 if total_cases == 0 else offset + 1,
        "end": min(offset + page_size, total_cases),
        "has_previous": page > 1,
        "has_next": page < total_pages,
        "previous_url": paged_worklist_url(filter, sort, q, request_type, date_range, max(page - 1, 1), page_size),
        "next_url": paged_worklist_url(filter, sort, q, request_type, date_range, min(page + 1, total_pages), page_size),
    }
    current_list_url = request.url.path
    if request.url.query:
        current_list_url = f"{current_list_url}?{request.url.query}"
    active_filter_label = next((item["label"] for item in filter_links if item["value"] == filter), filter.replace("_", " "))
    active_request_type_label = next((label for item, label in REQUEST_TYPE_CHIPS if item == request_type), "")
    notice_messages = {
        "case_resolved": "Case resolved. It no longer appears in the current Open filter.",
        "case_reopened": "Case reopened. It may no longer appear in the current Resolved filter.",
        "review_started": "Case moved into review.",
    }
    with connect() as conn:
        peak_hour = get_peak_hour(conn)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "cases": cases,
            "active_filter": filter,
            "active_sort": sort,
            "search_query": q,
            "active_request_type": request_type,
            "active_date_range": date_range,
            "pagination": pagination,
            "active_date_range_label": active_date_range_label,
            "date_range_options": DATE_RANGE_OPTIONS,
            "sort_options": SORT_OPTIONS,
            "filter_links": filter_links,
            "request_type_links": request_type_links,
            "all_request_types_url": worklist_url(filter, sort, q, "", date_range),
            "summary_cards": summary_cards,
            "kpi_cards": kpi_cards,
            "request_type_breakdown": request_type_breakdown,
            "visible_request_mix": visible_request_mix,
            "services_status": services_status,
            "current_staff": current_staff,
            "staff_users": staff_users,
            "show_demo_banner": show_demo_banner,
            "staff_activity": staff_activity,
            "urgent_attention": urgent_attention,
            "system_health": system_health,
            "workload": workload,
            "workload_card": workload_card,
            "queue_status_card": queue_status_card,
            "call_analytics_card": call_analytics_card,
            "staff_workload_list": staff_workload_list,
            "peak_hour": peak_hour,
            "filters": filters,
            "current_list_url": current_list_url,
            "active_filter_label": active_filter_label,
            "active_request_type_label": active_request_type_label,
            "reset_filters_url": "/requests?filter=all&sort=newest&range=all&page_size=20",
            "action_notice": notice_messages.get(notice, ""),
            "show_requests": show_requests,
            "show_dashboard_overview": not show_requests,
            "active_nav": "requests" if show_requests else "dashboard",
            "page_updated_at": utc_now_iso(),
        },
    )


@router.get("/requests")
def requests_page(
    request: Request,
    filter: str = "open",
    sort: str = "newest",
    q: str = "",
    request_type: str = "",
    date_range: str = Query("", alias="range"),
    page: int = 1,
    page_size: int = 20,
    notice: str = "",
) -> Any:
    return index(
        request=request,
        filter=filter,
        sort=sort,
        q=q,
        request_type=request_type,
        date_range=date_range,
        page=page,
        page_size=page_size,
        notice=notice,
        show_requests=True,
    )


@router.get("/patients")
def patients_page(request: Request, q: str = "") -> Any:

    ensure_ready()
    search = q.strip()
    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        staff_users = get_staff_users(conn)
        params: tuple[Any, ...] = ()
        where = "1=1"
        if search:
            like = f"%{search}%"
            where = """
                patient_name LIKE ? OR dob LIKE ? OR postcode LIKE ?
                OR emis_number LIKE ? OR nhs_number LIKE ? OR matched_patient_ref LIKE ?
                OR top_candidate_name LIKE ? OR verification_status LIKE ?
            """
            params = (like, like, like, like, like, like, like, like)
        rows = conn.execute(
            f"""
            SELECT call_id, patient_name, dob, postcode, verification_status,
                   verification_reason, matched_patient_ref, emis_number,
                   nhs_number, top_candidate_name, timestamp
            FROM cases
            WHERE {where}
            ORDER BY COALESCE(call_timestamp_sort, 0) DESC, call_id ASC
            LIMIT 80
            """,
            params,
        ).fetchall()
    patient_rows = []
    for row in rows:
        p = row_to_dict(row)
        p["dob_display"] = format_dob_uk(p.get("dob")) if p.get("dob") else "n/a"
        patient_rows.append(p)
    return templates.TemplateResponse(
        request,
        "patients.html",
        {
            "current_staff": current_staff,
            "staff_users": staff_users,
            "active_nav": "patients",
            "search_query": search,
            "patients": patient_rows,
        },
    )


@router.get("/reports")
def reports_page(request: Request, date_range: str = Query("today", alias="range")) -> Any:

    ensure_ready()
    with connect() as conn:
        date_range = resolve_date_range(date_range.strip(), conn)
        current_staff = current_staff_from_request(request, conn)
        staff_users = get_staff_users(conn)
        kpi_cards = get_kpi_cards(conn, date_range)
        request_type_breakdown = get_request_type_breakdown(conn, date_range)
        staff_activity = get_team_activity(conn, date_range)
    try:
        workload = get_system_workload()
    except Exception:
        workload = {"queue_depth": {}, "throughput": {}}
    return templates.TemplateResponse(
        request,
        "reports.html",
        {
            "current_staff": current_staff,
            "staff_users": staff_users,
            "active_nav": "reports",
            "active_date_range": date_range,
            "date_range_options": DATE_RANGE_OPTIONS,
            "kpi_cards": kpi_cards,
            "request_type_breakdown": request_type_breakdown,
            "staff_activity": staff_activity,
            "workload": workload,
        },
    )


@router.get("/settings")
def settings_page(request: Request) -> Any:

    import os as _os
    ensure_ready()
    config_files = [
        ("Model settings", ROOT_DIR / "config" / "model_settings.json"),
        ("Routing rules", ROOT_DIR / "config" / "routing_rules.json"),
        ("Google push/webhook", ROOT_DIR / "config" / "app_settings.json"),
        ("Pathway configuration", ROOT_DIR / "config" / "pathways.json"),
        ("Monitoring thresholds", ROOT_DIR / "config" / "model_monitoring.json"),
    ]
    db_path = DB_PATH
    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        staff_users = get_staff_users(conn)
        cases_total = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        active_sql, active_params = active_case_clause()
        resolved_sql, resolved_params = resolved_case_clause()
        resolved_range_where, resolved_range_params = resolved_at_range_clause("today")
        cases_open = conn.execute(f"SELECT COUNT(*) FROM cases WHERE ({active_sql})", active_params).fetchone()[0]
        cases_resolved_today = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE ({resolved_range_where}) AND ({resolved_sql})",
            (*resolved_range_params, *resolved_params),
        ).fetchone()[0]
        alerts_unacked = conn.execute(
            "SELECT COUNT(*) FROM alert_events WHERE acknowledged_at IS NULL"
        ).fetchone()[0]
        staff_active = conn.execute(
            "SELECT COUNT(*) FROM staff_users WHERE active = 1"
        ).fetchone()[0]
        last_import_row = conn.execute(
            "SELECT MAX(timestamp) FROM audit_events WHERE action = 'import'"
        ).fetchone()
        last_import_ts = format_display_timestamp(last_import_row[0]) if last_import_row and last_import_row[0] else "Never"
    db_exists = db_path.exists()
    db_writable = False
    if db_exists:
        try:
            db_writable = _os.access(str(db_path), _os.W_OK)
        except Exception:
            db_writable = False
    diagnostics = [
        {"label": "Database file", "value": "Found" if db_exists else "Missing", "state": "ok" if db_exists else "danger"},
        {"label": "Database writable", "value": "Yes" if db_writable else "No", "state": "ok" if db_writable else "warn"},
        {"label": "Last import", "value": last_import_ts, "state": "ok"},
        {"label": "Total cases", "value": str(cases_total), "state": "ok"},
        {"label": "Open cases", "value": str(cases_open), "state": "ok" if cases_open < 50 else "warn"},
        {"label": "Resolved today", "value": str(cases_resolved_today), "state": "ok"},
        {"label": "Unacknowledged alerts", "value": str(alerts_unacked), "state": "ok" if alerts_unacked == 0 else "warn"},
        {"label": "Active staff", "value": str(staff_active), "state": "ok" if staff_active > 0 else "warn"},
    ]
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "current_staff": current_staff,
            "staff_users": staff_users,
            "active_nav": "settings",
            "settings_items": [
                {
                    "label": label,
                    "path": str(path),
                    "state": "configured" if path.exists() else "missing",
                }
                for label, path in config_files
            ],
            "diagnostics": diagnostics,
        },
    )


@router.post("/import")
def import_cases() -> RedirectResponse:
    ensure_ready()
    with connect() as conn:
        import_handoffs(conn)
    return RedirectResponse("/", status_code=303)


@router.post("/api/import")
def api_import_cases() -> dict[str, Any]:
    ensure_ready()
    with connect() as conn:
        count = import_handoffs(conn)
    return {"ok": True, "imported": count, "timestamp": utc_now_iso()}

"""Cases management routes — individual and batch case operations."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from ..audit import write_audit_event
from ..consts import (
    DEFAULT_ACTION_NEEDED,
    DEFAULT_OUTCOME_NOTES,
    IDENTITY_REVIEW_STATUSES,
    LOCKED_DETAIL_FIELDS,
    LOCKED_FIELD_CATEGORIES,
    TERMINAL_CASE_STATUSES,
)
from ..case_domain import (
    attach_recording_metadata,
    batch_resolve_cases,
    build_suggested_actions,
    bulk_action_cases,
    calculate_turnaround_minutes,
    dedupe_repeated_display_sentences,
    detail_case_url,
    emis_workflow_steps,
    friendly_audit_text,
    get_recording_for_case,
    is_resolved_case,
    normalize_case_status,
    pathway_question_responses,
    prepare_case,
    return_url_with_notice,
    safe_local_return_url,
    transcript_conversation_lines,
    update_staff_fields,
)
from ..db import connect, row_to_dict
from ..helpers import current_staff_from_request, ensure_ready, require_staff_edit, staff_display
from ..models import ALLOWED_STATUSES, EDITABLE_FORM_FIELDS, FINAL_STATUSES, format_display_timestamp, utc_now_iso
from ..templates_config import templates

router = APIRouter()


@router.post("/api/cases/batch-resolve")
def api_cases_batch_resolve(request: Request, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    ensure_ready()

    call_ids = payload.get("call_ids")
    if not isinstance(call_ids, list) or not all(isinstance(call_id, str) for call_id in call_ids):
        raise HTTPException(status_code=400, detail="call_ids must be an array of strings")
    outcome_note = str(payload.get("outcome_note") or "Batch resolved after staff review in JeffLocal dashboard.").strip()
    if not outcome_note:
        raise HTTPException(status_code=400, detail="outcome_note is required")
    allow_demo_user = payload.get("allow_demo_user") is True
    with connect() as conn:
        staff = current_staff_from_request(request, conn)
        require_staff_edit(staff)
        if staff.get("demo_fallback") and not allow_demo_user:
            raise HTTPException(status_code=400, detail="Staff identity is required for batch resolve")
        staff_name = staff_display(staff)
        return batch_resolve_cases(conn, call_ids, staff_name, outcome_note)


@router.post("/api/cases/bulk-action")
def api_cases_bulk_action(request: Request, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    ensure_ready()

    call_ids = payload.get("call_ids")
    if not isinstance(call_ids, list) or not all(isinstance(call_id, str) for call_id in call_ids):
        raise HTTPException(status_code=400, detail="call_ids must be an array of strings")
    action = str(payload.get("action") or "").strip()
    note = str(payload.get("note") or DEFAULT_OUTCOME_NOTES).strip()
    allow_demo_user = payload.get("allow_demo_user") is True
    with connect() as conn:
        staff = current_staff_from_request(request, conn)
        require_staff_edit(staff)
        if staff.get("demo_fallback") and not allow_demo_user:
            raise HTTPException(status_code=400, detail="Staff identity is required for bulk actions")
        return bulk_action_cases(conn, call_ids, action, staff_display(staff), note)


@router.post("/api/calls/{call_id}/recording")
def api_call_recording(call_id: str, request: Request, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    ensure_ready()

    with connect() as conn:
        staff = current_staff_from_request(request, conn)
        require_staff_edit(staff)
        recording = attach_recording_metadata(conn, call_id, payload, staff_display(staff))
    return {"ok": True, "recording": recording}


@router.post("/api/cases/{call_id}/copy-audit")
def api_case_copy_audit(call_id: str, request: Request, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
    ensure_ready()
    action = str(payload.get("action") or "").strip()
    allowed = {"copied_patient_record_note", "copied_staff_task", "copied_ai_summary"}
    if action not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported copy audit action")
    with connect() as conn:
        staff = current_staff_from_request(request, conn)
        row = conn.execute("SELECT call_id FROM cases WHERE call_id = ?", (call_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Case not found")
        write_audit_event(
            conn,
            call_id=call_id,
            action=action,
            edited_by=staff_display(staff),
            changed_fields=[],
            old_values={},
            new_values={"copy_audit_only": True},
        )
    return {"ok": True, "audited": True, "action": action}


@router.post("/api/cases/{call_id}/action")
def api_case_action(
    request: Request,
    call_id: str,
    payload: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    """Perform a quick action (resolve/reopen/escalate/start_review) and return updated case JSON."""
    ensure_ready()

    action = str(payload.get("action") or "").strip()
    if action not in {"resolve", "reopen", "start_review", "escalate", "flag_issue"}:
        raise HTTPException(status_code=400, detail="Unsupported action")
    outcome_notes = str(payload.get("outcome_notes") or "").strip()
    resolved_by_override = str(payload.get("resolved_by") or "").strip()
    assigned_to_override = str(payload.get("assigned_to") or "").strip()
    now = utc_now_iso()

    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        require_staff_edit(current_staff)
        selected_staff_name = "" if current_staff.get("demo_fallback") else staff_display(current_staff)
        row = conn.execute("SELECT * FROM cases WHERE call_id = ?", (call_id,)).fetchone()
        case = row_to_dict(row)
        if case is None:
            raise HTTPException(status_code=404, detail="Case not found")

        updates: dict[str, Any] = {
            "last_updated": now,
            "last_edited_at": now,
            "last_edited_by": resolved_by_override or selected_staff_name,
        }

        if action == "start_review":
            updates["status"] = "In Progress"
            updates["resolved_at"] = ""
            updates["resolved_by"] = ""
            updates["turnaround_minutes"] = None
            if assigned_to_override or selected_staff_name:
                updates["assigned_to"] = assigned_to_override or selected_staff_name
            updates["action_needed"] = case.get("action_needed") or DEFAULT_ACTION_NEEDED
        elif action == "resolve":
            resolved_name = resolved_by_override or selected_staff_name
            protected_case = bool(case["red_flags_present"] or case["priority"] == "999 Emergency" or case["verification_status"] in IDENTITY_REVIEW_STATUSES)
            effective_outcome = outcome_notes or case["outcome_notes"] or ("" if protected_case else DEFAULT_OUTCOME_NOTES)
            if (case["red_flags_present"] or case["priority"] == "999 Emergency") and not effective_outcome:
                raise HTTPException(status_code=400, detail="Outcome notes are required before resolving a red-flag case.")
            if case["verification_status"] in IDENTITY_REVIEW_STATUSES and not effective_outcome:
                raise HTTPException(status_code=400, detail="Outcome notes are required before resolving an identity issue.")
            if not resolved_name:
                raise HTTPException(status_code=400, detail="Staff identity is required to resolve a case")
            updates.update({
                "status": "Resolved",
                "outcome_notes": effective_outcome,
                "resolved_by": resolved_name,
                "resolved_at": case["resolved_at"] or now,
                "turnaround_minutes": calculate_turnaround_minutes(case["timestamp"], case["resolved_at"] or now),
            })
        elif action == "reopen":
            updates.update({
                "status": "Needs Review",
                "resolved_at": "",
                "resolved_by": "",
                "turnaround_minutes": None,
            })
        elif action == "escalate":
            updates.update({
                "status": "Escalated",
                "action_needed": "Escalated for staff review",
                "resolved_at": "",
                "resolved_by": "",
                "turnaround_minutes": None,
            })
        elif action == "flag_issue":
            updates.update({
                "status": "Needs Review",
                "action_needed": "Issue flagged by staff",
                "resolved_at": "",
                "resolved_by": "",
                "turnaround_minutes": None,
            })

        update_staff_fields(conn, call_id, updates, updates.get("last_edited_by", ""), known_old=case)
        updated_row = conn.execute("SELECT * FROM cases WHERE call_id = ?", (call_id,)).fetchone()

    updated_case = prepare_case(row_to_dict(updated_row))
    _s = lambda k: str(updated_case.get(k) or "")
    return {
        "ok": True,
        "action": action,
        "call_id": call_id,
        "status": _s("status"),
        "is_resolved": bool(updated_case.get("is_resolved")),
        "primary_status_label": _s("primary_status_label"),
        "primary_status_class": _s("primary_status_class"),
        "ai_summary": _s("ai_summary"),
        "call_summary_short": _s("call_summary_short"),
        "assigned_to": _s("assigned_to"),
    }


@router.post("/api/cases/{call_id}/enrich")
async def api_case_enrich(call_id: str, request: Request) -> dict[str, Any]:
    """Re-run Ollama enrichment on an existing case and update ai_summary."""
    ensure_ready()
    from ..importer import ollama_clinical_summary
    with connect() as conn:
        require_staff_edit(current_staff_from_request(request, conn))
        row = conn.execute("SELECT * FROM cases WHERE call_id = ?", (call_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Case not found")
        case = row_to_dict(row)
    transcript = case.get("transcript") or ""
    summary = await ollama_clinical_summary(transcript, case)
    if not summary:
        return {"ok": False, "detail": "Ollama unavailable or no transcript"}
    now = utc_now_iso()
    with connect() as conn:
        conn.execute(
            "UPDATE cases SET ai_summary = ?, call_summary = ?, last_updated = ? WHERE call_id = ?",
            (summary, summary, now, call_id),
        )
        conn.commit()
    return {"ok": True, "ai_summary": summary}


@router.get("/api/cases/{call_id}")
def api_case_get(call_id: str) -> dict[str, Any]:
    """Return key case fields as JSON for the inline detail panel."""
    ensure_ready()

    with connect() as conn:
        row = conn.execute("SELECT * FROM cases WHERE call_id = ?", (call_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Case not found")
    case = prepare_case(row_to_dict(row))
    _safe_str = lambda k: str(case.get(k) or "")
    return {
        "call_id":                 _safe_str("call_id"),
        "patient_name":            _safe_str("patient_name"),
        "gender":                  _safe_str("gender"),
        "dob":                     _safe_str("dob"),
        "dob_display":             _safe_str("dob_display"),
        "age_label":               _safe_str("age_label"),
        "nhs_number":              _safe_str("nhs_number"),
        "emis_number":             _safe_str("emis_number") or _safe_str("matched_patient_ref"),
        "callback_number":         _safe_str("callback_number"),
        "callback_number_display": _safe_str("callback_number_display"),
        "postcode":                _safe_str("postcode"),
        "timestamp_display":       _safe_str("timestamp_display"),
        "time_display":            _safe_str("time_display"),
        "age_minutes":             case.get("age_minutes"),
        "age_label_short":         _safe_str("age_label_short"),
        "age_class":               _safe_str("age_class"),
        "request_type":            _safe_str("request_type"),
        "request_type_class":      _safe_str("request_type_class"),
        "request_type_label":      _safe_str("request_type_label"),
        "priority":                _safe_str("priority"),
        "red_flags_present":       bool(case.get("red_flags_present")),
        "is_emergency":            bool(case.get("is_emergency")),
        "status":                  _safe_str("status"),
        "primary_status_label":    _safe_str("primary_status_label"),
        "primary_status_class":    _safe_str("primary_status_class"),
        "assigned_to":             _safe_str("assigned_to"),
        "ai_summary":              _safe_str("ai_summary"),
        "staff_task_title":        _safe_str("staff_task_title"),
        "staff_task_body":         _safe_str("staff_task_body"),
        "patient_record_note":     _safe_str("patient_record_note"),
        "open_details":            _safe_str("open_details"),
        "is_resolved":             bool(case.get("is_resolved")),
        "requires_individual_review": bool(case.get("requires_individual_review")),
        "safe_to_queue":           bool(case.get("safe_to_queue")),
        "staff_review_required":   bool(case.get("staff_review_required")),
        "summary_chips":           case.get("summary_chips") or [],
        "call_summary_short":      _safe_str("call_summary_short"),
        "suggested_actions":       build_suggested_actions(case),
        "transcript_excerpt":      str(case.get("transcript") or "")[:400].strip(),
        "pathway_items":           pathway_question_responses(case),
        "resolved_by":             _safe_str("resolved_by"),
        "resolved_at":             _safe_str("resolved_at"),
        "resolved_at_display":     _safe_str("resolved_at_display"),
    }


@router.get("/case/{call_id}")
def case_detail(request: Request, call_id: str, return_url: str = "", error: str = "") -> Any:
    ensure_ready()

    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        row = conn.execute("SELECT * FROM cases WHERE call_id = ?", (call_id,)).fetchone()
        audit_rows = conn.execute(
            """
            SELECT timestamp, action, edited_by, changed_fields, new_values
            FROM audit_events
            WHERE call_id = ?
            ORDER BY timestamp DESC, id DESC
            LIMIT 5
            """,
            (call_id,),
        ).fetchall()
        recording = get_recording_for_case(conn, call_id)
    case_row = row_to_dict(row)
    if case_row is None:
        raise HTTPException(status_code=404, detail="Case not found")
    case = prepare_case(case_row)
    display_fields = [
        {
            "label": label,
            "value": (
                "Yes"
                if key in {"safe_to_queue", "staff_review_required", "red_flags_present"} and case.get(key)
                else "No"
                if key in {"safe_to_queue", "staff_review_required", "red_flags_present"}
                else case.get(key, "")
            ),
        }
        for label, key in LOCKED_DETAIL_FIELDS
    ]
    bool_keys = {"safe_to_queue", "staff_review_required", "red_flags_present"}
    ts_labels = {"Timestamp", "Last Updated", "Resolved At", "Last Edited At"}
    long_labels = {"Task Body", "Staff Task Body", "AI Summary", "Patient Record Note"}
    label_map = {key: label for label, key in LOCKED_DETAIL_FIELDS}
    field_lookup = {}
    for field in display_fields:
        field["value"] = format_display_timestamp(field["value"]) if field["label"] in ts_labels else field["value"]
        if field["label"] in long_labels:
            field["value"] = dedupe_repeated_display_sentences(field["value"])
        field_lookup[field["label"]] = field["value"]
    display_field_groups = []
    for cat in LOCKED_FIELD_CATEGORIES:
        rows = []
        for key in cat["fields"]:
            label = label_map.get(key, key.replace("_", " ").title())
            raw = case.get(key, "")
            if key in bool_keys:
                val = "Yes" if raw else "No"
            elif label in ts_labels:
                val = format_display_timestamp(str(raw)) if raw else ""
            elif label in long_labels:
                val = dedupe_repeated_display_sentences(str(raw)) if raw else ""
            else:
                val = str(raw) if raw not in (None, "") else ""
            rows.append({"label": label, "key": key, "value": val})
        display_field_groups.append({"title": cat["title"], "rows": rows})
    safe_return_url = safe_local_return_url(request, return_url)
    detail_error = ""
    detail_error_modal = False
    if error == "resolve_confirmation_required":
        detail_error = "Tick the confirmation box before marking this request as resolved."
    elif error == "outcome_notes_required":
        detail_error = "Outcome notes are required before resolving this case. Please add notes describing the action taken."
        detail_error_modal = True
    elif error == "resolved_by_required":
        detail_error = "Please ensure your name is set in the Resolved By field before resolving."
    return templates.TemplateResponse(
        request,
        "case_detail.html",
        {
            "case": case,
            "current_staff": current_staff,
            "display_fields": display_fields,
            "display_field_groups": display_field_groups,
            "audit_events": [
                {
                    **event_row,
                    "timestamp_display": format_display_timestamp(event_row.get("timestamp")),
                    "friendly_text": friendly_audit_text(event_row),
                }
                for event_row in [row_to_dict(event) for event in audit_rows]
            ],
            "recording": recording,
            "transcript_lines": transcript_conversation_lines(case.get("transcript")),
            "raw_transcript": case.get("transcript") or "",
            "pathway_items": pathway_question_responses(case),
            "emis_steps": emis_workflow_steps(case.get("request_type")),
            "statuses": ALLOWED_STATUSES,
            "return_url": safe_return_url,
            "detail_error": detail_error,
            "detail_error_modal": detail_error_modal,
            "active_nav": "requests",
        },
    )


@router.post("/case/{call_id}/update")
def update_case(
    request: Request,
    call_id: str,
    intent: str = Form(""),
    return_url: str = Form(""),
    status: str = Form("New"),
    assigned_to: str = Form(""),
    action_needed: str = Form(""),
    outcome_notes: str = Form(""),
    staff_action: str = Form(""),
    resolved_by: str = Form(""),
    last_edited_by: str = Form(""),
    mark_resolved: str = Form(""),
) -> RedirectResponse:
    ensure_ready()

    if status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Unsupported status")
    safe_return_url = safe_local_return_url(request, return_url)
    mark_checked = mark_resolved.lower() in {"yes", "true", "1", "on"}
    wants_resolve = intent == "resolve" or (not intent and mark_checked)
    if wants_resolve and not mark_checked:
        detail_url = detail_case_url(call_id, safe_return_url)
        separator = "&" if "?" in detail_url else "?"
        return RedirectResponse(f"{detail_url}{separator}error=resolve_confirmation_required", status_code=303)

    now = utc_now_iso()
    submitted = {
        "status": status,
        "assigned_to": assigned_to.strip(),
        "action_needed": action_needed.strip(),
        "outcome_notes": outcome_notes.strip(),
        "staff_action": staff_action.strip(),
        "resolved_by": resolved_by.strip(),
        "last_edited_by": last_edited_by.strip() or resolved_by.strip(),
    }

    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        require_staff_edit(current_staff)
        row = conn.execute("SELECT * FROM cases WHERE call_id = ?", (call_id,)).fetchone()
        old = row_to_dict(row)
        if old is None:
            raise HTTPException(status_code=404, detail="Case not found")

        selected_staff_name = "" if current_staff.get("demo_fallback") else staff_display(current_staff)
        if selected_staff_name:
            submitted["last_edited_by"] = submitted["last_edited_by"] or selected_staff_name
            if wants_resolve and mark_checked:
                submitted["resolved_by"] = submitted["resolved_by"] or selected_staff_name
        submitted["assigned_to"] = submitted["assigned_to"] or old.get("assigned_to") or selected_staff_name
        submitted["action_needed"] = submitted["action_needed"] or old.get("action_needed") or DEFAULT_ACTION_NEEDED
        needs_notes = (
            old["red_flags_present"]
            or old["priority"] == "999 Emergency"
            or old.get("verification_status") in IDENTITY_REVIEW_STATUSES
        )
        submitted["outcome_notes"] = submitted["outcome_notes"] or old.get("outcome_notes") or (
            "" if needs_notes else (DEFAULT_OUTCOME_NOTES if wants_resolve and mark_checked else "")
        )

        status_is_terminal = normalize_case_status(submitted["status"]) in TERMINAL_CASE_STATUSES
        if wants_resolve and mark_checked:
            if needs_notes and not submitted["outcome_notes"]:
                detail_url = detail_case_url(call_id, safe_return_url)
                sep = "&" if "?" in detail_url else "?"
                return RedirectResponse(f"{detail_url}{sep}error=outcome_notes_required", status_code=303)
            if not submitted["resolved_by"]:
                detail_url = detail_case_url(call_id, safe_return_url)
                sep = "&" if "?" in detail_url else "?"
                return RedirectResponse(f"{detail_url}{sep}error=resolved_by_required", status_code=303)
            if submitted["status"] not in FINAL_STATUSES:
                submitted["status"] = "Resolved"
            submitted["resolved_by"] = submitted["resolved_by"] or submitted["last_edited_by"]
            submitted["resolved_at"] = old["resolved_at"] or now
            submitted["turnaround_minutes"] = calculate_turnaround_minutes(old["timestamp"], submitted["resolved_at"])
        elif status_is_terminal:
            submitted["resolved_by"] = submitted["resolved_by"] or old.get("resolved_by") or submitted["last_edited_by"]
            submitted["resolved_at"] = old.get("resolved_at") or now
            submitted["turnaround_minutes"] = old.get("turnaround_minutes") or calculate_turnaround_minutes(old["timestamp"], submitted["resolved_at"])
        elif is_resolved_case({**old, "status": old.get("status"), "resolved_at": old.get("resolved_at")}):
            submitted["resolved_at"] = ""
            submitted["resolved_by"] = ""
            submitted["turnaround_minutes"] = None
        else:
            submitted["resolved_at"] = old["resolved_at"]
            submitted["resolved_by"] = old.get("resolved_by", submitted["resolved_by"])
            submitted["turnaround_minutes"] = old["turnaround_minutes"]

        submitted["last_updated"] = now
        submitted["last_edited_at"] = now

        allowed_updates = {key: submitted[key] for key in EDITABLE_FORM_FIELDS if key in submitted}
        allowed_updates.update(
            {
                "resolved_at": submitted["resolved_at"],
                "last_updated": submitted["last_updated"],
                "last_edited_at": submitted["last_edited_at"],
                "turnaround_minutes": submitted["turnaround_minutes"],
            }
        )

        update_staff_fields(conn, call_id, allowed_updates, allowed_updates.get("last_edited_by", ""))

    if wants_resolve and mark_checked:
        return RedirectResponse(return_url_with_notice(safe_return_url, "case_resolved"), status_code=303)
    return RedirectResponse(detail_case_url(call_id, safe_return_url), status_code=303)


@router.post("/case/{call_id}/quick_action")
def quick_action(
    request: Request,
    call_id: str,
    action: str = Form(...),
    return_url: str = Form(""),
    assigned_to: str = Form(""),
    outcome_notes: str = Form(""),
    resolved_by: str = Form(""),
    edited_by: str = Form(""),
) -> RedirectResponse:
    ensure_ready()

    now = utc_now_iso()
    safe_return_url = safe_local_return_url(request, return_url)

    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        require_staff_edit(current_staff)
        selected_staff_name = "" if current_staff.get("demo_fallback") else staff_display(current_staff)
        row = conn.execute("SELECT * FROM cases WHERE call_id = ?", (call_id,)).fetchone()
        case = row_to_dict(row)
        if case is None:
            raise HTTPException(status_code=404, detail="Case not found")

        updates: dict[str, Any] = {
            "last_updated": now,
            "last_edited_at": now,
            "last_edited_by": edited_by.strip() or resolved_by.strip() or selected_staff_name,
        }

        if action == "start_review":
            updates["status"] = "In Progress"
            updates["resolved_at"] = ""
            updates["resolved_by"] = ""
            updates["turnaround_minutes"] = None
            if assigned_to.strip() or selected_staff_name:
                updates["assigned_to"] = assigned_to.strip() or selected_staff_name
            updates["action_needed"] = case.get("action_needed") or DEFAULT_ACTION_NEEDED
        elif action == "resolve":
            resolved_name = resolved_by.strip() or selected_staff_name
            protected_case = bool(case["red_flags_present"] or case["priority"] == "999 Emergency" or case["verification_status"] in IDENTITY_REVIEW_STATUSES)
            effective_outcome = outcome_notes.strip() or case["outcome_notes"] or ("" if protected_case else DEFAULT_OUTCOME_NOTES)
            if (case["red_flags_present"] or case["priority"] == "999 Emergency") and not effective_outcome:
                raise HTTPException(status_code=400, detail="Outcome notes are required before resolving a red-flag case.")
            if case["verification_status"] in IDENTITY_REVIEW_STATUSES and not effective_outcome:
                raise HTTPException(status_code=400, detail="Outcome notes are required before resolving an identity issue.")
            if not resolved_name:
                raise HTTPException(status_code=400, detail="Resolved By is required before resolving a case")
            updates.update(
                {
                    "status": "Resolved",
                    "outcome_notes": effective_outcome,
                    "resolved_by": resolved_name,
                    "resolved_at": case["resolved_at"] or now,
                    "turnaround_minutes": calculate_turnaround_minutes(case["timestamp"], case["resolved_at"] or now),
                }
            )
        elif action == "reopen":
            updates.update(
                {
                    "status": "Needs Review",
                    "resolved_at": "",
                    "resolved_by": "",
                    "turnaround_minutes": None,
                }
            )
        elif action == "escalate":
            updates.update(
                {
                    "status": "Escalated",
                    "action_needed": "Escalated for staff review",
                    "resolved_at": "",
                    "resolved_by": "",
                    "turnaround_minutes": None,
                }
            )
        elif action == "flag_issue":
            updates.update(
                {
                    "status": "Needs Review",
                    "action_needed": "Issue flagged by staff",
                    "resolved_at": "",
                    "resolved_by": "",
                    "turnaround_minutes": None,
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported quick action")

        update_staff_fields(conn, call_id, updates, updates.get("last_edited_by", ""))
        if action == "reopen":
            write_audit_event(
                conn,
                call_id=call_id,
                action="case_reopened",
                edited_by=updates.get("last_edited_by", ""),
                changed_fields=["status", "resolved_at", "resolved_by", "turnaround_minutes"],
                old_values={
                    "status": case.get("status"),
                    "resolved_at": case.get("resolved_at"),
                    "resolved_by": case.get("resolved_by"),
                },
                new_values={"status": "Needs Review", "resolved_at": "", "resolved_by": ""},
            )

    notice = ""
    if action == "resolve":
        notice = "case_resolved"
    elif action == "reopen":
        notice = "case_reopened"
    elif action == "start_review":
        notice = "review_started"
    return RedirectResponse(return_url_with_notice(safe_return_url, notice), status_code=303)

from __future__ import annotations

import json
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import parse_call_timestamp_sort, utc_now_iso


ROOT_DIR = Path(__file__).resolve().parents[2]
HANDOFF_DIR = ROOT_DIR / "outputs" / "handoff_json"
OLLAMA_RAW_DIR = ROOT_DIR / "outputs" / "ollama_raw"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma4:e2b"
OLLAMA_TIMEOUT_SECONDS = 20

STAFF_PRESERVED_FIELDS = (
    "status",
    "assigned_to",
    "outcome_notes",
    "staff_action",
    "resolved_at",
    "resolved_by",
    "last_edited_at",
    "last_edited_by",
    "turnaround_minutes",
)

FALLBACK_TASK_TITLE = "Processing output unavailable - staff review required"
FALLBACK_TASK_BODY = "AI-generated task output was unavailable or invalid. Staff must review the transcript and structured call data."
FALLBACK_SUMMARY = "AI summary unavailable - staff review required."
URGENT_COPY_FOOTER = "Urgent/red-flag case: follow local urgent escalation protocol. Do not rely on copied note alone."


def nested_get(data: dict[str, Any], path: str, default: Any = "") -> Any:
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current if current is not None else default


def first_value(data: dict[str, Any], paths: list[str], default: Any = "") -> Any:
    for path in paths:
        value = nested_get(data, path, "")
        if value not in ("", None, []):
            return value
    return default


def as_int(value: Any) -> int | None:
    if value in ("", None):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def as_bool_int(value: Any) -> int:
    if isinstance(value, bool):
        return 1 if value else 0
    return 1 if str(value).strip().lower() in {"true", "1", "yes", "y"} else 0


def clean_text(value: Any) -> str:
    if value in ("", None, []):
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return " ".join(str(value).strip().split())


def transcript_from_payload(data: dict[str, Any]) -> str:
    transcript = clean_text(first_value(data, ["raw_transcript", "transcript", "transcript.text"], ""))
    if transcript:
        return transcript
    conversation = first_value(data, ["conversation", "messages", "turns"], [])
    if not isinstance(conversation, list):
        return ""
    lines: list[str] = []
    for turn in conversation:
        if not isinstance(turn, dict):
            continue
        speaker = clean_text(first_value(turn, ["speaker", "role"], "caller"))
        text = clean_text(first_value(turn, ["text", "utterance", "content"], ""))
        if text:
            lines.append(f"{speaker}: {text}")
    return "\n".join(lines)


def short_excerpt(value: str, limit: int = 360) -> str:
    text = clean_text(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def value_or_missing(value: Any) -> str:
    return clean_text(value) or "not provided"


def safe_label(value: Any) -> str:
    return "Safe to queue" if as_bool_int(value) else "Not safe to queue"


def review_label(value: Any) -> str:
    return "Staff review required" if as_bool_int(value) else "No staff review flag"


def identifier_for_patient_record(case: dict[str, Any]) -> str:
    emis = clean_text(case.get("emis_number") or case.get("matched_patient_ref"))
    nhs = clean_text(case.get("nhs_number"))
    patient_name = clean_text(case.get("patient_name"))
    if emis:
        return f"EMIS: {emis}"
    if nhs:
        return f"NHS: {nhs}"
    if patient_name:
        return f"Patient: {patient_name}"
    return "Patient identifier unavailable - verify patient before documenting."


def identifier_for_safe_staff_copy(case: dict[str, Any]) -> str:
    emis = clean_text(case.get("emis_number") or case.get("matched_patient_ref"))
    nhs = clean_text(case.get("nhs_number"))
    lines = [f"EMIS: {emis or 'not available'}", f"NHS: {nhs or 'not available'}"]
    if not emis and not nhs:
        lines.append("Patient identifier unavailable - verify patient before documenting.")
    return "\n".join(lines)


def build_patient_record_note(data: dict[str, Any], case: dict[str, Any], stated_request: str, action_needed: str) -> str:
    existing_note = clean_text(first_value(data, ["patient_record_note"], ""))
    if existing_note and "AI-assisted note prepared from voice-agent transcript" not in existing_note and "dob" not in existing_note.lower():
        return existing_note
    transcript = clean_text(case.get("transcript", ""))
    pathway_response = value_or_missing(first_value(data, ["pathway_response", "pathway.response", "pathway.advice", "signposting.advice"], ""))
    identifier = identifier_for_patient_record(case)
    callback = value_or_missing(case.get("callback_number"))
    verification = value_or_missing(case.get("verification_status"))
    priority = value_or_missing(case.get("priority"))
    safety = "Red-flag symptoms were identified from the transcript." if case.get("red_flags_present") else "No red-flag symptoms were identified from the transcript."
    queue_status = "safe to queue" if case.get("safe_to_queue") else "not safe to queue"
    context = short_excerpt(transcript, 260) or stated_request
    note = (
        f"{identifier}. The caller requested {stated_request}. "
        f"Relevant transcript context: {context}. "
        f"Callback number provided: {callback}. "
        f"Identity verification was {verification}. "
        f"{safety} The request was assessed as {priority} and {queue_status}. "
    )
    if pathway_response != "not provided":
        note += f"Pathway response/advice recorded: {pathway_response}. "
    note += f"Action: {action_needed}"
    if case.get("red_flags_present") or case.get("priority") == "999 Emergency":
        note += f" {URGENT_COPY_FOOTER}"
    return note


def build_processed_outputs(data: dict[str, Any], case: dict[str, Any]) -> tuple[str, str, str, str, str]:
    existing_title = clean_text(first_value(data, ["staff_task_title", "task_title"], ""))
    existing_task = clean_text(first_value(data, ["staff_task_body", "task_body", "staff_task", "staff_task_body"], ""))
    existing_summary = clean_text(first_value(data, ["ai_summary", "ai_assisted_summary", "call_summary", "transcript_summary"], ""))
    existing_action = clean_text(first_value(data, ["action_needed"], ""))
    transcript = clean_text(case.get("transcript", ""))
    explicit_request_detail = first_value(
        data,
        [
            "stated_request",
            "request_details.stated_request",
            "request_details.medication",
            "request_details.item",
            "request_details.reason",
            "requested_item",
            "medication",
        ],
        "",
    )
    if not any([existing_task, existing_summary, transcript, clean_text(explicit_request_detail)]):
        action_needed = existing_action or "Review and process according to local workflow."
        return "", "", "", build_patient_record_note(data, case, "not provided", action_needed), action_needed
    stated_request = value_or_missing(
        first_value(
            data,
            [
                "stated_request",
                "request_details.stated_request",
                "request_details.medication",
                "request_details.item",
                "request_details.reason",
                "requested_item",
                "medication",
            ],
            short_excerpt(existing_summary or transcript, 220),
        )
    )
    request_type = value_or_missing(case.get("request_type"))
    callback = value_or_missing(case.get("callback_number"))
    verification = value_or_missing(case.get("verification_status"))
    priority = value_or_missing(case.get("priority"))
    safety = "Red flags present" if case.get("red_flags_present") else "No red flags recorded"
    queue_status = safe_label(case.get("safe_to_queue"))
    review_status = review_label(case.get("staff_review_required"))
    action_needed = existing_action or (
        "Urgent staff review and local emergency escalation follow-up required."
        if case.get("red_flags_present") or case.get("priority") == "999 Emergency"
        else "Review and process according to local workflow."
    )
    urgent_footer = (
        "\nUrgent escalation: 999/A&E pathway advised where recorded. Follow local urgent escalation protocol."
        if case.get("red_flags_present") or case.get("priority") == "999 Emergency"
        else ""
    )
    task_title = existing_title or (
        "Possible emergency - chest pain and breathlessness"
        if case.get("red_flags_present") or case.get("priority") == "999 Emergency"
        else f"{request_type.replace('_', ' ').title()} request - staff action required"
    )
    task_body = existing_task or "\n".join(
        [
            f"Request type: {request_type}",
            f"Stated request: {stated_request}",
            f"Callback: {callback}",
            f"Verification status: {verification}",
            f"Priority: {priority}",
            f"Safety status: {safety}",
            f"Queue status: {queue_status}",
            f"Review status: {review_status}",
            f"Action needed: {action_needed}",
        ]
    ) + urgent_footer
    summary = existing_summary or "\n".join(
        [
            f"Caller asked for: {stated_request}",
            f"Important context: {short_excerpt(transcript, 420) or 'not provided'}",
            f"Identity and verification: {verification}",
            f"Callback status: {callback}",
            f"Safety and routing outcome: {priority}; {safety}; {queue_status}; {review_status}.",
            f"Staff action needed: {action_needed}",
        ]
    )
    patient_record_note = build_patient_record_note(data, case, stated_request, action_needed)
    return task_title, task_body, summary, patient_record_note, action_needed


def ollama_clinical_summary(transcript: str, case_ctx: dict[str, Any]) -> str | None:
    """Call local Ollama to generate a clinical AI summary. Returns string or None on failure."""
    if not transcript.strip():
        return None
    priority = str(case_ctx.get("priority") or "routine")
    red_flag = bool(case_ctx.get("red_flags_present"))
    request_type = str(case_ctx.get("request_type") or "").replace("_", " ")
    patient_name = str(case_ctx.get("patient_name") or "the patient")
    flag_note = " RED FLAGS DETECTED — treat as urgent." if red_flag else ""
    prompt = (
        f"You are a clinical assistant for a GP practice reception dashboard.{flag_note}\n"
        f"Patient: {patient_name}. Request type: {request_type}. Priority: {priority}.\n"
        f"Call transcript:\n{transcript[:1200]}\n\n"
        "Write a 2-3 sentence clinical summary for the staff dashboard. "
        "Be concise, factual, and use plain English. Do not repeat the patient name unnecessarily. "
        "Focus on what the patient reported and what action is needed."
    )
    payload = json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}).encode()
    try:
        req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_SECONDS) as resp:
            raw = resp.read().decode()
        result = json.loads(raw)
        summary = str(result.get("response") or "").strip()
        if summary:
            OLLAMA_RAW_DIR.mkdir(parents=True, exist_ok=True)
            ts = utc_now_iso().replace(":", "").replace("-", "")[:15]
            call_id = str(case_ctx.get("call_id") or "unknown")
            (OLLAMA_RAW_DIR / f"{ts}_{call_id}.json").write_text(
                json.dumps({"call_id": call_id, "model": OLLAMA_MODEL, "summary": summary, "prompt": prompt}, ensure_ascii=False),
                encoding="utf-8",
            )
        return summary or None
    except Exception:
        return None


def map_handoff_to_case(data: dict[str, Any], source_path: Path | None = None) -> dict[str, Any]:
    call_id = str(first_value(data, ["call_id"], "")).strip()
    timestamp = str(first_value(data, ["call_timestamp", "timestamp", "timestamp_utc"], "")).strip()
    priority = str(first_value(data, ["priority"], "routine")).strip()
    staff_review_required = as_bool_int(first_value(data, ["staff_review_required"], False))
    red_flags_present = as_bool_int(first_value(data, ["red_flags_present"], False))

    status = str(first_value(data, ["status"], "")).strip()
    if not status:
        if red_flags_present:
            status = "Urgent Review"
        elif staff_review_required:
            status = "Needs Review"
        else:
            status = "New"

    case = {
        "call_id": call_id,
        "open_details": call_id,
        "timestamp": timestamp,
        "call_timestamp_sort": parse_call_timestamp_sort(timestamp),
        "request_type": first_value(data, ["request_type", "normalized_input.request_type"], ""),
        "patient_name": first_value(data, ["normalized_input.patient_name", "patient_name", "patient.name"], ""),
        "dob": first_value(data, ["normalized_input.dob", "dob", "patient.dob"], ""),
        "postcode": first_value(data, ["normalized_input.postcode", "postcode", "patient.postcode"], ""),
        "gender": first_value(data, ["normalized_input.gender", "gender", "patient.gender"], ""),
        "age": as_int(first_value(data, ["normalized_input.age", "age", "patient.age"], None)),
        "callback_number": first_value(data, ["normalized_input.callback_number", "callback_number", "patient.callback_number", "callback.number"], ""),
        "verification_status": first_value(data, ["verification_status"], ""),
        "verification_reason": first_value(data, ["verification_reason"], ""),
        "matched_patient_ref": first_value(data, ["matched_patient_ref"], ""),
        "emis_number": first_value(data, ["matched_emis_number", "matched_patient_ref"], ""),
        "nhs_number": first_value(data, ["matched_nhs_number"], ""),
        "top_candidate_name": first_value(data, ["top_candidate_name"], ""),
        "priority": priority,
        "safe_to_queue": as_bool_int(first_value(data, ["safe_to_queue"], False)),
        "task_title": "",
        "task_body": "",
        "staff_task_title": "",
        "staff_task_body": "",
        "transcript": transcript_from_payload(data),
        "call_summary": "",
        "ai_summary": "",
        "patient_record_note": "",
        "call_duration_seconds": as_int(first_value(data, ["call_duration_seconds", "voice_agent.call_duration_seconds"], None)),
        "caller_sentiment": first_value(data, ["caller_sentiment", "voice_agent.caller_sentiment"], ""),
        "caller_difficulty": first_value(data, ["caller_difficulty", "voice_agent.caller_difficulty"], ""),
        "transcript_quality": first_value(data, ["transcript_quality", "transcript_quality_flag", "voice_agent.transcript_quality", "confidence.transcript_quality"], ""),
        "handoff_confidence": str(first_value(data, ["handoff_confidence", "confidence.handoff"], "")),
        "extraction_confidence": str(first_value(data, ["extraction_confidence", "confidence.extraction"], "")),
        "staff_review_required": staff_review_required,
        "red_flags_present": red_flags_present,
        "status": status,
        "assigned_to": first_value(data, ["assigned_to"], ""),
        "action_needed": "",
        "outcome_notes": first_value(data, ["outcome_notes"], ""),
        "staff_action": first_value(data, ["staff_action"], ""),
        "resolved_at": first_value(data, ["resolved_at"], ""),
        "resolved_by": first_value(data, ["resolved_by"], ""),
        "last_updated": first_value(data, ["last_updated", "last_edited_at"], utc_now_iso()),
        "last_edited_at": first_value(data, ["last_edited_at"], ""),
        "last_edited_by": first_value(data, ["last_edited_by"], ""),
        "turnaround_minutes": as_int(first_value(data, ["turnaround_minutes"], None)),
        "source_path": str(source_path) if source_path else "",
        "source_file_mtime": (
            utc_now_iso()
            if source_path is None
            else datetime.fromtimestamp(source_path.stat().st_mtime, tz=timezone.utc).isoformat()
        ),
        "imported_at": utc_now_iso(),
    }
    task_title, task_body, call_summary, patient_record_note, action_needed = build_processed_outputs(data, case)
    if not (task_title and task_body and call_summary and patient_record_note):
        if not task_title:
            task_title = FALLBACK_TASK_TITLE
        if not task_body:
            task_body = FALLBACK_TASK_BODY
        if not call_summary:
            call_summary = FALLBACK_SUMMARY
        if not patient_record_note:
            patient_record_note = build_patient_record_note(data, case, "not provided", action_needed or "Staff review required.")
        case["staff_review_required"] = 1
        if case.get("status") in {"", "New"}:
            case["status"] = "Needs Review"
    case["task_title"] = task_title
    case["task_body"] = task_body
    case["staff_task_title"] = task_title
    case["staff_task_body"] = task_body
    case["call_summary"] = call_summary
    case["ai_summary"] = call_summary
    case["patient_record_note"] = patient_record_note
    case["action_needed"] = action_needed
    return case


def upsert_case(conn: sqlite3.Connection, case: dict[str, Any]) -> None:
    if not case["call_id"]:
        raise ValueError("Cannot import handoff without call_id")

    existing = conn.execute(
        "SELECT * FROM cases WHERE call_id = ?",
        (case["call_id"],),
    ).fetchone()
    if existing is not None:
        staff_edited = bool(existing["last_edited_at"] or existing["last_edited_by"])
        for staff_field in STAFF_PRESERVED_FIELDS:
            case[staff_field] = existing[staff_field]
        if staff_edited:
            case["action_needed"] = existing["action_needed"]
            case["last_updated"] = existing["last_updated"]

    columns = list(case.keys())
    placeholders = ", ".join(["?"] * len(columns))
    update_clause = ", ".join([f"{column}=excluded.{column}" for column in columns if column != "call_id"])
    sql = f"""
        INSERT INTO cases ({", ".join(columns)})
        VALUES ({placeholders})
        ON CONFLICT(call_id) DO UPDATE SET {update_clause}
    """
    conn.execute(sql, [case[column] for column in columns])
    conn.commit()


def import_handoffs(
    conn: sqlite3.Connection,
    handoff_dir: Path | None = None,
    pattern: str = "*_handoff.json",
) -> int:
    source_dir = handoff_dir or HANDOFF_DIR
    count = 0
    for path in sorted(source_dir.glob(pattern)):
        with path.open("r", encoding="utf-8-sig") as handle:
            data = json.load(handle)
        upsert_case(conn, map_handoff_to_case(data, path))
        count += 1
    return count

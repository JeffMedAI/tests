from __future__ import annotations

from datetime import datetime, timezone


ALLOWED_STATUSES = [
    "New",
    "Needs Review",
    "Urgent Review",
    "In Progress",
    "Waiting for Patient",
    "Waiting for GP",
    "Resolved",
    "Escalated",
    "Unable to Complete",
]

FINAL_STATUSES = {"Resolved", "Escalated", "Unable to Complete"}

LOCKED_FIELDS = [
    "open_details",
    "timestamp",
    "call_id",
    "request_type",
    "patient_name",
    "dob",
    "postcode",
    "gender",
    "age",
    "callback_number",
    "verification_status",
    "verification_reason",
    "matched_patient_ref",
    "emis_number",
    "nhs_number",
    "top_candidate_name",
    "priority",
    "safe_to_queue",
    "task_title",
    "task_body",
    "staff_task_title",
    "staff_task_body",
    "transcript",
    "call_summary",
    "ai_summary",
    "patient_record_note",
    "call_duration_seconds",
    "caller_sentiment",
    "caller_difficulty",
    "transcript_quality",
    "handoff_confidence",
    "extraction_confidence",
    "staff_review_required",
    "red_flags_present",
]

STAFF_FIELDS = [
    "status",
    "assigned_to",
    "action_needed",
    "outcome_notes",
    "staff_action",
    "resolved_at",
    "resolved_by",
    "last_updated",
    "last_edited_at",
    "last_edited_by",
    "turnaround_minutes",
]

EDITABLE_FORM_FIELDS = [
    "status",
    "assigned_to",
    "action_needed",
    "outcome_notes",
    "staff_action",
    "resolved_by",
    "last_edited_by",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_call_timestamp_sort(value: object) -> float:
    if value in ("", None):
        return 0.0

    text = str(value).strip()
    candidates = [
        text,
        text.replace("Z", "+00:00"),
        text.replace(" ", "T"),
        text.replace(" ", "T").replace("Z", "+00:00"),
    ]
    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.timestamp()
        except ValueError:
            continue

    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
        try:
            parsed = datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
            return parsed.timestamp()
        except ValueError:
            continue

    return 0.0


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def format_display_timestamp(value: object) -> str:
    if value in ("", None):
        return ""

    text = str(value).strip()
    candidates = [
        text,
        text.replace("Z", "+00:00"),
        text.replace(" ", "T"),
        text.replace(" ", "T").replace("Z", "+00:00"),
    ]
    parsed = None
    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
            break
        except ValueError:
            continue

    if parsed is None:
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"):
            try:
                parsed = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue

    if parsed is None:
        return text

    return parsed.strftime("%d-%m-%Y T %H.%M")

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

    return parsed.strftime("%d-%m-%Y T %H:%M")


def format_dob_uk(value: object) -> str:
    """Format DOB to NHS/UK standard DD/MM/YYYY format."""
    if value in ("", None):
        return ""

    text = str(value).strip()
    if not text:
        return ""

    # Try to parse common formats
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
        for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                parsed = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue

    if parsed is None:
        return text

    return parsed.strftime("%d/%m/%Y")


def format_phone_uk(value: object) -> str:
    """Format UK phone number to standard format: 07XXX XXXXXX or +44 XXXX XXXXXX."""
    if value in ("", None):
        return ""

    text = str(value).strip()
    if not text:
        return ""

    # Remove common formatting characters
    digits = ''.join(filter(str.isdigit, text))

    if not digits:
        return text

    # UK phone numbers
    if len(digits) == 10 and digits.startswith('7'):
        # 07XXXXXXXXX format
        return f"0{digits[0]} {digits[1:5]} {digits[5:]}"
    elif len(digits) == 11 and digits.startswith('07'):
        # 07XXXXXXXXXX format
        return f"{digits[:4]} {digits[4:7]} {digits[7:]}"
    elif len(digits) == 12 and digits.startswith('447'):
        # +447XXXXXXXXX format
        return f"+44 {digits[2:5]} {digits[5:8]} {digits[8:]}"

    # Return original if can't parse
    return text


def format_turnaround_time(value: object) -> str:
    """Format turnaround time in minutes to human-readable format (e.g., '2h 15m', '45 mins')."""
    if value in ("", None):
        return ""

    try:
        minutes = int(str(value).strip())
    except (ValueError, TypeError):
        return ""

    if minutes <= 0:
        return ""

    if minutes < 60:
        return f"{minutes} min{'s' if minutes != 1 else ''}"

    hours = minutes // 60
    mins = minutes % 60

    if mins == 0:
        return f"{hours}h"

    return f"{hours}h {mins}m"

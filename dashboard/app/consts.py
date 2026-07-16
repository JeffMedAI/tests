"""
Dashboard constants — extracted from main.py.

Contains only pure literals with no dependency on __file__, env vars, or runtime
state. Anything that depends on BASE_DIR / ROOT_DIR stays in main.py.
"""

LOCKED_DETAIL_FIELDS: list[tuple[str, str]] = [
    ("Open Details", "open_details"),
    ("Timestamp", "timestamp"),
    ("Last Updated", "last_updated"),
    ("Call ID", "call_id"),
    ("Request Type", "request_type"),
    ("Patient Name", "patient_name"),
    ("DOB", "dob"),
    ("Postcode", "postcode"),
    ("Gender", "gender"),
    ("Age", "age"),
    ("Callback Number", "callback_number"),
    ("Verification Status", "verification_status"),
    ("Verification Reason", "verification_reason"),
    ("Matched Patient Ref", "matched_patient_ref"),
    ("EMIS Number", "emis_number"),
    ("NHS Number", "nhs_number"),
    ("Top Candidate Name", "top_candidate_name"),
    ("Priority", "priority"),
    ("Safe To Queue", "safe_to_queue"),
    ("Task Title", "task_title"),
    ("Task Body", "task_body"),
    ("Staff Task Title", "staff_task_title"),
    ("Staff Task Body", "staff_task_body"),
    ("Call Summary", "call_summary"),
    ("AI Summary", "ai_summary"),
    ("Patient Record Note", "patient_record_note"),
    ("Call Duration Seconds", "call_duration_seconds"),
    ("Caller Sentiment", "caller_sentiment"),
    ("Caller Difficulty", "caller_difficulty"),
    ("Transcript Quality", "transcript_quality"),
    ("Handoff Confidence", "handoff_confidence"),
    ("Extraction Confidence", "extraction_confidence"),
    ("Staff Review Required", "staff_review_required"),
    ("Red Flags Present", "red_flags_present"),
    ("Resolved At", "resolved_at"),
    ("Last Edited At", "last_edited_at"),
    ("Turnaround Minutes", "turnaround_minutes"),
]

LOCKED_FIELD_CATEGORIES: list[dict] = [
    {
        "title": "Call Details",
        "fields": ["call_id", "timestamp", "last_updated", "call_duration_seconds", "open_details"],
    },
    {
        "title": "Patient Identity",
        "fields": ["patient_name", "dob", "age", "gender", "postcode", "callback_number"],
    },
    {
        "title": "Verification & Matching",
        "fields": ["verification_status", "verification_reason", "matched_patient_ref", "emis_number", "nhs_number", "top_candidate_name"],
    },
    {
        "title": "Request & Routing",
        "fields": ["request_type", "priority", "safe_to_queue", "staff_review_required", "red_flags_present"],
    },
    {
        "title": "Task Content",
        "fields": ["task_title", "task_body", "staff_task_title", "staff_task_body"],
    },
    {
        "title": "AI & Quality Signals",
        "fields": ["ai_summary", "call_summary", "patient_record_note", "caller_sentiment", "caller_difficulty", "transcript_quality", "handoff_confidence", "extraction_confidence"],
    },
    {
        "title": "Audit & Timing",
        "fields": ["resolved_at", "last_edited_at", "turnaround_minutes"],
    },
]

SORT_OPTIONS: list[dict] = [
    {"value": "newest", "label": "Newest first"},
    {"value": "oldest", "label": "Oldest first"},
    {"value": "priority", "label": "Priority"},
    {"value": "unresolved", "label": "Unresolved first"},
]

RESOLVED_STATUSES: tuple[str, ...] = ("Resolved", "Unable to Complete")

TERMINAL_CASE_STATUSES: tuple[str, ...] = (
    "resolved",
    "closed",
    "completed",
    "complete",
    "cancelled",
    "canceled",
    "archived",
    "duplicate",
    "dismissed",
    "unable to complete",
)

STAFF_REVIEW_STATUS_NAMES: tuple[str, ...] = ("staff review", "needs review", "urgent review", "escalated")
IN_PROGRESS_STATUS_NAMES: tuple[str, ...] = ("in progress", "active processing")

IDENTITY_REVIEW_STATUSES: set[str] = {
    "possible_match", "possible_match_weak", "no_match", "insufficient_data", "needs_review",
    "partial", "unverified", "unable to verify", "failed",
}

SAFE_MATCH_STATUSES: set[str] = {"matched", "exact_match", "verified_match"}

OPEN_BATCH_STATUSES: set[str] = {"New", "In Progress", "Waiting for Patient", "Waiting for GP"}

DEMO_CALL_PREFIXES: tuple[str, ...] = ("TC-", "RX-TEST", "PRODSIM", "DEMO", "GPDEMO", "GPTDEMO", "AVA-TEST")

MODAL_ALERT_TYPE_KEYWORDS: tuple[str, ...] = ("red flag", "system error", "error", "missing", "required field", "validation")
NON_MODAL_ALERT_TYPE_KEYWORDS: tuple[str, ...] = ("daily summary", "summary")

STAFF_ROLES: set[str] = {"admin", "staff", "readonly"}

DEFAULT_OUTCOME_NOTES: str = "Processed according to JeffLocal workflow."
DEFAULT_ACTION_NEEDED: str = "Review and process according to local workflow."

REQUEST_TYPE_LABELS: dict[str, str] = {
    "prescription": "Prescription",
    "sick_note": "Sick Note",
    "referral": "Referral",
    "test_result": "Test Result",
    "appointment_redirect": "Appointment",
    "appointment": "Appointment",
    "admin": "Admin",
    "unknown": "Unknown",
}

REQUEST_TYPE_CANONICAL: dict[str, str] = {
    "prescription_request": "prescription",
    "medication_query":     "prescription",
    "sick_note_request":    "sick_note",
    "referral_chase":       "referral",
    "test_results_enquiry": "test_result",
    "appointment_request":  "appointment_redirect",
    "appointment":          "appointment_redirect",
    "admin_callback":       "admin",
    "urgent_callback":      "appointment_redirect",
    "needs_review":         "unknown",
}

REQUEST_TYPE_CHIPS: list[tuple[str, str]] = [
    ("prescription", "Prescription"),
    ("sick_note", "Sick Note"),
    ("referral", "Referral"),
    ("test_result", "Test Result"),
    ("appointment_redirect", "Appointment"),
    ("admin", "Admin"),
    ("unknown", "Unknown"),
]

DATE_RANGE_OPTIONS: list[dict] = [
    {"value": "today", "label": "Today"},
    {"value": "7d", "label": "Last 7 days"},
    {"value": "30d", "label": "Last 30 days"},
    {"value": "all", "label": "All"},
]

SUMMARY_REQUEST_TYPES: list[tuple[str, str]] = [
    ("prescription", "Prescription"),
    ("sick_note", "Sick Note"),
    ("referral", "Referral"),
    ("test_result", "Test Result"),
    ("appointment_redirect", "Appointment"),
    ("admin", "Admin"),
    ("unknown", "Unknown"),
]

N8NTEST_ARCHIVE_FOLDERS: list[str] = [
    "queue/encrypted_raw",
    "queue/incoming",
    "queue/processed",
    "queue/failed",
    "queue/deadletter",
    "outputs/handoff_json",
    "outputs/debug",
    "outputs/ollama_raw",
    "logs/transcripts",
]

LOCAL_SERVICE_URLS: dict[str, str] = {
    "dashboard": "http://127.0.0.1:8765",
    "n8n": "http://localhost:5678",
    "voice_agent": "local webhook/test intake",
}

SESSION_COOKIE: str = "jefflocal_session"

AUTH_PUBLIC_PATHS: set[str] = {"/login", "/logout", "/forgot", "/reset", "/favicon.ico"}

AUTH_PUBLIC_PREFIXES: tuple[str, ...] = ("/static/", "/api/health", "/api/n8n/", "/api/intake/")

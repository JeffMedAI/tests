from __future__ import annotations

import asyncio
import hashlib
import hmac
import http.client
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode, urlsplit
from uuid import uuid4

from fastapi import Body, Depends, FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .audit import write_audit_event
from .auth import (
    clear_failed_attempts,
    consume_reset_token,
    create_reset_token,
    create_session,
    get_session_user,
    hash_password,
    hash_pin,
    invalidate_session,
    is_account_locked,
    lookup_user_by_username,
    purge_expired_sessions,
    record_failed_attempt,
    set_new_password,
    set_new_pin,
    verify_password,
    verify_pin,
)
from .db import DB_PATH, connect, init_db, row_to_dict
from .importer import import_handoffs
from .models import (
    ALLOWED_STATUSES,
    EDITABLE_FORM_FIELDS,
    FINAL_STATUSES,
    format_display_timestamp,
    format_dob_uk,
    format_phone_uk,
    format_turnaround_time,
    utc_now_iso,
)


_log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BASE_DIR.parent
ALERT_DIR = ROOT_DIR / "logs" / "alerts"
N8NTEST_ARCHIVE_FOLDERS = [
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
SERVICE_START_SCRIPT = ROOT_DIR / "scripts" / "service_control" / "start_jefflocal_services.ps1"
LOCAL_SERVICE_URLS = {
    "dashboard": "http://127.0.0.1:5000",  # sandbox runs on 5000, not 8765
    "n8n": "http://localhost:5678",
    "voice_agent": "local webhook/test intake",
}

app = FastAPI(title="JeffLocal Staff Dashboard")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
templates.env.filters["display_ts"] = format_display_timestamp

SESSION_COOKIE = "jefflocal_session"
AUTH_PUBLIC_PATHS = {"/login", "/logout", "/forgot", "/reset", "/favicon.ico"}
AUTH_PUBLIC_PREFIXES = ("/static/", "/api/health", "/api/n8n/", "/api/alerts/")


def _is_public_path(path: str) -> bool:
    return path in AUTH_PUBLIC_PATHS or any(path.startswith(p) for p in AUTH_PUBLIC_PREFIXES)


@app.middleware("http")
async def enforce_auth(request: Request, call_next):
    if _is_public_path(request.url.path):
        return await call_next(request)
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return RedirectResponse(url=f"/login?next={quote(str(request.url.path), safe='')}", status_code=302)
    with connect() as conn:
        conn.row_factory = __import__("sqlite3").Row
        user = get_session_user(conn, token)
    if user is None:
        resp = RedirectResponse(url=f"/login?next={quote(str(request.url.path), safe='')}", status_code=302)
        resp.delete_cookie(SESSION_COOKIE)
        return resp
    return await call_next(request)


# ── Auth routes ────────────────────────────────────────────────────────────────

@app.get("/login")
def login_page(request: Request, next: str = "/", error: str = "", info: str = ""):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with connect() as conn:
            conn.row_factory = __import__("sqlite3").Row
            user = get_session_user(conn, token)
        if user:
            return RedirectResponse(url=next or "/", status_code=302)
    return templates.TemplateResponse(request, "login.html", {
        "error": error, "info": info, "next": next,
        "prefill_username": "", "auth_method": "password",
    })


@app.post("/login")
async def login_post(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    pin: str = Form(""),
    auth_method: str = Form("password"),
    next: str = Form("/"),
):
    username = username.strip().lower()
    error_ctx = {"prefill_username": username, "auth_method": auth_method, "next": next}

    def fail(msg: str):
        return templates.TemplateResponse(request, "login.html", {"error": msg, "info": "", **error_ctx})

    if not username:
        return fail("Please enter your username.")

    with connect() as conn:
        conn.row_factory = __import__("sqlite3").Row
        purge_expired_sessions(conn)
        user = lookup_user_by_username(conn, username)
        if user is None:
            return fail("Invalid username or credentials.")
        if not user.get("active"):
            return fail("Your account is inactive. Contact your administrator.")
        if is_account_locked(user):
            return fail(f"Account locked after too many failed attempts. Please try again in 15 minutes.")

        if auth_method == "pin":
            stored = user.get("pin_hash") or ""
            ok = bool(stored) and verify_pin(pin.strip(), stored)
        else:
            stored = user.get("password_hash") or ""
            ok = bool(stored) and verify_password(password, stored)

        if not ok:
            remaining = MAX_FAILED_ATTEMPTS - record_failed_attempt(conn, user["id"])
            msg = f"Invalid credentials. {max(0, remaining)} attempt(s) remaining before lockout."
            write_audit_event(conn, "__auth__", "login_failed", username, [], {}, {"method": auth_method})
            return fail(msg)

        clear_failed_attempts(conn, user["id"])
        ip = request.client.host if request.client else ""
        ua = request.headers.get("user-agent", "")[:200]
        token = create_session(conn, user["id"], ip, ua)
        write_audit_event(conn, "__auth__", "login_success", username, [], {}, {"method": auth_method})
        force_change = bool(user.get("must_change_password"))

    safe_next = next if next and next.startswith("/") and not next.startswith("//") else "/"
    # Force staff to update credentials before proceeding if flag is set
    if force_change:
        safe_next = "/profile?must_change=1"
    response = RedirectResponse(url=safe_next, status_code=302)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=3600)
    return response


@app.get("/logout")
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with connect() as conn:
            invalidate_session(conn, token)
    resp = RedirectResponse(url="/login?info=You+have+been+signed+out.", status_code=302)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@app.get("/forgot")
def forgot_page(request: Request):
    return templates.TemplateResponse(request, "forgot.html", {
        "mode": "request", "error": "", "success": "", "reset_link": None,
    })


@app.post("/forgot")
async def forgot_post(request: Request, username: str = Form(""), reset_type: str = Form("password")):
    """Generate a password/PIN reset link.

    Security notes:
    - No user enumeration: the same success message is shown regardless of
      whether the username exists, is inactive, or is rate-limited.
    - The reset link is only rendered when a valid, active user is found AND
      the rate limit has not been exceeded.
    - Rate limiting (3 requests/hr per user) is enforced in create_reset_token.
    """
    username = username.strip().lower()
    reset_link = None
    # Generic success message — identical for all outcomes (no user enumeration)
    success = (
        "If that username is registered, a reset link has been generated below. "
        "Share it securely with the user (e.g. via WhatsApp or in person)."
    )
    with connect() as conn:
        conn.row_factory = __import__("sqlite3").Row
        user = lookup_user_by_username(conn, username)
        if user and user.get("active"):
            try:
                token = create_reset_token(conn, user["id"], reset_type)
                base = str(request.base_url).rstrip("/")
                reset_link = f"{base}/reset?token={token}&type={reset_type}"
                write_audit_event(conn, "__auth__", "reset_requested", username, [], {}, {"type": reset_type})
            except ValueError:
                # rate_limit_exceeded — show no link but keep generic success
                # message so the rate-limit state is not revealed to the caller
                pass
    return templates.TemplateResponse(request, "forgot.html", {
        "mode": "request", "error": "", "success": success, "reset_link": reset_link,
    })


@app.get("/reset")
def reset_page(request: Request, token: str = "", type: str = "password"):
    if not token:
        return RedirectResponse(url="/forgot", status_code=302)
    return templates.TemplateResponse(request, "forgot.html", {
        "mode": "reset", "token": token, "reset_type": type, "error": "",
    })


@app.post("/reset")
async def reset_post(
    request: Request,
    token: str = Form(""),
    reset_type: str = Form("password"),
    new_value: str = Form(""),
    confirm_value: str = Form(""),
):
    error = ""
    if new_value != confirm_value:
        error = "Values do not match."
    elif reset_type == "password" and len(new_value) < 8:
        error = "Password must be at least 8 characters."
    elif reset_type == "pin" and (not new_value.isdigit() or not 4 <= len(new_value) <= 6):
        error = "PIN must be 4–6 digits."
    if error:
        return templates.TemplateResponse(request, "forgot.html", {
            "mode": "reset", "token": token, "reset_type": reset_type, "error": error,
        })
    with connect() as conn:
        conn.row_factory = __import__("sqlite3").Row
        user_id = consume_reset_token(conn, token, reset_type)
        if user_id is None:
            return templates.TemplateResponse(request, "forgot.html", {
                "mode": "reset", "token": token, "reset_type": reset_type,
                "error": "This reset link is invalid or has expired.",
            })
        if reset_type == "pin":
            set_new_pin(conn, user_id, new_value)
        else:
            set_new_password(conn, user_id, new_value)
        write_audit_event(conn, "__auth__", "credentials_reset", f"user_id:{user_id}", [], {}, {"type": reset_type})
    return templates.TemplateResponse(request, "forgot.html", {
        "mode": "done", "success": f"Your {reset_type} has been updated. You can now sign in.",
    })

MAX_FAILED_ATTEMPTS = 5


# ── Profile routes ─────────────────────────────────────────────────────────────

@app.get("/profile")
def profile_page(
    request: Request,
    pw_error: str = "", pw_success: str = "",
    pin_error: str = "", pin_success: str = "",
):
    ensure_ready()
    with connect() as conn:
        conn.row_factory = __import__("sqlite3").Row
        current_staff = current_staff_from_request(request, conn)
        sessions = []
        if current_staff.get("id"):
            token = request.cookies.get(SESSION_COOKIE, "")
            rows = conn.execute(
                "SELECT created_at, last_active_at, ip_address, token FROM sessions "
                "WHERE user_id=? AND expires_at > ? ORDER BY last_active_at DESC LIMIT 10",
                (current_staff["id"], __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()),
            ).fetchall()
            sessions = [dict(r) | {"is_current": r["token"] == token} for r in rows]
        staff_users = []
    return templates.TemplateResponse(request, "profile.html", {
        "current_staff": current_staff,
        "staff_users": staff_users,
        "sessions": sessions,
        "pw_error": pw_error, "pw_success": pw_success,
        "pin_error": pin_error, "pin_success": pin_success,
        "active_nav": "profile",
    })


@app.post("/profile/change-password")
async def profile_change_password(
    request: Request,
    current_password: str = Form(""),
    new_password: str = Form(""),
    confirm_password: str = Form(""),
):
    ensure_ready()

    def fail(msg: str):
        return RedirectResponse(url=f"/profile?pw_error={quote(msg, safe='')}", status_code=302)

    if new_password != confirm_password:
        return fail("New passwords do not match.")
    if len(new_password) < 8:
        return fail("New password must be at least 8 characters.")
    with connect() as conn:
        conn.row_factory = __import__("sqlite3").Row
        current_staff = current_staff_from_request(request, conn)
        if not current_staff.get("id"):
            return RedirectResponse(url="/login", status_code=302)
        user = conn.execute(
            "SELECT password_hash FROM staff_users WHERE id=?", (current_staff["id"],)
        ).fetchone()
        if user is None or not verify_password(current_password, user["password_hash"] or ""):
            return fail("Current password is incorrect.")
        set_new_password(conn, current_staff["id"], new_password)
        write_audit_event(conn, "__auth__", "password_changed", current_staff.get("username", ""), [], {}, {})
    token = request.cookies.get(SESSION_COOKIE, "")
    with connect() as conn:
        if token:
            conn.execute("INSERT OR IGNORE INTO sessions (token, user_id, created_at, last_active_at, expires_at) SELECT ?, ?, ?, ?, ? WHERE 0", (token, 0, "", "", ""))
        user_id = current_staff["id"]
        conn.execute("DELETE FROM sessions WHERE user_id=? AND token!=?", (user_id, token))
        conn.commit()
    resp = RedirectResponse(url="/profile?pw_success=Password+updated+successfully.", status_code=302)
    return resp


@app.post("/profile/change-pin")
async def profile_change_pin(
    request: Request,
    current_password: str = Form(""),
    new_pin: str = Form(""),
    confirm_pin: str = Form(""),
):
    ensure_ready()

    def fail(msg: str):
        return RedirectResponse(url=f"/profile?pin_error={quote(msg, safe='')}", status_code=302)

    if new_pin != confirm_pin:
        return fail("PINs do not match.")
    if not new_pin.isdigit() or not 4 <= len(new_pin) <= 6:
        return fail("PIN must be 4–6 digits.")
    with connect() as conn:
        conn.row_factory = __import__("sqlite3").Row
        current_staff = current_staff_from_request(request, conn)
        if not current_staff.get("id"):
            return RedirectResponse(url="/login", status_code=302)
        user = conn.execute(
            "SELECT password_hash FROM staff_users WHERE id=?", (current_staff["id"],)
        ).fetchone()
        if user is None or not verify_password(current_password, user["password_hash"] or ""):
            return fail("Current password is incorrect.")
        set_new_pin(conn, current_staff["id"], new_pin)
        write_audit_event(conn, "__auth__", "pin_changed", current_staff.get("username", ""), [], {}, {})
    return RedirectResponse(url="/profile?pin_success=PIN+updated+successfully.", status_code=302)


@app.post("/profile/sign-out-all")
async def profile_sign_out_all(request: Request):
    ensure_ready()
    token = request.cookies.get(SESSION_COOKIE, "")
    with connect() as conn:
        conn.row_factory = __import__("sqlite3").Row
        current_staff = current_staff_from_request(request, conn)
        if current_staff.get("id"):
            from .auth import invalidate_all_user_sessions
            invalidate_all_user_sessions(conn, current_staff["id"])
            write_audit_event(conn, "__auth__", "sign_out_all", current_staff.get("username", ""), [], {}, {})
    resp = RedirectResponse(url="/login?info=Signed+out+of+all+devices.", status_code=302)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


LOCKED_DETAIL_FIELDS = [
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

LOCKED_FIELD_CATEGORIES = [
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

SORT_OPTIONS = [
    {"value": "newest", "label": "Newest first"},
    {"value": "oldest", "label": "Oldest first"},
    {"value": "priority", "label": "Priority"},
    {"value": "unresolved", "label": "Unresolved first"},
]

RESOLVED_STATUSES = ("Resolved", "Unable to Complete")
TERMINAL_CASE_STATUSES = (
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
STAFF_REVIEW_STATUS_NAMES = ("staff review", "needs review", "urgent review", "escalated")
IN_PROGRESS_STATUS_NAMES = ("in progress", "active processing")
IDENTITY_REVIEW_STATUSES = {"possible_match", "possible_match_weak", "no_match", "insufficient_data", "needs_review"}
SAFE_MATCH_STATUSES = {"matched", "exact_match", "verified_match"}
OPEN_BATCH_STATUSES = {"New", "In Progress", "Waiting for Patient", "Waiting for GP"}
DEMO_CALL_PREFIXES = ("TC-", "RX-TEST", "PRODSIM", "DEMO", "GPDEMO", "GPTDEMO")
MODAL_ALERT_TYPE_KEYWORDS = ("red flag", "system error", "error", "missing", "required field", "validation")
NON_MODAL_ALERT_TYPE_KEYWORDS = ("daily summary", "summary")
STAFF_ROLES = {"admin", "staff", "readonly"}
DEFAULT_OUTCOME_NOTES = "Processed according to JeffLocal workflow."
DEFAULT_ACTION_NEEDED = "Review and process according to local workflow."
REQUEST_TYPE_LABELS = {
    "prescription": "Prescription",
    "sick_note": "Sick Note",
    "referral": "Referral",
    "test_result": "Test Result",
    "appointment_redirect": "Appointment",
    "admin": "Admin",
    "unknown": "Unknown",
}
REQUEST_TYPE_CHIPS = [
    ("prescription", "Prescription"),
    ("sick_note", "Sick Note"),
    ("referral", "Referral"),
    ("test_result", "Test Result"),
    ("appointment_redirect", "Appointment"),
    ("admin", "Admin"),
    ("unknown", "Unknown"),
]

DATE_RANGE_OPTIONS = [
    {"value": "today", "label": "Today"},
    {"value": "7d", "label": "Last 7 days"},
    {"value": "30d", "label": "Last 30 days"},
    {"value": "all", "label": "All"},
]

SUMMARY_REQUEST_TYPES = [
    ("prescription", "Prescription"),
    ("sick_note", "Sick Note"),
    ("referral", "Referral"),
    ("test_result", "Test Result"),
    ("appointment_redirect", "Appointment"),
    ("admin", "Admin"),
    ("unknown", "Unknown"),
]


def ensure_ready() -> None:
    with connect() as conn:
        init_db(conn)


async def _daily_session_purge() -> None:
    """Background task: purge expired sessions once per day."""
    while True:
        try:
            with connect() as conn:
                purge_expired_sessions(conn)
        except Exception:
            pass
        await asyncio.sleep(86400)


@app.on_event("startup")
def startup() -> None:
    with connect() as conn:
        init_db(conn)
        import_handoffs(conn)
    asyncio.create_task(_daily_session_purge())


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)


def calculate_turnaround_minutes(start_timestamp: str, end_timestamp: str) -> int | None:
    if not start_timestamp:
        return None
    try:
        start = datetime.fromisoformat(start_timestamp.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_timestamp.replace("Z", "+00:00"))
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        if end.tzinfo is None:
            end = end.replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    minutes = int((end - start).total_seconds() // 60)
    return max(minutes, 0)


def resolve_date_range(range_name: str, conn) -> str:
    valid = {item["value"] for item in DATE_RANGE_OPTIONS}
    if range_name in valid:
        return range_name

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    today_count = conn.execute(
        "SELECT COUNT(*) FROM cases WHERE COALESCE(call_timestamp_sort, 0) >= ?",
        (today_start,),
    ).fetchone()[0]
    return "today" if today_count else "all"


def range_clause(range_name: str) -> tuple[str, tuple[Any, ...]]:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    if range_name == "today":
        return "COALESCE(call_timestamp_sort, 0) >= ?", (today_start,)
    if range_name == "7d":
        return "COALESCE(call_timestamp_sort, 0) >= ?", (today_start - 6 * 86400,)
    if range_name == "30d":
        return "COALESCE(call_timestamp_sort, 0) >= ?", (today_start - 29 * 86400,)
    return "1=1", ()


def resolved_at_range_clause(range_name: str) -> tuple[str, tuple[Any, ...]]:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if range_name == "today":
        return "resolved_at >= ?", (today_start.isoformat(),)
    if range_name == "7d":
        return "resolved_at >= ?", ((today_start - timedelta(days=6)).isoformat(),)
    if range_name == "30d":
        return "resolved_at >= ?", ((today_start - timedelta(days=29)).isoformat(),)
    return "COALESCE(TRIM(resolved_at), '') <> ''", ()


def normalize_case_status(value: object) -> str:
    return str(value or "").replace("_", " ").strip().lower()


def normalize_lookup_value(value: object) -> str:
    return str(value or "").strip().lower()


def has_text(value: object) -> bool:
    return bool(str(value or "").strip())


def is_resolved_case(case: dict[str, Any]) -> bool:
    status = normalize_case_status(case.get("status"))
    if status in TERMINAL_CASE_STATUSES:
        return True
    return has_text(case.get("resolved_at"))


def is_active_case(case: dict[str, Any]) -> bool:
    return not is_resolved_case(case)


def requires_staff_action(case: dict[str, Any]) -> bool:
    return bool(
        is_active_red_flag(case)
        or is_active_staff_review(case)
        or is_active_identity_check(case)
        or normalize_case_status(case.get("status")) in {"failed", "failed safety queue", "awaiting processing", "active processing"}
    )


def is_active_red_flag(case: dict[str, Any]) -> bool:
    return is_active_case(case) and bool(case.get("red_flags_present") or str(case.get("priority") or "").strip() == "999 Emergency")


def is_active_identity_check(case: dict[str, Any]) -> bool:
    return is_active_case(case) and normalize_lookup_value(case.get("verification_status")) in IDENTITY_REVIEW_STATUSES


def is_active_staff_review(case: dict[str, Any]) -> bool:
    return is_active_case(case) and bool(case.get("staff_review_required") or normalize_case_status(case.get("status")) in STAFF_REVIEW_STATUS_NAMES)


def sql_placeholders(values: tuple[Any, ...]) -> str:
    return ", ".join(["?"] * len(values))


def sql_column(column: str, table_alias: str = "") -> str:
    return f"{table_alias}.{column}" if table_alias else column


def normalized_status_sql(table_alias: str = "", column: str = "status") -> str:
    return f"LOWER(REPLACE(TRIM(COALESCE({sql_column(column, table_alias)}, '')), '_', ' '))"


def normalized_lookup_sql(table_alias: str = "", column: str = "status") -> str:
    return f"LOWER(TRIM(COALESCE({sql_column(column, table_alias)}, '')))"


def active_case_clause(table_alias: str = "") -> tuple[str, tuple[Any, ...]]:
    status_expr = normalized_status_sql(table_alias)
    resolved_at_expr = f"COALESCE(TRIM({sql_column('resolved_at', table_alias)}), '') <> ''"
    clause = f"NOT ({status_expr} IN ({sql_placeholders(TERMINAL_CASE_STATUSES)}) OR {resolved_at_expr})"
    return clause, TERMINAL_CASE_STATUSES


def resolved_case_clause(table_alias: str = "") -> tuple[str, tuple[Any, ...]]:
    active_sql, active_params = active_case_clause(table_alias)
    return f"NOT ({active_sql})", active_params


def active_red_flag_clause(table_alias: str = "") -> tuple[str, tuple[Any, ...]]:
    active_sql, active_params = active_case_clause(table_alias)
    return f"({active_sql}) AND ({sql_column('red_flags_present', table_alias)} = 1 OR {sql_column('priority', table_alias)} = ?)", (*active_params, "999 Emergency")


def active_staff_review_clause(table_alias: str = "") -> tuple[str, tuple[Any, ...]]:
    active_sql, active_params = active_case_clause(table_alias)
    status_expr = normalized_status_sql(table_alias)
    clause = (
        f"({active_sql}) AND ({sql_column('staff_review_required', table_alias)} = 1 "
        f"OR {status_expr} IN ({sql_placeholders(STAFF_REVIEW_STATUS_NAMES)}))"
    )
    return clause, (*active_params, *STAFF_REVIEW_STATUS_NAMES)


def active_identity_check_clause(table_alias: str = "") -> tuple[str, tuple[Any, ...]]:
    active_sql, active_params = active_case_clause(table_alias)
    verification_expr = normalized_lookup_sql(table_alias, "verification_status")
    clause = f"({active_sql}) AND {verification_expr} IN ({sql_placeholders(tuple(IDENTITY_REVIEW_STATUSES))})"
    return clause, (*active_params, *tuple(IDENTITY_REVIEW_STATUSES))


def update_staff_fields(
    conn,
    call_id: str,
    allowed_updates: dict[str, Any],
    edited_by: str,
) -> bool:
    row = conn.execute("SELECT * FROM cases WHERE call_id = ?", (call_id,)).fetchone()
    old = row_to_dict(row)
    if old is None:
        raise HTTPException(status_code=404, detail="Case not found")

    changed_fields = [key for key, value in allowed_updates.items() if old.get(key) != value]
    if not changed_fields:
        return False

    assignments = ", ".join([f"{key} = ?" for key in allowed_updates])
    conn.execute(
        f"UPDATE cases SET {assignments} WHERE call_id = ?",
        [allowed_updates[key] for key in allowed_updates] + [call_id],
    )
    write_audit_event(
        conn,
        call_id=call_id,
        action="staff_update",
        edited_by=edited_by,
        changed_fields=changed_fields,
        old_values={key: old.get(key) for key in changed_fields},
        new_values={key: allowed_updates.get(key) for key in changed_fields},
    )
    return True


def filter_clause(filter_name: str) -> tuple[str, tuple[Any, ...]]:
    today = datetime.now(timezone.utc).date().isoformat()
    active_sql, active_params = active_case_clause()
    resolved_sql, resolved_params = resolved_case_clause()
    red_flag_sql, red_flag_params = active_red_flag_clause()
    staff_review_sql, staff_review_params = active_staff_review_clause()
    identity_sql, identity_params = active_identity_check_clause()
    resolved_today_sql = f"({resolved_sql}) AND resolved_at LIKE ?"
    filters: dict[str, tuple[str, tuple[Any, ...]]] = {
        "all": ("1=1", ()),
        "urgent_red_flags": (red_flag_sql, red_flag_params),
        "needs_review": (staff_review_sql, staff_review_params),
        "identity_issues": (identity_sql, identity_params),
        "open": (active_sql, active_params),
        "unresolved": (active_sql, active_params),
        "resolved": (resolved_sql, resolved_params),
        "resolved_today": (resolved_today_sql, (*resolved_params, f"{today}%")),
    }
    return filters.get(filter_name, filters["all"])


def sort_clause(sort: str) -> str:
    clauses = {
        "newest": "COALESCE(call_timestamp_sort, 0) DESC, call_id ASC",
        "oldest": "COALESCE(call_timestamp_sort, 0) ASC, call_id ASC",
        "priority": """
            CASE priority
                WHEN '999 Emergency' THEN 0
                WHEN 'urgent_review' THEN 1
                WHEN 'review_required' THEN 2
                WHEN 'routine' THEN 3
                WHEN 'normal' THEN 4
                ELSE 5
            END ASC,
            COALESCE(call_timestamp_sort, 0) DESC,
            call_id ASC
        """,
        "unresolved": """
            CASE WHEN LOWER(REPLACE(TRIM(COALESCE(status, '')), '_', ' ')) IN ('resolved', 'closed', 'completed', 'complete', 'cancelled', 'canceled', 'archived', 'duplicate', 'dismissed', 'unable to complete') THEN 1 ELSE 0 END ASC,
            red_flags_present DESC,
            staff_review_required DESC,
            COALESCE(call_timestamp_sort, 0) DESC,
            call_id ASC
        """,
    }
    return clauses.get(sort, clauses["newest"])


def worklist_order_clause(sort: str, filter_name: str, explicit_sort: bool) -> str:
    if not explicit_sort and filter_name in {"all", "open", "unresolved"}:
        return """
            CASE WHEN red_flags_present = 1 OR priority = '999 Emergency' THEN 0 ELSE 1 END ASC,
            COALESCE(call_timestamp_sort, 0) DESC,
            call_id ASC
        """
    return sort_clause(sort)


def make_query(filter_name: str, sort: str, q: str, request_type: str) -> tuple[str, tuple[Any, ...]]:
    where, params = filter_clause(filter_name)
    parts = [where]
    values: list[Any] = list(params)
    if request_type:
        parts.append("request_type = ?")
        values.append(request_type)
    if q:
        like = f"%{q}%"
        parts.append(
            """
            (
                call_id LIKE ? OR patient_name LIKE ? OR dob LIKE ? OR postcode LIKE ?
                OR callback_number LIKE ? OR emis_number LIKE ? OR nhs_number LIKE ?
                OR call_summary LIKE ? OR ai_summary LIKE ? OR task_title LIKE ? OR task_body LIKE ?
                OR staff_task_title LIKE ? OR staff_task_body LIKE ? OR patient_record_note LIKE ?
                OR verification_status LIKE ?
            )
            """
        )
        values.extend([like] * 15)
    return " AND ".join(f"({part})" for part in parts), tuple(values)


def worklist_url(filter_name: str, sort: str, q: str, request_type: str, date_range: str) -> str:
    params = {
        "filter": filter_name,
        "sort": sort,
        "range": date_range,
    }
    if q:
        params["q"] = q
    if request_type:
        params["request_type"] = request_type
    return "/requests?" + urlencode(params)


def paged_worklist_url(filter_name: str, sort: str, q: str, request_type: str, date_range: str, page: int, page_size: int) -> str:
    params = {
        "filter": filter_name,
        "sort": sort,
        "range": date_range,
        "page": page,
        "page_size": page_size,
    }
    if q:
        params["q"] = q
    if request_type:
        params["request_type"] = request_type
    return "/requests?" + urlencode(params)


DEFAULT_RETURN_URL = "/requests?filter=all&sort=newest&range=today&page_size=20"


def safe_local_return_url(request: Request, value: str | None, default: str = DEFAULT_RETURN_URL) -> str:
    candidate = (value or "").strip()
    if not candidate:
        return default
    parsed = urlsplit(candidate)
    if parsed.scheme or parsed.netloc or not candidate.startswith("/") or candidate.startswith("//"):
        return default
    return candidate


def detail_case_url(call_id: str, return_url: str) -> str:
    params = {"return_url": return_url} if return_url else {}
    suffix = f"?{urlencode(params)}" if params else ""
    return f"/case/{quote(call_id)}{suffix}"


def return_url_with_notice(return_url: str, notice: str) -> str:
    if not notice:
        return return_url
    separator = "&" if "?" in return_url else "?"
    return f"{return_url}{separator}{urlencode({'notice': notice})}"


def friendly_request_type(value: str) -> str:
    return REQUEST_TYPE_LABELS.get((value or "").strip(), (value or "Unknown").replace("_", " ").title())


def friendly_status(value: str) -> str:
    return (value or "New").replace("_", " ").title()


def calculate_age_label(dob: object, age: object = None) -> str:
    if age not in ("", None):
        return str(age)
    text = str(dob or "").strip()
    if not text:
        return ""
    try:
        born = datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return ""
    today = datetime.now(timezone.utc).date()
    years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return str(years) if years >= 0 else ""


def normalize_staff_name(value: object) -> str:
    return str(value or "").strip() or "demo_user"


def get_staff_users(conn, active_only: bool = True) -> list[dict[str, Any]]:
    where = "WHERE active = 1" if active_only else ""
    rows = conn.execute(
        f"""
        SELECT id, display_name, email, role, active, created_at, updated_at
        FROM staff_users
        {where}
        ORDER BY active DESC, role ASC, display_name ASC
        """
    ).fetchall()
    return [row_to_dict(row) or {} for row in rows]


def get_staff_any_by_id(conn, staff_id: object) -> dict[str, Any] | None:
    try:
        numeric_id = int(str(staff_id))
    except (TypeError, ValueError):
        return None
    row = conn.execute(
        """
        SELECT id, display_name, email, role, active, created_at, updated_at
        FROM staff_users
        WHERE id = ?
        """,
        (numeric_id,),
    ).fetchone()
    return row_to_dict(row)


def current_staff_from_request(request: Request | None, conn) -> dict[str, Any]:
    if request:
        token = request.cookies.get(SESSION_COOKIE)
        if token:
            import sqlite3 as _sqlite3
            conn.row_factory = _sqlite3.Row
            user = get_session_user(conn, token)
            if user:
                return {
                    "id": user.get("id") or user.get("user_id"),
                    "display_name": user.get("display_name", ""),
                    "email": user.get("email", ""),
                    "role": user.get("role", "staff"),
                    "active": 1,
                    "username": user.get("username", ""),
                }
        # Fallback: jefflocal_staff_id cookie (test environments where session auth is bypassed)
        staff_id_cookie = request.cookies.get("jefflocal_staff_id")
        if staff_id_cookie:
            import sqlite3 as _sqlite3
            conn.row_factory = _sqlite3.Row
            staff = get_staff_any_by_id(conn, staff_id_cookie)
            if staff and staff.get("active"):
                return staff
    return {"id": None, "display_name": "demo_user", "email": "", "role": "staff", "active": 1, "demo_fallback": True}


def staff_can_edit(staff: dict[str, Any]) -> bool:
    return staff.get("role") in {"admin", "staff"}


def staff_can_manage(staff: dict[str, Any]) -> bool:
    return staff.get("role") == "admin"


def staff_display(staff: dict[str, Any] | None) -> str:
    return normalize_staff_name((staff or {}).get("display_name"))


def require_staff_edit(staff: dict[str, Any]) -> None:
    if not staff_can_edit(staff):
        raise HTTPException(status_code=403, detail="Read-only staff cannot update cases.")


def require_staff_admin(staff: dict[str, Any]) -> None:
    if not staff_can_manage(staff):
        raise HTTPException(status_code=403, detail="Admin staff required.")


def format_staff_review(value: object) -> str:
    return "Review Required" if value else "routine"


def format_safe_to_queue(value: object) -> str:
    return "Safe To Queue" if value else "Not Safe To Queue"


def primary_display_status(case: dict[str, Any]) -> tuple[str, str]:
    status = str(case.get("status") or "").replace("_", " ").strip().lower()
    if is_resolved_case(case):
        return "RESOLVED", "resolved"
    if status in {"in review", "in progress"}:
        return "IN REVIEW", "in-review"
    if status == "reopened":
        return "REOPENED", "review"
    if status == "escalated":
        return "ESCALATED", "review"
    if status in {"failed", "error", "failed / error"}:
        return "FAILED / ERROR", "danger"
    if status in {"new", "open", ""}:
        return "OPEN", "open"
    return "OPEN", "open"


def build_suggested_actions(case: dict[str, Any]) -> list[str]:
    """Return 3-5 clinical triage action strings derived from case data."""
    actions: list[str] = []
    priority = str(case.get("priority") or "routine").strip().lower()
    red_flag = bool(case.get("red_flags_present"))
    verification = str(case.get("verification_status") or "").strip().lower()
    request_type = str(case.get("request_type") or "").strip().lower()
    staff_review = bool(case.get("staff_review_required"))
    is_emergency = red_flag or priority in {"999 emergency", "urgent"}

    if is_emergency:
        actions.append("Escalate immediately — possible urgent / emergency presentation")
    actions.append("Assess urgency and triage category")
    if red_flag:
        actions.append("Check for red flag symptoms — follow local emergency protocol")
    if verification in {"failed", "unverified", "partial", "unable to verify"}:
        actions.append("Verify patient identity before routing")
    if request_type in {"appointment", "gp appointment", "urgent appointment"}:
        actions.append("Route to appropriate GP or duty clinician")
    elif request_type in {"prescription", "repeat prescription"}:
        actions.append("Route to prescribing team for authorisation")
    elif request_type in {"sick note", "sick_note", "fit note"}:
        actions.append("Assign to GP for fit note review")
    elif request_type in {"test result", "test_result"}:
        actions.append("Check if results are available and notify clinician")
    elif request_type in {"referral"}:
        actions.append("Check referral pathway and confirm with GP")
    else:
        actions.append("Route to appropriate GP or team")
    if staff_review and not is_emergency:
        actions.append("Staff review required before processing")
    return actions[:5]


_EMIS_STEPS: dict[str, list[str]] = {
    "prescription": [
        "Find patient on EMIS",
        "Paste AI-generated record note into patient record",
        "Assign task to Medicines Management",
    ],
    "sick_note": [
        "Find patient on EMIS",
        "Check GP fit note policy and prior sick notes",
        "Create task for GP to authorise and issue fit note",
    ],
    "referral": [
        "Find patient on EMIS",
        "Confirm referral pathway with GP or clinical lead",
        "Raise referral via EMIS task or e-Referrals (eRS)",
    ],
    "test_result": [
        "Find patient on EMIS",
        "File result in patient record",
        "Assign to responsible clinician for review and action",
    ],
    "admin": [
        "Find patient on EMIS",
        "Log contact in patient record",
        "Action or route to appropriate team",
    ],
    "appointment_redirect": [
        "Find patient on EMIS",
        "Check appointment availability or redirect protocol",
        "Book or redirect as appropriate",
    ],
}


def emis_workflow_steps(request_type: str | None) -> list[str]:
    rt = str(request_type or "").strip().lower()
    return _EMIS_STEPS.get(rt, _EMIS_STEPS["admin"])


def summary_chips_for_case(case: dict[str, Any]) -> list[dict[str, str]]:
    """Generate status pills for case display. Avoids duplicate/redundant pills."""
    chips: list[dict[str, str]] = []
    priority = str(case.get("priority") or "routine").replace("_", " ")
    is_emergency = bool(case.get("red_flags_present") or str(case.get("priority") or "").strip() == "999 Emergency")
    verification_status = str(case.get("verification_status") or "").strip().lower()
    recording_label = case.get("recording", {}).get("recording_label") if isinstance(case.get("recording"), dict) else ""
    staff_review = case.get("staff_review_required")

    # Resolved cases: no action-required chips — type badge + RESOLVED footer is sufficient
    # Emergency resolved cases retain Red Flag badge for audit visibility
    if case.get("is_resolved") or is_resolved_case(case):
        if is_emergency:
            chips.append({"label": "Red Flag", "class": "danger"})
        return chips

    # Emergency cases: Priority + Red Flag + Safe to Queue
    if is_emergency:
        chips.append({"label": priority, "class": "danger"})
        chips.append({"label": "Red Flag", "class": "danger"})
        chips.append({"label": format_safe_to_queue(case.get("safe_to_queue")), "class": "safe" if case.get("safe_to_queue") else "not-safe"})
        return chips[:3]

    # Identity check cases: Priority + merged ID pill
    if verification_status in IDENTITY_REVIEW_STATUSES:
        chips.append({"label": priority, "class": "priority-routine" if priority.lower() == "routine" else "review"})
        _vs_human = (case.get("verification_status") or "unknown").replace("_", " ").title()
        chips.append({
            "label": f"ID: {_vs_human}",
            "class": "review",
            "tooltip": f"Identity Check · Verification: {case.get('verification_status') or 'unknown'}",
        })
        return chips[:3]

    # Staff review cases: Priority + Review Required + Safe to Queue
    if staff_review:
        chips.append({"label": priority, "class": "priority-routine" if priority.lower() == "routine" else "review"})
        chips.append({"label": "Review Required", "class": "review"})
        chips.append({"label": format_safe_to_queue(case.get("safe_to_queue")), "class": "safe" if case.get("safe_to_queue") else "not-safe"})
        return chips[:3]

    # Default case: Priority + Safe to Queue only (minimal)
    chips.append({
        "label": priority,
        "class": "danger" if case.get("priority") == "999 Emergency" else "priority-routine" if priority.lower() == "routine" else "review",
    })
    chips.append({
        "label": format_safe_to_queue(case.get("safe_to_queue")),
        "class": "safe" if case.get("safe_to_queue") else "not-safe",
    })
    return chips[:2]


def dedupe_repeated_display_sentences(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parts = re.split(r"(?<=[.!?])\s+", text)
    cleaned: list[str] = []
    previous = ""
    for part in parts:
        normalized = re.sub(r"\s+", " ", part).strip().lower()
        if normalized and normalized != previous:
            cleaned.append(part.strip())
        previous = normalized
    return " ".join(cleaned)


def prepare_case(row: dict[str, Any]) -> dict[str, Any]:
    case = dict(row)
    case["staff_task_title"] = dedupe_repeated_display_sentences(case.get("staff_task_title") or case.get("task_title") or "")
    case["staff_task_body"] = dedupe_repeated_display_sentences(case.get("staff_task_body") or case.get("task_body") or "")
    case["ai_summary"] = dedupe_repeated_display_sentences(case.get("ai_summary") or case.get("call_summary") or "")
    case["patient_record_note"] = dedupe_repeated_display_sentences(case.get("patient_record_note") or "")
    case["request_type_label"] = friendly_request_type(str(case.get("request_type", "")))
    case["status_label"] = friendly_status(str(case.get("status", "")))
    case["safe_to_queue_label"] = format_safe_to_queue(case.get("safe_to_queue"))
    case["staff_review_label"] = format_staff_review(case.get("staff_review_required"))
    case["red_flag_label"] = "EMERGENCY / RED FLAG" if case.get("red_flags_present") or case.get("priority") == "999 Emergency" else ""
    case["identity_review_required"] = str(case.get("verification_status", "")) in IDENTITY_REVIEW_STATUSES
    case["identity_label"] = "Identity review required" if case["identity_review_required"] else str(case.get("verification_status", "")).replace("_", " ").title()
    case["age_label"] = calculate_age_label(case.get("dob"), case.get("age"))
    case["call_summary_short"] = case.get("ai_summary") or case.get("staff_task_body") or ""
    case["duration_label"] = f"{case.get('call_duration_seconds')}s" if case.get("call_duration_seconds") not in ("", None) else ""
    case["is_resolved"] = is_resolved_case(case)
    case["is_emergency"] = bool(case.get("red_flags_present") or case.get("priority") == "999 Emergency")
    case["timestamp_display"] = format_display_timestamp(case.get("timestamp"))
    case["last_updated_display"] = format_display_timestamp(case.get("last_updated"))
    case["resolved_at_display"] = format_display_timestamp(case.get("resolved_at"))
    case["last_edited_at_display"] = format_display_timestamp(case.get("last_edited_at"))
    # Format resolved_by staff name (fallback to empty if not available)
    case["resolved_by_display"] = str(case.get("resolved_by") or "").strip()
    # Format turnaround time (show as "2h 15m" or "45 mins")
    case["turnaround_minutes_display"] = format_turnaround_time(case.get("turnaround_minutes"))
    # Format DOB and phone number to NHS/UK standards
    case["dob_display"] = format_dob_uk(case.get("dob")) if case.get("dob") else ""
    case["callback_number_display"] = format_phone_uk(case.get("callback_number")) if case.get("callback_number") else ""
    case["primary_status_label"], case["primary_status_class"] = primary_display_status(case)
    case["summary_chips"] = summary_chips_for_case(case)
    case["suggested_actions"] = build_suggested_actions(case)
    # Age since the call (used for card age colouring)
    try:
        ts_raw = str(case.get("timestamp") or "").strip()
        if ts_raw:
            _dt = datetime.fromisoformat(ts_raw.replace("Z", "+00:00").replace(" ", "T"))
            _age_secs = max(0, int((datetime.now(timezone.utc) - _dt).total_seconds()))
            _age_mins = _age_secs // 60
            case["age_minutes"] = _age_mins
            if _age_mins < 60:
                case["age_label_short"] = f"{_age_mins}m ago"
            elif _age_mins < 1440:
                case["age_label_short"] = f"{_age_mins // 60}h {_age_mins % 60}m ago"
            else:
                case["age_label_short"] = f"{_age_mins // 1440}d ago"
            case["age_class"] = "fresh" if _age_mins < 15 else "recent" if _age_mins < 60 else "old"
        else:
            case["age_minutes"] = None
            case["age_label_short"] = ""
            case["age_class"] = ""
    except Exception:
        case["age_minutes"] = None
        case["age_label_short"] = ""
        case["age_class"] = ""
    # Short time display: extract HH:MM from timestamp_display ("DD-MM-YYYY T HH:MM")
    _ts_disp = case.get("timestamp_display") or ""
    case["time_display"] = _ts_disp.split(" T ")[-1] if " T " in _ts_disp else _ts_disp
    case["processing_output_missing"] = not (
        str(case.get("staff_task_title") or "").strip()
        and str(case.get("staff_task_body") or "").strip()
        and str(case.get("ai_summary") or "").strip()
        and str(case.get("patient_record_note") or "").strip()
    )
    missing_message = "Processing output missing - staff review required."
    case["staff_task_display"] = case.get("staff_task_body") or missing_message
    case["ai_summary_display"] = case.get("ai_summary") or missing_message
    case["patient_record_note_display"] = case.get("patient_record_note") or missing_message
    if case["processing_output_missing"]:
        case["call_summary_short"] = missing_message
    case["recording_badge_class"] = "safe" if case.get("recording_status") == "available" else "neutral"
    emis_value = case.get("emis_number") or case.get("matched_patient_ref") or "not available"
    nhs_value = case.get("nhs_number") or "not available"
    identifier_warning = "" if (case.get("emis_number") or case.get("matched_patient_ref") or case.get("nhs_number")) else "Patient identifier unavailable - verify patient before documenting."
    case["identifier_warning"] = identifier_warning
    identifier_header = "\n".join(
        [
            f"EMIS: {emis_value}",
            f"NHS: {nhs_value}",
            identifier_warning,
        ]
    ).replace("\n\n", "\n")
    urgent_copy_footer = (
        "\nUrgent/red-flag case: follow local urgent escalation protocol. Do not rely on copied note alone."
        if case["is_emergency"]
        else ""
    )
    case["emis_note"] = "\n".join(
        [
            "JeffLocal call summary:",
            f"Call ID: {case.get('call_id') or ''}",
            f"Request type: {case.get('request_type') or ''}",
            f"EMIS: {emis_value}",
            f"NHS: {nhs_value}",
            identifier_warning,
            f"DOB: {case.get('dob') or ''}",
            f"Callback: {case.get('callback_number') or ''}",
            f"Verification: {case.get('verification_status') or ''}",
            f"Priority: {case.get('priority') or ''}",
            f"Safe to queue: {case.get('safe_to_queue_label') or ''}",
            f"Summary: {case.get('ai_summary_display') or ''}",
            f"Action needed: {case.get('action_needed') or ''}",
            urgent_copy_footer,
        ]
    ).replace("\n\n", "\n")
    patient_name = str(case.get("patient_name") or "").strip()
    def copy_safe(value: object) -> str:
        text = str(value or "")
        return text.replace(patient_name, "[patient]") if patient_name else text

    case["copy_safe_summary"] = copy_safe("\n".join([identifier_header, str(case.get("ai_summary_display") or ""), urgent_copy_footer]).strip())
    case["copy_safe_task"] = copy_safe("\n".join([identifier_header, str(case.get("staff_task_title") or ""), str(case.get("staff_task_display") or ""), urgent_copy_footer]).strip())
    case["copy_safe_identifiers"] = copy_safe(
        "\n".join(
            [
                f"EMIS: {emis_value}",
                f"NHS: {nhs_value}",
                f"Callback: {case.get('callback_number') or 'not available'}",
                identifier_warning,
            ]
        ).replace("\n\n", "\n").strip()
    )
    patient_note = str(case.get("patient_record_note_display") or "")
    if case.get("emis_number") or case.get("matched_patient_ref") or case.get("nhs_number"):
        patient_note = copy_safe(patient_note)
    case["copy_safe_emis_note"] = patient_note
    case["resolve_eligible"] = (
        not case["is_resolved"]
        and str(case.get("priority") or "").lower() == "routine"
        and not case.get("red_flags_present")
        and bool(case.get("safe_to_queue"))
        and not case.get("staff_review_required")
        and str(case.get("verification_status") or "").lower() in SAFE_MATCH_STATUSES
        and bool(case.get("callback_number"))
        and bool(case.get("emis_number") or case.get("matched_patient_ref") or case.get("nhs_number") or case.get("patient_name"))
    )
    _already_in_review = normalize_case_status(str(case.get("status") or "")) in {"in review", "in progress"}
    case["requires_individual_review"] = bool(
        not _already_in_review
        and (case["is_emergency"] or case["identity_review_required"] or case.get("staff_review_required"))
    )
    case["audit_events"] = []
    return case


def attach_recent_audit_events(conn, cases: list[dict[str, Any]]) -> None:
    call_ids = [case["call_id"] for case in cases]
    if not call_ids:
        return
    placeholders = ", ".join(["?"] * len(call_ids))
    rows = conn.execute(
        f"""
        SELECT timestamp, call_id, action, edited_by, changed_fields, new_values
        FROM audit_events
        WHERE call_id IN ({placeholders})
        ORDER BY timestamp DESC, id DESC
        """,
        tuple(call_ids),
    ).fetchall()
    by_call_id: dict[str, list[dict[str, Any]]] = {call_id: [] for call_id in call_ids}
    for row in rows:
        if len(by_call_id[row["call_id"]]) >= 5:
            continue
        audit_row = row_to_dict(row)
        audit_row["timestamp_display"] = format_display_timestamp(audit_row.get("timestamp"))
        audit_row["friendly_text"] = friendly_audit_text(audit_row)
        by_call_id[row["call_id"]].append(audit_row)
    for case in cases:
        case["audit_events"] = by_call_id.get(case["call_id"], [])


def transcript_conversation_lines(transcript: object) -> list[dict[str, str]]:
    text = str(transcript or "").strip()
    if not text:
        return []
    speaker_pattern = re.compile(r"\b(Jeff|Agent|Jackie|Digital Receptionist|Caller|Patient)\s*:", re.IGNORECASE)
    matches = list(speaker_pattern.finditer(text))
    if matches:
        parsed_lines: list[dict[str, str]] = []
        for index, match in enumerate(matches):
            speaker = match.group(1).strip()
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            content = re.sub(r"\s+", " ", text[start:end]).strip()
            if not content:
                continue
            speaker_lower = speaker.lower()
            if speaker_lower in {"agent", "digital receptionist", "jackie", "jeff"}:
                parsed_lines.append({"speaker": "Jeff", "role": "agent", "text": content})
            else:
                parsed_lines.append({"speaker": "Caller", "role": "caller", "text": content})
        if parsed_lines:
            return parsed_lines
    lines: list[dict[str, str]] = []
    raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(raw_lines) <= 1:
        return [{"speaker": "Transcript", "role": "system", "text": text}]
    for line in raw_lines:
        if ":" in line:
            speaker, content = line.split(":", 1)
            speaker = speaker.strip() or "Speaker"
            content = content.strip()
        else:
            speaker, content = "Transcript", line
        speaker_lower = speaker.lower()
        if speaker_lower in {"agent", "digital receptionist", "jackie", "assistant"}:
            display_speaker = "Digital Receptionist"
            role = "agent"
        elif speaker_lower in {"caller", "patient", "user"}:
            display_speaker = "Caller"
            role = "caller"
        else:
            display_speaker = speaker.title()
            role = "system"
        if content:
            lines.append({"speaker": display_speaker, "role": role, "text": content})
    return lines


def load_case_source_payload(case: dict[str, Any]) -> dict[str, Any]:
    source_path = str(case.get("source_path") or "").strip()
    if not source_path:
        return {}
    path = Path(source_path)
    if not path.is_absolute():
        path = ROOT_DIR / path
    try:
        resolved = path.resolve()
        if ROOT_DIR.resolve() not in resolved.parents and resolved != ROOT_DIR.resolve():
            return {}
        if not resolved.exists() or not resolved.is_file():
            return {}
        return json.loads(resolved.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, RuntimeError):
        return {}


def pathway_display_value(value: Any) -> str:
    if value in ("", None, [], {}):
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(cleaned) if cleaned else "None"
    return str(value).strip()


def add_pathway_item(items: list[dict[str, str]], label: str, value: Any) -> None:
    display = pathway_display_value(value)
    if display:
        items.append({"label": label, "value": display})


def pathway_question_responses(case: dict[str, Any]) -> list[dict[str, str]]:
    payload = load_case_source_payload(case)
    pathway = payload.get("pathway_responses") if isinstance(payload.get("pathway_responses"), dict) else {}
    normalized = payload.get("normalized_input") if isinstance(payload.get("normalized_input"), dict) else {}
    items: list[dict[str, str]] = []
    request_type = str(case.get("request_type") or payload.get("request_type") or "").strip()

    # Caller identity — always shown
    caller_for = (
        pathway.get("caller_for")
        or normalized.get("caller_for")
        or (pathway.get("admin") or {}).get("caller_relationship") if isinstance(pathway.get("admin"), dict) else None
    )
    add_pathway_item(items, "Caller for", caller_for)

    # Pathway-specific fields
    section = pathway.get(request_type) if isinstance(pathway.get(request_type), dict) else {}

    if request_type == "prescription":
        add_pathway_item(items, "Prescription type", section.get("prescription_type"))
        add_pathway_item(items, "Medication requested", section.get("medications_requested") or normalized.get("medications_requested"))
        add_pathway_item(items, "Pharmacy", section.get("pharmacy") or normalized.get("pharmacy"))
        add_pathway_item(items, "Run-out status", section.get("run_out_status"))

    elif request_type == "sick_note":
        add_pathway_item(items, "Note type", section.get("request_type"))
        add_pathway_item(items, "Start date requested", section.get("start_date_requested") or section.get("start_date"))
        add_pathway_item(items, "Duration requested", section.get("duration_requested") or section.get("requested_duration"))
        add_pathway_item(items, "Reason", section.get("reason"))
        add_pathway_item(items, "Purpose", section.get("purpose"))
        add_pathway_item(items, "Already spoken to doctor", section.get("already_spoken_to_doctor"))
        add_pathway_item(items, "Workplace adjustments discussed", section.get("workplace_adjustments_discussed"))

    elif request_type == "referral":
        add_pathway_item(items, "Referral type", section.get("referral_type"))
        add_pathway_item(items, "Specialty", section.get("specialty"))
        add_pathway_item(items, "Hospital", section.get("hospital_name"))
        add_pathway_item(items, "Approx submission date", section.get("approx_submission_date"))
        add_pathway_item(items, "Choose & Book code", section.get("choose_and_book_code"))

    elif request_type == "test_result":
        add_pathway_item(items, "Test type", section.get("test_type"))
        add_pathway_item(items, "Approx test date", section.get("approx_test_date"))
        add_pathway_item(items, "Reference number", section.get("reference_number"))
        add_pathway_item(items, "GP seen about result", section.get("gp_seen_about_result"))
        add_pathway_item(items, "Patient expressed urgency concern", section.get("urgency_concern"))

    elif request_type == "appointment_redirect":
        add_pathway_item(items, "Appointment reason", section.get("appointment_reason"))
        add_pathway_item(items, "Preferred timeframe", section.get("preferred_timeframe"))
        add_pathway_item(items, "Who for", section.get("who_for"))
        add_pathway_item(items, "Urgency", section.get("urgency"))
        add_pathway_item(items, "Clinician preference", section.get("clinician_preference"))
        add_pathway_item(items, "Previously declined appointment", section.get("previous_appointment_declined"))

    elif request_type == "admin":
        add_pathway_item(items, "Admin reason", section.get("admin_reason"))
        add_pathway_item(items, "Caller relationship", section.get("caller_relationship"))
        add_pathway_item(items, "Needs identity check", section.get("needs_identity_check"))
        add_pathway_item(items, "Website answer available", section.get("website_answer_available"))
        add_pathway_item(items, "Callback needed", section.get("callback_needed"))

    elif request_type == "unknown":
        unknown_sec = pathway.get("unknown") if isinstance(pathway.get("unknown"), dict) else {}
        add_pathway_item(items, "Caller stated reason", unknown_sec.get("caller_stated_reason"))
        add_pathway_item(items, "Suggested pathway", unknown_sec.get("suggested_pathway"))

    # Identity confirmation — always shown
    # Reads from payload.identity (top-level, set by Ollama) or pathway.identity (legacy)
    identity = (
        payload.get("identity") if isinstance(payload.get("identity"), dict)
        else pathway.get("identity") if isinstance(pathway.get("identity"), dict)
        else {}
    )
    add_pathway_item(items, "Callback confirmed", identity.get("callback_confirmed"))
    add_pathway_item(items, "Name stated", identity.get("name_stated"))
    add_pathway_item(items, "DOB stated", identity.get("dob_stated"))
    add_pathway_item(items, "Verification", case.get("verification_status"))

    # Urgency assessment — reads from payload top-level (Ollama places it there)
    # with fallback to pathway_responses.urgency_assessment (legacy location)
    urgency = (
        payload.get("urgency_assessment") if isinstance(payload.get("urgency_assessment"), dict)
        else pathway.get("urgency_assessment") if isinstance(pathway.get("urgency_assessment"), dict)
        else {}
    )
    add_pathway_item(items, "Urgency level", urgency.get("urgency_level") or case.get("priority"))
    red_flags_mentioned = urgency.get("red_flags_mentioned")
    add_pathway_item(items, "Red flags mentioned", red_flags_mentioned if red_flags_mentioned else "None")
    add_pathway_item(items, "Emergency advice given", urgency.get("emergency_advice_given"))

    # Appointment redirected flag — reads from payload top-level (Ollama places it there)
    appt_redirected = payload.get("appointment_redirected") or pathway.get("appointment_redirected")
    add_pathway_item(items, "Appointment redirected", appt_redirected)

    return items


def friendly_audit_text(event: dict[str, Any]) -> str:
    actor = event.get("edited_by") or "Staff"
    action = str(event.get("action") or "").replace("_", " ")
    try:
        new_values = json.loads(event.get("new_values") or "{}")
    except (TypeError, json.JSONDecodeError):
        new_values = {}
    if event.get("action") == "staff_update":
        if new_values.get("status"):
            return f"{actor} updated case status to {new_values['status']}."
        if new_values.get("assigned_to"):
            return f"{actor} assigned the case to {new_values['assigned_to']}."
        if new_values.get("resolved_by"):
            return f"{actor} resolved the case."
        return f"{actor} updated the case."
    if event.get("action") == "batch_resolve":
        return f"{actor} batch resolved this case."
    if event.get("action") == "case_reopened":
        return f"{actor} reopened the case for staff review."
    if event.get("action") == "alert_acknowledged":
        return f"{actor} acknowledged a local alert."
    return f"{actor} recorded {action}."


def get_summary_cards(conn, date_range: str) -> list[dict[str, Any]]:
    range_where, range_params = range_clause(date_range)
    active_sql, active_params = active_case_clause()
    resolved_sql, resolved_params = resolved_case_clause()
    red_flag_sql, red_flag_params = active_red_flag_clause()
    staff_review_sql, staff_review_params = active_staff_review_clause()
    identity_sql, identity_params = active_identity_check_clause()
    total_open = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE ({range_where}) AND ({active_sql})",
        (*range_params, *active_params),
    ).fetchone()[0]
    red_flags = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE ({range_where}) AND ({red_flag_sql})",
        (*range_params, *red_flag_params),
    ).fetchone()[0]
    needs_review = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE ({range_where}) AND ({staff_review_sql})",
        (*range_params, *staff_review_params),
    ).fetchone()[0]
    identity_issues = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE ({range_where}) AND ({identity_sql})",
        (*range_params, *identity_params),
    ).fetchone()[0]
    resolved_label = "Resolved Today" if date_range == "today" else "Resolved in Range"
    resolved_range_where, resolved_range_params = resolved_at_range_clause(date_range)
    resolved_count = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE ({resolved_range_where}) AND ({resolved_sql})",
        (*resolved_range_params, *resolved_params),
    ).fetchone()[0]
    return [
        {"label": "Total Open", "value": total_open, "url": worklist_url("open", "newest", "", "", date_range)},
        {"label": "Emergency / Red Flags", "value": red_flags, "url": worklist_url("urgent_red_flags", "newest", "", "", date_range)},
        {"label": "Needs Review", "value": needs_review, "url": worklist_url("needs_review", "newest", "", "", date_range)},
        {"label": "Identity Issues", "value": identity_issues, "url": worklist_url("identity_issues", "newest", "", "", date_range)},
        {"label": resolved_label, "value": resolved_count, "url": worklist_url("resolved", "newest", "", "", date_range)},
    ]


def get_request_type_breakdown(conn, date_range: str) -> list[dict[str, Any]]:
    range_where, range_params = range_clause(date_range)
    active_sql, active_params = active_case_clause()
    rows = conn.execute(
        f"""
        SELECT COALESCE(request_type, 'unknown') AS request_type, COUNT(*) AS count
        FROM cases
        WHERE ({range_where}) AND ({active_sql})
        GROUP BY COALESCE(request_type, 'unknown')
        """,
        (*range_params, *active_params),
    ).fetchall()
    counts = {row["request_type"] or "unknown": row["count"] for row in rows}
    max_count = max(counts.values(), default=0)
    breakdown = []
    for value, label in SUMMARY_REQUEST_TYPES:
        count = counts.get(value, 0)
        width = 0 if max_count == 0 else int((count / max_count) * 100)
        breakdown.append(
            {
                "value": value,
                "label": label,
                "count": count,
                "width": width,
                "url": worklist_url("open", "newest", "", value, date_range),
            }
        )
    return breakdown


def get_kpi_cards(conn, date_range: str) -> list[dict[str, Any]]:
    range_where, range_params = range_clause(date_range)
    today = datetime.now(timezone.utc).date().isoformat()
    active_sql, active_params = active_case_clause()
    resolved_sql, resolved_params = resolved_case_clause()
    red_flag_sql, red_flag_params = active_red_flag_clause()
    staff_review_sql, staff_review_params = active_staff_review_clause()
    identity_sql, identity_params = active_identity_check_clause()
    open_cases = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE ({range_where}) AND ({active_sql})",
        (*range_params, *active_params),
    ).fetchone()[0]
    red_flags = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE ({range_where}) AND ({red_flag_sql})",
        (*range_params, *red_flag_params),
    ).fetchone()[0]
    staff_review = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE ({range_where}) AND ({staff_review_sql})",
        (*range_params, *staff_review_params),
    ).fetchone()[0]
    identity_checks = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE ({range_where}) AND ({identity_sql})",
        (*range_params, *identity_params),
    ).fetchone()[0]
    resolved_today = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE resolved_at LIKE ? AND ({resolved_sql})",
        (f"{today}%", *resolved_params),
    ).fetchone()[0]
    return [
        {"label": "Open Cases", "value": open_cases, "url": worklist_url("open", "newest", "", "", date_range)},
        {"label": "Red Flags", "value": red_flags, "url": worklist_url("urgent_red_flags", "newest", "", "", date_range)},
        {"label": "Staff Review", "value": staff_review, "url": worklist_url("needs_review", "newest", "", "", date_range)},
        {"label": "Identity Checks", "value": identity_checks, "url": worklist_url("identity_issues", "newest", "", "", date_range)},
        {"label": "Processed Today", "value": resolved_today, "url": worklist_url("resolved_today", "newest", "", "", date_range)},
    ]


def get_urgent_attention(conn) -> dict[str, Any]:
    red_flag_sql, red_flag_params = active_red_flag_clause()
    staff_review_sql, staff_review_params = active_staff_review_clause()
    identity_sql, identity_params = active_identity_check_clause()
    alert_case_active_sql, alert_case_active_params = active_case_clause("c")
    red_flags = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE {red_flag_sql}",
        red_flag_params,
    ).fetchone()[0]
    staff_review = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE {staff_review_sql}",
        staff_review_params,
    ).fetchone()[0]
    identity_checks = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE {identity_sql}",
        identity_params,
    ).fetchone()[0]
    alert_row = conn.execute(
        f"""
        SELECT ae.alert_id, ae.timestamp, ae.alert_type, ae.severity, ae.count, ae.message,
               ae.first_call_id, ae.first_patient, ae.first_priority, ae.source_workflow,
               ae.dedupe_key, ae.acknowledged_at, ae.acknowledged_by, ae.acknowledgement_source
        FROM alert_events ae
        LEFT JOIN cases c ON c.call_id = ae.first_call_id
        WHERE ae.acknowledged_at IS NULL
          AND LOWER(COALESCE(ae.severity, '')) = 'critical'
          AND (
            COALESCE(TRIM(ae.first_call_id), '') = ''
            OR c.call_id IS NULL
            OR ({alert_case_active_sql})
          )
        ORDER BY ae.timestamp DESC, ae.id DESC
        LIMIT 1
        """,
        alert_case_active_params,
    ).fetchone()
    latest = alert_row_to_display(alert_row) if alert_row is not None else None
    return {
        "red_flags": red_flags,
        "staff_review": staff_review,
        "identity_checks": identity_checks,
        "latest": latest,
    }


def get_queue_status_card(conn, date_range: str) -> dict[str, Any]:
    """Return queue status counts matching the Churchtown sidebar design."""
    today = datetime.now(timezone.utc).date().isoformat()
    active_sql, active_params = active_case_clause()
    resolved_sql, resolved_params = resolved_case_clause()
    red_flag_sql, red_flag_params = active_red_flag_clause()
    open_count = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE {active_sql}", active_params
    ).fetchone()[0]
    resolved_today = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE resolved_at LIKE ? AND ({resolved_sql})",
        (f"{today}%", *resolved_params),
    ).fetchone()[0]
    red_flags = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE {red_flag_sql}", red_flag_params
    ).fetchone()[0]
    # Overdue: active cases older than 2 hours (7200 seconds)
    cutoff = datetime.now(timezone.utc).timestamp() - 7200
    overdue = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE ({active_sql}) AND COALESCE(call_timestamp_sort,0) > 0 AND call_timestamp_sort <= ?",
        (*active_params, cutoff),
    ).fetchone()[0]
    return {
        "open": open_count,
        "overdue": overdue,
        "resolved_today": resolved_today,
        "red_flags": red_flags,
    }


def get_call_analytics_card(conn) -> dict[str, Any]:
    """Return call analytics metrics for the sidebar."""
    total = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    safe = conn.execute("SELECT COUNT(*) FROM cases WHERE safe_to_queue = 1").fetchone()[0]
    avg_row = conn.execute(
        "SELECT AVG(turnaround_minutes) FROM cases WHERE turnaround_minutes IS NOT NULL AND turnaround_minutes > 0"
    ).fetchone()[0]
    avg_turnaround = round(avg_row) if avg_row else None
    success_rate = round((safe / total) * 100, 1) if total else 0.0
    resolved_sql, resolved_params = resolved_case_clause()
    dropped = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE LOWER(COALESCE(status,'')) LIKE '%unable%' OR LOWER(COALESCE(status,'')) LIKE '%fail%'"
    ).fetchone()[0]
    return {
        "total_calls": total,
        "safe_to_queue": safe,
        "dropped": dropped,
        "avg_turnaround": avg_turnaround,
        "success_rate": success_rate,
    }


def health_indicator(status: str, label: str = "") -> dict[str, str]:
    value = (status or "unknown").lower()
    if value in {"online", "test_ready", "active", "healthy"}:
        return {"state": "good", "label": label or "Active"}
    if value in {"offline", "error", "failed"}:
        return {"state": "bad", "label": label or "Offline"}
    if value in {"unknown", "degraded"}:
        return {"state": "warn", "label": label or "Degraded"}
    return {"state": "idle", "label": label or value.replace("_", " ").title()}


def get_system_health_card(services_status: dict[str, Any], demo_mode: bool) -> dict[str, Any]:
    services = services_status.get("services", {}) if services_status else {}
    return {
        "dashboard": health_indicator(services.get("dashboard", {}).get("status", "unknown")),
        "n8n": health_indicator(services.get("n8n", {}).get("status", "unknown")),
        "voice_agent": health_indicator(services.get("voice_agent", {}).get("status", "not_configured"), "Test Ready" if services.get("voice_agent", {}).get("status") == "test_ready" else ""),
        "google_push": {"state": "idle", "label": "Disabled for demo" if demo_mode else "Configured"},
    }


def compact_workload(workload: dict[str, Any]) -> dict[str, Any]:
    queue = workload.get("queue_depth", {})
    active = workload.get("active_processing", "not available")
    return {
        "status": str(workload.get("status", "unknown")).replace("_", " ").title(),
        "incoming": queue.get("incoming", 0),
        "awaiting_processing": queue.get("encrypted_raw", 0),
        "active_processing": "Not tracked" if str(active).lower() == "not available" else active,
        "processed_today": queue.get("processed_today", 0),
        "failed": queue.get("failed", 0),
        "failed_safety_queue": queue.get("failed_safety_queue", queue.get("deadletter", 0)),
        "last_checked": format_display_timestamp(workload.get("timestamp")),
    }


def clean_alert_message(message: object) -> str:
    text = str(message or "").strip()
    return text[1:].lstrip() if text.startswith("=") else text


def is_modal_worthy_alert(alert_type: object, severity: object) -> bool:
    alert_text = str(alert_type or "").strip().lower()
    severity_text = str(severity or "").strip().lower()
    if any(keyword in alert_text for keyword in NON_MODAL_ALERT_TYPE_KEYWORDS):
        return False
    if severity_text == "critical":
        return True
    return any(keyword in alert_text for keyword in MODAL_ALERT_TYPE_KEYWORDS)


def demo_mode_enabled_from_config() -> bool:
    config_dir = ROOT_DIR / "config"
    for path in (config_dir / "app_settings.json", config_dir / "dashboard_settings.json"):
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue
        for key in ("demo_mode", "test_mode", "demo_data_mode", "enable_demo_mode"):
            if data.get(key) is True:
                return True
    return False


def demo_data_present(conn) -> bool:
    clauses = " OR ".join(["call_id LIKE ?" for _prefix in DEMO_CALL_PREFIXES])
    params = tuple(f"{prefix}%" for prefix in DEMO_CALL_PREFIXES)
    count = conn.execute(f"SELECT COUNT(*) FROM cases WHERE {clauses}", params).fetchone()[0]
    return bool(count) or demo_mode_enabled_from_config()


def get_team_activity(conn, range_name: str = "today") -> dict[str, Any]:
    range_name = range_name if range_name in {"today", "7d", "30d"} else "today"
    resolved_range_where, resolved_range_params = resolved_at_range_clause(range_name)
    active_sql, active_params = active_case_clause()
    resolved_sql, resolved_params = resolved_case_clause()
    status_expr = normalized_status_sql()
    resolved_today = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE ({resolved_range_where}) AND ({resolved_sql})",
        (*resolved_range_params, *resolved_params),
    ).fetchone()[0]
    in_progress = conn.execute(
        f"""
        SELECT COUNT(*) FROM cases
        WHERE ({active_sql})
          AND ({status_expr} IN ({sql_placeholders(IN_PROGRESS_STATUS_NAMES)}) OR COALESCE(TRIM(assigned_to), '') <> '')
        """,
        (*active_params, *IN_PROGRESS_STATUS_NAMES),
    ).fetchone()[0]
    avg_turnaround = conn.execute(
        f"SELECT AVG(turnaround_minutes) FROM cases WHERE ({resolved_range_where}) AND turnaround_minutes IS NOT NULL",
        resolved_range_params,
    ).fetchone()[0]
    escalations = conn.execute(
        f"SELECT COUNT(*) FROM cases WHERE ({active_sql}) AND {status_expr} = ?",
        (*active_params, "escalated"),
    ).fetchone()[0]
    reopened = conn.execute(
        """
        SELECT COUNT(*) FROM audit_events
        WHERE action = ? AND timestamp >= ?
        """,
        ("staff_update", datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()),
    ).fetchone()[0]
    acknowledged_since = {
        "today": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0),
        "7d": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=6),
        "30d": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=29),
    }[range_name].isoformat()
    alerts_acknowledged = conn.execute(
        "SELECT COUNT(*) FROM alert_events WHERE acknowledged_at IS NOT NULL AND acknowledged_at >= ?",
        (acknowledged_since,),
    ).fetchone()[0]
    staff_rows = get_staff_users(conn, active_only=False)
    rows: list[dict[str, Any]] = []
    for staff in staff_rows:
        name = staff["display_name"]
        assigned_open = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE assigned_to = ? AND ({active_sql})",
            (name, *active_params),
        ).fetchone()[0]
        staff_resolved = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE ({resolved_range_where}) AND (resolved_by = ? OR assigned_to = ?) AND ({resolved_sql})",
            (*resolved_range_params, name, name, *resolved_params),
        ).fetchone()[0]
        staff_avg = conn.execute(
            f"SELECT AVG(turnaround_minutes) FROM cases WHERE ({resolved_range_where}) AND (resolved_by = ? OR assigned_to = ?) AND turnaround_minutes IS NOT NULL",
            (*resolved_range_params, name, name),
        ).fetchone()[0]
        staff_alerts = conn.execute(
            "SELECT COUNT(*) FROM alert_events WHERE acknowledged_by = ?",
            (name,),
        ).fetchone()[0]
        staff_escalations = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE last_edited_by = ? AND ({active_sql}) AND {status_expr} = ?",
            (name, *active_params, "escalated"),
        ).fetchone()[0]
        rows.append(
            {
                "staff_name": name,
                "role": staff["role"],
                "assigned_open": assigned_open,
                "resolved_today": staff_resolved,
                "avg_turnaround": "" if staff_avg is None else f"{int(staff_avg)} min",
                "alerts_acknowledged": staff_alerts,
                "escalations_handled": staff_escalations,
            }
        )
    rows.sort(key=lambda item: (item["resolved_today"], item["assigned_open"], item["alerts_acknowledged"]), reverse=True)
    return {
        "ok": True,
        "range": range_name,
        "team": {
            "resolved_today": resolved_today,
            "in_progress": in_progress,
            "average_turnaround": None if avg_turnaround is None else int(avg_turnaround),
            "escalations": escalations,
            "reopened": reopened,
            "alerts_acknowledged": alerts_acknowledged,
        },
        "rows": rows[:5],
    }


def folder_file_count(relative_folder: str, pattern: str = "*") -> int:
    folder = ROOT_DIR / relative_folder
    if not folder.exists():
        return 0
    return len([path for path in folder.glob(pattern) if path.is_file()])


def get_system_workload() -> dict[str, Any]:
    try:
        services = get_service_statuses().get("services", {})
    except Exception:
        services = fallback_service_statuses().get("services", {})
    queue_depth = {
        "incoming": folder_file_count("queue/incoming"),
        "encrypted_raw": folder_file_count("queue/encrypted_raw"),
        "processing": folder_file_count("queue/processing"),
        "processed_today": 0,
        "failed": folder_file_count("queue/failed"),
        "deadletter": folder_file_count("queue/deadletter"),
        "failed_safety_queue": folder_file_count("queue/deadletter"),
    }
    processed_folder = ROOT_DIR / "queue" / "processed"
    today = datetime.now(timezone.utc).date()
    if processed_folder.exists():
        queue_depth["processed_today"] = sum(
            1
            for path in processed_folder.glob("*")
            if path.is_file() and datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).date() == today
        )
    with connect() as conn:
        active_sql, active_params = active_case_clause()
        status_expr = normalized_status_sql()
        awaiting_cases = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE ({active_sql}) AND {status_expr} = ?",
            (*active_params, "awaiting processing"),
        ).fetchone()[0]
        active_processing_cases = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE ({active_sql}) AND {status_expr} = ?",
            (*active_params, "active processing"),
        ).fetchone()[0]
        failed_cases = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE ({active_sql}) AND {status_expr} = ?",
            (*active_params, "failed"),
        ).fetchone()[0]
        failed_safety_cases = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE ({active_sql}) AND {status_expr} = ?",
            (*active_params, "failed safety queue"),
        ).fetchone()[0]
        queue_depth["encrypted_raw"] += awaiting_cases
        queue_depth["processing"] += active_processing_cases
        queue_depth["failed"] += failed_cases
        queue_depth["failed_safety_queue"] += failed_safety_cases
        processed_cases_today = conn.execute(
            f"SELECT COUNT(*) FROM cases WHERE resolved_at LIKE ? AND ({resolved_case_clause()[0]})",
            (f"{today.isoformat()}%", *resolved_case_clause()[1]),
        ).fetchone()[0]
        queue_depth["processed_today"] = max(queue_depth["processed_today"], processed_cases_today)
        avg_turnaround = conn.execute(
            f"SELECT AVG(turnaround_minutes) FROM cases WHERE resolved_at LIKE ? AND ({resolved_case_clause()[0]}) AND turnaround_minutes IS NOT NULL",
            (f"{today.isoformat()}%", *resolved_case_clause()[1]),
        ).fetchone()[0]
    active_queue = queue_depth["incoming"] + queue_depth["encrypted_raw"] + queue_depth["processing"]
    status = "idle"
    if queue_depth["failed"] or queue_depth["deadletter"] or any(service.get("status") == "offline" for service in services.values()):
        status = "attention_needed"
    elif active_queue >= 10:
        status = "busy"
    elif active_queue or queue_depth["processed_today"]:
        status = "normal"
    return {
        "ok": True,
        "timestamp": utc_now_iso(),
        "status": status,
        "services": {
            "dashboard": services.get("dashboard", {}).get("status", "unknown"),
            "n8n": services.get("n8n", {}).get("status", "unknown"),
            "voice_agent": services.get("voice_agent", {}).get("status", "not_configured"),
        },
        "queue_depth": queue_depth,
        "active_processing": "not available" if queue_depth["processing"] == 0 else queue_depth["processing"],
        "throughput": {
            "calls_processed_today": processed_cases_today,
            "average_processing_time": "" if avg_turnaround is None else f"{int(avg_turnaround)} min",
        },
    }


def batch_resolve_block_reason(case: dict[str, Any], baseline: dict[str, Any]) -> str | None:
    if case.get("request_type") != baseline.get("request_type") or case.get("priority") != baseline.get("priority"):
        return "selected cases must have the same request type and priority"
    if case.get("priority") != "routine":
        return "priority is not eligible for batch resolve"
    if case.get("red_flags_present"):
        return "red flag cases cannot be batch resolved"
    if not case.get("safe_to_queue"):
        return "case is not safe to queue"
    if case.get("staff_review_required"):
        return "case requires staff review"
    if str(case.get("verification_status") or "").lower() not in SAFE_MATCH_STATUSES:
        return "case is not safely matched"
    if case.get("status") not in OPEN_BATCH_STATUSES:
        return "case status is not eligible"
    if case.get("status") in {"Escalated", "Needs Review", "Urgent Review"}:
        return "case is escalated or review-required"
    if not case.get("patient_name") or not case.get("callback_number"):
        return "case is missing required patient or callback details"
    return None


def batch_resolve_cases(conn, call_ids: list[str], staff_name: str, outcome_note: str) -> dict[str, Any]:
    if not call_ids:
        raise HTTPException(status_code=400, detail="call_ids is required")
    if len(set(call_ids)) != len(call_ids):
        raise HTTPException(status_code=400, detail="duplicate call_id values")
    placeholders = ", ".join(["?"] * len(call_ids))
    rows = conn.execute(f"SELECT * FROM cases WHERE call_id IN ({placeholders})", tuple(call_ids)).fetchall()
    cases = [row_to_dict(row) or {} for row in rows]
    found = {case["call_id"] for case in cases}
    missing = [call_id for call_id in call_ids if call_id not in found]
    if missing:
        raise HTTPException(status_code=404, detail={"message": "Cases not found", "call_ids": missing})
    baseline = cases[0]
    invalid = []
    for case in cases:
        reason = batch_resolve_block_reason(case, baseline)
        if reason:
            invalid.append({"call_id": case["call_id"], "ok": False, "reason": reason})
    if invalid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Batch resolve unavailable: selected cases must be same request type, routine, matched, safe to queue, and not require review.",
                "results": invalid,
            },
        )
    now = utc_now_iso()
    batch_id = f"batch-{uuid4()}"
    results = []
    for case in cases:
        updates = {
            "status": "Resolved",
            "outcome_notes": outcome_note,
            "staff_action": "Batch resolved",
            "resolved_by": staff_name,
            "resolved_at": case["resolved_at"] or now,
            "last_updated": now,
            "last_edited_at": now,
            "last_edited_by": staff_name,
            "turnaround_minutes": calculate_turnaround_minutes(case["timestamp"], case["resolved_at"] or now),
        }
        update_staff_fields(conn, case["call_id"], updates, staff_name)
        write_audit_event(
            conn,
            call_id=case["call_id"],
            action="batch_resolve",
            edited_by=staff_name,
            changed_fields=["batch_id", "status", "resolved_by"],
            old_values={"status": case.get("status"), "batch_id": None},
            new_values={"status": "Resolved", "batch_id": batch_id, "resolved_by": staff_name},
        )
        results.append({"call_id": case["call_id"], "ok": True, "batch_id": batch_id})
    return {"ok": True, "batch_id": batch_id, "resolved": len(results), "results": results}


def get_recording_for_case(conn, call_id: str) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT *
        FROM call_recordings
        WHERE call_id = ?
        ORDER BY updated_at DESC, id DESC
        LIMIT 1
        """,
        (call_id,),
    ).fetchone()
    recording = row_to_dict(row)
    if recording is None:
        return {
            "recording_status": "pending",
            "recording_label": "Pending",
            "recording_reference": "",
            "recording_help": "Recording expected after call completion.",
        }
    reference = recording.get("recording_local_path") or recording.get("recording_url") or ""
    recording["recording_label"] = str(recording.get("recording_status") or "pending").replace("_", " ").title()
    recording["recording_reference"] = reference
    recording["recording_help"] = "Recording metadata is stored locally. External URLs are not fetched."
    return recording


def attach_recording_metadata(
    conn,
    call_id: str,
    payload: dict[str, Any],
    staff_name: str,
) -> dict[str, Any]:
    case = conn.execute("SELECT call_id FROM cases WHERE call_id = ?", (call_id,)).fetchone()
    if case is None:
        raise HTTPException(status_code=404, detail="Call not found; recording attachment can be retried after the call is imported.")
    recording_url = str(payload.get("recording_url") or "").strip()
    recording_local_path = str(payload.get("recording_local_path") or "").strip()
    if not recording_url and not recording_local_path:
        raise HTTPException(status_code=400, detail="recording_url or recording_local_path is required")
    replace = payload.get("replace") is True
    existing = conn.execute(
        "SELECT * FROM call_recordings WHERE call_id = ? ORDER BY updated_at DESC, id DESC LIMIT 1",
        (call_id,),
    ).fetchone()
    if existing is not None and not replace:
        raise HTTPException(status_code=409, detail="Recording already attached; use replace=true to update metadata")
    now = utc_now_iso()
    status = "available" if recording_url or recording_local_path else "pending"
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    values = (
        call_id,
        recording_url,
        recording_local_path,
        now,
        as_optional_int(payload.get("duration_seconds")),
        status,
        json.dumps(metadata, sort_keys=True),
        staff_name,
        str(payload.get("source") or "dashboard").strip(),
        now,
        now,
    )
    conn.execute(
        """
        INSERT INTO call_recordings (
            call_id, recording_url, recording_local_path, recording_received_at,
            recording_duration_seconds, recording_status, recording_metadata_json,
            attached_by, source, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )
    write_audit_event(
        conn,
        call_id=call_id,
        action="recording_attached",
        edited_by=staff_name,
        changed_fields=["recording_status", "recording_reference"],
        old_values={},
        new_values={"recording_status": status, "recording_reference": recording_local_path or recording_url},
    )
    return get_recording_for_case(conn, call_id)


def as_optional_int(value: Any) -> int | None:
    if value in ("", None):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="duration_seconds must be numeric")


def resolve_skip_reason(case: dict[str, Any]) -> str | None:
    if is_resolved_case(case):
        return "already_resolved"
    if case.get("red_flags_present") or case.get("priority") == "999 Emergency":
        return "red_flag"
    if case.get("staff_review_required") or case.get("status") in {"Needs Review", "Urgent Review", "Escalated"}:
        return "requires_individual_review"
    if str(case.get("verification_status") or "").lower() not in SAFE_MATCH_STATUSES:
        return "identity_issue"
    if case.get("priority") != "routine":
        return "not_routine"
    if not case.get("safe_to_queue"):
        return "not_safe_to_queue"
    if not case.get("patient_name") or not case.get("callback_number"):
        return "missing_required_details"
    return None


def bulk_action_cases(conn, call_ids: list[str], action: str, staff_name: str, note: str) -> dict[str, Any]:
    if action not in {"assign_to_me", "start_review", "resolve_eligible_only"}:
        raise HTTPException(status_code=400, detail="Unsupported bulk action")
    if not call_ids:
        raise HTTPException(status_code=400, detail="call_ids is required")
    placeholders = ", ".join(["?"] * len(call_ids))
    rows = conn.execute(f"SELECT * FROM cases WHERE call_id IN ({placeholders})", tuple(call_ids)).fetchall()
    cases = [row_to_dict(row) or {} for row in rows]
    by_id = {case["call_id"]: case for case in cases}
    now = utc_now_iso()
    updated: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for call_id in call_ids:
        case = by_id.get(call_id)
        if case is None:
            skipped.append({"call_id": call_id, "reason": "not_found"})
            continue
        if action in {"assign_to_me", "start_review"}:
            if is_resolved_case(case):
                skipped.append({"call_id": call_id, "reason": "already_resolved"})
                continue
            updates = {
                "assigned_to": case.get("assigned_to") or staff_name,
                "status": "In Progress" if case.get("status") in {"", "New", "Open"} else case.get("status"),
                "last_updated": now,
                "last_edited_at": now,
                "last_edited_by": staff_name,
            }
            if action == "start_review":
                updates["status"] = "In Progress"
                updates["action_needed"] = case.get("action_needed") or DEFAULT_ACTION_NEEDED
            update_staff_fields(conn, call_id, updates, staff_name)
            updated.append({"call_id": call_id})
            continue
        reason = resolve_skip_reason(case)
        if reason:
            skipped.append({"call_id": call_id, "reason": reason})
            continue
        updates = {
            "status": "Resolved",
            "outcome_notes": note or case.get("outcome_notes") or DEFAULT_OUTCOME_NOTES,
            "staff_action": "Bulk resolved eligible case",
            "resolved_by": case.get("resolved_by") or staff_name,
            "resolved_at": case.get("resolved_at") or now,
            "last_updated": now,
            "last_edited_at": now,
            "last_edited_by": staff_name,
            "turnaround_minutes": calculate_turnaround_minutes(case["timestamp"], case.get("resolved_at") or now),
        }
        update_staff_fields(conn, call_id, updates, staff_name)
        updated.append({"call_id": call_id})
    action_label = action.replace("_", " ")
    return {
        "ok": True,
        "action": action,
        "updated": updated,
        "skipped": skipped,
        "message": f"{action_label.title()}: updated {len(updated)} case(s). Skipped {len(skipped)}.",
    }


def api_case(row: Any) -> dict[str, Any]:
    case = row_to_dict(row) or {}
    return {
        "call_id": case.get("call_id", ""),
        "patient_name": case.get("patient_name", ""),
        "request_type": case.get("request_type", ""),
        "priority": case.get("priority", ""),
        "red_flags_present": bool(case.get("red_flags_present")),
        "safe_to_queue": bool(case.get("safe_to_queue")),
        "status": case.get("status", ""),
        "call_summary": case.get("call_summary", ""),
    }


@app.get("/api/health")
def api_health() -> dict[str, Any]:
    ensure_ready()
    handoff_folder = BASE_DIR.parent / "outputs" / "handoff_json"
    with connect() as conn:
        case_count = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    return {
        "ok": True,
        "service": "JeffLocal",
        "timestamp": utc_now_iso(),
        "checks": {
            "dashboard": True,
            "database": True,
            "handoff_folder": handoff_folder.exists(),
            "case_count": case_count,
        },
    }


@app.post("/api/sync")
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


@app.get("/api/red-flags")
def api_red_flags() -> dict[str, Any]:
    ensure_ready()
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


@app.get("/api/overdue")
def api_overdue(threshold_hours: float = 24) -> dict[str, Any]:
    ensure_ready()
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


def alert_row_to_display(row: Any) -> dict[str, Any]:
    alert = row_to_dict(row) or {}
    alert["timestamp_display"] = format_display_timestamp(alert.get("timestamp"))
    alert["message"] = clean_alert_message(alert.get("message"))
    alert["modal_worthy"] = is_modal_worthy_alert(alert.get("alert_type"), alert.get("severity"))
    alert["acknowledged_at_display"] = format_display_timestamp(alert.get("acknowledged_at"))
    return alert


@app.get("/api/daily-summary")
def api_daily_summary() -> dict[str, Any]:
    ensure_ready()
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


@app.get("/api/staff-workload")
def api_staff_workload() -> dict[str, Any]:
    """Live per-staff workload: open, in-progress, resolved today for each active staff member."""
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
            # Open (unresolved, assigned to this staff member)
            open_count = conn.execute(
                "SELECT COUNT(*) FROM cases WHERE assigned_to=? AND status NOT IN ('resolved','cancelled','closed')",
                (assigned,),
            ).fetchone()[0]
            # In-progress
            inprogress = conn.execute(
                "SELECT COUNT(*) FROM cases WHERE assigned_to=? AND status='in_progress'",
                (assigned,),
            ).fetchone()[0]
            # Resolved today
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
        # Team totals
        totals = conn.execute(
            """SELECT
                SUM(CASE WHEN status NOT IN ('resolved','cancelled','closed') THEN 1 ELSE 0 END) AS open,
                SUM(CASE WHEN status='in_progress' THEN 1 ELSE 0 END) AS in_progress,
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


def service_status(name: str, status: str, url: str, details: str, checked_at: str) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "url": url,
        "details": details,
        "last_checked": checked_at,
    }


def fallback_service_statuses(reason: str = "Service status unavailable") -> dict[str, Any]:
    timestamp = utc_now_iso()
    return {
        "ok": True,
        "timestamp": timestamp,
        "services": {
            "dashboard": service_status(
                "JeffLocal Dashboard",
                "unknown",
                LOCAL_SERVICE_URLS["dashboard"],
                reason,
                timestamp,
            ),
            "n8n": service_status(
                "n8n",
                "unknown",
                LOCAL_SERVICE_URLS["n8n"],
                reason,
                timestamp,
            ),
            "voice_agent": service_status(
                "Voice Agent Intake",
                "not_configured",
                LOCAL_SERVICE_URLS["voice_agent"],
                "Live voice provider not configured; local test intake can be checked after services refresh.",
                timestamp,
            ),
        },
    }


def check_local_n8n(timeout_seconds: float = 2.0) -> dict[str, Any]:
    """Check n8n health via /healthz (not /). Timeout raised to 2 s so the
    dashboard doesn't falsely report n8n as Offline when it's merely slow."""
    checked_at = utc_now_iso()
    try:
        conn = http.client.HTTPConnection("localhost", 5678, timeout=timeout_seconds)
        conn.request("GET", "/healthz")
        response = conn.getresponse()
        response.read(256)
        conn.close()
        return service_status(
            "n8n",
            "online" if response.status < 500 else "unknown",
            LOCAL_SERVICE_URLS["n8n"],
            f"HTTP {response.status}",
            checked_at,
        )
    except Exception as exc:
        return service_status(
            "n8n",
            "offline",
            LOCAL_SERVICE_URLS["n8n"],
            f"Localhost check failed: {type(exc).__name__}",
            checked_at,
        )


def get_service_statuses() -> dict[str, Any]:
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
        n8n_status = check_local_n8n()
    except Exception as exc:
        n8n_status = service_status(
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
            "dashboard": service_status(
                "JeffLocal Dashboard",
                "online" if dashboard_ok else "unknown",
                LOCAL_SERVICE_URLS["dashboard"],
                dashboard_detail,
                timestamp,
            ),
            "n8n": n8n_status,
            "voice_agent": service_status(
                "Voice Agent Intake",
                voice_status,
                LOCAL_SERVICE_URLS["voice_agent"],
                voice_details,
                timestamp,
            ),
        },
    }


@app.get("/api/services/status")
def api_services_status() -> dict[str, Any]:
    return get_service_statuses()


@app.post("/api/services/refresh")
def api_services_refresh(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
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
    status = get_service_statuses()
    status["actions"] = actions
    return status



@app.get("/staff")
def staff_page(request: Request) -> Any:
    ensure_ready()
    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        staff_users = get_staff_users(conn, active_only=False)
        invitation_rows = conn.execute(
            """
            SELECT invitations.id, invitations.email, invitations.role, invitations.status,
                   invitations.created_at, invitations.expires_at, invitations.cancelled_at,
                   staff.display_name AS invited_by
            FROM staff_invitations AS invitations
            LEFT JOIN staff_users AS staff ON staff.id = invitations.invited_by_staff_id
            ORDER BY invitations.created_at DESC, invitations.id DESC
            """
        ).fetchall()
    return templates.TemplateResponse(
        request,
        "staff.html",
        {
            "current_staff": current_staff,
            "staff_users": staff_users,
            "active_staff_users": [staff for staff in staff_users if staff.get("active")],
            "inactive_staff_users": [staff for staff in staff_users if not staff.get("active")],
            "invitations": [row_to_dict(row) for row in invitation_rows],
            "roles": ["admin", "staff", "readonly"],
            "active_nav": "staff",
            "can_manage_staff": staff_can_manage(current_staff),
        },
    )


@app.post("/staff/create")
def staff_create(
    request: Request,
    display_name: str = Form(...),
    username: str = Form(""),
    email: str = Form(""),
    role: str = Form("staff"),
    password: str = Form(""),
    pin: str = Form(""),
) -> RedirectResponse:
    ensure_ready()
    display_name = display_name.strip()
    username = username.strip().lower().replace(" ", ".")
    email = email.strip()
    role = role.strip()
    if not display_name:
        raise HTTPException(status_code=400, detail="display_name is required")
    if not username:
        # Auto-generate username from display name
        username = display_name.lower().replace(" ", ".")
    if role not in STAFF_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported role")
    if password and len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if pin and not pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN must be numeric digits only")
    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        require_staff_admin(current_staff)
        now = utc_now_iso()
        pw_hash = hash_password(password) if password else None
        pin_hash = hash_pin(pin) if pin else None
        conn.execute(
            """
            INSERT INTO staff_users (display_name, username, email, role, password_hash, pin_hash,
                                     failed_attempts, must_change_password, active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, 0, 1, ?, ?)
            """,
            (display_name, username, email or None, role, pw_hash, pin_hash, now, now),
        )
        write_audit_event(
            conn,
            call_id="staff",
            action="staff_created",
            edited_by=staff_display(current_staff),
            changed_fields=["display_name", "username", "email", "role", "active"],
            old_values={},
            new_values={"display_name": display_name, "username": username, "email": email, "role": role, "active": True},
        )
    return RedirectResponse("/staff", status_code=303)


@app.post("/staff/{staff_id}/edit")
def staff_edit(
    request: Request,
    staff_id: int,
    display_name: str = Form(...),
    email: str = Form(""),
    role: str = Form("staff"),
    active: str = Form(""),
) -> RedirectResponse:
    ensure_ready()
    display_name = display_name.strip()
    email = email.strip()
    role = role.strip()
    if not display_name:
        raise HTTPException(status_code=400, detail="display_name is required")
    if role not in STAFF_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported role")
    active_value = 1 if active.lower() in {"yes", "true", "1", "on"} else 0
    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        require_staff_admin(current_staff)
        old = get_staff_any_by_id(conn, staff_id)
        if old is None:
            raise HTTPException(status_code=404, detail="Staff user not found")
        conn.execute(
            """
            UPDATE staff_users
            SET display_name = ?, email = ?, role = ?, active = ?, updated_at = ?
            WHERE id = ?
            """,
            (display_name, email or None, role, active_value, utc_now_iso(), staff_id),
        )
        write_audit_event(
            conn,
            call_id="staff",
            action="staff_updated",
            edited_by=staff_display(current_staff),
            changed_fields=["display_name", "email", "role", "active"],
            old_values={key: old.get(key) for key in ("display_name", "email", "role", "active")},
            new_values={"display_name": display_name, "email": email, "role": role, "active": bool(active_value)},
        )
    return RedirectResponse("/staff", status_code=303)


@app.post("/staff/{staff_id}/deactivate")
def staff_deactivate(request: Request, staff_id: int) -> RedirectResponse:
    ensure_ready()
    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        require_staff_admin(current_staff)
        old = get_staff_any_by_id(conn, staff_id)
        if old is None:
            raise HTTPException(status_code=404, detail="Staff user not found")
        conn.execute("UPDATE staff_users SET active = 0, updated_at = ? WHERE id = ?", (utc_now_iso(), staff_id))
        write_audit_event(
            conn,
            call_id="staff",
            action="staff_deactivated",
            edited_by=staff_display(current_staff),
            changed_fields=["active"],
            old_values={"active": old.get("active")},
            new_values={"active": False, "staff_id": staff_id},
        )
    return RedirectResponse("/staff", status_code=303)


@app.post("/staff/{staff_id}/reactivate")
def staff_reactivate(request: Request, staff_id: int) -> RedirectResponse:
    ensure_ready()
    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        require_staff_admin(current_staff)
        old = get_staff_any_by_id(conn, staff_id)
        if old is None:
            raise HTTPException(status_code=404, detail="Staff user not found")
        conn.execute("UPDATE staff_users SET active = 1, updated_at = ? WHERE id = ?", (utc_now_iso(), staff_id))
        write_audit_event(
            conn,
            call_id="staff",
            action="staff_reactivated",
            edited_by=staff_display(current_staff),
            changed_fields=["active"],
            old_values={"active": old.get("active")},
            new_values={"active": True, "staff_id": staff_id},
        )
    return RedirectResponse("/staff", status_code=303)


@app.get("/staff/invitations")
def staff_invitations_page(request: Request) -> Any:
    return staff_page(request)


@app.post("/staff/invitations/create")
def staff_invitation_create(
    request: Request,
    email: str = Form(...),
    role: str = Form("staff"),
) -> RedirectResponse:
    ensure_ready()
    email = email.strip()
    role = role.strip()
    if not email:
        raise HTTPException(status_code=400, detail="email is required")
    if role not in STAFF_ROLES:
        raise HTTPException(status_code=400, detail="Unsupported role")
    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        require_staff_admin(current_staff)
        now = utc_now_iso()
        token_hash = hashlib.sha256(f"{email}|{role}|{now}".encode("utf-8")).hexdigest()
        conn.execute(
            """
            INSERT INTO staff_invitations (
                email, role, invited_by_staff_id, token_hash, status, created_at, expires_at,
                accepted_at, cancelled_at
            )
            VALUES (?, ?, ?, ?, 'pending', ?, NULL, NULL, NULL)
            """,
            (email, role, current_staff.get("id"), token_hash, now),
        )
        write_audit_event(
            conn,
            call_id="staff",
            action="staff_invitation_created",
            edited_by=staff_display(current_staff),
            changed_fields=["email", "role", "status"],
            old_values={},
            new_values={"email": email, "role": role, "status": "pending", "email_sending": "not_enabled"},
        )
    return RedirectResponse("/staff", status_code=303)


@app.post("/staff/invitations/{invitation_id}/cancel")
def staff_invitation_cancel(request: Request, invitation_id: int) -> RedirectResponse:
    ensure_ready()
    with connect() as conn:
        current_staff = current_staff_from_request(request, conn)
        require_staff_admin(current_staff)
        row = conn.execute("SELECT * FROM staff_invitations WHERE id = ?", (invitation_id,)).fetchone()
        invitation = row_to_dict(row)
        if invitation is None:
            raise HTTPException(status_code=404, detail="Invitation not found")
        conn.execute(
            "UPDATE staff_invitations SET status = 'cancelled', cancelled_at = ? WHERE id = ?",
            (utc_now_iso(), invitation_id),
        )
        write_audit_event(
            conn,
            call_id="staff",
            action="staff_invitation_cancelled",
            edited_by=staff_display(current_staff),
            changed_fields=["status", "cancelled_at"],
            old_values={"status": invitation.get("status")},
            new_values={"status": "cancelled", "invitation_id": invitation_id},
        )
    return RedirectResponse("/staff", status_code=303)


@app.get("/api/staff/performance")
def api_staff_performance(range: str = "today") -> dict[str, Any]:
    ensure_ready()
    with connect() as conn:
        return get_team_activity(conn, range)


@app.get("/api/system/workload")
def api_system_workload() -> dict[str, Any]:
    ensure_ready()
    return get_system_workload()


@app.post("/api/cases/batch-resolve")
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


@app.post("/api/cases/bulk-action")
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


@app.post("/api/calls/{call_id}/recording")
def api_call_recording(call_id: str, request: Request, payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    ensure_ready()
    with connect() as conn:
        staff = current_staff_from_request(request, conn)
        require_staff_edit(staff)
        recording = attach_recording_metadata(conn, call_id, payload, staff_display(staff))
    return {"ok": True, "recording": recording}


@app.post("/api/cases/{call_id}/copy-audit")
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


@app.post("/api/cases/{call_id}/action")
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

        update_staff_fields(conn, call_id, updates, updates.get("last_edited_by", ""))
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


@app.post("/api/cases/{call_id}/enrich")
def api_case_enrich(call_id: str, request: Request) -> dict[str, Any]:
    """Re-run Ollama enrichment on an existing case and update ai_summary."""
    ensure_ready()
    from .importer import ollama_clinical_summary
    with connect() as conn:
        require_staff_edit(current_staff_from_request(request, conn))
        row = conn.execute("SELECT * FROM cases WHERE call_id = ?", (call_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Case not found")
        case = row_to_dict(row)
        transcript = case.get("transcript") or ""
        summary = ollama_clinical_summary(transcript, case)
        if not summary:
            return {"ok": False, "detail": "Ollama unavailable or no transcript"}
        now = utc_now_iso()
        conn.execute(
            "UPDATE cases SET ai_summary = ?, call_summary = ?, last_updated = ? WHERE call_id = ?",
            (summary, summary, now, call_id),
        )
        conn.commit()
    return {"ok": True, "ai_summary": summary}


@app.get("/api/cases/{call_id}")
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
    }


def alert_dedupe_key(payload: dict[str, Any]) -> str:
    parts = [
        str(payload.get("alert_type", "")).strip().lower(),
        str(payload.get("first_call_id", "")).strip().lower(),
        str(payload.get("source_workflow", "")).strip().lower(),
    ]
    return "|".join(parts)


def sanitize_alert_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "alert_type": str(payload.get("alert_type", "")).strip(),
        "severity": str(payload.get("severity", "")).strip(),
        "count": int(payload.get("count") or 0),
        "message": clean_alert_message(payload.get("message", "")),
        "first_call_id": str(payload.get("first_call_id", "")).strip(),
        "first_patient": str(payload.get("first_patient", "")).strip(),
        "first_priority": str(payload.get("first_priority", "")).strip(),
        "source_workflow": str(payload.get("source_workflow", "")).strip(),
    }


def write_alert_jsonl(alert: dict[str, Any]) -> None:
    ALERT_DIR.mkdir(parents=True, exist_ok=True)
    jsonl_path = ALERT_DIR / f"alerts_{alert['timestamp'][:10]}.jsonl"
    with jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(alert, sort_keys=True) + "\n")


@app.post("/api/alerts/log")
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
            return {
                "ok": True,
                "logged": False,
                "deduped": True,
                "reason": "duplicate_recent_alert",
            }

        timestamp = utc_now_iso()
        alert_id = f"alert-{uuid4()}"
        alert.update(
            {
                "alert_id": alert_id,
                "timestamp": timestamp,
                "dedupe_key": dedupe_key,
            }
        )
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
                alert["alert_id"],
                alert["timestamp"],
                alert["alert_type"],
                alert["severity"],
                alert["count"],
                alert["message"],
                alert["first_call_id"],
                alert["first_patient"],
                alert["first_priority"],
                alert["source_workflow"],
                alert["dedupe_key"],
            ),
        )
        conn.commit()
    write_alert_jsonl(alert)
    return {
        "ok": True,
        "logged": True,
        "alert_id": alert_id,
        "timestamp": timestamp,
    }


@app.get("/api/alerts/recent")
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
    alerts = [row_to_dict(row) for row in rows]
    return {
        "ok": True,
        "limit": safe_limit,
        "count": len(alerts),
        "alerts": [alert_row_to_display(row) for row in rows],
    }


@app.get("/api/alerts/unacknowledged")
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


@app.post("/api/alerts/{alert_id}/acknowledge")
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


@app.get("/alerts")
def alerts_page(
    request: Request,
    severity: str = "all",
    limit: int = 50,
) -> Any:
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


def is_encrypted_envelope(call: dict[str, Any]) -> bool:
    required_fields = {
        "protocol",
        "alg",
        "key_id",
        "sender_id",
        "message_id",
        "timestamp_utc",
        "nonce",
        "encrypted_key",
        "iv",
        "ciphertext",
        "tag",
        "signature_alg",
        "signature",
    }
    return required_fields.issubset(call.keys())


def call_id_from_test_call(call: dict[str, Any]) -> str:
    if is_encrypted_envelope(call):
        return str(call.get("message_id", "")).strip()
    return str(call.get("call_id", "")).strip()


def encrypt_local_test_call(call: dict[str, Any]) -> dict[str, Any]:
    fixtures_dir = ROOT_DIR / "tests" / "fixtures"
    if str(fixtures_dir) not in sys.path:
        sys.path.insert(0, str(fixtures_dir))
    from live_lookup_test_payloads import encrypt_envelope  # type: ignore

    return encrypt_envelope(call)


def archive_n8ntest_artifacts() -> dict[str, Any]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive_root = ROOT_DIR / "backup" / f"n8ntest_regeneration_{timestamp}"
    summary = []
    total_archived = 0
    for relative_folder in N8NTEST_ARCHIVE_FOLDERS:
        source_folder = ROOT_DIR / relative_folder
        archived_count = 0
        if source_folder.exists():
            for path in sorted(source_folder.glob("*")):
                if not path.is_file():
                    continue
                target_folder = archive_root / relative_folder
                target_folder.mkdir(parents=True, exist_ok=True)
                path.replace(target_folder / path.name)
                archived_count += 1
                total_archived += 1
        summary.append({"folder": relative_folder.replace("/", "\\"), "archived_count": archived_count})
    return {
        "archive_root": str(archive_root) if total_archived else "",
        "total_archived": total_archived,
        "folders": summary,
    }


def write_n8ntest_envelopes(calls: list[dict[str, Any]]) -> list[str]:
    output_dir = ROOT_DIR / "queue" / "encrypted_raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for call in calls:
        call_id = call_id_from_test_call(call)
        envelope = call if is_encrypted_envelope(call) else encrypt_local_test_call(call)
        path = output_dir / f"{call_id}.json"
        path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
        written.append(str(path))
    return written


def run_encrypted_cycle_disable_google_push() -> dict[str, Any]:
    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(ROOT_DIR / "app" / "run_encrypted_intake_cycle.ps1"),
        "-DisableGooglePush",
    ]
    result = subprocess.run(
        command,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
    }


def count_n8ntest_files(relative_folder: str, pattern: str = "*N8NTEST*") -> int:
    folder = ROOT_DIR / relative_folder
    if not folder.exists():
        return 0
    return len([path for path in folder.glob(pattern) if path.is_file()])


def count_batch_files(relative_folder: str, call_ids: list[str], suffix: str = "") -> int:
    folder = ROOT_DIR / relative_folder
    if not folder.exists():
        return 0
    count = 0
    for call_id in call_ids:
        candidates = [folder / f"{call_id}{suffix}", folder / f"{call_id}.json"] if suffix else [folder / f"{call_id}.json"]
        if any(path.exists() and path.is_file() for path in candidates):
            count += 1
    return count


def n8ntest_dashboard_cases(call_ids: list[str] | None = None) -> list[dict[str, Any]]:
    with connect() as conn:
        if call_ids:
            placeholders = ", ".join(["?"] * len(call_ids))
            rows = conn.execute(
                f"""
                SELECT call_id, patient_name, request_type, priority, red_flags_present,
                       safe_to_queue, staff_review_required, verification_status, status,
                       call_summary
                FROM cases
                WHERE call_id IN ({placeholders})
                ORDER BY call_id ASC
                """,
                tuple(call_ids),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT call_id, patient_name, request_type, priority, red_flags_present,
                       safe_to_queue, staff_review_required, verification_status, status,
                       call_summary
                FROM cases
                ORDER BY call_id ASC
                """
            ).fetchall()
    cases = []
    for row in rows:
        case = row_to_dict(row) or {}
        case["red_flags_present"] = bool(case.get("red_flags_present"))
        case["safe_to_queue"] = bool(case.get("safe_to_queue"))
        case["staff_review_required"] = bool(case.get("staff_review_required"))
        cases.append(case)
    return cases


# ── HMAC verification ─────────────────────────────────────────────────────────


def verify_hmac_signature(
    payload_bytes: bytes,
    signature_header: str,
    secret: bytes,
) -> bool:
    """
    Verify an HMAC-SHA256 webhook signature in constant time.

    The caller (Jeff / n8n) must include the header:
        X-Hub-Signature-256: sha256=<hex-digest>

    The digest is computed over the raw request body using the shared secret.
    Comparison uses ``hmac.compare_digest`` to prevent timing attacks.

    Args:
        payload_bytes:    Raw request body bytes (must be read before JSON parsing).
        signature_header: Value of the X-Hub-Signature-256 header (e.g. "sha256=abc123").
        secret:           Shared secret as bytes.  Must not be empty — callers are
                          responsible for checking that the secret is configured before
                          calling this function.

    Returns:
        True  — signature present, well-formed, and matches.
        False — header missing, malformed (no "sha256=" prefix), or digest mismatch.

    Security notes:
        - Constant-time comparison via hmac.compare_digest; safe against timing attacks.
        - Payload bytes are never logged.
        - Algorithm is HMAC-SHA256 (suitable for webhook authentication per OWASP).
    """
    if not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


async def verify_webhook_hmac(request: Request) -> None:
    """
    FastAPI dependency: enforce HMAC-SHA256 signature on the raw request body.

    Reads the secret from the ``JEFF_WEBHOOK_SECRET`` environment variable.
    If the variable is absent or empty, verification is skipped — this allows
    local sandbox runs without a configured secret, but Saeed MUST set the
    variable before any live traffic reaches this endpoint.

    Raises:
        HTTPException(401): if the secret is set and the signature is absent,
                            malformed, or does not match.  The response detail
                            contains no secret material and no payload content.
    """
    secret = os.environ.get("JEFF_WEBHOOK_SECRET", "").encode()
    if not secret:
        _log.warning(
            "HMAC verification SKIPPED — JEFF_WEBHOOK_SECRET not set. "
            "Set this env var before accepting live traffic."
        )
        return
    sig_header = request.headers.get("X-Hub-Signature-256", "")
    body = await request.body()
    if not verify_hmac_signature(body, sig_header, secret):
        _log.warning(
            "Webhook HMAC verification FAILED — path=%s method=%s "
            "sig_header_present=%s",
            request.url.path,
            request.method,
            bool(sig_header),
        )
        raise HTTPException(status_code=401, detail="Invalid or missing webhook signature")


@app.post("/api/n8n/test-intake-batch")
async def api_n8n_test_intake_batch(
    request: Request,
    payload: dict[str, Any] = Body(...),
    _hmac_verified: None = Depends(verify_webhook_hmac),
) -> dict[str, Any]:
    """SANDBOX / TEST ONLY — bypasses n8n entirely.
    All real calls must route through n8n webhook: POST /webhook/jefflocal-test-intake (port 5678).
    This endpoint is guarded by test_mode=true and N8NTEST-/GPDEMO- prefix requirements.
    It will be removed before production deployment.
    """
    ensure_ready()
    if payload.get("test_mode") is not True:
        raise HTTPException(status_code=400, detail="test_mode must be true")
    if payload.get("disable_google_push") is not True:
        raise HTTPException(status_code=400, detail="disable_google_push must be true")

    batch_id = str(payload.get("batch_id", "")).strip()

    calls = payload.get("calls")
    if not isinstance(calls, list):
        raise HTTPException(status_code=400, detail="calls must be an array")
    if not 1 <= len(calls) <= 5:
        raise HTTPException(status_code=400, detail="calls must contain 1 to 5 items")
    if not all(isinstance(call, dict) for call in calls):
        raise HTTPException(status_code=400, detail="each call must be an object")

    call_ids = [call_id_from_test_call(call) for call in calls]
    if len(set(call_ids)) != len(call_ids):
        raise HTTPException(status_code=400, detail="duplicate call_id values in batch")

    archive = archive_n8ntest_artifacts() if payload.get("refresh_artifacts", True) is True else {"total_archived": 0, "folders": []}
    written = write_n8ntest_envelopes(calls)
    cycle = run_encrypted_cycle_disable_google_push()
    if cycle["returncode"] != 0:
        raise HTTPException(status_code=500, detail={"message": "encrypted intake cycle failed", "cycle": cycle})

    with connect() as conn:
        dashboard_imported = import_handoffs(conn, pattern="*_handoff.json")

    total_processed = count_n8ntest_files("queue/processed", "*")
    total_handoffs = count_n8ntest_files("outputs/handoff_json", "*_handoff.json")
    batch_processed = count_batch_files("queue/processed", call_ids)
    batch_handoffs = count_batch_files("outputs/handoff_json", call_ids, "_handoff.json")
    batch_failed = count_batch_files("queue/failed", call_ids)
    batch_deadletter = count_batch_files("queue/deadletter", call_ids)
    try:
        cases = n8ntest_dashboard_cases(call_ids)
    except TypeError:
        cases = n8ntest_dashboard_cases()
    return {
        "ok": True,
        "batch_id": batch_id,
        "received": len(calls),
        "written": len(written),
        "batch_processed": batch_processed,
        "batch_handoffs": batch_handoffs,
        "batch_failed": batch_failed,
        "batch_deadletter": batch_deadletter,
        "total_n8ntest_handoffs": total_handoffs,
        "dashboard_imported_batch": len(cases),
        "processed": batch_processed if batch_processed else total_processed,
        "handoffs": batch_handoffs if batch_handoffs else total_handoffs,
        "failed": batch_failed,
        "deadletter": batch_deadletter,
        "google_push": "disabled_for_test",
        "dashboard_imported": dashboard_imported,
        "dashboard_imported_total": dashboard_imported,
        "archive": archive,
        "cases": cases,
    }


@app.get("/")
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
        visible_request_mix = [item for item in request_type_breakdown if item["count"] > 0][:5]
        current_staff = current_staff_from_request(request, conn)
        staff_users = get_staff_users(conn)
        show_demo_banner = demo_data_present(conn)
        staff_activity = get_team_activity(conn, "today")
        urgent_attention = get_urgent_attention(conn)
        queue_status_card = get_queue_status_card(conn, date_range)
        call_analytics_card = get_call_analytics_card(conn)
        range_where, range_params = range_clause(date_range)
        # Live per-staff workload for sidebar widget (seeded server-side, refreshed by AJAX)
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        staff_workload_rows = conn.execute(
            "SELECT display_name, username FROM staff_users WHERE active=1 ORDER BY display_name"
        ).fetchall()
        staff_workload_list = []
        for sw in staff_workload_rows:
            _name = sw["display_name"] or sw["username"] or "Unknown"
            _open = conn.execute(
                "SELECT COUNT(*) FROM cases WHERE assigned_to=? AND status NOT IN ('resolved','cancelled','closed')",
                (_name,),
            ).fetchone()[0]
            _prog = conn.execute(
                "SELECT COUNT(*) FROM cases WHERE assigned_to=? AND status='in_progress'", (_name,)
            ).fetchone()[0]
            _done = conn.execute(
                "SELECT COUNT(*) FROM cases WHERE resolved_by=? AND resolved_at LIKE ?",
                (_name, f"{today_str}%"),
            ).fetchone()[0]
            staff_workload_list.append({"name": _name, "open": _open, "in_progress": _prog, "resolved_today": _done})
    try:
        services_status = get_service_statuses()
    except Exception as exc:
        services_status = fallback_service_statuses(f"Service status unavailable: {type(exc).__name__}")
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


@app.get("/requests")
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


@app.get("/patients")
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


@app.get("/reports")
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


@app.get("/settings")
def settings_page(request: Request) -> Any:
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
            import os as _os
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


@app.post("/import")
def import_cases() -> RedirectResponse:
    ensure_ready()
    with connect() as conn:
        import_handoffs(conn)
    return RedirectResponse("/", status_code=303)


@app.post("/api/import")
def api_import_cases() -> dict[str, Any]:
    """JSON import endpoint — returns count of newly imported cases.
    Used by the dashboard AJAX import button to trigger audio/toast on new arrivals."""
    ensure_ready()
    with connect() as conn:
        count = import_handoffs(conn)
    return {"ok": True, "imported": count, "timestamp": utc_now_iso()}


@app.get("/case/{call_id}")
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


@app.post("/case/{call_id}/update")
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
        submitted["outcome_notes"] = submitted["outcome_notes"] or old.get("outcome_notes") or (DEFAULT_OUTCOME_NOTES if wants_resolve and mark_checked else "")

        status_is_terminal = normalize_case_status(submitted["status"]) in TERMINAL_CASE_STATUSES
        if wants_resolve and mark_checked:
            needs_notes = (
                old["red_flags_present"]
                or old["priority"] == "999 Emergency"
                or old.get("verification_status") in IDENTITY_REVIEW_STATUSES
            )
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


@app.post("/case/{call_id}/quick_action")
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

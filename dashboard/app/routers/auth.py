"""
Auth and profile routes — extracted from main.py.

Covers: /login, /logout, /forgot, /reset, /profile and all sub-routes.
"""
from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse

from ..audit import write_audit_event
from ..auth import (
    clear_failed_attempts,
    consume_reset_token,
    create_reset_token,
    create_session,
    get_session_user,
    invalidate_session,
    is_account_locked,
    lookup_user_by_username,
    purge_expired_sessions,
    record_failed_attempt,
    set_new_password,
    set_new_pin,
    verify_password,
)
from ..consts import SESSION_COOKIE
from ..db import connect
from ..helpers import current_staff_from_request, ensure_ready

router = APIRouter()

MAX_FAILED_ATTEMPTS = 5


@router.get("/login")
def login_page(request: Request, next: str = "/", error: str = "", info: str = ""):
    from ..main import templates  # late import to avoid circular dependency
    safe_next = next if next and next.startswith("/") and not next.startswith("//") else "/"
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with connect() as conn:
            conn.row_factory = __import__("sqlite3").Row
            user = get_session_user(conn, token)
        if user:
            return RedirectResponse(url=safe_next, status_code=302)
    return templates.TemplateResponse(request, "login.html", {
        "error": error, "info": info, "next": safe_next,
        "prefill_username": "", "auth_method": "password",
    })


@router.post("/login")
async def login_post(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    pin: str = Form(""),
    auth_method: str = Form("password"),
    next: str = Form("/"),
):
    from ..main import templates
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
            ok = bool(stored) and __import__("app.auth", fromlist=["verify_pin"]).verify_pin(pin.strip(), stored)
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
    if force_change:
        safe_next = "/profile?must_change=1"
    response = RedirectResponse(url=safe_next, status_code=302)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="lax", max_age=3600, secure=True)
    return response


@router.get("/logout")
def logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        with connect() as conn:
            invalidate_session(conn, token)
    resp = RedirectResponse(url="/login?info=You+have+been+signed+out.", status_code=302)
    resp.delete_cookie(SESSION_COOKIE)
    return resp


@router.get("/forgot")
def forgot_page(request: Request):
    from ..main import templates
    return templates.TemplateResponse(request, "forgot.html", {
        "mode": "request", "error": "", "success": "", "reset_link": None,
    })


@router.post("/forgot")
async def forgot_post(request: Request, username: str = Form(""), reset_type: str = Form("password")):
    from ..main import templates
    username = username.strip().lower()
    reset_link = None
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
                pass
    return templates.TemplateResponse(request, "forgot.html", {
        "mode": "request", "error": "", "success": success, "reset_link": reset_link,
    })


@router.get("/reset")
def reset_page(request: Request, token: str = "", type: str = "password"):
    from ..main import templates
    if not token:
        return RedirectResponse(url="/forgot", status_code=302)
    return templates.TemplateResponse(request, "forgot.html", {
        "mode": "reset", "token": token, "reset_type": type, "error": "",
    })


@router.post("/reset")
async def reset_post(
    request: Request,
    token: str = Form(""),
    reset_type: str = Form("password"),
    new_value: str = Form(""),
    confirm_value: str = Form(""),
):
    from ..main import templates
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


@router.get("/profile")
def profile_page(
    request: Request,
    pw_error: str = "", pw_success: str = "",
    pin_error: str = "", pin_success: str = "",
):
    from ..main import templates
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


@router.post("/profile/change-password")
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
        ip = request.client.host if request.client else ""
        ua = request.headers.get("user-agent", "")
        new_token = create_session(conn, current_staff["id"], ip, ua)
    resp = RedirectResponse(url="/profile?pw_success=Password+updated+successfully.", status_code=302)
    resp.set_cookie(SESSION_COOKIE, new_token, httponly=True, samesite="lax", max_age=3600, secure=True)
    return resp


@router.post("/profile/change-pin")
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


@router.post("/profile/sign-out-all")
async def profile_sign_out_all(request: Request):
    ensure_ready()
    with connect() as conn:
        conn.row_factory = __import__("sqlite3").Row
        current_staff = current_staff_from_request(request, conn)
        if current_staff.get("id"):
            from ..auth import invalidate_all_user_sessions
            invalidate_all_user_sessions(conn, current_staff["id"])
            write_audit_event(conn, "__auth__", "sign_out_all", current_staff.get("username", ""), [], {}, {})
    resp = RedirectResponse(url="/login?info=Signed+out+of+all+devices.", status_code=302)
    resp.delete_cookie(SESSION_COOKIE)
    return resp

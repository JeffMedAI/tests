"""
Staff management routes — extracted from main.py.

Covers: /staff, /staff/create, /staff/{staff_id}/edit|deactivate|reactivate,
        /staff/invitations/*, /api/staff/performance
"""
from __future__ import annotations

import hashlib
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from ..audit import write_audit_event
from ..auth import hash_password, hash_pin
from ..case_domain import get_team_activity
from ..consts import STAFF_ROLES
from ..db import connect, row_to_dict
from ..helpers import (
    current_staff_from_request,
    ensure_ready,
    require_staff_admin,
    staff_display,
)
from ..models import utc_now_iso
from ..staff_queries import get_staff_any_by_id, get_staff_users
from ..templates_config import templates

router = APIRouter()


@router.get("/staff")
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
            "active_staff_users": [s for s in staff_users if s.get("active")],
            "inactive_staff_users": [s for s in staff_users if not s.get("active")],
            "invitations": [row_to_dict(row) for row in invitation_rows],
            "roles": ["admin", "staff", "readonly"],
            "active_nav": "staff",
            "can_manage_staff": current_staff.get("role") == "admin",
        },
    )


@router.post("/staff/create")
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


@router.post("/staff/{staff_id}/edit")
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


@router.post("/staff/{staff_id}/deactivate")
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


@router.post("/staff/{staff_id}/reactivate")
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


@router.get("/staff/invitations")
def staff_invitations_page(request: Request) -> Any:
    return staff_page(request)


@router.post("/staff/invitations/create")
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


@router.post("/staff/invitations/{invitation_id}/cancel")
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


@router.get("/api/staff/performance")
def api_staff_performance(range: str = "today") -> dict[str, Any]:

    ensure_ready()
    with connect() as conn:
        return get_team_activity(conn, range)

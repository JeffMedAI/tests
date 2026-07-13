"""
Shared helper functions extracted from main.py.

These are used by multiple route modules and cannot live in a single router.
No imports from main.py — only from external packages and sibling modules.
"""
from __future__ import annotations

import sqlite3 as _sqlite3
from typing import Any

from fastapi import HTTPException, Request

from .auth import get_session_user
from .consts import SESSION_COOKIE
from .db import connect, init_db


def normalize_staff_name(value: object) -> str:
    return str(value or "").strip() or "demo_user"


def ensure_ready() -> None:
    with connect() as conn:
        init_db(conn)


def current_staff_from_request(request: Request | None, conn) -> dict[str, Any]:
    if request:
        token = request.cookies.get(SESSION_COOKIE)
        if token:
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

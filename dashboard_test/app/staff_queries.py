"""
Staff-related DB query helpers.

Extracted from main.py so routers can import them without circular imports.
No imports from main.py — only from external packages and sibling modules.
"""
from __future__ import annotations

from typing import Any

from .db import row_to_dict


def get_staff_users(conn, active_only: bool = True) -> list[dict[str, Any]]:
    where = "WHERE active = 1" if active_only else ""
    rows = conn.execute(
        f"""
        SELECT id, username, display_name, email, role, active, created_at, updated_at
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

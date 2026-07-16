"""
St Marks Pharmacy contact-form intake.

St Marks Pharmacy is a separate business/website (Cloudflare Workers static
site, not part of this repo) — this endpoint receives its contact-form
submissions and lands them in the same JeffLocal case queue as GP triage
cases, tagged by call_id prefix and task text (no schema change, no EMIS/NHS
matching — this is a general pharmacy enquiry, not a GP patient identity case).

Auth: shared secret via X-StMarks-Secret header, same pattern as the n8n
webhook HMAC check — /api/intake/ is public-path-exempted from session auth
in consts.AUTH_PUBLIC_PREFIXES, so this header is the only gate.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Body, Header, HTTPException

from ..db import connect
from ..importer import map_handoff_to_case, upsert_case
from ..models import utc_now_iso

router = APIRouter()

STMARKS_SECRET_ENV = "STMARKS_INTAKE_SECRET"


def _check_secret(secret: str | None) -> None:
    expected = os.environ.get(STMARKS_SECRET_ENV)
    if not expected:
        raise HTTPException(status_code=503, detail=f"St Marks intake not configured — set {STMARKS_SECRET_ENV}")
    if not secret or secret != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing intake secret")


@router.post("/api/intake/stmarks-contact")
def api_stmarks_contact(
    payload: dict[str, Any] = Body(...),
    x_stmarks_secret: str | None = Header(default=None),
) -> dict[str, Any]:
    _check_secret(x_stmarks_secret)

    name = str(payload.get("name") or "").strip()
    phone = str(payload.get("phone") or "").strip()
    email = str(payload.get("email") or "").strip()
    message = str(payload.get("message") or "").strip()
    page = str(payload.get("page") or "").strip()

    if not name or not message:
        raise HTTPException(status_code=422, detail="name and message are required")
    if not phone and not email:
        raise HTTPException(status_code=422, detail="phone or email is required")

    callback = phone or email
    call_id = f"STMARKS-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:6]}"

    data = {
        "call_id": call_id,
        "call_timestamp": utc_now_iso(),
        "request_type": "admin",
        "task_title": f"St Marks Pharmacy enquiry - {name}",
        "patient_name": name,
        "callback_number": callback,
        "priority": "routine",
        "safe_to_queue": True,
        "staff_review_required": False,
        "red_flags_present": False,
        "verification_status": "",
        "stated_request": f"St Marks Pharmacy website enquiry{f' ({page})' if page else ''}: {message}",
        "action_needed": "Respond to St Marks Pharmacy website enquiry via provided contact details.",
        "raw_transcript": (
            "[St Marks Pharmacy contact form]\n"
            f"Name: {name}\nPhone: {phone or 'not provided'}\nEmail: {email or 'not provided'}\n"
            f"Page: {page or 'not provided'}\nMessage: {message}"
        ),
    }
    case = map_handoff_to_case(data)
    with connect() as conn:
        upsert_case(conn, case)

    return {"ok": True, "call_id": call_id}

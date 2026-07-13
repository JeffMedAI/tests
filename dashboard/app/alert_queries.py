"""
Alert helper functions extracted from main.py.

No imports from main.py — only from external packages and sibling modules.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from .consts import MODAL_ALERT_TYPE_KEYWORDS, NON_MODAL_ALERT_TYPE_KEYWORDS
from .db import row_to_dict
from .models import format_display_timestamp

_BASE = Path(__file__).resolve().parent.parent
_ROOT_DIR = Path(os.environ["JEFFLOCAL_ROOT_DIR"]) if os.environ.get("JEFFLOCAL_ROOT_DIR") else _BASE.parent
ALERT_DIR = _ROOT_DIR / "logs" / "alerts"


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


def alert_row_to_display(row: Any) -> dict[str, Any]:
    alert = row_to_dict(row) or {}
    alert["timestamp_display"] = format_display_timestamp(alert.get("timestamp"))
    alert["message"] = clean_alert_message(alert.get("message"))
    alert["modal_worthy"] = is_modal_worthy_alert(alert.get("alert_type"), alert.get("severity"))
    alert["acknowledged_at_display"] = format_display_timestamp(alert.get("acknowledged_at"))
    return alert


def write_alert_jsonl(alert: dict[str, Any]) -> None:
    ALERT_DIR.mkdir(parents=True, exist_ok=True)
    jsonl_path = ALERT_DIR / f"alerts_{alert['timestamp'][:10]}.jsonl"
    with jsonl_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(alert, sort_keys=True) + "\n")

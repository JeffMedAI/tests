"""
whatsapp_handoff.py — Build and write JeffLocal handoff JSON from WhatsApp intake

Converts the collected conversation data into the same handoff JSON format
as the voice pipeline, so the dashboard importer picks it up identically.
Adds source_channel = "whatsapp" so the dashboard can show the WA badge.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

HANDOFF_OUTPUT_DIR = Path(os.environ.get(
    "HANDOFF_JSON_DIR",
    r"C:\JeffLocal\outputs\handoff_json"
))


def build_and_write_handoff(collected_data: dict, phone: str, session_id: int,
                             emergency: bool = False) -> Path:
    """
    Build a handoff JSON file from WhatsApp conversation data and write it
    to the handoff_json output directory for the dashboard importer to pick up.

    Returns the path of the written file.
    """
    HANDOFF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    case_id = str(uuid.uuid4())
    now     = datetime.utcnow().isoformat()

    # Extract fields gathered during conversation
    name_raw    = collected_data.get("name_raw", "")
    dob_raw     = collected_data.get("dob_raw", "")
    reason      = collected_data.get("reason", "")
    duration    = collected_data.get("duration", "")
    extra_notes = collected_data.get("extra_notes", "")
    raw_input   = collected_data.get("raw_name_dob", "")

    # Build staff summary line
    summary_parts = []
    if reason:
        summary_parts.append(reason)
    if duration:
        summary_parts.append(f"for {duration}")
    if extra_notes:
        summary_parts.append(f"Note: {extra_notes}")
    staff_summary = ". ".join(summary_parts) if summary_parts else "WhatsApp intake — see details."

    if emergency:
        staff_summary = f"⚠️ EMERGENCY FLAG: {collected_data.get('emergency_trigger', '')} | {staff_summary}"

    handoff = {
        "schema_version":   "1.0",
        "case_id":          case_id,
        "source_channel":   "whatsapp",
        "source_session_id": str(session_id),
        "timestamp":        now,
        "emergency":        emergency,

        "patient": {
            "name_raw":     name_raw,
            "dob_raw":      dob_raw,
            "raw_input":    raw_input,
            # Patient matching (name+DOB→EMIS) happens in importer via Ollama
            "matched":      False,
            "patient_id":   None,
        },

        "intake": {
            "reason":       reason,
            "duration":     duration,
            "extra_notes":  extra_notes,
            "channel":      "whatsapp",
        },

        "staff_summary": staff_summary,

        "flags": {
            "emergency":    emergency,
            "incomplete":   not bool(reason),
            "needs_review": emergency or not bool(name_raw),
        },

        "meta": {
            "wa_session_id":    str(session_id),
            "ollama_processed": False,  # importer will trigger Ollama extraction
        }
    }

    filename = HANDOFF_OUTPUT_DIR / f"wa_{case_id}.json"
    filename.write_text(json.dumps(handoff, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"WhatsApp handoff written: {filename.name} emergency={emergency}")
    return filename

"""
whatsapp_conversation.py — JeffLocal WhatsApp Conversation Engine

Jeff's conversation logic for patient intake via WhatsApp.
Handles: opt-in, multi-turn intake, emergency escalation, confirmation.

All replies are returned as strings — the caller (webhook handler) sends them
back to the patient via the Meta API.
"""

import re
import logging
from typing import Optional

from .whatsapp_state import (
    STAGE_OPT_IN, STAGE_GREETING, STAGE_REASON,
    STAGE_CLARIFY, STAGE_EXTRAS, STAGE_COMPLETE, STAGE_ESCALATED,
    SESSION_STATUS_COMPLETE, SESSION_STATUS_ESCALATED, SESSION_STATUS_STOPPED,
    has_valid_consent, record_consent, revoke_consent,
    get_active_session, create_session, update_session, close_session,
)

logger = logging.getLogger(__name__)

# Surgery details — update for each deployment
SURGERY_NAME    = "Churchtown Medical Centre"
SURGERY_PHONE   = "01704 228 000"
PRIVACY_URL     = "https://dashboard.app-avamed.uk/privacy"

# ─── Emergency keywords ───────────────────────────────────────────────────────
EMERGENCY_KEYWORDS = [
    r"\bchest pain\b", r"\bcan'?t breathe\b", r"\bshortness of breath\b",
    r"\bdifficulty breathing\b", r"\bunconscious\b", r"\bpassed out\b",
    r"\bstroke\b", r"\bface drooping\b", r"\barm weakness\b",
    r"\bsevere bleeding\b", r"\bnot breathing\b", r"\bheart attack\b",
    r"\bsuicid\b", r"\bkill myself\b", r"\bend my life\b",
    r"\boverdose\b", r"\bsevere pain\b", r"\bpain 10\b",
    r"\bseizure\b", r"\bfitting\b", r"\ballergic reaction\b", r"\banaphylax\b",
]

STOP_KEYWORDS = [r"\bstop\b", r"\bopt.?out\b", r"\bdelete my data\b", r"\bunsubscribe\b"]

CONSENT_TEXT = (
    f"👋 Hello! I'm Jeff, the virtual assistant at {SURGERY_NAME}.\n\n"
    "Before I can help, I need your consent to process your message via WhatsApp.\n\n"
    "📋 Your message will be handled securely by our system. "
    f"Full Privacy Notice: {PRIVACY_URL}\n\n"
    "✅ Reply *YES* to continue\n"
    f"📞 Or call us on {SURGERY_PHONE} if you prefer not to use WhatsApp."
)

GREETING_TEXT = (
    f"Great, thank you! I'm Jeff, the virtual assistant at {SURGERY_NAME}.\n\n"
    "I can take your appointment request right now, so you don't have to wait on hold. 📋\n\n"
    "To get started, please tell me:\n"
    "👤 Your *full name* and *date of birth* (e.g. John Smith, 15 Jan 1975)"
)

STOP_REPLY = (
    f"Understood. I've stopped processing your messages. "
    f"Please call us on {SURGERY_PHONE} if you need to speak to someone. "
    "Your data will be removed within 72 hours. Take care! 👋"
)

EMERGENCY_REPLY = (
    "⚠️ *This sounds like a medical emergency.*\n\n"
    "Please *call 999 immediately* or go to your nearest A&E.\n\n"
    "Do not wait for a callback — call 999 NOW.\n\n"
    "If you are unsure, call *111* for urgent medical advice.\n\n"
    f"The team at {SURGERY_NAME} has been alerted."
)

COMPLETION_TEXT = (
    "✅ *Thank you! Your request has been passed to our reception team.*\n\n"
    "They will contact you shortly to book an appointment.\n\n"
    f"⚠️ If your condition worsens urgently, please call *999* or *111*.\n\n"
    f"For non-urgent queries, call us on {SURGERY_PHONE}.\n\n"
    f"— Jeff at {SURGERY_NAME}"
)


# ─── Emergency detection ─────────────────────────────────────────────────────

def is_emergency(message: str) -> bool:
    """Return True if the message contains emergency/red-flag keywords."""
    msg_lower = message.lower()
    for pattern in EMERGENCY_KEYWORDS:
        if re.search(pattern, msg_lower, re.IGNORECASE):
            logger.warning(f"Emergency keyword detected: {pattern}")
            return True
    return False


def is_stop(message: str) -> bool:
    """Return True if patient is opting out."""
    msg_lower = message.lower().strip()
    for pattern in STOP_KEYWORDS:
        if re.search(pattern, msg_lower, re.IGNORECASE):
            return True
    return False


def is_yes(message: str) -> bool:
    """Return True if message is an affirmative consent reply."""
    return message.strip().lower() in {"yes", "yes.", "yes!", "y", "ok", "okay", "agree", "i agree"}


# ─── Field extraction helpers ────────────────────────────────────────────────

def extract_name_dob(message: str) -> dict:
    """
    Attempt to extract name and DOB from a free-text message.
    Returns dict with 'name' and 'dob' (both may be None if not found).
    Ollama will do the full extraction — this is a lightweight pre-parse.
    """
    result = {"raw_name_dob": message.strip()}
    # Simple DOB pattern: dd/mm/yyyy, dd-mm-yyyy, dd mon yyyy, dd month yyyy
    dob_patterns = [
        r"\b(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})\b",
        r"\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{2,4})\b",
    ]
    for pattern in dob_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            result["dob_raw"] = match.group(1)
            # Name is approximately everything before the DOB
            name_part = message[:match.start()].strip().rstrip(",").strip()
            if len(name_part) > 2:
                result["name_raw"] = name_part
            break
    return result


# ─── Main conversation handler ───────────────────────────────────────────────

def handle_message(conn, phone: str, message: str, wa_message_id: str = None) -> dict:
    """
    Process an incoming WhatsApp message from a patient.

    Returns:
        {
            "reply": str,           — message to send back to patient
            "stage": int,           — new conversation stage
            "is_complete": bool,    — True if intake is done
            "is_emergency": bool,   — True if emergency escalation triggered
            "collected_data": dict, — fields gathered so far
            "session_id": int,
        }
    """
    message = message.strip()

    # ── STOP / opt-out at any stage ──────────────────────────────────────────
    if is_stop(message):
        session = get_active_session(conn, phone)
        if session:
            close_session(conn, session["id"], STATUS_STOPPED := SESSION_STATUS_STOPPED)
        revoke_consent(conn, phone)
        return _result(STOP_REPLY, STAGE_COMPLETE, False, False, {}, session["id"] if session else None)

    # ── Emergency check — always fires regardless of stage ──────────────────
    if is_emergency(message):
        session = get_active_session(conn, phone) or create_session(conn, phone, wa_message_id)
        collected = session.get("collected_data", {})
        collected["emergency_trigger"] = message
        close_session(conn, session["id"], SESSION_STATUS_ESCALATED)
        update_session(conn, session["id"], collected_data=collected)
        return _result(EMERGENCY_REPLY, STAGE_ESCALATED, False, True, collected, session["id"])

    # ── Consent check ────────────────────────────────────────────────────────
    if not has_valid_consent(conn, phone):
        session = get_active_session(conn, phone)

        # If session exists and we're in opt-in stage, check for YES
        if session and session["stage"] == STAGE_OPT_IN:
            if is_yes(message):
                record_consent(conn, phone)
                update_session(conn, session["id"], stage=STAGE_GREETING, opted_in=True)
                return _result(GREETING_TEXT, STAGE_GREETING, False, False, {}, session["id"])
            else:
                # Prompt once more then abandon
                if session.get("collected_data", {}).get("consent_prompted_twice"):
                    close_session(conn, session["id"], SESSION_STATUS_STOPPED)
                    return _result(
                        f"No problem. Please call us on {SURGERY_PHONE} if you need help. Goodbye! 👋",
                        STAGE_COMPLETE, True, False, {}, session["id"]
                    )
                else:
                    collected = {"consent_prompted_twice": True}
                    update_session(conn, session["id"], collected_data=collected)
                    return _result(
                        f"Just to confirm — please reply *YES* to continue, or call {SURGERY_PHONE}.",
                        STAGE_OPT_IN, False, False, {}, session["id"]
                    )
        else:
            # New contact — create session and send consent prompt
            new_session = create_session(conn, phone, wa_message_id)
            return _result(CONSENT_TEXT, STAGE_OPT_IN, False, False, {}, new_session["id"])

    # ── Active session with consent ──────────────────────────────────────────
    session = get_active_session(conn, phone)
    if not session:
        session = create_session(conn, phone, wa_message_id)
        update_session(conn, session["id"], stage=STAGE_GREETING, opted_in=True)
        return _result(GREETING_TEXT, STAGE_GREETING, False, False, {}, session["id"])

    stage = session["stage"]
    collected = session.get("collected_data", {})

    # ── Stage 0: opt-in (shouldn't reach here if consent valid, but guard) ──
    if stage == STAGE_OPT_IN:
        update_session(conn, session["id"], stage=STAGE_GREETING)
        return _result(GREETING_TEXT, STAGE_GREETING, False, False, collected, session["id"])

    # ── Stage 1: Greeting — waiting for name + DOB ───────────────────────────
    if stage == STAGE_GREETING:
        parsed = extract_name_dob(message)
        collected.update(parsed)
        update_session(conn, session["id"], stage=STAGE_REASON, collected_data=collected)
        name_display = collected.get("name_raw", "")
        greeting = f"Thank you{', ' + name_display if name_display else ''}! 😊\n\n"
        return _result(
            greeting + "What is the *reason for your contact* today? "
            "Please describe your concern or symptom briefly.",
            STAGE_REASON, False, False, collected, session["id"]
        )

    # ── Stage 2: Reason ───────────────────────────────────────────────────────
    if stage == STAGE_REASON:
        collected["reason"] = message
        update_session(conn, session["id"], stage=STAGE_CLARIFY, collected_data=collected)
        return _result(
            "Got it. *How long have you had this?* "
            "(e.g. a few days, about a week, longer than a month)",
            STAGE_CLARIFY, False, False, collected, session["id"]
        )

    # ── Stage 3: Clarification — duration ────────────────────────────────────
    if stage == STAGE_CLARIFY:
        collected["duration"] = message
        update_session(conn, session["id"], stage=STAGE_EXTRAS, collected_data=collected)
        return _result(
            "Thank you. Is there *anything else* you'd like the doctor or receptionist to know? "
            "(or reply *no* to finish)",
            STAGE_EXTRAS, False, False, collected, session["id"]
        )

    # ── Stage 4: Extras — final notes ────────────────────────────────────────
    if stage == STAGE_EXTRAS:
        if message.lower().strip() not in {"no", "no.", "nope", "n", "nothing", "none"}:
            collected["extra_notes"] = message
        close_session(conn, session["id"], SESSION_STATUS_COMPLETE)
        update_session(conn, session["id"], stage=STAGE_COMPLETE, collected_data=collected)
        return _result(COMPLETION_TEXT, STAGE_COMPLETE, True, False, collected, session["id"])

    # ── Fallback: session already complete ───────────────────────────────────
    return _result(
        f"Your request has already been submitted. "
        f"For further help, call {SURGERY_PHONE}.",
        STAGE_COMPLETE, True, False, collected, session["id"]
    )


def _result(reply: str, stage: int, is_complete: bool, is_emergency: bool,
            collected_data: dict, session_id: Optional[int]) -> dict:
    return {
        "reply": reply,
        "stage": stage,
        "is_complete": is_complete,
        "is_emergency": is_emergency,
        "collected_data": collected_data,
        "session_id": session_id,
    }

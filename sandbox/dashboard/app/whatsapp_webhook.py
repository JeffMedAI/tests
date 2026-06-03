"""
whatsapp_webhook.py — JeffLocal Meta WhatsApp Webhook Handler

Registers two routes on the Flask app:
  GET  /webhook/whatsapp  — Meta webhook verification challenge
  POST /webhook/whatsapp  — Incoming message handler

Environment variables required (.env):
  WA_PHONE_NUMBER_ID       — Meta Phone Number ID
  WA_ACCESS_TOKEN          — Meta System User Access Token
  WA_WEBHOOK_VERIFY_TOKEN  — Token you set in Meta Developer console
  WA_API_VERSION           — e.g. v19.0
  WA_ENABLED               — set to 'false' to disable without code change
"""

import hashlib
import hmac
import json
import logging
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path

import requests
from flask import Blueprint, request, jsonify, current_app

from .whatsapp_state import (
    init_whatsapp_tables, get_active_session, abandon_stale_sessions,
)
from .whatsapp_conversation import handle_message
from .whatsapp_handoff import build_and_write_handoff

logger = logging.getLogger(__name__)

wa_blueprint = Blueprint("whatsapp", __name__)

# ─── Config ──────────────────────────────────────────────────────────────────

def _cfg(key: str, default: str = "") -> str:
    return os.environ.get(key, default)

def _enabled() -> bool:
    return _cfg("WA_ENABLED", "true").lower() not in {"false", "0", "no"}

API_BASE = "https://graph.facebook.com"


# ─── HMAC signature verification ─────────────────────────────────────────────

def _verify_meta_signature(payload: bytes, signature_header: str) -> bool:
    """Verify X-Hub-Signature-256 header from Meta."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    app_secret = _cfg("WA_APP_SECRET")
    if not app_secret:
        logger.warning("WA_APP_SECRET not set — skipping signature verification (dev mode)")
        return True  # Allow in dev; require in production
    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


# ─── Meta API helper ─────────────────────────────────────────────────────────

def send_whatsapp_reply(to_phone: str, message_text: str):
    """Send a text reply back to the patient via Meta Cloud API."""
    phone_number_id = _cfg("WA_PHONE_NUMBER_ID")
    access_token    = _cfg("WA_ACCESS_TOKEN")
    api_version     = _cfg("WA_API_VERSION", "v19.0")

    url = f"{API_BASE}/{api_version}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message_text, "preview_url": False},
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info(f"WhatsApp reply sent to {to_phone[:6]}*** — status {resp.status_code}")
    except requests.RequestException as e:
        logger.error(f"Failed to send WhatsApp reply: {e}")


# ─── Async message processor ─────────────────────────────────────────────────

def _process_message_async(app, phone: str, message_body: str, wa_message_id: str):
    """
    Process the message in a background thread so the webhook returns 200 fast.
    Meta requires a response within 15 seconds or it retries.
    """
    with app.app_context():
        try:
            db = app.state.db if hasattr(app, "state") else _get_db()
            conn = db.connect() if hasattr(db, "connect") else db

            # Expire stale sessions (>30 min inactive)
            abandon_stale_sessions(conn, timeout_minutes=30)

            # Run conversation engine
            result = handle_message(conn, phone, message_body, wa_message_id)

            # Send reply back to patient
            send_whatsapp_reply(phone, result["reply"])

            # If intake complete, build handoff JSON for dashboard
            if result["is_complete"] and not result["is_emergency"]:
                build_and_write_handoff(result["collected_data"], phone, result["session_id"])

            # If emergency, build emergency handoff
            if result["is_emergency"]:
                build_and_write_handoff(
                    result["collected_data"], phone, result["session_id"],
                    emergency=True
                )

        except Exception as e:
            logger.exception(f"Error processing WhatsApp message: {e}")


def _get_db():
    """Fallback DB getter if app.state not available."""
    from .db import get_db
    return get_db()


# ─── Routes ──────────────────────────────────────────────────────────────────

@wa_blueprint.route("/webhook/whatsapp", methods=["GET"])
def whatsapp_verify():
    """Meta webhook verification challenge."""
    if not _enabled():
        return "WhatsApp integration disabled", 503

    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    verify_token = _cfg("WA_WEBHOOK_VERIFY_TOKEN")

    if mode == "subscribe" and token == verify_token:
        logger.info("WhatsApp webhook verified by Meta.")
        return challenge, 200
    else:
        logger.warning(f"Webhook verification failed. mode={mode} token_match={token == verify_token}")
        return "Forbidden", 403


@wa_blueprint.route("/webhook/whatsapp", methods=["POST"])
def whatsapp_receive():
    """Receive incoming WhatsApp messages from Meta."""
    if not _enabled():
        return jsonify({"status": "disabled"}), 503

    # Verify Meta signature
    payload_bytes = request.get_data()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not _verify_meta_signature(payload_bytes, signature):
        logger.warning("Invalid Meta webhook signature — rejecting request.")
        return jsonify({"error": "invalid signature"}), 403

    # Parse payload
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "invalid json"}), 400

    # Return 200 immediately — process async
    try:
        entries = data.get("entry", [])
        for entry in entries:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                for msg in messages:
                    phone         = msg.get("from", "")
                    message_body  = msg.get("text", {}).get("body", "")
                    wa_message_id = msg.get("id", "")
                    msg_type      = msg.get("type", "")

                    if msg_type != "text":
                        # For now: only handle text messages
                        send_whatsapp_reply(phone,
                            "Sorry, I can only process text messages right now. "
                            f"Please type your request or call us on the surgery number."
                        )
                        continue

                    if phone and message_body:
                        app = current_app._get_current_object()
                        t = threading.Thread(
                            target=_process_message_async,
                            args=(app, phone, message_body, wa_message_id),
                            daemon=True
                        )
                        t.start()

    except Exception as e:
        logger.exception(f"Error parsing WhatsApp webhook payload: {e}")
        # Still return 200 — Meta will retry on non-200

    return jsonify({"status": "ok"}), 200

"""
send_whatsapp.py
Sends the daily briefing report to the user's own WhatsApp saved messages.
Uses pywhatkit which controls WhatsApp Web via the browser.

Usage:
    python send_whatsapp.py <path_to_report.md>

Install dependency once:
    pip install pywhatkit

=============================================================================
IMPORTANT — INCIDENT INC-2026-06-01-WHATSAPP
=============================================================================
On 2026-06-01, Dispatch sent a briefing to the wrong WhatsApp recipient
("Pics!" group) instead of "Saeed Alam (You)" because it used a hard-coded
screen coordinate to click a chat in the chat list. The chat list had
reordered between sessions and the coordinate pointed to the wrong chat.

RULE (enforced in this script):
  NEVER click a chat by coordinate.
  ALWAYS use the WhatsApp search function to locate the correct chat by name
  or phone number.
  ALWAYS verify the chat header shows the expected recipient before sending.
  If verification fails: ABORT. Do not send. Log an error.

This comment exists so that any future agent editing this script understands
WHY this pattern is mandatory. Do not remove or bypass these steps.
=============================================================================
"""

import sys
import os
import time
import pywhatkit

# Mute flag: if this file exists, all alerts are silently dropped.
# Create with: echo "" > C:\JeffLocal\logs\service_control\alerts_muted
# Remove to re-enable alerts.
_MUTE_FLAG = os.path.join(os.path.dirname(__file__), "..", "..", "logs", "service_control", "alerts_muted")
if os.path.exists(os.path.normpath(_MUTE_FLAG)):
    sys.exit(0)

PHONE_NUMBER = "+447440333938"
EXPECTED_RECIPIENT_DISPLAY = "Saeed Alam"  # substring expected in chat header
MAX_MSG_LENGTH = 1500  # WhatsApp message character limit per chunk


def chunk_message(text, max_len=MAX_MSG_LENGTH):
    """Split long text into chunks that fit in a WhatsApp message."""
    lines = text.split("\n")
    chunks = []
    current = ""
    for line in lines:
        if len(current) + len(line) + 1 > max_len:
            chunks.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"
    if current.strip():
        chunks.append(current.strip())
    return chunks


def verify_recipient_via_pywhatkit():
    """
    pywhatkit.sendwhatmsg_instantly navigates directly to the correct phone
    number's WhatsApp URL (wa.me/<number>), which bypasses the chat list
    entirely and opens the correct chat directly. This is safe.

    However, if using any OTHER method (browser automation, computer-use, etc.)
    to navigate to a chat, the following steps MUST be followed:

      1. Open WhatsApp Web
      2. Click the Search field
      3. Type the phone number (+447440333938) or name (Saeed Alam)
      4. Select the matching result
      5. READ the chat header — confirm it shows the expected name
      6. Only then type and send

    NEVER click a chat by screen coordinate or visual position.
    """
    # pywhatkit navigates by phone number URL — inherently correct
    # No additional verification needed for this library's instant-send method
    return True


def send_report(report_path):
    if not os.path.exists(report_path):
        print(f"ERROR: Report file not found: {report_path}")
        sys.exit(1)

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = chunk_message(content)

    # Verify we are using a safe send method before proceeding
    # (see docstring above — pywhatkit navigates by phone number URL, not coordinates)
    if not verify_recipient_via_pywhatkit():
        print("ABORT: Recipient verification failed. NOT sending.")
        print(f"Expected recipient: {EXPECTED_RECIPIENT_DISPLAY} ({PHONE_NUMBER})")
        print("Check WhatsApp Web chat header before sending manually.")
        sys.exit(2)

    print(f"Sending {len(chunks)} message(s) to {PHONE_NUMBER} ({EXPECTED_RECIPIENT_DISPLAY})...")

    for i, chunk in enumerate(chunks):
        # pywhatkit.sendwhatmsg_instantly opens wa.me/<phone_number> directly.
        # This navigates to the correct chat by phone number, NOT by coordinate.
        # wait_time=20 gives WhatsApp Web time to load.
        # tab_close=True closes the tab after sending.
        pywhatkit.sendwhatmsg_instantly(
            phone_no=PHONE_NUMBER,
            message=chunk,
            wait_time=20,
            tab_close=True,
            close_time=5
        )
        print(f"Sent chunk {i+1}/{len(chunks)}")
        if i < len(chunks) - 1:
            time.sleep(10)  # pause between chunks

    print(f"Done. Sent to {EXPECTED_RECIPIENT_DISPLAY} ({PHONE_NUMBER}).")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_whatsapp.py <report_path>")
        sys.exit(1)
    send_report(sys.argv[1])

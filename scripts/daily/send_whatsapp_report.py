"""
send_whatsapp_report.py
JeffLocal — sends daily strategy briefing to Saeed's WhatsApp saved messages.

Called by strategy_daily.ps1 after the report is generated.
Requires: pywhatkit, pyautogui (pip install pywhatkit pyautogui)
Chrome must be running and WhatsApp Web must be logged in.

Usage:
    python send_whatsapp_report.py [report_path]
    If no path given, uses today's report: C:\JeffLocal\docs\reports\YYYY-MM-DD.md
"""

import sys
import os
import time
import datetime
import re

# ── Config ────────────────────────────────────────────────────────────────────
PHONE_NUMBER  = "+447440333938"   # Saeed — "Message yourself" thread
REPO_ROOT     = r"C:\JeffLocal"
REPORTS_DIR   = r"C:\JeffLocal\docs\reports"
# How long (seconds) to wait for WhatsApp Web tab to load before typing
WAIT_SECONDS  = 12
# Max characters per WhatsApp message (WA limit is ~65k but keep it readable)
MAX_CHARS     = 3000

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_report(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def condense_report(raw: str) -> str:
    """Strip markdown decorations and trim to a readable WhatsApp message."""
    lines = raw.splitlines()
    out = []
    for line in lines:
        stripped = line.strip()
        # Skip horizontal rules and empty lines at the top of sections
        if stripped in ("---", ""):
            if out and out[-1] != "":
                out.append("")
            continue
        # Convert ## headers to ALLCAPS with dashes for readability
        m = re.match(r"^#{1,3}\s+(.+)", stripped)
        if m:
            out.append(f"*{m.group(1).upper()}*")
            continue
        out.append(stripped)

    text = "\n".join(out).strip()
    # Trim to max chars, breaking at a newline
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS]
        last_nl = text.rfind("\n")
        if last_nl > MAX_CHARS * 0.8:
            text = text[:last_nl]
        text += "\n\n_(message trimmed — see docs/reports/ for full briefing)_"
    return text


def send_via_pywhatkit(phone: str, message: str, wait: int) -> None:
    """Open WhatsApp Web in a new Chrome tab and send the message."""
    import pywhatkit as pwk
    # sendwhatmsg_instantly: opens WA Web immediately (no scheduled time).
    # tab_close=False so Chrome doesn't close the tab (avoids focus issues).
    # close_time is how many seconds after sending before closing (0 = don't).
    pwk.sendwhatmsg_instantly(
        phone_no=phone,
        message=message,
        wait_time=wait,
        tab_close=False,
    )
    # Give it a moment to settle before the script exits
    time.sleep(3)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    today = datetime.date.today().strftime("%Y-%m-%d")

    # Determine report path
    if len(sys.argv) > 1:
        report_path = sys.argv[1]
    else:
        report_path = os.path.join(REPORTS_DIR, f"{today}.md")

    if not os.path.exists(report_path):
        print(f"ERROR: Report not found: {report_path}")
        sys.exit(1)

    print(f"Loading report: {report_path}")
    raw = load_report(report_path)
    message = condense_report(raw)

    print(f"Sending {len(message)} chars to {PHONE_NUMBER} via WhatsApp Web...")
    send_via_pywhatkit(PHONE_NUMBER, message, WAIT_SECONDS)
    print("Done — message sent.")


if __name__ == "__main__":
    main()

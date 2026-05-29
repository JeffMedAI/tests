"""
send_whatsapp.py
Sends the daily briefing report to the user's own WhatsApp saved messages.
Uses pywhatkit which controls WhatsApp Web via the browser.

Usage:
    python send_whatsapp.py <path_to_report.md>

Install dependency once:
    pip install pywhatkit
"""

import sys
import os
import time
import pywhatkit

PHONE_NUMBER = "+447440333938"
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


def send_report(report_path):
    if not os.path.exists(report_path):
        print(f"ERROR: Report file not found: {report_path}")
        sys.exit(1)

    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    chunks = chunk_message(content)
    print(f"Sending {len(chunks)} message(s) to {PHONE_NUMBER}...")

    for i, chunk in enumerate(chunks):
        # Send instantly via WhatsApp Web (tab must be open or will open Chrome)
        # wait_time=15 gives WhatsApp Web time to load
        # tab_close=True closes the tab after sending
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

    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_whatsapp.py <report_path>")
        sys.exit(1)
    send_report(sys.argv[1])

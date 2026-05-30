"""
send_gp_demo_n8n_webhook_calls.py
Sends demo GP call payloads to the n8n test-intake-batch endpoint.
Requires --confirm-send flag. Google push is always disabled.

Usage:
    python send_gp_demo_n8n_webhook_calls.py --confirm-send
"""

import argparse
import json
import sys
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

ENDPOINT = "http://localhost:5000/api/n8n/test-intake-batch"

DEMO_CALLS = [
    {
        "call_id": f"TC-GP-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-001-PRESCRIPTION",
        "call_timestamp": datetime.now(timezone.utc).isoformat(),
        "request_type": "prescription",
        "normalized_input": {"patient_name": "Demo Patient A", "dob": "1970-01-01"},
        "verification_status": "matched",
        "priority": "routine",
        "safe_to_queue": True,
        "staff_review_required": False,
        "red_flags_present": False,
        "task_title": "Demo prescription request",
        "task_body": "Demo only.",
        "call_summary": "Demo prescription.",
        "raw_transcript": "Demo call.",
    },
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-send", action="store_true", required=True,
                        help="Required flag to confirm you want to send demo calls")
    args = parser.parse_args()

    if not args.confirm_send:
        print("ERROR: --confirm-send is required.")
        sys.exit(1)

    batch_id = f"TC-GP-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    payload = {
        "test_mode": True,
        "batch_id": batch_id,
        "disable_google_push": True,
        "calls": DEMO_CALLS,
    }

    print(f"Sending {len(DEMO_CALLS)} demo call(s) to {ENDPOINT}")
    resp = requests.post(ENDPOINT, json=payload, timeout=30)
    print(f"Status: {resp.status_code}")
    print(json.dumps(resp.json(), indent=2))


if __name__ == "__main__":
    main()

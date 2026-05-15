from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT_DIR / "tests" / "fixtures"
for path in (ROOT_DIR, FIXTURE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from live_lookup_test_payloads import encrypt_envelope  # noqa: E402

try:  # noqa: E402
    from app.decrypt_encrypted_raw import decrypt_envelope as local_decrypt_envelope  # type: ignore
except Exception:  # pragma: no cover - local fallback only
    local_decrypt_envelope = None

try:  # noqa: E402
    from n8n_webhook_test_pack import build_batch as build_n8ntest_batch  # type: ignore
except Exception:  # pragma: no cover - local fallback only
    build_n8ntest_batch = None


DEFAULT_WEBHOOK_URL = "http://localhost:5678/webhook-test/jefflocal-test-intake"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
REQUIRED_ENVELOPE_FIELDS = {
    "protocol",
    "alg",
    "key_id",
    "sender_id",
    "message_id",
    "timestamp_utc",
    "nonce",
    "encrypted_key",
    "iv",
    "ciphertext",
    "tag",
    "signature_alg",
    "signature",
}


def is_local_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.hostname in LOCAL_HOSTS


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def transcript_blocks() -> list[dict[str, str]]:
    return [
        {
            "suffix": "001-PRESCRIPTION",
            "request_type": "prescription",
            "stated_request": "Repeat prescription requested for atorvastatin 20mg. Caller says there are two tablets left and asks for the prescription to be sent to the nominated pharmacy today.",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "staff_review_required": False,
            "red_flags_present": False,
            "patient_name": "Jason Morrey",
            "dob": "1970-01-10",
            "postcode": "PR9 7LT",
            "callback_number": "07111000001",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Routine repeat prescription request. Caller reported no urgent symptoms and provided a callback number.",
            "summary": "Routine repeat prescription request for atorvastatin 20mg. Caller reported two tablets left and no urgent symptoms.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I need my repeat "
                "prescription please, atorvastatin 20 milligrams. I have two tablets left and I am trying not to run "
                "out. Agent: Thank you. Have you had any chest pain, breathlessness, sweating, fainting, or any other "
                "urgent symptoms? Caller: No, nothing like that. I just need the medication renewed in time. Agent: "
                "Can I confirm your callback number and a couple of details so the practice can review the request? "
                "Caller: Yes, the callback is 07111000001 and my details are up to date. Agent: Thank you, I will "
                "pass this routine repeat prescription request to the practice team using the local demo workflow. "
                "Caller: Fine, thank you."
            ),
        },
        {
            "suffix": "002-SICKNOTE",
            "request_type": "sick_note",
            "stated_request": "Fit note requested after a viral illness absence. Caller says they need documentation for work and understands staff review is required before anything is issued.",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Mathew Morrey",
            "dob": "1978-09-15",
            "postcode": "PR9 7LT",
            "callback_number": "07111000002",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Fit note request. Caller understood the request will need staff review before completion.",
            "summary": "Fit note request after viral illness absence. Caller understands staff review is required before issue.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I need a fit note "
                "because I have been off work with a viral illness. Agent: I can help capture the request. Have your "
                "symptoms worsened or do you have any red flag symptoms such as chest pain or breathlessness? Caller: "
                "No, I just need the note because I am still not well enough to go back. Agent: Thank you. Please "
                "confirm a callback number and any relevant dates so the team can review the request. Caller: The "
                "callback is 07111000002 and I missed work from Monday. Agent: I will pass this fit note request to "
                "the practice team for staff review."
            ),
        },
        {
            "suffix": "003-REFERRAL",
            "request_type": "referral",
            "stated_request": "Referral follow-up requested for orthopaedics. Caller wants to know whether the referral has been sent and whether there is any update from the practice team.",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Peter Morrey",
            "dob": "1978-09-15",
            "postcode": "PR9 7LT",
            "callback_number": "07111000003",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Referral follow-up request. Staff review is required before any update is provided.",
            "summary": "Referral follow-up for orthopaedics. Caller is chasing whether the referral has been sent.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I am calling about "
                "a referral I was meant to have for orthopaedics. Agent: Thanks. Do you have any new symptoms or "
                "urgent problems today? Caller: No, I just want to know whether the referral has gone through. "
                "Agent: Can I confirm your callback number so the team can review the record and respond? Caller: "
                "Yes, it is 07111000003. Agent: I will pass this referral follow-up to the practice team for review "
                "using the local demo workflow."
            ),
        },
        {
            "suffix": "004-IDENTITY",
            "request_type": "admin",
            "stated_request": "Third-party caller gave partial details for another patient. Identity review is required before any discussion or processing can happen.",
            "verification_status": "possible_match",
            "priority": "review_required",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Jayson Morrey",
            "dob": "1970-01-10",
            "postcode": "PR9 7LT",
            "callback_number": "07111000004",
            "caller_for": "third_party",
            "caller_relationship": "third_party",
            "pathway_response": "Identity could not be confirmed from the transcript. Staff review required before processing.",
            "summary": "Third-party caller gave partial details only. Identity review is required before processing.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm who the request is for? Caller: It is for my brother, I "
                "think he is called Michael, but I am not sure of the full details. Agent: For safety, I need the "
                "patient's details or an authorised callback before the practice can discuss anything. Caller: I do "
                "not have all of that with me right now, I can call back later. Agent: That is fine, please leave a "
                "callback number and the practice will review the request. Caller: The callback is 07111000004. "
                "Agent: Thank you. I will mark this as an identity review case and pass it to staff."
            ),
        },
        {
            "suffix": "005-REDFLAG",
            "request_type": "appointment_redirect",
            "stated_request": "Possible emergency symptoms reported: chest pain, breathlessness and sweating. Caller was advised to call 999 immediately and not to wait for routine practice contact.",
            "verification_status": "matched",
            "priority": "999 Emergency",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": True,
            "patient_name": "Geoffrey Mynne",
            "dob": "1941-02-21",
            "postcode": "PR9 7LT",
            "callback_number": "07111000005",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Emergency symptoms identified. Caller advised to call 999 immediately.",
            "summary": "Possible emergency symptoms identified. Caller advised to call 999 immediately.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I am not feeling "
                "right, I have chest pain and I am short of breath. Agent: Are you alone, and are you feeling sweaty "
                "or faint as well? Caller: Yes, I am sweating and I feel worse when I move. Agent: This sounds "
                "urgent. Please call 999 now for emergency help and do not wait for a routine callback. Caller: "
                "Okay, I will call 999 right now. Agent: I am recording this as an emergency red-flag case for the "
                "practice record, but the immediate instruction is to seek emergency help first."
            ),
        },
    ]


def build_plain_calls(batch_id: str) -> list[dict]:
    batch_root = batch_id.rstrip("-")
    timestamp = utc_now_iso()
    calls: list[dict] = []
    for item in transcript_blocks():
        transcript = item["transcript"].strip()
        if len(transcript) <= 500:
            raise ValueError(f"Transcript too short for {item['suffix']}: {len(transcript)} chars")
        call_id = f"{batch_root}-{item['suffix']}"
        calls.append(
            {
                "call_id": call_id,
                "call_timestamp": timestamp,
                "workflow": "voice_agent_demo_batch",
                "request_type": item["request_type"],
                "source": "voice_agent",
                "voice_agent": {
                    "agent_name": "Jeff Voice Agent",
                    "session_id": f"VA-{call_id}",
                    "caller_channel": "phone",
                    "call_direction": "inbound",
                    "caller_id_captured": True,
                    "call_duration_seconds": 180,
                    "language": "en-GB",
                    "caller_sentiment": "demo",
                    "caller_difficulty": "demo",
                    "transcript_quality": "demo_realistic",
                },
                "normalized_input": {
                    "patient_name": item["patient_name"],
                    "dob": item["dob"],
                    "postcode": item["postcode"],
                    "callback_number": item["callback_number"],
                    "medications_requested": ["atorvastatin 20mg"] if item["request_type"] == "prescription" else [],
                    "urgency_note": item["priority"],
                    "pharmacy": "Demo Pharmacy" if item["request_type"] == "prescription" else "",
                    "caller_for": item["caller_for"],
                    "supplied_nhs_number": "",
                },
                "pathway_responses": {
                    "consent_to_questions": "yes",
                    "caller_for": item["caller_for"],
                    "selected_pathway": item["request_type"],
                    "appointment_redirected": item["request_type"] == "appointment_redirect",
                    "identity": {
                        "patient_name": item["patient_name"],
                        "dob": item["dob"],
                        "postcode": item["postcode"],
                        "callback_number_from_caller_id": item["callback_number"],
                        "callback_confirmed": True,
                    },
                    "prescription": {
                        "prescription_type": "repeat" if item["request_type"] == "prescription" else "",
                        "medications_requested": ["atorvastatin 20mg"] if item["request_type"] == "prescription" else [],
                        "pharmacy": "Demo Pharmacy" if item["request_type"] == "prescription" else "",
                        "run_out_status": "two tablets left" if item["request_type"] == "prescription" else "",
                    },
                    "sick_note": {
                        "request_type": "new" if item["request_type"] == "sick_note" else "",
                        "purpose": "work" if item["request_type"] == "sick_note" else "",
                        "requested_duration": "one week" if item["request_type"] == "sick_note" else "",
                        "reason": "viral illness" if item["request_type"] == "sick_note" else "",
                    },
                    "referral": {
                        "referral_type": "chasing" if item["request_type"] == "referral" else "",
                        "specialty": "orthopaedics" if item["request_type"] == "referral" else "",
                        "approx_submission_date": "about four weeks ago" if item["request_type"] == "referral" else "",
                    },
                    "admin": {
                        "caller_relationship": item["caller_relationship"],
                        "needs_identity_check": item["request_type"] == "admin",
                    },
                    "urgency_assessment": {
                        "urgency_level": item["priority"],
                        "red_flags_mentioned": ["chest pain", "breathlessness", "sweating"] if item["red_flags_present"] else [],
                        "red_flag_followup_questions": [],
                        "emergency_advice_given": item["red_flags_present"],
                        "transfer_offered": False,
                        "transfer_accepted": False,
                    },
                    "summary_confirmation": {
                        "summary_read_back": item["summary"],
                        "caller_confirmed_correct": True,
                        "anything_else": "no",
                    },
                },
                "raw_transcript": transcript,
                "transcript_summary": item["summary"],
                "call_duration_seconds": 180,
                "caller_sentiment": "demo",
                "caller_difficulty": "demo",
                "transcript_quality": "demo_realistic",
                "handoff_confidence": 0.91,
                "extraction_confidence": 0.88,
                "staff_review_required": item["staff_review_required"],
                "red_flags_present": item["red_flags_present"],
                "assigned_to": "",
                "outcome_notes": "",
                "staff_action": "",
                "resolved_at": "",
                "resolved_by": "",
                "last_edited_at": "",
                "last_edited_by": "",
                "turnaround_minutes": "",
            }
        )
    return calls


def encrypt_calls(batch_id: str) -> list[dict]:
    return [encrypt_envelope(call) for call in build_plain_calls(batch_id)]


def build_batch(batch_id: str) -> dict:
    batch_root = batch_id.rstrip("-")
    return {
        "test_mode": True,
        "disable_google_push": True,
        "refresh_artifacts": True,
        "batch_id": batch_root,
        "source": "voice_agent_demo",
        "calls": encrypt_calls(batch_root),
    }


def assert_envelope_shape(envelope: dict) -> None:
    missing = REQUIRED_ENVELOPE_FIELDS.difference(envelope.keys())
    if missing:
        raise ValueError(f"Envelope missing fields: {', '.join(sorted(missing))}")
    if envelope["protocol"] != "JEIE-1":
        raise ValueError(f"Unexpected protocol: {envelope['protocol']}")
    if envelope["alg"] != "RSA-OAEP-256+A256GCM":
        raise ValueError(f"Unexpected alg: {envelope['alg']}")
    if envelope["key_id"] != "jefflocal-rsa-test-001":
        raise ValueError(f"Unexpected key_id: {envelope['key_id']}")
    if envelope["signature_alg"] != "HMAC-SHA256":
        raise ValueError(f"Unexpected signature_alg: {envelope['signature_alg']}")


def local_self_check(batch_id: str, batch: dict) -> None:
    sample = batch["calls"][0]
    assert_envelope_shape(sample)
    if local_decrypt_envelope is not None:
        plain = build_plain_calls(batch_id)[0]
        decrypted = local_decrypt_envelope(sample)
        if decrypted.get("call_id") != plain["call_id"]:
            raise ValueError("Local decrypt check failed: call_id mismatch")
        if decrypted.get("source") != "voice_agent":
            raise ValueError("Local decrypt check failed: source mismatch")
        if decrypted.get("raw_transcript") != plain["raw_transcript"]:
            raise ValueError("Local decrypt check failed: transcript mismatch")
        return
    if build_n8ntest_batch is not None:
        working_shape = set(build_n8ntest_batch("N8NTEST-LOCAL-SHAPE")["calls"][0].keys())
        if set(sample.keys()) != working_shape:
            raise ValueError("Envelope shape mismatch against working N8NTEST fixture")


def print_summary(target_url: str, batch_id: str, calls: list[dict], dry_run: bool) -> None:
    summary = {
        "target_url": target_url,
        "batch_id": batch_id,
        "call_ids": [item["message_id"] for item in calls],
        "num_calls": len(calls),
        "mode": "dry-run" if dry_run else "send",
    }
    print(json.dumps(summary, indent=2))


def report_deadletter_issue(batch_id: str) -> None:
    deadletter_dir = ROOT_DIR / "queue" / "deadletter"
    if not deadletter_dir.exists():
        return
    matches = sorted(deadletter_dir.glob(f"*{batch_id}*.json"))
    if matches:
        print("Likely decrypt format mismatch: JeffLocal created decrypt_failed files for this batch.")
        for path in matches:
            print(f"  {path.name}")


def send_batch(target_url: str, payload: dict) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        target_url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Send one encrypted GPDEMO batch to a local n8n webhook.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-send", action="store_true")
    parser.add_argument("--prefix", default="")
    parser.add_argument("--url", default=DEFAULT_WEBHOOK_URL)
    args = parser.parse_args()

    if not args.url.strip():
        print("ERROR: --url is required", file=sys.stderr)
        return 2
    if not is_local_url(args.url):
        print("ERROR: refusing non-local webhook URL", file=sys.stderr)
        return 2

    batch_id = args.prefix.strip() or f"GPDEMO-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    batch = build_batch(batch_id)
    plain_calls = build_plain_calls(batch_id)
    print_summary(args.url, batch_id, batch["calls"], dry_run=args.dry_run)
    print(json.dumps({"plaintext_transcripts_over_500": all(len(call["raw_transcript"]) > 500 for call in plain_calls)}, indent=2))

    local_self_check(batch_id, batch)

    if args.dry_run:
        return 0
    if not args.confirm_send:
        print("Refusing to send without --confirm-send.", file=sys.stderr)
        return 2

    status, body = send_batch(args.url, batch)
    print(json.dumps({"batch_id": batch_id, "status": status}, indent=2))
    if status == 404:
        print(
            "n8n webhook not found. For /webhook-test, click Execute workflow / Listen for test event in n8n. "
            "For active workflows, use /webhook/..."
        )
    if status in {400, 500}:
        print(body)
    if 200 <= status < 300:
        time.sleep(1)
        report_deadletter_issue(batch_id)
    return 0 if 200 <= status < 300 else 1


if __name__ == "__main__":
    raise SystemExit(main())

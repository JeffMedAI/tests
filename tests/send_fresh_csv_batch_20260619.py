"""
Fresh 5-call batch using real patients from mock_patient_lookup_v3.csv.
Run: python tests/send_fresh_csv_batch_20260619.py --dry-run
     python tests/send_fresh_csv_batch_20260619.py --confirm-send
"""
from __future__ import annotations
import argparse, json, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT_DIR / "tests" / "fixtures"
for p in (ROOT_DIR, FIXTURE_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from live_lookup_test_payloads import encrypt_envelope  # noqa: E402

DEFAULT_URL = "http://localhost:5678/webhook/ava-live-intake"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fresh_blocks() -> list[dict]:
    return [
        # ── 001: Kevin Bradbury — prescription, matched, routine ───────────
        {
            "suffix": "001-PRESCRIPTION",
            "request_type": "prescription",
            "stated_request": "Repeat prescription for ramipril 10mg. Running low with three days supply remaining.",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "staff_review_required": False,
            "red_flags_present": False,
            "patient_name": "Kevin Bradbury",
            "dob": "1982-06-03",
            "postcode": "PR9 7LT",
            "callback_number": "07700100001",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Routine repeat prescription. No urgent symptoms. Callback confirmed.",
            "summary": "Routine repeat prescription request for ramipril 10mg. Three days supply left.",
            "transcript": (
                "Agent: Good morning, this is Jeff at Churchtown Medical Centre. How can I help you today? "
                "Caller: Morning, yes I need my repeat prescription please. It is ramipril, ten milligrams, "
                "for my blood pressure. I have about three days left so I do not want to run out. "
                "Agent: Of course. Can I confirm your name and date of birth for the records? "
                "Caller: Yes, it is Kevin Bradbury, third of June nineteen eighty two. "
                "Agent: Thank you Kevin. Are you experiencing any chest pain, breathlessness, severe headache, "
                "or any other urgent symptoms today? "
                "Caller: No, nothing like that. Blood pressure has been stable, I just need the tablets renewed. "
                "Agent: Understood. Can I take a callback number in case the team needs to reach you? "
                "Caller: Yes, it is 07700100001. "
                "Agent: And your postcode for verification? "
                "Caller: PR9 7LT. "
                "Agent: Perfect. I will pass this routine repeat prescription request for ramipril to the practice "
                "team. They will process it and send it to your nominated pharmacy. Is there anything else? "
                "Caller: No, that is everything. Thank you very much. "
                "Agent: You are welcome, Kevin. Have a good day."
            ),
        },
        # ── 002: Paul Callister — test_result, matched, needs review ───────
        {
            "suffix": "002-TESTRESULT",
            "request_type": "test_result",
            "stated_request": "Chasing blood test results taken last week — HbA1c and cholesterol panel. No results received yet.",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Paul Callister",
            "dob": "1958-11-10",
            "postcode": "PR9 7LT",
            "callback_number": "07700100002",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Test result chase. Staff review required to check whether results are ready.",
            "summary": "Chasing blood test results — HbA1c and cholesterol. Staff to review and call back.",
            "transcript": (
                "Agent: Hello, this is Jeff at Churchtown Medical Centre. How can I help? "
                "Caller: Hi yes, I am ringing to chase some blood test results. I had bloods taken last Tuesday "
                "and I have not heard anything back. The doctor wanted to check my HbA1c and my cholesterol. "
                "Agent: Thank you. Can I confirm your full name and date of birth please? "
                "Caller: Paul Callister, tenth of November nineteen fifty eight. "
                "Agent: Thank you Paul. Before I log this, are you experiencing any new or worrying symptoms "
                "at the moment — chest pain, breathlessness, anything that feels urgent? "
                "Caller: No, nothing urgent. I just want to know whether the results are back and whether "
                "they are normal or not. The GP said they would review and contact me but I have heard nothing. "
                "Agent: I understand. I will log a result-chase request for the practice team to review the "
                "blood results and arrange a callback. Can I take your best number? "
                "Caller: Yes, 07700100002 is fine. I am usually available in the afternoon. "
                "Agent: And your postcode for our records? "
                "Caller: PR9 7LT. "
                "Agent: Logged. A member of staff will review your results and call you back. "
                "Is there anything else today? "
                "Caller: No, that is all. Thank you."
            ),
        },
        # ── 003: Alexandra Cohen — sick_note, matched, needs review ─────────
        {
            "suffix": "003-SICKNOTE",
            "request_type": "sick_note",
            "stated_request": "Fit note requested for work-related stress and anxiety. Two weeks off recommended by previous GP.",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Alexandra Cohen",
            "dob": "1987-05-19",
            "postcode": "PR9 7LT",
            "callback_number": "07700100003",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Fit note request for anxiety and work stress. Staff review required before issue.",
            "summary": "Fit note requested for stress and anxiety. GP previously recommended two weeks off.",
            "transcript": (
                "Agent: Good afternoon, Churchtown Medical Centre. How can I help you today? "
                "Caller: Hi, I need a fit note please. I have been off work for the past week with stress and "
                "anxiety and my employer needs the documentation by Friday. I saw a GP last week who said I "
                "should take two weeks off but I did not get a formal fit note at the time. "
                "Agent: I am sorry to hear you have been struggling. Can I take your name and date of birth? "
                "Caller: Alexandra Cohen, nineteenth of May nineteen eighty seven. "
                "Agent: Thank you Alexandra. I just need to ask a few quick questions for your safety. Are you "
                "having any thoughts of harming yourself, or any other urgent health concerns beyond the anxiety? "
                "Caller: No, nothing like that. I am managing, I just need to rest and I need the paperwork for "
                "work. My manager has been quite understanding but they need the official note. "
                "Agent: I understand completely. I will log a fit note request for a GP to review. They will "
                "need to confirm the details before issuing. A callback number please? "
                "Caller: 07700100003. And my postcode is PR9 7LT. "
                "Agent: Perfect. Request logged. A GP will review and either issue the note or arrange a call "
                "with you. Is there anything else I can help with today? "
                "Caller: No, that is everything. I really appreciate it, thank you."
            ),
        },
        # ── 004: Dorothy Bridge — admin, third-party, identity issue ────────
        {
            "suffix": "004-THIRDPARTY",
            "request_type": "admin",
            "stated_request": "Daughter calling on behalf of elderly mother Dorothy Bridge. Requesting medication review appointment.",
            "verification_status": "possible_match",
            "priority": "review_required",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Dorothy Bridge",
            "dob": "1942-01-31",
            "postcode": "PR9 7LT",
            "callback_number": "07700100004",
            "caller_for": "third_party",
            "caller_relationship": "third_party",
            "pathway_response": "Third-party caller. Identity could not be fully confirmed. Staff identity check required.",
            "summary": "Daughter calling for mother Dorothy Bridge. Medication review requested. Identity check required.",
            "transcript": (
                "Agent: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Hello, I am calling on behalf of my mother. She is eighty four and she cannot manage "
                "the phone very well any more so I usually ring for her. Her name is Dorothy Bridge. "
                "Agent: Thank you. Can I confirm your relationship to the patient and check a few details? "
                "Caller: Yes, I am her daughter, Sandra. She lives with me now. I can give you her date of "
                "birth if that helps — it is the thirty first of January nineteen forty two. "
                "Agent: Thank you Sandra. What does Dorothy need help with today? "
                "Caller: She had her medication changed last month and I am not sure one of the new tablets "
                "is agreeing with her. She has been a bit dizzy. I wanted to get her booked in for a medication "
                "review before it gets any worse. She is not in immediate danger, just a bit off. "
                "Agent: I understand. For the safety of your mother, I need to flag this as a third-party "
                "call for staff to verify identity before any clinical information is shared. A staff member "
                "will call this number back to confirm authorisation. Is 07700100004 the best number? "
                "Caller: Yes, that is my mobile. I am available most of the day. "
                "Agent: Thank you Sandra. I will pass this to the team as an identity review case. "
                "They will contact you shortly to verify and arrange the medication review."
            ),
        },
        # ── 005: Steven Cain — red flag, 999 Emergency, meningitis signs ───
        {
            "suffix": "005-REDFLAG",
            "request_type": "appointment_redirect",
            "stated_request": "Emergency symptoms — severe sudden headache, neck stiffness, sensitivity to light, high fever. Possible meningitis. Caller advised 999 immediately.",
            "verification_status": "matched",
            "priority": "999 Emergency",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": True,
            "patient_name": "Steven Cain",
            "dob": "1988-10-15",
            "postcode": "PR9 7LT",
            "callback_number": "07700100005",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Emergency red-flag symptoms. Caller advised to call 999 immediately. Do not wait.",
            "summary": "Severe sudden headache, neck stiffness, fever, light sensitivity. 999 Emergency. Call 999 now.",
            "transcript": (
                "Agent: Good morning, Churchtown Medical Centre. How can I help you? "
                "Caller: I feel really unwell, I need to speak to someone urgently. I woke up with the worst "
                "headache I have ever had in my life, it came on suddenly about two hours ago. My neck is "
                "really stiff and it hurts to move it. I have a high temperature and light is hurting my eyes. "
                "Agent: I hear you. This is very important. Can you confirm your name and date of birth quickly? "
                "Caller: Steven Cain, fifteenth of October nineteen eighty eight. "
                "Agent: Steven, the symptoms you are describing — sudden severe headache, stiff neck, fever "
                "and sensitivity to light — are warning signs that need emergency assessment right now. "
                "I need you to call nine nine nine immediately or have someone take you to A and E. "
                "Do not wait for a GP callback. This cannot wait. "
                "Caller: Should I drive myself? I live alone. "
                "Agent: Do not drive. Call nine nine nine right now and tell them your symptoms. They will "
                "come to you. Can you do that right now? "
                "Caller: Yes, okay, I will call nine nine nine. "
                "Agent: Good. I am logging this as an emergency red-flag case for the practice record. "
                "But your immediate action is to call nine nine nine. Do that now, Steven. "
                "Caller: Okay. Thank you. Calling now."
            ),
        },
    ]


def build_plain_calls(batch_id: str) -> list[dict]:
    ts = utc_now()
    calls = []
    for item in fresh_blocks():
        transcript = item["transcript"].strip()
        if len(transcript) <= 500:
            raise ValueError(f"Transcript too short ({item['suffix']}): {len(transcript)} chars")
        call_id = f"{batch_id}-{item['suffix']}"
        calls.append({
            "call_id": call_id,
            "call_timestamp": ts,
            "workflow": "voice_agent_fresh_batch",
            "request_type": item["request_type"],
            "source": "voice_agent",
            "voice_agent": {
                "agent_name": "Jeff Voice Agent",
                "session_id": f"VA-{call_id}",
                "caller_channel": "phone",
                "call_direction": "inbound",
                "caller_id_captured": True,
                "call_duration_seconds": 200,
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
                "medications_requested": ["ramipril 10mg"] if item["request_type"] == "prescription" else [],
                "urgency_note": item["priority"],
                "pharmacy": "Churchtown Pharmacy" if item["request_type"] == "prescription" else "",
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
                    "medications_requested": ["ramipril 10mg"] if item["request_type"] == "prescription" else [],
                    "pharmacy": "Churchtown Pharmacy" if item["request_type"] == "prescription" else "",
                    "run_out_status": "three days left" if item["request_type"] == "prescription" else "",
                },
                "sick_note": {
                    "request_type": "new" if item["request_type"] == "sick_note" else "",
                    "purpose": "work" if item["request_type"] == "sick_note" else "",
                    "requested_duration": "two weeks" if item["request_type"] == "sick_note" else "",
                    "reason": "stress and anxiety" if item["request_type"] == "sick_note" else "",
                },
                "referral": {},
                "admin": {
                    "caller_relationship": item["caller_relationship"],
                    "needs_identity_check": item["caller_for"] == "third_party",
                },
                "urgency_assessment": {
                    "urgency_level": item["priority"],
                    "red_flags_mentioned": (
                        ["sudden severe headache", "neck stiffness", "fever", "photophobia"]
                        if item["red_flags_present"] else []
                    ),
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
            "call_duration_seconds": 200,
            "caller_sentiment": "demo",
            "caller_difficulty": "demo",
            "transcript_quality": "demo_realistic",
            "handoff_confidence": 0.92,
            "extraction_confidence": 0.89,
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
        })
    return calls


def build_batch(batch_id: str) -> dict:
    return {
        "test_mode": True,
        "disable_google_push": True,
        "refresh_artifacts": True,
        "batch_id": batch_id,
        "source": "voice_agent_fresh_batch",
        "calls": [encrypt_envelope(c) for c in build_plain_calls(batch_id)],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-send", action="store_true")
    parser.add_argument("--prefix", default="")
    parser.add_argument("--url", default=DEFAULT_URL)
    args = parser.parse_args()

    parsed = urllib.parse.urlparse(args.url)
    if parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
        print("ERROR: refusing non-local URL", file=sys.stderr)
        return 2

    batch_id = args.prefix or f"CSV-FRESH-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    plain = build_plain_calls(batch_id)
    print(json.dumps({
        "batch_id": batch_id,
        "mode": "dry-run" if args.dry_run else "send",
        "call_ids": [c["call_id"] for c in plain],
        "all_transcripts_over_500": all(len(c["raw_transcript"]) > 500 for c in plain),
    }, indent=2))

    if args.dry_run:
        return 0
    if not args.confirm_send:
        print("Refusing to send without --confirm-send.", file=sys.stderr)
        return 2

    batch = build_batch(batch_id)
    data = json.dumps(batch).encode()
    req = urllib.request.Request(
        args.url, data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            status, body = resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        status, body = e.code, e.read().decode()

    print(json.dumps({"batch_id": batch_id, "status": status}, indent=2))
    if status in {400, 500}:
        print(body)
    if 200 <= status < 300:
        time.sleep(1)
        dl = ROOT_DIR / "queue" / "deadletter"
        if dl.exists():
            hits = sorted(dl.glob(f"*{batch_id}*.json"))
            if hits:
                print("DEADLETTER HITS:")
                for h in hits:
                    print(f"  {h.name}")
    return 0 if 200 <= status < 300 else 1


if __name__ == "__main__":
    raise SystemExit(main())

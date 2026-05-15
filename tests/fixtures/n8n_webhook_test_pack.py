from __future__ import annotations

import json
import sys
from pathlib import Path


FIXTURE_DIR = Path(__file__).resolve().parent
if str(FIXTURE_DIR) not in sys.path:
    sys.path.insert(0, str(FIXTURE_DIR))


BASE_TIMESTAMP = "2026-05-12T09:00:00Z"


def _voice(call_id: str, duration: int, sentiment: str, difficulty: str, quality: str) -> dict:
    return {
        "agent_name": "Jeff Voice Agent",
        "session_id": f"VA-{call_id}",
        "caller_channel": "phone",
        "call_direction": "inbound",
        "caller_id_captured": True,
        "call_duration_seconds": duration,
        "language": "en-GB",
        "caller_sentiment": sentiment,
        "caller_difficulty": difficulty,
        "transcript_quality": quality,
    }


def _base_call(
    call_id: str,
    request_type: str,
    patient_name: str,
    dob: str,
    postcode: str,
    callback: str,
    transcript: str,
    summary: str,
    duration: int,
    sentiment: str,
    difficulty: str,
    quality: str,
    pathway_responses: dict,
    caller_for: str = "self",
    staff_review_required: bool = False,
    red_flags_present: bool = False,
    handoff_confidence: float = 0.9,
    extraction_confidence: float = 0.88,
) -> dict:
    selected_pathway = request_type
    return {
        "call_id": call_id,
        "call_timestamp": BASE_TIMESTAMP,
        "workflow": "n8n_local_webhook_test",
        "request_type": request_type,
        "source": "voice_agent",
        "voice_agent": _voice(call_id, duration, sentiment, difficulty, quality),
        "normalized_input": {
            "patient_name": patient_name,
            "dob": dob,
            "postcode": postcode,
            "callback_number": callback,
            "medications_requested": pathway_responses.get("prescription", {}).get("medications_requested", []),
            "urgency_note": pathway_responses.get("urgency_assessment", {}).get("urgency_level", "routine"),
            "pharmacy": pathway_responses.get("prescription", {}).get("pharmacy", ""),
            "caller_for": caller_for,
            "supplied_nhs_number": "",
        },
        "pathway_responses": {
            "consent_to_questions": "yes",
            "caller_for": caller_for,
            "selected_pathway": selected_pathway,
            "appointment_redirected": selected_pathway == "appointment_redirect",
            "identity": {
                "patient_name": patient_name,
                "dob": dob,
                "postcode": postcode,
                "callback_number_from_caller_id": callback,
                "callback_confirmed": bool(callback),
            },
            "prescription": pathway_responses.get("prescription", {}),
            "sick_note": pathway_responses.get("sick_note", {}),
            "referral": pathway_responses.get("referral", {}),
            "test_result": pathway_responses.get("test_result", {}),
            "appointment_redirect": pathway_responses.get("appointment_redirect", {}),
            "admin": pathway_responses.get("admin", {}),
            "urgency_assessment": pathway_responses.get(
                "urgency_assessment",
                {
                    "urgency_level": "routine",
                    "red_flags_mentioned": [],
                    "red_flag_followup_questions": [],
                    "emergency_advice_given": False,
                    "transfer_offered": False,
                    "transfer_accepted": False,
                },
            ),
            "summary_confirmation": {
                "summary_read_back": summary,
                "caller_confirmed_correct": True,
                "anything_else": "no",
            },
        },
        "raw_transcript": transcript,
        "transcript_summary": summary,
        "call_duration_seconds": duration,
        "caller_sentiment": sentiment,
        "caller_difficulty": difficulty,
        "transcript_quality": quality,
        "handoff_confidence": handoff_confidence,
        "extraction_confidence": extraction_confidence,
        "staff_review_required": staff_review_required,
        "red_flags_present": red_flags_present,
        "assigned_to": "",
        "outcome_notes": "",
        "staff_action": "",
        "resolved_at": "",
        "resolved_by": "",
        "last_edited_at": "",
        "last_edited_by": "",
        "turnaround_minutes": "",
    }


def build_test_calls() -> list[dict]:
    return [
        _base_call(
            "N8NTEST-001-PRESCRIPTION",
            "prescription",
            "Jason Morrey",
            "1970-01-10",
            "PR9 7LT",
            "07111002001",
            "Jeff: Good morning, how can I help? Caller: I need my repeat atorvastatin twenty milligrams please. Jeff: Can I confirm your name, date of birth and postcode? Caller: Jason Morrey, tenth January nineteen seventy, PR9 7LT. Jeff: Is this number ending 2001 best for callback? Caller: Yes. Jeff: Which pharmacy? Caller: Test Pharmacy. Jeff: I will pass the routine repeat request to the practice team.",
            "Routine repeat prescription request for Jason Morrey for atorvastatin 20mg.",
            184,
            "calm",
            "easy",
            "good",
            {"prescription": {"prescription_type": "repeat", "medications_requested": ["atorvastatin 20mg"], "pharmacy": "Test Pharmacy", "run_out_status": "has one week left"}},
        ),
        _base_call(
            "N8NTEST-002-SICKNOTE",
            "sick_note",
            "Mathew Morrey",
            "1978-09-15",
            "PR9 7LT",
            "07111002002",
            "Jeff: How can I help today? Caller: I need a fit note for work after flu. Jeff: Can I confirm your details? Caller: Mathew Morrey, fifteenth September nineteen seventy eight, postcode PR9 7LT. Jeff: What dates should it cover? Caller: From Monday for one week. Jeff: I will pass the sick note request to the admin team.",
            "Fit note request for Mathew Morrey after flu, one week from Monday.",
            178,
            "calm",
            "easy",
            "good",
            {"sick_note": {"request_type": "new", "purpose": "work", "start_date": "Monday", "requested_duration": "one week", "reason": "flu symptoms"}},
            staff_review_required=True,
        ),
        _base_call(
            "N8NTEST-003-REFERRAL",
            "referral",
            "Peter Morrey",
            "1978-09-15",
            "PR9 7LT",
            "07111002003",
            "Jeff: What can I help with? Caller: I am chasing a hospital referral for orthopaedics. Jeff: Please confirm your name, date of birth and postcode. Caller: Peter Morrey, fifteenth September nineteen seventy eight, PR9 7LT. Jeff: When was it discussed? Caller: About four weeks ago. Jeff: I will send this to the referrals team for review.",
            "Referral chase for Peter Morrey, orthopaedics, discussed about four weeks ago.",
            210,
            "concerned",
            "medium",
            "good",
            {"referral": {"referral_type": "chasing", "hospital_name": "Southport Hospital", "approx_submission_date": "four weeks ago", "specialty": "orthopaedics"}},
            staff_review_required=True,
        ),
        _base_call(
            "N8NTEST-004-IDENTITY",
            "prescription",
            "Jayson Morrey",
            "1970-01-10",
            "PR9 7LT",
            "07111002004",
            "Jeff: Are you calling for yourself? Caller: No, I am calling for my brother Jason, but I may have spelt his name wrong. Jeff: What is his date of birth and postcode? Caller: Tenth January nineteen seventy, PR9 7LT. Jeff: What does he need? Caller: His repeat atorvastatin. Jeff: I will mark this for staff review because this is a third-party call and identity needs checking.",
            "Third-party repeat prescription request with similar stated name Jayson Morrey.",
            222,
            "uncertain",
            "medium",
            "good",
            {"prescription": {"prescription_type": "repeat", "medications_requested": ["atorvastatin 20mg"], "pharmacy": "Test Pharmacy", "run_out_status": "unknown"}},
            caller_for="brother",
            staff_review_required=True,
            handoff_confidence=0.84,
            extraction_confidence=0.82,
        ),
        _base_call(
            "N8NTEST-005-REDFLAG",
            "appointment_redirect",
            "Geoffrey Mynne",
            "1941-02-21",
            "PR9 7LT",
            "07111002005",
            "Jeff: Tell me what is happening. Caller: I have chest pain, I feel sweaty and I am struggling to breathe. Jeff: This could be an emergency. Please call nine nine nine now or go to A and E. Can I confirm your name and date of birth for the practice note? Caller: Geoffrey Mynne, twenty first February nineteen forty one, PR9 7LT. Jeff: I will mark this as possible emergency red flag.",
            "Possible emergency: chest pain, sweating and breathlessness. 999 advice given.",
            246,
            "distressed",
            "hard",
            "good",
            {
                "appointment_redirect": {"appointment_reason": "chest pain and breathlessness", "preferred_timeframe": "immediate"},
                "urgency_assessment": {
                    "urgency_level": "999 Emergency",
                    "red_flags_mentioned": ["chest pain", "sweating", "breathlessness"],
                    "red_flag_followup_questions": [],
                    "emergency_advice_given": True,
                    "transfer_offered": False,
                    "transfer_accepted": False,
                },
            },
            staff_review_required=True,
            red_flags_present=True,
            handoff_confidence=0.96,
            extraction_confidence=0.92,
        ),
    ]


def build_encrypted_calls() -> list[dict]:
    from live_lookup_test_payloads import encrypt_envelope

    return [encrypt_envelope(call) for call in build_test_calls()]


def build_batch(batch_id: str = "N8NTEST-LOCAL-BATCH") -> dict:
    return {
        "test_mode": True,
        "batch_id": batch_id,
        "disable_google_push": True,
        "refresh_artifacts": True,
        "calls": build_encrypted_calls(),
    }


def main() -> None:
    print(json.dumps(build_batch(), indent=2))


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


FIXTURE_DIR = Path(__file__).resolve().parent
if str(FIXTURE_DIR) not in sys.path:
    sys.path.insert(0, str(FIXTURE_DIR))

from live_lookup_test_payloads import encrypt_envelope  # noqa: E402
from n8n_webhook_test_pack import _base_call  # noqa: E402


def build_test_calls(batch_id: str) -> list[dict]:
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    prefix = batch_id.rstrip("-")
    calls = [
        _base_call(
            f"{prefix}-001-PRESCRIPTION",
            "prescription",
            "Jason Morrey",
            "1970-01-10",
            "PR9 7LT",
            "07111003001",
            "Jeff: Good morning, how can I help? Caller: I need my repeat atorvastatin twenty milligrams please. Jeff: Can I confirm your name, date of birth and postcode? Caller: Jason Morrey, tenth January nineteen seventy, PR9 7LT. Jeff: Is this number ending 3001 best for callback? Caller: Yes. Jeff: Which pharmacy? Caller: Test Pharmacy. Jeff: I will pass the routine repeat request to the practice team.",
            "Routine repeat prescription request for Jason Morrey for atorvastatin 20mg.",
            186,
            "calm",
            "easy",
            "good",
            {"prescription": {"prescription_type": "repeat", "medications_requested": ["atorvastatin 20mg"], "pharmacy": "Test Pharmacy", "run_out_status": "has one week left"}},
        ),
        _base_call(
            f"{prefix}-002-SICKNOTE",
            "sick_note",
            "Mathew Morrey",
            "1978-09-15",
            "PR9 7LT",
            "07111003002",
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
            f"{prefix}-003-REFERRAL",
            "referral",
            "Peter Morrey",
            "1978-09-15",
            "PR9 7LT",
            "07111003003",
            "Jeff: What can I help with? Caller: I am chasing a hospital referral for orthopaedics. Jeff: Please confirm your name, date of birth and postcode. Caller: Peter Morrey, fifteenth September nineteen seventy eight, PR9 7LT. Jeff: When was it discussed? Caller: About four weeks ago. Jeff: I will send this to the referrals team for review.",
            "Referral chase for Peter Morrey, orthopaedics, discussed about four weeks ago.",
            211,
            "concerned",
            "medium",
            "good",
            {"referral": {"referral_type": "chasing", "hospital_name": "Southport Hospital", "approx_submission_date": "four weeks ago", "specialty": "orthopaedics"}},
            staff_review_required=True,
        ),
        _base_call(
            f"{prefix}-004-IDENTITY",
            "prescription",
            "Jayson Morrey",
            "1970-01-10",
            "PR9 7LT",
            "07111003004",
            "Jeff: Are you calling for yourself? Caller: No, I am calling for my brother Jason, but I may have spelt his name wrong. Jeff: What is his date of birth and postcode? Caller: Tenth January nineteen seventy, PR9 7LT. Jeff: What does he need? Caller: His repeat atorvastatin. Jeff: I will mark this for staff review because this is a third-party call and identity needs checking.",
            "Third-party repeat prescription request with similar stated name Jayson Morrey.",
            223,
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
            f"{prefix}-005-REDFLAG",
            "appointment_redirect",
            "Geoffrey Mynne",
            "1941-02-21",
            "PR9 7LT",
            "07111003005",
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
    for call in calls:
        call["call_timestamp"] = timestamp
        call["workflow"] = "production_grade_local_simulation"
    return calls


def build_batch(batch_id: str) -> dict:
    if not batch_id.startswith("N8NTEST-PRODSIM-"):
        raise ValueError("batch_id must start with N8NTEST-PRODSIM-")
    return {
        "test_mode": True,
        "batch_id": batch_id,
        "disable_google_push": True,
        "refresh_artifacts": False,
        "calls": [encrypt_envelope(call) for call in build_test_calls(batch_id)],
    }


def main() -> None:
    batch_id = "N8NTEST-PRODSIM-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    print(json.dumps(build_batch(batch_id), indent=2))


if __name__ == "__main__":
    main()

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path

FIXTURE_DIR = Path(r"C:\JeffLocal\tests\fixtures")
sys.path.insert(0, str(FIXTURE_DIR))

from live_lookup_test_payloads import encrypt_envelope  # noqa: E402


DEFAULT_OUTPUT_DIR = Path(r"C:\JeffLocal\queue\encrypted_raw")


BASE_TIMESTAMP = "2026-05-11T12:00:00Z"


def _identity(name, dob, postcode, callback):
    return {
        "patient_name": name,
        "dob": dob,
        "postcode": postcode,
        "callback_number_from_caller_id": callback,
        "callback_confirmed": bool(callback),
    }


def _voice(call_id, duration, sentiment, difficulty, quality):
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


def _quality(handoff=0.92, extraction=0.9, staff_review=False, red_flags=False):
    return {
        "handoff_confidence": handoff,
        "extraction_confidence": extraction,
        "staff_review_required": staff_review,
        "red_flags_present": red_flags,
    }


def _base_call(
    call_id,
    request_type,
    selected_pathway,
    patient_name,
    dob,
    postcode,
    callback,
    transcript,
    transcript_summary,
    duration,
    sentiment,
    difficulty,
    transcript_quality,
    pathway_specific,
    workflow="universal_mock",
    caller_for="self",
    staff_review_required=False,
    red_flags_present=False,
    handoff_confidence=0.92,
    extraction_confidence=0.9,
):
    pathway_responses = {
        "consent_to_questions": "yes",
        "caller_for": caller_for,
        "selected_pathway": selected_pathway,
        "appointment_redirected": selected_pathway == "appointment_redirect",
        "identity": _identity(patient_name, dob, postcode, callback),
        "prescription": pathway_specific.get("prescription", {}),
        "sick_note": pathway_specific.get("sick_note", {}),
        "referral": pathway_specific.get("referral", {}),
        "test_result": pathway_specific.get("test_result", {}),
        "appointment_redirect": pathway_specific.get("appointment_redirect", {}),
        "admin": pathway_specific.get("admin", {}),
        "urgency_assessment": pathway_specific.get("urgency_assessment", {
            "urgency_level": "routine",
            "red_flags_mentioned": [],
            "red_flag_followup_questions": [],
            "emergency_advice_given": False,
            "transfer_offered": False,
            "transfer_accepted": False,
        }),
        "summary_confirmation": {
            "summary_read_back": transcript_summary,
            "caller_confirmed_correct": True,
            "anything_else": "no",
        },
    }

    meds = pathway_responses["prescription"].get("medications_requested", [])
    pharmacy = pathway_responses["prescription"].get("pharmacy", "")
    urgency = pathway_responses["urgency_assessment"].get("urgency_level", "")

    return {
        "call_id": call_id,
        "call_timestamp": BASE_TIMESTAMP,
        "workflow": workflow,
        "request_type": request_type,
        "source": "voice_agent",
        "voice_agent": _voice(call_id, duration, sentiment, difficulty, transcript_quality),
        "normalized_input": {
            "patient_name": patient_name,
            "dob": dob,
            "postcode": postcode,
            "callback_number": callback,
            "medications_requested": meds,
            "urgency_note": urgency,
            "pharmacy": pharmacy,
            "caller_for": caller_for,
            "supplied_nhs_number": "",
        },
        "pathway_responses": pathway_responses,
        "raw_transcript": transcript,
        "transcript_summary": transcript_summary,
        "call_duration_seconds": duration,
        "caller_sentiment": sentiment,
        "caller_difficulty": difficulty,
        "transcript_quality": transcript_quality,
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


def build_mock_calls():
    return [
        _base_call(
            "RAWMOCK-001-REPEAT-EXACT",
            "prescription",
            "prescription",
            "Jason Morrey",
            "1970-01-10",
            "PR9 7LT",
            "07111001001",
            "Jeff: Good morning, how can I help? Caller: I need my repeat prescription for atorvastatin twenty milligrams please. Jeff: Can I confirm your name, date of birth and postcode? Caller: Jason Morrey, tenth January nineteen seventy, PR9 7LT. Jeff: Is this number ending 1001 best for callback? Caller: Yes. Jeff: Which pharmacy? Caller: Test Pharmacy. Jeff: I will pass the routine repeat request to the practice team.",
            "Routine repeat prescription request for Jason Morrey for atorvastatin 20mg.",
            188,
            "calm",
            "easy",
            "good",
            {"prescription": {"prescription_type": "repeat", "medications_requested": ["atorvastatin 20mg"], "pharmacy": "Test Pharmacy", "run_out_status": "has seven days left"}},
        ),
        _base_call(
            "RAWMOCK-002-CALLBACK-NOT-CONFIRMED",
            "prescription",
            "prescription",
            "Marcus Morrey",
            "1972-10-12",
            "PR9 7LT",
            "",
            "Jeff: Prescription line, how can I help? Caller: I need ramipril five milligrams. Jeff: Can I take your name and date of birth? Caller: Marcus Morrey, twelfth October nineteen seventy two, PR9 7LT. Jeff: I cannot confirm a callback number from this call. Caller: I do not want to give one now. Jeff: I will send this for staff review because the team may need to contact you.",
            "Repeat prescription request for Marcus Morrey with no confirmed callback number.",
            205,
            "guarded",
            "medium",
            "good",
            {"prescription": {"prescription_type": "repeat", "medications_requested": ["ramipril 5mg"], "pharmacy": "Test Pharmacy", "run_out_status": "running low"}},
            staff_review_required=True,
            handoff_confidence=0.88,
            extraction_confidence=0.86,
        ),
        _base_call(
            "RAWMOCK-003-SICKNOTE",
            "sick_note",
            "sick_note",
            "Mathew Morrey",
            "1978-09-15",
            "PR9 7LT",
            "07111001003",
            "Jeff: How can I help? Caller: I need a fit note for work after flu. Jeff: Can I confirm your details? Caller: Mathew Morrey, fifteenth September nineteen seventy eight, postcode PR9 7LT. Jeff: What dates should it cover? Caller: From Monday for one week. Jeff: I will pass the sick note request to the admin team.",
            "Fit note request for Mathew Morrey after flu, one week from Monday.",
            176,
            "calm",
            "easy",
            "good",
            {"sick_note": {"request_type": "new", "purpose": "work", "start_date": "Monday", "requested_duration": "one week", "reason": "flu symptoms"}},
        ),
        _base_call(
            "RAWMOCK-004-REFERRAL-CHASE",
            "referral",
            "referral",
            "Peter Morrey",
            "1978-09-15",
            "PR9 7LT",
            "07111001004",
            "Jeff: What can I help with today? Caller: I am chasing a hospital referral for orthopaedics. Jeff: Please confirm your name, date of birth and postcode. Caller: Peter Morrey, fifteenth September nineteen seventy eight, PR9 7LT. Jeff: When was it discussed? Caller: About four weeks ago. Jeff: I will send this to the referrals team for review.",
            "Referral chase for Peter Morrey, orthopaedics, discussed about four weeks ago.",
            212,
            "concerned",
            "medium",
            "good",
            {"referral": {"referral_type": "chasing", "hospital_name": "Southport Hospital", "approx_submission_date": "four weeks ago", "specialty": "orthopaedics"}},
        ),
        _base_call(
            "RAWMOCK-005-TEST-RESULT",
            "test_result",
            "test_result",
            "Barbara Mynne",
            "1945-01-28",
            "PR9 7LT",
            "07111001005",
            "Jeff: How can I help? Caller: I am asking about my blood test result. Jeff: Can I confirm your name, date of birth and postcode? Caller: Barbara Mynne, twenty eighth January nineteen forty five, PR9 7LT. Jeff: When was the blood test? Caller: Last Tuesday morning. Jeff: I will pass this to the results team.",
            "Blood test result query for Barbara Mynne, test taken last Tuesday.",
            184,
            "calm",
            "easy",
            "good",
            {"test_result": {"test_type": "blood test", "approx_test_date": "last Tuesday", "reference_number": ""}},
        ),
        _base_call(
            "RAWMOCK-006-URGENT-REDFLAG",
            "appointment_redirect",
            "appointment_redirect",
            "Geoffrey Mynne",
            "1941-02-21",
            "PR9 7LT",
            "07111001006",
            "Jeff: Tell me what is happening. Caller: I have chest pain, I feel sweaty and I am struggling to breathe. Jeff: This could be an emergency. Please call nine nine nine now or go to A and E. Can I confirm your name and date of birth for the practice note? Caller: Geoffrey Mynne, twenty first February nineteen forty one, PR9 7LT. Jeff: I will mark this as possible emergency red flag.",
            "Possible emergency: chest pain, sweating and breathlessness. 999 advice given.",
            244,
            "distressed",
            "hard",
            "good",
            {
                "appointment_redirect": {"appointment_reason": "chest pain and breathlessness", "preferred_timeframe": "immediate"},
                "urgency_assessment": {"urgency_level": "999 Emergency", "red_flags_mentioned": ["chest pain", "sweating", "breathlessness"], "red_flag_followup_questions": [], "emergency_advice_given": True, "transfer_offered": False, "transfer_accepted": False},
            },
            workflow="clinical_admin",
            staff_review_required=True,
            red_flags_present=True,
            handoff_confidence=0.96,
            extraction_confidence=0.92,
        ),
        _base_call(
            "RAWMOCK-007-ADMIN-ADDRESS",
            "admin",
            "admin",
            "Cheryl Shepherd",
            "1961-11-26",
            "PR9 7LT",
            "07111001007",
            "Jeff: How can I help? Caller: I have moved and need to update my address and contact number. Jeff: Can I confirm your identity? Caller: Cheryl Shepherd, twenty sixth November nineteen sixty one, PR9 7LT. My new address is still in Southport and the callback number ending 1007 is correct. Jeff: I will pass this admin update to reception.",
            "Admin address and contact update for Cheryl Shepherd.",
            195,
            "calm",
            "easy",
            "good",
            {"admin": {"admin_reason": "address and contact update", "website_answer_available": False, "callback_needed": True}},
            staff_review_required=True,
        ),
        _base_call(
            "RAWMOCK-008-THIRD-PARTY-POSSIBLE",
            "prescription",
            "prescription",
            "Jayson Morrey",
            "1970-01-10",
            "PR9 7LT",
            "07111001008",
            "Jeff: Are you calling for yourself? Caller: No, I am calling for my brother Jason, but I may have spelt his name wrong. Jeff: What is his date of birth and postcode? Caller: Tenth January nineteen seventy, PR9 7LT. Jeff: What does he need? Caller: His repeat atorvastatin. Jeff: I will mark this for staff review because this is a third-party call and identity needs checking.",
            "Third-party repeat prescription request with similar stated name Jayson Morrey.",
            221,
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
            "RAWMOCK-009-INSUFFICIENT-ID",
            "admin",
            "admin",
            "Mr Morrey",
            "",
            "PR9 7LT",
            "07111001009",
            "Jeff: Can I confirm your full name and date of birth? Caller: It is Mr Morrey, I do not want to give my date of birth. Jeff: I need enough details for the team to identify the record. Caller: I just need someone to call me back about forms. Jeff: I will pass this as insufficient identity for staff review.",
            "Caller did not provide enough identity detail; asked for callback about forms.",
            166,
            "guarded",
            "hard",
            "fair",
            {"admin": {"admin_reason": "forms query with insufficient identity", "website_answer_available": False, "callback_needed": True}},
            staff_review_required=True,
            handoff_confidence=0.72,
            extraction_confidence=0.7,
        ),
        _base_call(
            "RAWMOCK-010-UNKNOWN-REQUEST",
            "unknown",
            "unknown",
            "John Murray",
            "1947-11-16",
            "PR9 7LT",
            "07111001010",
            "Jeff: How can I help? Caller: I am not sure. There was something from the surgery and maybe a message, or maybe a letter. Jeff: Can I confirm your details? Caller: John Murray, sixteenth November nineteen forty seven, PR9 7LT. Jeff: I will send this unclear request to staff review.",
            "Unclear request from John Murray; staff review needed.",
            172,
            "confused",
            "medium",
            "fair",
            {"admin": {"admin_reason": "unclear request", "website_answer_available": False, "callback_needed": True}},
            staff_review_required=True,
            handoff_confidence=0.7,
            extraction_confidence=0.68,
        ),
        _base_call(
            "RAWMOCK-011-NO-MATCH",
            "admin",
            "admin",
            "Oliver Testperson",
            "1980-04-04",
            "PR9 7LT",
            "07111001011",
            "Jeff: Can I take your name and date of birth? Caller: Oliver Testperson, fourth April nineteen eighty, PR9 7LT. Jeff: What do you need help with? Caller: I want to check whether I can register. Jeff: I will pass this to reception because I cannot confirm a current record.",
            "Registration/admin query for Oliver Testperson; no local match expected.",
            181,
            "calm",
            "easy",
            "good",
            {"admin": {"admin_reason": "registration query", "website_answer_available": False, "callback_needed": True}},
            staff_review_required=True,
            handoff_confidence=0.8,
            extraction_confidence=0.82,
        ),
        _base_call(
            "RAWMOCK-012-MESSY-MULTI-INTENT",
            "admin",
            "admin",
            "Marcus Mosey",
            "1967-03-11",
            "PR9 7LT",
            "07111001012",
            "Jeff: How can I help? Caller: I need tablets, or maybe it is about a referral, and also my address is wrong. Jeff: Let us confirm who you are first. Caller: Marcus Mosey, eleventh March nineteen sixty seven, PR9 7LT. Jeff: Which is the main thing today? Caller: I am not sure, please ask someone to look at my record and call me. Jeff: I will pass this as a messy multi-part admin request for staff review.",
            "Messy multi-intent call mentioning medication, referral and address; conservative admin review.",
            238,
            "frustrated",
            "hard",
            "fair",
            {"admin": {"admin_reason": "multiple unclear intents", "website_answer_available": False, "callback_needed": True}},
            staff_review_required=True,
            handoff_confidence=0.68,
            extraction_confidence=0.66,
        ),
    ]


def build_expected_handoffs():
    rows = []
    for call in build_mock_calls():
        ni = call["normalized_input"]
        handoff = deepcopy(call)
        request_type = call["request_type"] if call["request_type"] != "unknown" else "admin"
        verification = EXPECTED_OUTCOMES[call["call_id"]]["expected_verification_status"]
        handoff.update({
            "status": "New",
            "request_type": request_type,
            "request_subtype": call["request_type"],
            "verification_status": verification,
            "verification_reason": "Expected mock verification status for Raw Intake column contract.",
            "matched_patient_ref": "" if verification in {"no_match", "insufficient_data"} else "TEST-EMIS-" + call["call_id"][8:11],
            "matched_nhs_number": "" if verification in {"no_match", "insufficient_data"} else "TEST-NHS-" + call["call_id"][8:11],
            "top_candidate_name": ni["patient_name"] if verification != "no_match" else "",
            "priority": EXPECTED_OUTCOMES[call["call_id"]]["expected_priority"],
            "safe_to_queue": EXPECTED_OUTCOMES[call["call_id"]]["expected_safe_to_queue"],
            "task_title": f"{request_type.replace('_', ' ').title()} - mock contract",
            "task_body": "Mock handoff body for Raw Intake column contract validation.",
            "action_needed": EXPECTED_OUTCOMES[call["call_id"]]["expected_action_needed"],
            "call_summary": call["transcript_summary"],
            "staff_review_required": EXPECTED_OUTCOMES[call["call_id"]]["expected_staff_review_required"],
            "red_flags_present": EXPECTED_OUTCOMES[call["call_id"]]["expected_red_flags_present"],
        })
        rows.append(handoff)
    return rows


EXPECTED_OUTCOMES = {
    "RAWMOCK-001-REPEAT-EXACT": {"expected_status": "New", "expected_request_type": "prescription", "expected_patient_name": "Jason Morrey", "expected_dob": "1970-01-10", "expected_postcode": "PR9 7LT", "expected_callback_number": "07111001001", "expected_verification_status": "matched", "expected_priority": "routine", "expected_safe_to_queue": True, "expected_staff_review_required": False, "expected_red_flags_present": False, "expected_transcript_quality": "good", "expected_caller_sentiment": "calm", "expected_caller_difficulty": "easy", "expected_action_needed": "Process according to workflow", "expected_staff_action": "", "expected_notes": "Routine exact-match repeat prescription."},
    "RAWMOCK-002-CALLBACK-NOT-CONFIRMED": {"expected_status": "New", "expected_request_type": "prescription", "expected_patient_name": "Marcus Morrey", "expected_dob": "1972-10-12", "expected_postcode": "PR9 7LT", "expected_callback_number": "", "expected_verification_status": "matched", "expected_priority": "review_required", "expected_safe_to_queue": True, "expected_staff_review_required": True, "expected_red_flags_present": False, "expected_transcript_quality": "good", "expected_caller_sentiment": "guarded", "expected_caller_difficulty": "medium", "expected_action_needed": "Staff review required", "expected_staff_action": "", "expected_notes": "Callback not confirmed."},
    "RAWMOCK-003-SICKNOTE": {"expected_status": "New", "expected_request_type": "sick_note", "expected_patient_name": "Mathew Morrey", "expected_dob": "1978-09-15", "expected_postcode": "PR9 7LT", "expected_callback_number": "07111001003", "expected_verification_status": "matched", "expected_priority": "routine", "expected_safe_to_queue": True, "expected_staff_review_required": True, "expected_red_flags_present": False, "expected_transcript_quality": "good", "expected_caller_sentiment": "calm", "expected_caller_difficulty": "easy", "expected_action_needed": "Staff review required", "expected_staff_action": "", "expected_notes": "Sick note request."},
    "RAWMOCK-004-REFERRAL-CHASE": {"expected_status": "New", "expected_request_type": "referral", "expected_patient_name": "Peter Morrey", "expected_dob": "1978-09-15", "expected_postcode": "PR9 7LT", "expected_callback_number": "07111001004", "expected_verification_status": "matched", "expected_priority": "routine", "expected_safe_to_queue": True, "expected_staff_review_required": True, "expected_red_flags_present": False, "expected_transcript_quality": "good", "expected_caller_sentiment": "concerned", "expected_caller_difficulty": "medium", "expected_action_needed": "Staff review required", "expected_staff_action": "", "expected_notes": "Referral chase."},
    "RAWMOCK-005-TEST-RESULT": {"expected_status": "New", "expected_request_type": "test_result", "expected_patient_name": "Barbara Mynne", "expected_dob": "1945-01-28", "expected_postcode": "PR9 7LT", "expected_callback_number": "07111001005", "expected_verification_status": "matched", "expected_priority": "routine", "expected_safe_to_queue": True, "expected_staff_review_required": True, "expected_red_flags_present": False, "expected_transcript_quality": "good", "expected_caller_sentiment": "calm", "expected_caller_difficulty": "easy", "expected_action_needed": "Staff review required", "expected_staff_action": "", "expected_notes": "Test result query."},
    "RAWMOCK-006-URGENT-REDFLAG": {"expected_status": "New", "expected_request_type": "appointment_redirect", "expected_patient_name": "Geoffrey Mynne", "expected_dob": "1941-02-21", "expected_postcode": "PR9 7LT", "expected_callback_number": "07111001006", "expected_verification_status": "matched", "expected_priority": "999 Emergency", "expected_safe_to_queue": False, "expected_staff_review_required": True, "expected_red_flags_present": True, "expected_transcript_quality": "good", "expected_caller_sentiment": "distressed", "expected_caller_difficulty": "hard", "expected_action_needed": "Staff review required", "expected_staff_action": "", "expected_notes": "Emergency red flags."},
    "RAWMOCK-007-ADMIN-ADDRESS": {"expected_status": "New", "expected_request_type": "admin", "expected_patient_name": "Cheryl Shepherd", "expected_dob": "1961-11-26", "expected_postcode": "PR9 7LT", "expected_callback_number": "07111001007", "expected_verification_status": "matched", "expected_priority": "routine", "expected_safe_to_queue": True, "expected_staff_review_required": True, "expected_red_flags_present": False, "expected_transcript_quality": "good", "expected_caller_sentiment": "calm", "expected_caller_difficulty": "easy", "expected_action_needed": "Staff review required", "expected_staff_action": "", "expected_notes": "Admin address/contact update."},
    "RAWMOCK-008-THIRD-PARTY-POSSIBLE": {"expected_status": "New", "expected_request_type": "prescription", "expected_patient_name": "Jayson Morrey", "expected_dob": "1970-01-10", "expected_postcode": "PR9 7LT", "expected_callback_number": "07111001008", "expected_verification_status": "possible_match", "expected_priority": "review_required", "expected_safe_to_queue": True, "expected_staff_review_required": True, "expected_red_flags_present": False, "expected_transcript_quality": "good", "expected_caller_sentiment": "uncertain", "expected_caller_difficulty": "medium", "expected_action_needed": "Staff review required", "expected_staff_action": "", "expected_notes": "Third-party possible match."},
    "RAWMOCK-009-INSUFFICIENT-ID": {"expected_status": "New", "expected_request_type": "admin", "expected_patient_name": "Mr Morrey", "expected_dob": "", "expected_postcode": "PR9 7LT", "expected_callback_number": "07111001009", "expected_verification_status": "insufficient_data", "expected_priority": "review_required", "expected_safe_to_queue": True, "expected_staff_review_required": True, "expected_red_flags_present": False, "expected_transcript_quality": "fair", "expected_caller_sentiment": "guarded", "expected_caller_difficulty": "hard", "expected_action_needed": "Staff review required", "expected_staff_action": "", "expected_notes": "Missing DOB."},
    "RAWMOCK-010-UNKNOWN-REQUEST": {"expected_status": "New", "expected_request_type": "admin", "expected_patient_name": "John Murray", "expected_dob": "1947-11-16", "expected_postcode": "PR9 7LT", "expected_callback_number": "07111001010", "expected_verification_status": "matched", "expected_priority": "routine", "expected_safe_to_queue": True, "expected_staff_review_required": True, "expected_red_flags_present": False, "expected_transcript_quality": "fair", "expected_caller_sentiment": "confused", "expected_caller_difficulty": "medium", "expected_action_needed": "Staff review required", "expected_staff_action": "", "expected_notes": "Unknown request handled conservatively."},
    "RAWMOCK-011-NO-MATCH": {"expected_status": "New", "expected_request_type": "admin", "expected_patient_name": "Oliver Testperson", "expected_dob": "1980-04-04", "expected_postcode": "PR9 7LT", "expected_callback_number": "07111001011", "expected_verification_status": "no_match", "expected_priority": "review_required", "expected_safe_to_queue": True, "expected_staff_review_required": True, "expected_red_flags_present": False, "expected_transcript_quality": "good", "expected_caller_sentiment": "calm", "expected_caller_difficulty": "easy", "expected_action_needed": "Staff review required", "expected_staff_action": "", "expected_notes": "No patient match expected."},
    "RAWMOCK-012-MESSY-MULTI-INTENT": {"expected_status": "New", "expected_request_type": "admin", "expected_patient_name": "Marcus Mosey", "expected_dob": "1967-03-11", "expected_postcode": "PR9 7LT", "expected_callback_number": "07111001012", "expected_verification_status": "matched", "expected_priority": "routine", "expected_safe_to_queue": True, "expected_staff_review_required": True, "expected_red_flags_present": False, "expected_transcript_quality": "fair", "expected_caller_sentiment": "frustrated", "expected_caller_difficulty": "hard", "expected_action_needed": "Staff review required", "expected_staff_action": "", "expected_notes": "Messy multi-intent conservative admin routing."}
}


def write_encrypted_mock_calls(output_dir=DEFAULT_OUTPUT_DIR):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for call in build_mock_calls():
        envelope = encrypt_envelope(call)
        path = output_dir / f"{call['call_id']}.json"
        path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
        written.append(str(path))
    return written


def main():
    parser = argparse.ArgumentParser(description="Write 12 encrypted Raw Intake mock calls to encrypted_raw.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    args = parser.parse_args()
    written = write_encrypted_mock_calls(args.output_dir)
    print(json.dumps({"written_count": len(written), "paths": written}, indent=2))


if __name__ == "__main__":
    main()

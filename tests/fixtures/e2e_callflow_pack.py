"""
E2E Call Flow Test Pack — JeffLocal
Generates 10 mixed-case payloads with unique timestamped call IDs.
All 8 pathways covered. Full realistic transcripts. No collision with existing data.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


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


def _call(
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
    handoff_confidence: float = 0.92,
    extraction_confidence: float = 0.90,
) -> dict:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "call_id": call_id,
        "call_timestamp": timestamp,
        "workflow": "e2e_callflow_test",
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
            "selected_pathway": request_type,
            "appointment_redirected": request_type == "appointment_redirect",
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


def build_e2e_calls(run_ts: str | None = None) -> list[dict]:
    """
    Returns 10 mixed-case payloads with unique call IDs for the given run timestamp.
    All 8 pathways covered. run_ts defaults to now if not supplied.
    """
    ts = run_ts or _ts()

    def cid(seq: int, label: str) -> str:
        return f"E2E-{ts}-{seq:02d}-{label}"

    return [

        # ── Case 01: Routine repeat prescription, clean identity ───────────────
        _call(
            call_id=cid(1, "PRESCRIPTION"),
            request_type="prescription",
            patient_name="Margaret Holden",
            dob="1958-03-22",
            postcode="PR8 4NL",
            callback="07700900101",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help you today? "
                "Caller: Hello, I need to order my repeat prescription please. "
                "Jeff: Of course. Can I take your full name, date of birth and postcode? "
                "Caller: It's Margaret Holden, twenty second of March nineteen fifty eight, PR8 4NL. "
                "Jeff: And is this number ending 0101 the best number for a callback? "
                "Caller: Yes that's fine. "
                "Jeff: What medication do you need today? "
                "Caller: Ramipril five milligrams and amlodipine ten milligrams please. "
                "Jeff: And which pharmacy would you like to collect from? "
                "Caller: Boots on Lord Street please. "
                "Jeff: Do you have enough to last you until it's ready, usually two working days? "
                "Caller: Yes I have about a week left. "
                "Jeff: Perfect. I'll pass your repeat prescription request to the practice team. "
                "Is there anything else I can help with today? "
                "Caller: No that's everything thank you. "
                "Jeff: Thank you Margaret. Goodbye."
            ),
            summary="Routine repeat prescription for Margaret Holden: ramipril 5mg and amlodipine 10mg. Collection from Boots on Lord Street. Approximately one week of supply remaining.",
            duration=198,
            sentiment="calm",
            difficulty="easy",
            quality="good",
            pathway_responses={
                "prescription": {
                    "prescription_type": "repeat",
                    "medications_requested": ["ramipril 5mg", "amlodipine 10mg"],
                    "pharmacy": "Boots Lord Street",
                    "run_out_status": "has one week left",
                }
            },
            handoff_confidence=0.96,
            extraction_confidence=0.94,
        ),

        # ── Case 02: New fit note request, staff review required ───────────────
        _call(
            call_id=cid(2, "SICKNOTE"),
            request_type="sick_note",
            patient_name="Daniel Firth",
            dob="1985-11-04",
            postcode="PR9 0BT",
            callback="07700900102",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Hi, I need a sick note for work. I've been off since Monday with a bad back. "
                "Jeff: I can help with that. Can I take your name, date of birth and postcode please? "
                "Caller: Daniel Firth, fourth of November nineteen eighty five, PR9 0BT. "
                "Jeff: Thank you. And is this number ending 0102 okay for a callback? "
                "Caller: Yeah that's my mobile. "
                "Jeff: How long do you need the note to cover? "
                "Caller: Two weeks if possible. My GP said it might be a slipped disc. "
                "Jeff: And is this a new sick note or are you extending a previous one? "
                "Caller: New one, I haven't had one before for this. "
                "Jeff: Has a GP seen you about this back problem? "
                "Caller: Yes I had a phone appointment on Monday, that's when they mentioned the disc. "
                "Jeff: Thank you Daniel. I'll pass this to the admin team. "
                "A GP will need to review and authorise the fit note so you may get a callback. "
                "Caller: Okay thanks. "
                "Jeff: Is there anything else today? "
                "Caller: No that's it. "
                "Jeff: Thank you. Goodbye."
            ),
            summary="New fit note request for Daniel Firth. Off since Monday with back pain, possible slipped disc. GP appointment already taken place Monday. Requesting two-week note.",
            duration=214,
            sentiment="calm",
            difficulty="easy",
            quality="good",
            pathway_responses={
                "sick_note": {
                    "request_type": "new",
                    "purpose": "work",
                    "start_date": "Monday",
                    "requested_duration": "two weeks",
                    "reason": "back pain, possible slipped disc",
                    "gp_seen": True,
                }
            },
            staff_review_required=True,
            handoff_confidence=0.93,
            extraction_confidence=0.91,
        ),

        # ── Case 03: Referral chase, medium confidence ─────────────────────────
        _call(
            call_id=cid(3, "REFERRAL"),
            request_type="referral",
            patient_name="Susan Blackwell",
            dob="1962-07-19",
            postcode="PR8 6RS",
            callback="07700900103",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Yes, hello. I'm ringing about a referral. I was told I'd be referred to a dermatologist "
                "about six weeks ago and I haven't heard anything. I'm getting quite worried. "
                "Jeff: I understand. Let me take your details. Name, date of birth and postcode please? "
                "Caller: Susan Blackwell, nineteenth July nineteen sixty two, PR8 6RS. "
                "Jeff: And is this number ending 0103 okay for a callback? "
                "Caller: Yes. "
                "Jeff: Which hospital or clinic was the referral to? "
                "Caller: I think it was Southport and Ormskirk. The dermatology department. "
                "Jeff: And roughly when was the referral discussed with your GP? "
                "Caller: Early April I think. Maybe the third or fourth. "
                "Jeff: Thank you Susan. I'll pass this to the referrals team to check the status. "
                "Someone will call you back with an update. "
                "Caller: How long will that take? "
                "Jeff: The team aim to respond within one working day. "
                "Caller: Okay. Thank you. "
                "Jeff: Is there anything else? "
                "Caller: No that's all. "
                "Jeff: Thank you. Goodbye."
            ),
            summary="Referral chase for Susan Blackwell. Dermatology referral to Southport and Ormskirk discussed approximately six weeks ago (early April). No appointment received. Patient concerned.",
            duration=226,
            sentiment="concerned",
            difficulty="medium",
            quality="good",
            pathway_responses={
                "referral": {
                    "referral_type": "chasing",
                    "hospital_name": "Southport and Ormskirk Hospital",
                    "specialty": "dermatology",
                    "approx_submission_date": "early April 2026",
                }
            },
            staff_review_required=True,
            handoff_confidence=0.88,
            extraction_confidence=0.85,
        ),

        # ── Case 04: Test result chase ─────────────────────────────────────────
        _call(
            call_id=cid(4, "TEST-RESULT"),
            request_type="test_result",
            patient_name="Robert Kaye",
            dob="1949-05-30",
            postcode="PR9 7DQ",
            callback="07700900104",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Good morning. I had blood tests done last Thursday and I haven't had any results yet. "
                "Jeff: I can pass that on. Can I take your name, date of birth and postcode? "
                "Caller: Robert Kaye. K-A-Y-E. Thirtieth May nineteen forty nine. PR9 7DQ. "
                "Jeff: Thank you. Is this number ending 0104 okay for a callback? "
                "Caller: Yes that's my home number. "
                "Jeff: Do you know what the blood tests were checking for? "
                "Caller: My GP said it was for kidney function and thyroid. I'm on levothyroxine. "
                "Jeff: And were you expecting to be contacted, or were you just checking in? "
                "Caller: My GP said someone would call if there was anything to worry about "
                "but I just want to make sure they've come back. "
                "Jeff: Understood. I'll let the clinical team know and someone will call you with the results. "
                "Caller: Thank you very much. "
                "Jeff: Is there anything else today? "
                "Caller: No that's everything. "
                "Jeff: Thank you Robert. Goodbye."
            ),
            summary="Test result chase for Robert Kaye. Blood tests taken last Thursday (kidney function and thyroid). Patient on levothyroxine. No results received. Clinical team to review and call back.",
            duration=207,
            sentiment="calm",
            difficulty="easy",
            quality="good",
            pathway_responses={
                "test_result": {
                    "test_type": "blood tests",
                    "tests_requested": ["kidney function", "thyroid"],
                    "test_date": "last Thursday",
                    "result_status": "not received",
                }
            },
            handoff_confidence=0.94,
            extraction_confidence=0.92,
        ),

        # ── Case 05: Red flag — chest pain + breathlessness, 999 advised ───────
        _call(
            call_id=cid(5, "REDFLAG"),
            request_type="appointment_redirect",
            patient_name="Geoffrey Hargreaves",
            dob="1938-08-14",
            postcode="PR8 5TN",
            callback="07700900105",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: I've got chest pain. It started about twenty minutes ago and I'm sweating. "
                "Jeff: I need to ask you a few quick questions. Is the pain crushing or tight? "
                "Caller: Yes it's like a heavy weight on my chest. And I feel sick. "
                "Jeff: Are you having any difficulty breathing? "
                "Caller: Yes a bit. I'm short of breath just sitting here. "
                "Jeff: This sounds like it could be a medical emergency. "
                "You need to call nine nine nine immediately or have someone take you to A and E right now. "
                "Please do not drive yourself. "
                "Caller: Oh. Okay. My wife is here. "
                "Jeff: Please get your wife to call nine nine nine straight away. "
                "Do not wait. Can I take your name and date of birth for the practice record? "
                "Caller: Geoffrey Hargreaves. Fourteenth August nineteen thirty eight. PR8 5TN. "
                "Jeff: Thank you Geoffrey. Please call nine nine nine now. "
                "Caller: Okay. Thank you. "
                "Jeff: Goodbye and please act immediately."
            ),
            summary="EMERGENCY: Possible cardiac event. Geoffrey Hargreaves, 87, chest pain, sweating, nausea and breathlessness. 999 advice given. Wife present. Practice notified.",
            duration=187,
            sentiment="distressed",
            difficulty="hard",
            quality="good",
            pathway_responses={
                "appointment_redirect": {
                    "appointment_reason": "chest pain, sweating, nausea, breathlessness",
                    "preferred_timeframe": "immediate",
                },
                "urgency_assessment": {
                    "urgency_level": "999 Emergency",
                    "red_flags_mentioned": ["chest pain", "sweating", "difficulty breathing", "nausea"],
                    "red_flag_followup_questions": ["crushing or tight pain", "breathing difficulty"],
                    "emergency_advice_given": True,
                    "transfer_offered": False,
                    "transfer_accepted": False,
                },
            },
            staff_review_required=True,
            red_flags_present=True,
            handoff_confidence=0.97,
            extraction_confidence=0.95,
        ),

        # ── Case 06: Identity mismatch — third-party call, name unclear ────────
        _call(
            call_id=cid(6, "IDENTITY-MISMATCH"),
            request_type="prescription",
            patient_name="Kathrine Nolan",
            dob="1971-02-28",
            postcode="PR9 8EF",
            callback="07700900106",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Hi, I'm ringing for my mum. She needs her blood pressure tablets. "
                "Jeff: Of course. Are you calling on her behalf with her permission? "
                "Caller: Yes she's sitting right here, she just can't use the phone very well. "
                "Jeff: I'll need to take her details. What is her full name? "
                "Caller: Catherine Nolan. Or it might be Kathrine. I'm not sure how she spells it. "
                "Jeff: And her date of birth and postcode? "
                "Caller: Twenty eighth of February nineteen seventy one. PR9 8EF. "
                "Jeff: What medication does she need? "
                "Caller: Amlodipine. The five milligram ones. "
                "Jeff: Which pharmacy? "
                "Caller: The one on Botanic Road. "
                "Jeff: Thank you. I'll flag this for staff to verify the patient name before processing "
                "as there is some uncertainty about the spelling. "
                "Caller: Okay, is that a problem? "
                "Jeff: It just means a team member will double check the record. "
                "Caller: That's fine. "
                "Jeff: Is there anything else? "
                "Caller: No that's all. Thanks. "
                "Jeff: Thank you. Goodbye."
            ),
            summary="Third-party prescription request for amlodipine 5mg. Patient name uncertain — caller unsure if Catherine or Kathrine Nolan. DOB 28/02/1971, PR9 8EF. Botanic Road pharmacy. Identity verification required.",
            duration=231,
            sentiment="cooperative",
            difficulty="medium",
            quality="good",
            pathway_responses={
                "prescription": {
                    "prescription_type": "repeat",
                    "medications_requested": ["amlodipine 5mg"],
                    "pharmacy": "Botanic Road pharmacy",
                    "run_out_status": "unknown",
                }
            },
            caller_for="mother",
            staff_review_required=True,
            handoff_confidence=0.79,
            extraction_confidence=0.76,
        ),

        # ── Case 07: Admin — address change ────────────────────────────────────
        _call(
            call_id=cid(7, "ADMIN"),
            request_type="admin",
            patient_name="Priya Sharma",
            dob="1990-06-15",
            postcode="PR8 2JW",
            callback="07700900107",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Hi, I've moved house and I need to update my address on my records. "
                "Jeff: Of course. Can I take your name, date of birth and current postcode on file? "
                "Caller: Priya Sharma. Fifteenth June nineteen ninety. PR8 2JW — but that's the old one. "
                "Jeff: And is this number ending 0107 okay for a callback if needed? "
                "Caller: Yes. "
                "Jeff: What is your new address? "
                "Caller: Fourteen Kew Gardens, Southport, PR8 6AB. "
                "Jeff: And has your GP surgery changed or are you staying registered with us? "
                "Caller: Staying with you, yes. The surgery is close enough. "
                "Jeff: Perfect. I'll pass your address update to the admin team. "
                "They may send you a confirmation letter to the new address. "
                "Caller: That's fine. Thank you. "
                "Jeff: Is there anything else today? "
                "Caller: No that's all. "
                "Jeff: Thank you Priya. Goodbye."
            ),
            summary="Address change request for Priya Sharma. Moving from PR8 2JW to 14 Kew Gardens, Southport, PR8 6AB. Remaining registered at Churchtown. Admin team to update records.",
            duration=193,
            sentiment="calm",
            difficulty="easy",
            quality="good",
            pathway_responses={
                "admin": {
                    "admin_type": "address_change",
                    "new_address": "14 Kew Gardens, Southport, PR8 6AB",
                    "old_postcode": "PR8 2JW",
                    "staying_registered": True,
                }
            },
            handoff_confidence=0.95,
            extraction_confidence=0.93,
        ),

        # ── Case 08: Low confidence — unclear intent, below 0.72 floor ─────────
        _call(
            call_id=cid(8, "LOW-CONFIDENCE"),
            request_type="unknown",
            patient_name="Terry Bowden",
            dob="1966-09-09",
            postcode="PR9 0LN",
            callback="07700900108",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Yeah hi. I need to speak to someone. It's about my, erm, my condition. "
                "Jeff: Of course. Can you tell me a bit more about what you need? "
                "Caller: It's difficult to explain. I've been having these episodes. "
                "My doctor knows about it. I just need, I don't know, something sorted. "
                "Jeff: I see. Can I take your name, date of birth and postcode? "
                "Caller: Terry Bowden. Ninth September sixty six. PR9 0LN. "
                "Jeff: And is this number ending 0108 okay? "
                "Caller: Yes. "
                "Jeff: Are you looking to speak to a GP, or is it more of an admin matter? "
                "Caller: I'm not sure really. Maybe both. It's about my medication and an appointment. "
                "Jeff: I'll mark this for a team member to call you back and work out the best way to help. "
                "Caller: Okay yeah. Thanks. "
                "Jeff: Is there anything else? "
                "Caller: No that's it. "
                "Jeff: Thank you Terry. Goodbye."
            ),
            summary="Unclear request from Terry Bowden. Patient has ongoing condition, experiencing episodes. Mentions medication and possibly an appointment. Intent unclear — staff review and callback required.",
            duration=241,
            sentiment="uncertain",
            difficulty="hard",
            quality="fair",
            pathway_responses={
                "urgency_assessment": {
                    "urgency_level": "routine",
                    "red_flags_mentioned": [],
                    "red_flag_followup_questions": [],
                    "emergency_advice_given": False,
                    "transfer_offered": False,
                    "transfer_accepted": False,
                }
            },
            staff_review_required=True,
            handoff_confidence=0.65,
            extraction_confidence=0.61,
        ),

        # ── Case 09: Multi-intent — prescription + sick note, messy ───────────
        _call(
            call_id=cid(9, "MULTI-INTENT"),
            request_type="prescription",
            patient_name="Carol Whitfield",
            dob="1974-12-01",
            postcode="PR8 3HG",
            callback="07700900109",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Oh hi yes. I need a couple of things actually. I need my prescription — "
                "metformin — and also I was wondering about a sick note. I've been off work. "
                "Jeff: I can help with both. Let me take your details first. "
                "Name, date of birth and postcode please? "
                "Caller: Carol Whitfield. First December nineteen seventy four. PR8 3HG. "
                "Jeff: And is this number ending 0109 okay? "
                "Caller: Yes. "
                "Jeff: Let's start with the prescription. Is the metformin a repeat? "
                "Caller: Yes, five hundred milligrams twice a day. I get it from Lloyds. "
                "Jeff: And for the sick note — is this a new note or extending an existing one? "
                "Caller: New. I've been off two weeks with stress and anxiety. "
                "Jeff: Has a GP been involved in your care for this? "
                "Caller: I had a phone call with Dr Ahmed last week about it. "
                "Jeff: I'll pass both requests through. The prescription should be ready in two working days. "
                "The fit note will need GP authorisation so someone may call you. "
                "Caller: Brilliant, thank you. "
                "Jeff: Anything else? "
                "Caller: No that's great. "
                "Jeff: Thank you Carol. Goodbye."
            ),
            summary="Dual request from Carol Whitfield: (1) repeat prescription for metformin 500mg twice daily from Lloyds Pharmacy; (2) new sick note for two weeks off with stress and anxiety. GP Dr Ahmed consulted last week. Both require processing.",
            duration=258,
            sentiment="calm",
            difficulty="medium",
            quality="good",
            pathway_responses={
                "prescription": {
                    "prescription_type": "repeat",
                    "medications_requested": ["metformin 500mg"],
                    "pharmacy": "Lloyds Pharmacy",
                    "run_out_status": "unknown",
                },
                "sick_note": {
                    "request_type": "new",
                    "purpose": "work",
                    "start_date": "two weeks ago",
                    "requested_duration": "two weeks",
                    "reason": "stress and anxiety",
                    "gp_seen": True,
                },
            },
            staff_review_required=True,
            handoff_confidence=0.82,
            extraction_confidence=0.80,
        ),

        # ── Case 10: Emergency escalation — stroke symptoms ────────────────────
        _call(
            call_id=cid(10, "EMERGENCY-ESCALATION"),
            request_type="appointment_redirect",
            patient_name="Alan Forsyth",
            dob="1944-01-27",
            postcode="PR9 9GH",
            callback="07700900110",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: It's my husband. His face has dropped on one side and his arm is weak. "
                "He's trying to speak but the words aren't coming out right. It started about ten minutes ago. "
                "Jeff: This sounds like a possible stroke. You need to call nine nine nine immediately. "
                "Do not wait — please call nine nine nine right now. "
                "Caller: Should I bring him in to the surgery? "
                "Jeff: No. Do not travel to the surgery. Call nine nine nine immediately. "
                "Every minute matters with a stroke. "
                "Caller: Okay. Oh God. Okay I'm calling. "
                "Jeff: Please call nine nine nine now. Can I take his name and date of birth for our record? "
                "Caller: Alan Forsyth. Twenty seventh January nineteen forty four. PR9 9GH. "
                "Jeff: Thank you. Please hang up and call nine nine nine immediately. "
                "Caller: Yes. Going now. "
                "Jeff: Goodbye. Act now please."
            ),
            summary="STROKE EMERGENCY: Alan Forsyth, 82. Facial drooping, arm weakness, speech difficulty onset approximately 10 minutes ago. 999 advice given immediately. Caller (wife) confirmed calling 999. DO NOT WAIT — FAST criteria met.",
            duration=143,
            sentiment="panicked",
            difficulty="hard",
            quality="good",
            pathway_responses={
                "appointment_redirect": {
                    "appointment_reason": "facial drooping, arm weakness, speech difficulty — FAST criteria",
                    "preferred_timeframe": "immediate",
                },
                "urgency_assessment": {
                    "urgency_level": "999 Emergency",
                    "red_flags_mentioned": ["facial drooping", "arm weakness", "slurred speech", "sudden onset"],
                    "red_flag_followup_questions": ["FAST: Face drooping confirmed", "FAST: Arm weakness confirmed", "FAST: Speech difficulty confirmed"],
                    "emergency_advice_given": True,
                    "transfer_offered": False,
                    "transfer_accepted": False,
                },
            },
            caller_for="husband",
            staff_review_required=True,
            red_flags_present=True,
            handoff_confidence=0.98,
            extraction_confidence=0.97,
        ),
    ]


def build_e2e_batch(run_ts: str | None = None) -> dict:
    """Returns a complete batch payload for the n8n webhook."""
    ts = run_ts or _ts()
    return {
        "test_mode": True,
        "batch_id": f"E2E-{ts}",
        "disable_google_push": True,
        "refresh_artifacts": True,
        "calls": build_e2e_calls(ts),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build_e2e_batch(), indent=2))

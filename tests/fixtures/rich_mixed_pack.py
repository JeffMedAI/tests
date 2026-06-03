"""
Rich Mixed Test Pack — JeffLocal
Generates 12 comprehensive test calls covering ALL dashboard fields and caller scenarios.
Extended from e2e_callflow_pack.py with additional metadata: sentiment, difficulty,
transcript quality, confidence scores, verification status, and new fields.
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
    priority: str = "routine",
    verification_status: str = "verified",
    verification_reason: str = "",
    safe_to_queue: bool = True,
    transcript_score: float | None = None,
    caller_emotion_intensity: str = "low",
    call_difficulty_score: float | None = None,
    missing_information: list[str] | None = None,
    information_gaps: list[str] | None = None,
    clarification_needed: bool = False,
    ai_confidence_flags: list[str] | None = None,
    information_completeness: float | None = None,
    suggested_next_action: str = "",
) -> dict:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if call_difficulty_score is None:
        difficulty_map = {"easy": 0.15, "moderate": 0.45, "difficult": 0.70, "very_difficult": 0.85}
        call_difficulty_score = difficulty_map.get(difficulty, 0.5)

    if transcript_score is None:
        quality_map = {"good": 0.95, "fair": 0.70, "poor": 0.40, "very_poor": 0.15}
        transcript_score = quality_map.get(quality, 0.75)

    if information_completeness is None:
        information_completeness = 0.92 if not information_gaps else 0.65

    return {
        "call_id": call_id,
        "call_timestamp": timestamp,
        "workflow": "rich_mixed_test",
        "request_type": request_type,
        "source": "voice_agent",
        "voice_agent": _voice(call_id, duration, sentiment, difficulty, quality),
        "normalized_input": {
            "patient_name": patient_name,
            "dob": dob,
            "postcode": postcode,
            "callback_number": callback,
            "medications_requested": pathway_responses.get("prescription", {}).get("medications_requested", []),
            "urgency_note": pathway_responses.get("urgency_assessment", {}).get("urgency_level", priority),
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
                    "urgency_level": priority,
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
        "priority": priority,
        "verification_status": verification_status,
        "verification_reason": verification_reason,
        "safe_to_queue": safe_to_queue,
        "staff_review_required": staff_review_required,
        "red_flags_present": red_flags_present,
        "transcript_score": transcript_score,
        "caller_emotion_intensity": caller_emotion_intensity,
        "call_difficulty_score": call_difficulty_score,
        "missing_information": missing_information or [],
        "information_gaps": information_gaps or [],
        "clarification_needed": clarification_needed,
        "ai_confidence_flags": ai_confidence_flags or [],
        "information_completeness": information_completeness,
        "suggested_next_action": suggested_next_action,
        "assigned_to": "",
        "outcome_notes": "",
        "staff_action": "",
        "resolved_at": "",
        "resolved_by": "",
        "last_edited_at": "",
        "last_edited_by": "",
        "turnaround_minutes": "",
    }


def build_rich_calls(run_ts: str | None = None) -> list[dict]:
    """Returns 12 comprehensive test payloads covering all dashboard fields and scenarios."""
    ts = run_ts or _ts()

    def cid(seq: int, label: str) -> str:
        return f"RICH-{ts}-{seq:02d}-{label}"

    return [
        # 01: Routine prescription, clean and easy
        _call(
            call_id=cid(1, "ROUTINE-PRESCRIPTION"),
            request_type="prescription",
            patient_name="Margaret Holden",
            dob="1958-03-22",
            postcode="PR8 4NL",
            callback="07700900201",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help you today? "
                "Caller: Hello, I need to order my repeat prescription please. "
                "Jeff: Of course. Can I take your full name, date of birth and postcode? "
                "Caller: It's Margaret Holden, twenty second of March nineteen fifty eight, PR8 4NL. "
                "Jeff: And is this number ending 0201 the best number for a callback? "
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
            summary="Routine repeat prescription for Margaret Holden: ramipril 5mg and amlodipine 10mg. Collection from Boots on Lord Street. One week of supply remaining.",
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
            priority="routine",
            verification_status="verified",
            verification_reason="All fields matched EMIS record immediately",
            handoff_confidence=0.96,
            extraction_confidence=0.94,
            transcript_score=0.98,
            caller_emotion_intensity="low",
            information_completeness=0.99,
        ),

        # 02: Sick note, anxious patient, staff review required
        _call(
            call_id=cid(2, "ANXIOUS-SICKNOTE"),
            request_type="sick_note",
            patient_name="James Mitchell",
            dob="1975-07-14",
            postcode="PR9 0BT",
            callback="07700900202",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Oh, um, hi. I need a sick note. For work. I've been... um... off since Monday. "
                "Jeff: I can help with that. Can I take your name, date of birth and postcode please? "
                "Caller: Yes, um, James Mitchell. That's M-I-T-C-H-E-L-L. Erm, fourteenth July nineteen seventy five. "
                "Jeff: And the postcode? "
                "Caller: PR9 0BT. I'm quite worried about my job, you see. I've had anxiety attacks. "
                "Jeff: I understand. Is this number ending 0202 okay for callback? "
                "Caller: Yes, yes. Um, how long do you think it'll take? I'm worried they'll sack me. "
                "Jeff: How long do you need the note to cover? "
                "Caller: Two weeks? I don't know. The GP said it could be two weeks. Is that... is that okay? "
                "Jeff: That's fine. Has a GP seen you already? "
                "Caller: Yes, on Monday. Dr Ahmed. She was very nice but I'm still quite worried. "
                "Jeff: Thank you James. I'll pass this to the admin team and a GP will review it. You may get a callback. "
                "Caller: Okay. Thank you. I hope it's quick. "
                "Jeff: Is there anything else? "
                "Caller: No. No that's it. Thanks. "
                "Jeff: You're welcome. Goodbye."
            ),
            summary="New sick note request from James Mitchell. Off since Monday with anxiety attacks. GP (Dr Ahmed) consulted. Requesting two-week note. Patient anxious about employment.",
            duration=256,
            sentiment="anxious",
            difficulty="moderate",
            quality="good",
            pathway_responses={
                "sick_note": {
                    "request_type": "new",
                    "purpose": "work",
                    "start_date": "Monday",
                    "requested_duration": "two weeks",
                    "reason": "anxiety",
                    "gp_seen": True,
                }
            },
            staff_review_required=True,
            priority="routine",
            verification_status="verified",
            verification_reason="All identity details confirmed",
            handoff_confidence=0.89,
            extraction_confidence=0.87,
            transcript_score=0.92,
            caller_emotion_intensity="high",
            information_completeness=0.94,
        ),

        # 03: Dermatology referral status check, staff review needed
        _call(
            call_id=cid(3, "DERMATOLOGY-REFERRAL"),
            request_type="referral",
            patient_name="Susan Blackwell",
            dob="1962-07-19",
            postcode="PR8 6RS",
            callback="07700900203",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Yes, hello. I'm ringing about a referral. I was told I'd be referred to a dermatologist "
                "about six weeks ago and I haven't heard anything. I'm getting quite worried. "
                "Jeff: I understand. Let me take your details. Name, date of birth and postcode please? "
                "Caller: Susan Blackwell, nineteenth July nineteen sixty two, PR8 6RS. "
                "Jeff: And is this number ending 0203 okay for a callback? "
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
            summary="Referral chase for Susan Blackwell. Dermatology referral to Southport and Ormskirk Hospital discussed early April. No appointment received yet. Patient concerned.",
            duration=226,
            sentiment="concerned",
            difficulty="moderate",
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
            priority="routine",
            verification_status="verified",
            handoff_confidence=0.88,
            extraction_confidence=0.85,
            transcript_score=0.91,
            caller_emotion_intensity="medium",
            information_completeness=0.88,
        ),

        # 04: Test result enquiry, frustrated caller
        _call(
            call_id=cid(4, "FRUSTRATED-TEST-RESULT"),
            request_type="test_result",
            patient_name="Robert Kaye",
            dob="1949-05-30",
            postcode="PR9 7DQ",
            callback="07700900204",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Yeah, hi. I had blood tests done last Thursday and I still haven't got the results. "
                "I've been waiting a week. "
                "Jeff: I can pass that on. Can I take your name, date of birth and postcode? "
                "Caller: Robert Kaye, K-A-Y-E. Thirtieth May nineteen forty nine. PR9 7DQ. Look, I'm getting "
                "frustrated. Can't you just tell me when they'll be ready? "
                "Jeff: I understand. Is this number ending 0204 okay? "
                "Caller: Yeah yeah it's fine. "
                "Jeff: Do you know what the blood tests were checking for? "
                "Caller: Kidney function and thyroid. I'm on levothyroxine as I mentioned to the GP. "
                "Jeff: And were you expecting to be contacted, or just checking in? "
                "Caller: I was told someone would ring if there's a problem but I'd like to know either way. "
                "Jeff: I'll let the clinical team know. Someone will call you back with the results. "
                "Caller: When though? This is the second time I've had to phone. "
                "Jeff: The team aim to respond within two working days. "
                "Caller: Fine. That should've been done already. "
                "Jeff: Is there anything else? "
                "Caller: No. "
                "Jeff: Thank you Robert. Goodbye."
            ),
            summary="Test result chase for Robert Kaye. Blood tests: kidney function and thyroid (Thursday). On levothyroxine. Patient frustrated, expecting two-day turnaround.",
            duration=243,
            sentiment="frustrated",
            difficulty="moderate",
            quality="good",
            pathway_responses={
                "test_result": {
                    "test_type": "blood tests",
                    "tests_requested": ["kidney function", "thyroid"],
                    "test_date": "last Thursday",
                    "result_status": "not received",
                }
            },
            staff_review_required=True,
            priority="routine",
            verification_status="verified",
            handoff_confidence=0.91,
            extraction_confidence=0.89,
            transcript_score=0.93,
            caller_emotion_intensity="high",
            information_completeness=0.90,
            suggested_next_action="Expedite clinical review and results callback",
        ),

        # 05: RED FLAG — chest pain, 999 Emergency
        _call(
            call_id=cid(5, "CHEST-PAIN-EMERGENCY"),
            request_type="appointment_redirect",
            patient_name="Geoffrey Hargreaves",
            dob="1938-08-14",
            postcode="PR8 5TN",
            callback="07700900205",
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
            summary="EMERGENCY: Possible acute cardiac event. Geoffrey Hargreaves, 87, chest pain (crushing, 20 min onset), sweating, nausea, breathlessness. 999 advised and confirmed. Wife present.",
            duration=187,
            sentiment="distressed",
            difficulty="difficult",
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
            priority="999 Emergency",
            verification_status="verified",
            handoff_confidence=0.97,
            extraction_confidence=0.95,
            transcript_score=0.96,
            caller_emotion_intensity="high",
            information_completeness=0.92,
        ),

        # 06: Appointment redirect, elderly, confused, poor audio
        _call(
            call_id=cid(6, "CONFUSED-ELDERLY-POOR-AUDIO"),
            request_type="appointment_redirect",
            patient_name="Iris Edmondson",
            dob="1934-11-08",
            postcode="PR9 8PN",
            callback="07700900206",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: [inaudible] is it the doctors? "
                "Jeff: Yes, this is Churchtown Medical Centre. How can I help you? "
                "Caller: I need an appointment. I'm in pain. My... [unclear] is bad. "
                "Jeff: Can I take your name, date of birth and postcode please? "
                "Caller: Iris. Iris Edmondson. [inaudible] of the eighth. Nineteen thirty four. "
                "Jeff: Can you repeat the postcode? "
                "Caller: [unclear] 8PN? Is that right? Eight P N? PR9 8PN. "
                "Jeff: Thank you. And is this number ending 0206 okay? "
                "Caller: What? Yes, yes that's fine. "
                "Jeff: What is the pain about? "
                "Caller: It's my [inaudible]. The arthritis I think. I can barely... [unclear] "
                "Jeff: I understand. I'll pass this to the appointments team and someone will call you back. "
                "Caller: How long will that take? "
                "Jeff: Usually one to two hours. "
                "Caller: Okay. Thank you dear. "
                "Jeff: You're welcome. Is there anything else? "
                "Caller: No. Thank you. "
                "Jeff: Goodbye."
            ),
            summary="Appointment request from Iris Edmondson, 89. Pain (possibly arthritis), impact on mobility. Poor audio quality, multiple inaudible sections. Callback required for clarification.",
            duration=215,
            sentiment="confused",
            difficulty="very_difficult",
            quality="poor",
            pathway_responses={
                "appointment_redirect": {
                    "appointment_reason": "arthritis pain, [unclear from audio]",
                    "preferred_timeframe": "flexible",
                }
            },
            staff_review_required=True,
            priority="routine",
            verification_status="partial",
            verification_reason="Postcode unclear on initial attempt, age inference only, pain reason partially unclear due to audio",
            handoff_confidence=0.68,
            extraction_confidence=0.62,
            transcript_score=0.35,
            caller_emotion_intensity="low",
            call_difficulty_score=0.78,
            missing_information=["exact pain location", "medication history", "mobility baseline"],
            information_gaps=["pain location inferred, not confirmed", "no NHS number provided"],
            clarification_needed=True,
            ai_confidence_flags=["multiple inaudible sections", "postcode required repetition", "pain reason unclear"],
            information_completeness=0.55,
            suggested_next_action="Call back to confirm location of pain, medication history, and mobility impact",
        ),

        # 07: Admin request, address change, easy
        _call(
            call_id=cid(7, "ADDRESS-CHANGE-ADMIN"),
            request_type="admin",
            patient_name="Priya Sharma",
            dob="1990-06-15",
            postcode="PR8 2JW",
            callback="07700900207",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Hi, I've moved house and I need to update my address on my records. "
                "Jeff: Of course. Can I take your name, date of birth and current postcode on file? "
                "Caller: Priya Sharma. Fifteenth June nineteen ninety. PR8 2JW — but that's the old one. "
                "Jeff: And is this number ending 0207 okay for a callback if needed? "
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
            summary="Address update for Priya Sharma. Moving from PR8 2JW to 14 Kew Gardens, Southport, PR8 6AB. Remaining registered.",
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
            priority="routine",
            verification_status="verified",
            handoff_confidence=0.95,
            extraction_confidence=0.93,
            transcript_score=0.97,
            caller_emotion_intensity="low",
            information_completeness=0.98,
        ),

        # 08: Missing information, low confidence, DOB not provided
        _call(
            call_id=cid(8, "MISSING-INFO-LOW-CONFIDENCE"),
            request_type="prescription",
            patient_name="Peter Richardson",
            dob="",
            postcode="PR8 1XY",
            callback="07700900208",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Hi, I need to order a repeat prescription. "
                "Jeff: Of course. Can I take your full name, date of birth and postcode? "
                "Caller: Peter Richardson. PR8 1XY. "
                "Jeff: Thank you. And your date of birth? "
                "Caller: Oh, I'd rather not say that over the phone if that's okay. "
                "Jeff: I understand, but I need it to check your records. "
                "Caller: Yeah, but I've got privacy concerns. Can't you look it up from my postcode? "
                "Jeff: I need the date of birth to find the right record. What medication do you need? "
                "Caller: Atorvastatin. The twenty milligram tablets. And maybe a repeat blood pressure one too. "
                "Jeff: Which pharmacy? "
                "Caller: Boots. The one on Lord Street. "
                "Jeff: I'll flag this for the team. Because we can't confirm your full identity without the date of birth, "
                "someone will call you back to verify and process the prescription. "
                "Caller: Okay, that's fine. "
                "Jeff: Is there anything else? "
                "Caller: No that's it. "
                "Jeff: Thank you. Goodbye."
            ),
            summary="Prescription request from Peter Richardson, PR8 1XY. Atorvastatin 20mg and blood pressure medication. DOB not provided (privacy concern). Identity verification required before processing.",
            duration=218,
            sentiment="calm",
            difficulty="moderate",
            quality="good",
            pathway_responses={
                "prescription": {
                    "prescription_type": "repeat",
                    "medications_requested": ["atorvastatin 20mg", "blood pressure medication (unspecified)"],
                    "pharmacy": "Boots Lord Street",
                    "run_out_status": "unknown",
                }
            },
            staff_review_required=True,
            priority="routine",
            verification_status="unverified",
            verification_reason="DOB not provided; cannot verify identity without it",
            handoff_confidence=0.58,
            extraction_confidence=0.64,
            transcript_score=0.88,
            caller_emotion_intensity="low",
            missing_information=["date of birth"],
            information_gaps=["DOB refused by caller", "blood pressure medication type unspecified"],
            clarification_needed=True,
            ai_confidence_flags=["DOB missing", "medication ambiguous (blood pressure drug not named)"],
            information_completeness=0.72,
            suggested_next_action="Call back to obtain DOB and confirm blood pressure medication name",
        ),

        # 09: Parent calling for child, happy and clear
        _call(
            call_id=cid(9, "PARENT-CHILD-APPOINTMENT"),
            request_type="appointment_redirect",
            patient_name="Sarah Thompson",
            dob="2014-02-17",
            postcode="PR9 0EJ",
            callback="07700900209",
            caller_for="child",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Hi, I'd like to book an appointment for my daughter Sarah. She's got a cough and hasn't been well for a few days. "
                "Jeff: Of course. Can I take the patient's full name, date of birth and your postcode? "
                "Caller: Sarah Thompson, seventeenth February two thousand and fourteen. PR9 0EJ. "
                "Jeff: And is this number ending 0209 a good callback number for you? "
                "Caller: Yes, that's my mobile. "
                "Jeff: Can you tell me a bit more about the cough? Has she had a fever? "
                "Caller: She's had a temperature for a couple of days, around thirty eight point five. And she's a bit grumpy. "
                "Jeff: I understand. I'll pass this to the appointments team and someone will call you back with an appointment time. "
                "Caller: Thank you. How long roughly? "
                "Jeff: Usually within one working day. "
                "Caller: That's great. "
                "Jeff: Is there anything else? "
                "Caller: No that's all. Thanks very much. "
                "Jeff: You're welcome. Goodbye."
            ),
            summary="Appointment request for Sarah Thompson, 9, from parent. Persistent cough, fever (38.5°C) for 2 days, irritable. Parent calling on behalf of child.",
            duration=212,
            sentiment="friendly",
            difficulty="easy",
            quality="good",
            pathway_responses={
                "appointment_redirect": {
                    "appointment_reason": "persistent cough, fever, irritability",
                    "preferred_timeframe": "flexible",
                }
            },
            priority="routine",
            verification_status="verified",
            handoff_confidence=0.94,
            extraction_confidence=0.92,
            transcript_score=0.96,
            caller_emotion_intensity="low",
            information_completeness=0.96,
        ),

        # 10: Duplicate medication concern, higher confidence
        _call(
            call_id=cid(10, "DUPLICATE-MEDS-ALERT"),
            request_type="prescription",
            patient_name="David Foster",
            dob="1951-11-03",
            postcode="PR8 3QW",
            callback="07700900210",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Hi, I'm a bit worried. I just picked up my prescription from the pharmacy and "
                "I've realised I'm now on two different blood pressure medications. I think there might be a mistake. "
                "Jeff: I see. Let me take your details. Name, date of birth, postcode? "
                "Caller: David Foster. Third November nineteen fifty one. PR8 3QW. "
                "Jeff: And is this ending 0210 okay? "
                "Caller: Yes. "
                "Jeff: What are the two medications you're on? "
                "Caller: I've got the Lisinopril bottle from last month and then the pharmacy just gave me Atenolol. "
                "I wasn't told to stop the Lisinopril. "
                "Jeff: That does sound like it needs checking. I'll pass this straight to the clinical team. "
                "Please don't take both medications until someone calls you back to clarify. "
                "Caller: Okay, I won't. When will someone ring? "
                "Jeff: Within the hour if possible, as this is a safety matter. "
                "Caller: Thank you. I appreciate that. "
                "Jeff: Is there anything else? "
                "Caller: No that's all. "
                "Jeff: Goodbye."
            ),
            summary="SAFETY ALERT: David Foster reports duplicate blood pressure medication. Currently on Lisinopril (continuing) and newly prescribed Atenolol. No stop instruction received. Clinical review urgent.",
            duration=198,
            sentiment="concerned",
            difficulty="moderate",
            quality="good",
            pathway_responses={
                "prescription": {
                    "prescription_type": "safety_concern",
                    "concern_type": "duplicate_medication",
                    "current_meds": ["Lisinopril"],
                    "newly_prescribed": ["Atenolol"],
                }
            },
            staff_review_required=True,
            red_flags_present=True,
            priority="urgent",
            verification_status="verified",
            handoff_confidence=0.93,
            extraction_confidence=0.91,
            transcript_score=0.94,
            caller_emotion_intensity="medium",
            information_completeness=0.95,
            suggested_next_action="Clinical review within 1 hour; verify medication stop/continue instructions",
        ),

        # 11: Happy, clear, longer call with multiple details
        _call(
            call_id=cid(11, "COMPREHENSIVE-CLEAR-CALL"),
            request_type="prescription",
            patient_name="Elizabeth Warren",
            dob="1946-05-11",
            postcode="PR9 9AH",
            callback="07700900211",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help you today? "
                "Caller: Hello dear. I need my repeat prescriptions please. The usual ones. "
                "Jeff: Of course. Can I take your full name, date of birth and postcode? "
                "Caller: Elizabeth Warren. Eleventh May nineteen forty six. PR9 9AH. "
                "Jeff: Thank you Elizabeth. And is this number ending 0211 the best number for a callback? "
                "Caller: Yes, that's my landline and I'm usually in. "
                "Jeff: What medications are you requesting today? "
                "Caller: I'm after my lisinopril, my amlodipine, and my metformin. All the usual doses. "
                "Jeff: And when do you need them by? "
                "Caller: Well, I've got about five days worth left so sometime this week would be lovely. "
                "Jeff: Which pharmacy should I send this to? "
                "Caller: Lloyds in Southport. The one near the shopping centre. "
                "Jeff: Perfect. I'll pass your request to the dispensing team straight away. "
                "Caller: How long do you think it'll take? "
                "Jeff: Usually two to three working days. "
                "Caller: That's fine. I've got enough. "
                "Jeff: Is there anything else I can help you with today? "
                "Caller: No, that's everything. Thank you dear. "
                "Jeff: You're very welcome Elizabeth. Goodbye."
            ),
            summary="Routine repeat prescriptions for Elizabeth Warren: lisinopril, amlodipine, metformin. Five days' supply remaining. Collection from Lloyds Southport. High patient satisfaction.",
            duration=267,
            sentiment="satisfied",
            difficulty="easy",
            quality="good",
            pathway_responses={
                "prescription": {
                    "prescription_type": "repeat",
                    "medications_requested": ["lisinopril", "amlodipine", "metformin"],
                    "pharmacy": "Lloyds Southport",
                    "run_out_status": "five days left",
                    "standard_doses": True,
                }
            },
            priority="routine",
            verification_status="verified",
            handoff_confidence=0.97,
            extraction_confidence=0.96,
            transcript_score=0.98,
            caller_emotion_intensity="low",
            information_completeness=0.99,
        ),

        # 12: Confused about symptoms, multiple clarifications needed
        _call(
            call_id=cid(12, "SYMPTOM-CLARIFICATION-NEEDED"),
            request_type="appointment_redirect",
            patient_name="Thomas Wright",
            dob="1968-09-24",
            postcode="PR8 4DW",
            callback="07700900212",
            transcript=(
                "Jeff: Good morning, Churchtown Medical Centre. How can I help? "
                "Caller: Um, hi. I don't feel very well. I think I need to see someone. "
                "Jeff: I can help you book an appointment. Can I take your name, date of birth and postcode please? "
                "Caller: Thomas Wright. Twenty fourth September sixty eight. PR8 4DW. "
                "Jeff: Thank you Thomas. Is this number ending 0212 okay for a callback? "
                "Caller: Yes. "
                "Jeff: Can you tell me what's been bothering you? "
                "Caller: Well, I've got a headache. And also my stomach feels a bit odd. And I'm tired. "
                "Jeff: When did the headache start? "
                "Caller: Erm, I'm not sure. Maybe two days ago? Or was it three? "
                "Jeff: And is there anything else? Any fever or vomiting? "
                "Caller: No, no fever I don't think. My stomach's just a bit uncomfortable. Not sick. "
                "Jeff: Have you taken anything for the headache? "
                "Caller: Some paracetamol but it didn't really help much. "
                "Jeff: I'll pass this to the appointments team. The symptoms sound fairly general so someone will call to discuss further. "
                "Caller: Okay. How long will that take? "
                "Jeff: Usually one working day. "
                "Caller: That should be fine. "
                "Jeff: Is there anything else? "
                "Caller: No, I don't think so. "
                "Jeff: Thank you Thomas. Goodbye."
            ),
            summary="Appointment request from Thomas Wright. Non-specific symptoms: headache (onset 2-3 days ago), abdominal discomfort, fatigue. No fever or vomiting. Paracetamol ineffective. Requires clinical assessment.",
            duration=248,
            sentiment="concerned",
            difficulty="moderate",
            quality="good",
            pathway_responses={
                "appointment_redirect": {
                    "appointment_reason": "headache, abdominal discomfort, fatigue",
                    "preferred_timeframe": "flexible",
                    "symptom_clarity": "low",
                }
            },
            staff_review_required=True,
            priority="routine",
            verification_status="verified",
            handoff_confidence=0.75,
            extraction_confidence=0.73,
            transcript_score=0.89,
            caller_emotion_intensity="medium",
            missing_information=["precise headache onset", "abdominal pain location/severity", "duration of fatigue"],
            information_gaps=["symptom timeline vague", "pain characteristics not detailed"],
            clarification_needed=True,
            ai_confidence_flags=["non-specific symptoms", "timeline uncertain", "requires clinical assessment"],
            information_completeness=0.78,
            suggested_next_action="Clinical callback for detailed symptom assessment and safety check",
        ),
    ]

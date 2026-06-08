"""
seed_demo_data.py — Seed realistic demo triage cases into the JeffLocal dashboard DB.

IMPORTANT: All patient names, NHS numbers, EMIS numbers, postcodes, and phone numbers
in this file are from a test fixture (mock_patient_lookup_v3.csv) and are entirely
fictional. They are NOT real patients. NHS numbers and EMIS numbers are test data only.
No real patient data is used or implied anywhere in this script.

Usage:
    python seed_demo_data.py              # Insert / replace demo rows
    python seed_demo_data.py --clear      # Delete demo rows then re-insert
    python seed_demo_data.py --db C:\\path\\to\\dashboard.sqlite
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Default DB path ─────────────────────────────────────────────────────────────
DEFAULT_DB = Path(__file__).resolve().parents[2] / "dashboard" / "data" / "dashboard.sqlite"

DEMO_PREFIX = "DEMO-"

# ── Timestamp helpers ────────────────────────────────────────────────────────────
_BASE = datetime(2026, 6, 8, 9, 0, 0, tzinfo=timezone.utc)   # 09:00 UTC today
_YESTERDAY_BASE = datetime(2026, 6, 7, 8, 30, 0, tzinfo=timezone.utc)


def _ts_offset(base: datetime, add_minutes: int) -> tuple[str, float]:
    """Return (ISO string, unix float) for base + add_minutes."""
    dt = base + timedelta(minutes=add_minutes)
    return dt.isoformat(timespec="seconds"), dt.timestamp()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ── Demo cases ───────────────────────────────────────────────────────────────────
# Source: mock_patient_lookup_v3.csv (test fixture — not real patients)
# Verification logic is deterministic — NOT set by the AI/LLM layer.
# verified     = name + DOB + NHS number all matched EMIS record exactly
# partial_match= name matched but DOB year stated by caller differed by 1 year
# unverified   = caller could not confirm identity (wrong NHS number given)
# failed       = name not found on register at all

DEMO_CASES: list[dict] = [

    # ── DEMO-001 ─────────────────────────────────────────────────────────────────
    # URGENT — chest pain, red flag. Patient: BOUMNIJEL Abdel, M, 18-Dec-1952
    # Verification: verified. Priority: urgent. Request: urgent_callback
    {
        "call_id": "DEMO-001",
        "request_type": "urgent_callback",
        "patient_name": "Abdel Boumnijel",
        "dob": "1952-12-18",
        "postcode": "PR8 4LJ",
        "gender": "Male",
        "age": 73,
        "callback_number": "07412 883201",
        "verification_status": "verified",
        "verification_reason": "Name, DOB (18 Dec 1952), and NHS number all confirmed by caller against EMIS record.",
        "matched_patient_ref": "EMIS-230",
        "emis_number": "EMIS-230",
        "nhs_number": "626 283 3153",
        "top_candidate_name": "BOUMNIJEL Abdel",
        "priority": "urgent",
        "safe_to_queue": 1,
        "task_title": "URGENT — Chest pain and breathlessness, duty GP callback required",
        "task_body": (
            "Patient Abdel Boumnijel (73M) called at 09:12 reporting chest tightness and "
            "shortness of breath starting this morning. Symptoms began approximately 2 hours "
            "ago at rest. No history of MI but has known hypertension and is on Amlodipine 10mg "
            "and Ramipril 5mg. Denies radiation to jaw or left arm. Denies syncope. "
            "Wife is present. Patient is anxious but coherent. GP duty callback requested urgently. "
            "If no callback within 30 minutes, patient instructed to call 999."
        ),
        "staff_task_title": "URGENT CALLBACK — Chest pain, Abdel Boumnijel, 07412 883201",
        "staff_task_body": (
            "Call Abdel Boumnijel on 07412 883201 immediately. "
            "73-year-old male with chest tightness and breathlessness since this morning. "
            "Known hypertension. On Amlodipine 10mg and Ramipril 5mg. "
            "Duty GP to assess and advise — consider 999 if delay. "
            "EMIS ref: EMIS-230. NHS: 626 283 3153."
        ),
        "transcript": (
            "Jeff: Good morning, you have reached Churchtown Medical Centre. I am Jeff, "
            "the automated triage assistant. How can I help you today?\n\n"
            "Caller: Yes, hello. I need to speak to a doctor please. I am not feeling well at all.\n\n"
            "Jeff: I am sorry to hear that. Can I take your name please?\n\n"
            "Caller: Yes, my name is Abdel Boumnijel. B-O-U-M-N-I-J-E-L.\n\n"
            "Jeff: Thank you Mr Boumnijel. And your date of birth please?\n\n"
            "Caller: The eighteenth of December, nineteen fifty-two.\n\n"
            "Jeff: Thank you. Could you also confirm your NHS number if you have it?\n\n"
            "Caller: Yes, it is six two six, two eight three, three one five three.\n\n"
            "Jeff: Thank you, I have verified your details. Can you tell me what is troubling you today?\n\n"
            "Caller: Yes, I woke up about two hours ago and I have this tightness in my chest. "
            "And I am struggling a little bit to breathe. It has not gone away. My wife is here "
            "with me and she is worried. I take tablets for blood pressure — Amlodipine and Ramipril. "
            "I have never had a heart attack before but this does not feel right.\n\n"
            "Jeff: I understand, that does sound uncomfortable. Is the pain going anywhere — "
            "into your arm, jaw, or back?\n\n"
            "Caller: No, just here in my chest. And the breathing.\n\n"
            "Jeff: I am going to flag this as urgent for the duty doctor. They will call you back "
            "on this number shortly. If you feel significantly worse before then, please call 999. "
            "Do you understand?\n\n"
            "Caller: Yes, yes I understand. Thank you.\n\n"
            "Jeff: Thank you Mr Boumnijel. Your GP will be in touch very shortly. Take care."
        ),
        "call_summary": "Urgent: 73M with chest tightness and breathlessness x2 hours. Known hypertension. Duty GP callback required.",
        "ai_summary": (
            "Caller is a 73-year-old male reporting chest tightness and breathlessness for "
            "approximately 2 hours starting at rest. Known hypertension. Current medications: "
            "Amlodipine 10mg, Ramipril 5mg. No radiation to arm or jaw reported. No syncope. "
            "Wife present. Patient is anxious but cooperative. Requests urgent GP callback. "
            "Red flag: chest pain + breathlessness in 73M with cardiovascular risk factors."
        ),
        "patient_record_note": (
            "JeffLocal triage 2026-06-08 09:12: Patient called re chest tightness and "
            "breathlessness x2 hours. Hypertensive, on Amlodipine/Ramipril. "
            "Duty GP urgent callback arranged. Red flag logged."
        ),
        "open_details": "Urgent callback — chest pain + breathlessness. Red flag.",
        "call_duration_seconds": 312,
        "caller_sentiment": "anxious",
        "caller_difficulty": "low",
        "transcript_quality": "good",
        "handoff_confidence": "high",
        "extraction_confidence": "high",
        "staff_review_required": 1,
        "red_flags_present": 1,
        "status": "in_progress",
        "assigned_to": "Duty GP",
        "action_needed": "GP urgent callback — do not delay",
        "outcome_notes": "",
        "staff_action": "",
        "resolved_at": None,
        "resolved_by": None,
        "last_edited_at": None,
        "last_edited_by": None,
        "turnaround_minutes": None,
        "source_path": "outputs/handoff_json/demo_case_001.json",
        "_ts_base": _BASE,
        "_ts_offset": 12,
    },

    # ── DEMO-002 ─────────────────────────────────────────────────────────────────
    # ROUTINE — repeat prescription. Patient: BOUMNIJEL Elizabeth, F, 19-Jun-1949
    # Verification: verified. Priority: routine. Request: prescription_request
    {
        "call_id": "DEMO-002",
        "request_type": "prescription_request",
        "patient_name": "Elizabeth Boumnijel",
        "dob": "1949-06-19",
        "postcode": "PR8 4LJ",
        "gender": "Female",
        "age": 76,
        "callback_number": "01704 553847",
        "verification_status": "verified",
        "verification_reason": "Name, DOB (19 Jun 1949), and NHS number confirmed against EMIS record.",
        "matched_patient_ref": "EMIS-231",
        "emis_number": "EMIS-231",
        "nhs_number": "452 864 7400",
        "top_candidate_name": "BOUMNIJEL Elizabeth",
        "priority": "routine",
        "safe_to_queue": 1,
        "task_title": "Repeat prescription — Atorvastatin 40mg and Bisoprolol 2.5mg",
        "task_body": (
            "Patient Elizabeth Boumnijel (76F) requests repeat prescription for Atorvastatin 40mg "
            "and Bisoprolol 2.5mg. Last issued approximately 28 days ago. Preferred pharmacy: "
            "Day Lewis Pharmacy, Lord Street, Southport. No new symptoms reported. "
            "Patient confirmed she has approximately 3 days of Bisoprolol remaining."
        ),
        "staff_task_title": "Prescription request — Atorvastatin + Bisoprolol, Elizabeth Boumnijel",
        "staff_task_body": (
            "Route to medicines management for Elizabeth Boumnijel (EMIS-231). "
            "Medications: Atorvastatin 40mg, Bisoprolol 2.5mg. "
            "Preferred pharmacy: Day Lewis, Lord Street, Southport. "
            "Running low on Bisoprolol — process today if possible."
        ),
        "transcript": (
            "Jeff: Good morning, Churchtown Medical Centre. I am Jeff. How can I help?\n\n"
            "Caller: Hello, I would like to order my repeat prescription please.\n\n"
            "Jeff: Of course. Can I take your full name please?\n\n"
            "Caller: Elizabeth Boumnijel.\n\n"
            "Jeff: Thank you. And your date of birth?\n\n"
            "Caller: Nineteenth of June, nineteen forty-nine.\n\n"
            "Jeff: Thank you. And your NHS number?\n\n"
            "Caller: Four five two, eight six four, seven four zero zero.\n\n"
            "Jeff: Perfect, your details are confirmed. Which medications would you like to reorder?\n\n"
            "Caller: It is the Atorvastatin — forty milligrams — and Bisoprolol, two point five. "
            "I have about three days left of the Bisoprolol so I do not want to run out.\n\n"
            "Jeff: Understood. Any particular pharmacy?\n\n"
            "Caller: Day Lewis on Lord Street please.\n\n"
            "Jeff: I have noted that. Is there anything else I can help with today?\n\n"
            "Caller: No, that is everything. Thank you.\n\n"
            "Jeff: Thank you Mrs Boumnijel. Your prescription request has been passed to the team. Goodbye."
        ),
        "call_summary": "Repeat prescription — Atorvastatin 40mg and Bisoprolol 2.5mg. 3 days Bisoprolol remaining.",
        "ai_summary": (
            "76-year-old female requesting repeat of Atorvastatin 40mg and Bisoprolol 2.5mg. "
            "Approximately 3 days of Bisoprolol remaining — some urgency to process today. "
            "Preferred pharmacy: Day Lewis, Lord Street, Southport. No new symptoms. "
            "Identity fully verified."
        ),
        "patient_record_note": (
            "JeffLocal triage 2026-06-08 09:28: Repeat prescription request — "
            "Atorvastatin 40mg + Bisoprolol 2.5mg. Low supply of Bisoprolol. "
            "Preferred pharmacy: Day Lewis Southport."
        ),
        "open_details": "Repeat prescription — Atorvastatin + Bisoprolol. Low supply.",
        "call_duration_seconds": 148,
        "caller_sentiment": "calm",
        "caller_difficulty": "low",
        "transcript_quality": "good",
        "handoff_confidence": "high",
        "extraction_confidence": "high",
        "staff_review_required": 0,
        "red_flags_present": 0,
        "status": "new",
        "assigned_to": None,
        "action_needed": "Route to medicines management — process Bisoprolol today",
        "outcome_notes": "",
        "staff_action": "",
        "resolved_at": None,
        "resolved_by": None,
        "last_edited_at": None,
        "last_edited_by": None,
        "turnaround_minutes": None,
        "source_path": "outputs/handoff_json/demo_case_002.json",
        "_ts_base": _BASE,
        "_ts_offset": 28,
    },

    # ── DEMO-003 ─────────────────────────────────────────────────────────────────
    # ROUTINE — appointment request. Patient: BRADBURY Kevin, M, 03-Jun-1982
    # Verification: verified. Priority: routine. Request: appointment_request
    {
        "call_id": "DEMO-003",
        "request_type": "appointment_request",
        "patient_name": "Kevin Bradbury",
        "dob": "1982-06-03",
        "postcode": "PR9 7EH",
        "gender": "Male",
        "age": 43,
        "callback_number": "07891 224570",
        "verification_status": "verified",
        "verification_reason": "Name, DOB (03 Jun 1982), and NHS number confirmed against EMIS record.",
        "matched_patient_ref": "EMIS-237",
        "emis_number": "EMIS-237",
        "nhs_number": "620 925 5116",
        "top_candidate_name": "BRADBURY Kevin",
        "priority": "routine",
        "safe_to_queue": 1,
        "task_title": "Routine GP appointment — persistent lower back pain, 3 weeks",
        "task_body": (
            "Patient Kevin Bradbury (43M) requests a routine GP appointment for lower back pain "
            "that has persisted for 3 weeks. Pain is worse on sitting and relieved slightly by "
            "walking. He has been taking ibuprofen 400mg PRN with partial effect. No radiation "
            "to legs, no bladder or bowel symptoms. Works as a delivery driver — condition is "
            "affecting ability to work. Prefers morning appointments."
        ),
        "staff_task_title": "GP appointment — lower back pain x3 weeks, Kevin Bradbury",
        "staff_task_body": (
            "Book routine GP appointment for Kevin Bradbury (EMIS-237). "
            "Reason: lower back pain x3 weeks, worse on sitting, ibuprofen partially effective. "
            "No red flags. Prefers morning slots. Works as delivery driver — condition affecting work."
        ),
        "transcript": (
            "Jeff: Good morning, Churchtown Medical Centre. How can I help you?\n\n"
            "Caller: Hi yes, I need to make an appointment to see a doctor please.\n\n"
            "Jeff: Of course. Can I take your name?\n\n"
            "Caller: Kevin Bradbury.\n\n"
            "Jeff: And your date of birth?\n\n"
            "Caller: Third of June, nineteen eighty-two.\n\n"
            "Jeff: And your NHS number?\n\n"
            "Caller: Six two zero, nine two five, five one one six.\n\n"
            "Jeff: Thank you, your details are confirmed. What is the reason for your appointment?\n\n"
            "Caller: It is my back. It has been killing me for about three weeks now. "
            "I sit a lot for work — I am a delivery driver — and it just keeps getting worse. "
            "I have been taking ibuprofen, that helps a bit but it comes back. "
            "No tingling in my legs or anything like that, nothing weird with the toilet. "
            "Just the pain in my lower back.\n\n"
            "Jeff: Do you have a preference for appointment time?\n\n"
            "Caller: Mornings are better for me if possible. "
            "I can do most mornings this week or next.\n\n"
            "Jeff: I have noted that. Is there anything else today?\n\n"
            "Caller: No, that is it. Thanks.\n\n"
            "Jeff: Thank you Kevin. The team will arrange a morning appointment for you. Goodbye."
        ),
        "call_summary": "Routine appointment — lower back pain x3 weeks. Works as delivery driver. No red flags.",
        "ai_summary": (
            "43-year-old male with 3-week history of lower back pain, worse on sitting, "
            "partially relieved by walking and ibuprofen 400mg PRN. No leg radiation, "
            "no bladder or bowel symptoms. Works as a delivery driver — condition affecting work. "
            "Requests routine GP appointment, prefers mornings."
        ),
        "patient_record_note": (
            "JeffLocal triage 2026-06-08 09:45: Appointment request — lower back pain x3 weeks. "
            "Ibuprofen partially effective. No neurological symptoms. Routine booking."
        ),
        "open_details": "Routine appointment — back pain x3 weeks. Mornings preferred.",
        "call_duration_seconds": 193,
        "caller_sentiment": "neutral",
        "caller_difficulty": "low",
        "transcript_quality": "good",
        "handoff_confidence": "high",
        "extraction_confidence": "high",
        "staff_review_required": 0,
        "red_flags_present": 0,
        "status": "new",
        "assigned_to": None,
        "action_needed": "Book routine morning GP appointment",
        "outcome_notes": "",
        "staff_action": "",
        "resolved_at": None,
        "resolved_by": None,
        "last_edited_at": None,
        "last_edited_by": None,
        "turnaround_minutes": None,
        "source_path": "outputs/handoff_json/demo_case_003.json",
        "_ts_base": _BASE,
        "_ts_offset": 45,
    },

    # ── DEMO-004 ─────────────────────────────────────────────────────────────────
    # LOW — sick note request (resolved yesterday). Patient: BRIDGE Dorothy, F, 31-Jan-1942
    # Verification: verified. Priority: low. Request: sick_note_request
    {
        "call_id": "DEMO-004",
        "request_type": "sick_note_request",
        "patient_name": "Dorothy Bridge",
        "dob": "1942-01-31",
        "postcode": "PR8 2QN",
        "gender": "Female",
        "age": 84,
        "callback_number": "01704 448291",
        "verification_status": "verified",
        "verification_reason": "Name, DOB (31 Jan 1942), and NHS number confirmed against EMIS record.",
        "matched_patient_ref": "EMIS-242",
        "emis_number": "EMIS-242",
        "nhs_number": "440 929 0460",
        "top_candidate_name": "BRIDGE Dorothy",
        "priority": "low",
        "safe_to_queue": 1,
        "task_title": "Fit note request — carer absence, 1 week, viral illness",
        "task_body": (
            "Patient Dorothy Bridge (84F) requesting a fit note for her carer "
            "who has been off sick with a viral illness for one week. "
            "GP had already consulted with the carer on 06 Jun 2026. "
            "Carer's employer has requested official documentation. "
            "Patient's daughter called on behalf of her mother."
        ),
        "staff_task_title": "Fit note request — carer absence (Dorothy Bridge, EMIS-242)",
        "staff_task_body": (
            "Issue fit note for carer of Dorothy Bridge (EMIS-242). "
            "Carer absent with viral illness x1 week. GP consultation already occurred 06 Jun. "
            "Send to patient's address: PR8 2QN. Mark resolved when issued."
        ),
        "transcript": (
            "Jeff: Good morning, Churchtown Medical Centre. How can I help?\n\n"
            "Caller: Hello, I am calling on behalf of my mother, Dorothy Bridge. "
            "She needs a fit note for her carer.\n\n"
            "Jeff: I see. Can you confirm your mother's date of birth?\n\n"
            "Caller: Thirty-first of January, nineteen forty-two.\n\n"
            "Jeff: And her NHS number?\n\n"
            "Caller: Four four zero, nine two nine, zero four six zero.\n\n"
            "Jeff: Thank you, identity confirmed. What is the fit note for?\n\n"
            "Caller: Her carer has been off sick since Monday with a viral infection. "
            "The GP saw her last Friday — the sixth of June — and said she would need a week off. "
            "Her employer is now asking for an official note. Could someone issue that?\n\n"
            "Jeff: I have noted that. Is there anything else today?\n\n"
            "Caller: No that is all, thank you.\n\n"
            "Jeff: Thank you. The team will arrange the fit note. Goodbye."
        ),
        "call_summary": "Fit note for carer — viral illness x1 week. GP consultation already done 06 Jun.",
        "ai_summary": (
            "Caller is daughter of patient Dorothy Bridge (84F). Requesting fit note for patient's "
            "carer who has been off sick since Monday with viral illness. GP consultation occurred "
            "06 Jun 2026. Employer has requested documentation. Routine admin task."
        ),
        "patient_record_note": (
            "JeffLocal triage 2026-06-07 10:15: Fit note requested for carer. "
            "Viral illness x1 week. GP consultation 06 Jun confirmed. "
            "Fit note issued and posted 2026-06-07."
        ),
        "open_details": "Fit note for carer — issued and resolved.",
        "call_duration_seconds": 112,
        "caller_sentiment": "calm",
        "caller_difficulty": "low",
        "transcript_quality": "good",
        "handoff_confidence": "high",
        "extraction_confidence": "high",
        "staff_review_required": 0,
        "red_flags_present": 0,
        "status": "resolved",
        "assigned_to": "Admin Team",
        "action_needed": "",
        "outcome_notes": "Fit note issued and posted. Case closed.",
        "staff_action": "Fit note printed and posted 2026-06-07 14:30.",
        "resolved_at": "2026-06-07T14:30:00+00:00",
        "resolved_by": "Reception — S. Mellor",
        "last_edited_at": "2026-06-07T14:30:00+00:00",
        "last_edited_by": "S. Mellor",
        "turnaround_minutes": 255,
        "source_path": "outputs/handoff_json/demo_case_004.json",
        "_ts_base": _YESTERDAY_BASE,
        "_ts_offset": 105,
    },

    # ── DEMO-005 ─────────────────────────────────────────────────────────────────
    # ROUTINE — test results enquiry. Patient: CHADWICK Julie, F, 16-Mar-1965
    # Verification: partial_match (DOB year off by 1). Priority: routine. Request: test_results_enquiry
    {
        "call_id": "DEMO-005",
        "request_type": "test_results_enquiry",
        "patient_name": "Julie Chadwick",
        "dob": "1966-03-16",
        "postcode": "PR9 0BW",
        "gender": "Female",
        "age": 60,
        "callback_number": "07734 009182",
        "verification_status": "partial_match",
        "verification_reason": (
            "Name matched EMIS record. DOB day and month confirmed (16 March) "
            "but caller stated year 1966 — EMIS record shows 1965. "
            "Likely caller error. Staff to verify before releasing results."
        ),
        "matched_patient_ref": "EMIS-243",
        "emis_number": "EMIS-243",
        "nhs_number": "620 934 6707",
        "top_candidate_name": "CHADWICK Julie",
        "priority": "routine",
        "safe_to_queue": 1,
        "task_title": "Test results enquiry — blood panel, identity partially matched",
        "task_body": (
            "Patient Julie Chadwick enquiring about results of a blood panel taken "
            "approximately 10 days ago. Tests included HbA1c, full blood count, and thyroid function. "
            "GP had not yet contacted patient. IDENTITY PARTIALLY MATCHED — "
            "DOB year stated (1966) differs from EMIS (1965). "
            "Staff must confirm identity before discussing or releasing results."
        ),
        "staff_task_title": "Results chase — identity check required first (Julie Chadwick, EMIS-243)",
        "staff_task_body": (
            "Call Julie Chadwick on 07734 009182. Before discussing results, "
            "confirm DOB: caller said 16 March 1966 — EMIS shows 16 March 1965. "
            "Once confirmed, advise on HbA1c / FBC / TFT results as per GP instructions. "
            "Do not release results until identity confirmed."
        ),
        "transcript": (
            "Jeff: Good morning, Churchtown Medical Centre. How can I help?\n\n"
            "Caller: Hi, I am calling to find out if my blood test results are back yet.\n\n"
            "Jeff: Of course. Can I take your name please?\n\n"
            "Caller: Julie Chadwick.\n\n"
            "Jeff: Thank you. And your date of birth?\n\n"
            "Caller: Sixteenth of March, nineteen sixty-six.\n\n"
            "Jeff: Thank you. And your NHS number?\n\n"
            "Caller: Six two zero, nine three four, six seven zero seven.\n\n"
            "Jeff: I have a partial match on your record. The name and NHS number match, "
            "but there is a small discrepancy with the date of birth on file. "
            "A member of the team will need to confirm a couple of details with you when they call back. "
            "Can you confirm a good number to reach you on?\n\n"
            "Caller: Yes, zero seven seven three four, zero zero nine one eight two.\n\n"
            "Jeff: Thank you. Which tests were you enquiring about?\n\n"
            "Caller: I had a blood panel done about ten days ago — HbA1c, blood count, "
            "thyroid I think. The doctor said she would be in touch if anything was abnormal "
            "but I have not heard anything and I wanted to check.\n\n"
            "Jeff: I have noted all of that. A member of the team will call you back today. "
            "They will need to verify your date of birth before discussing the results. "
            "Is there anything else?\n\n"
            "Caller: No, that is fine. Thank you.\n\n"
            "Jeff: Thank you Julie. Goodbye."
        ),
        "call_summary": "Test results enquiry — HbA1c, FBC, TFT. Partial identity match — DOB year discrepancy.",
        "ai_summary": (
            "60-year-old female enquiring about blood results taken approximately 10 days ago "
            "(HbA1c, FBC, thyroid function). Has not been contacted by GP. "
            "Identity partially matched — name and NHS number confirmed but DOB year stated "
            "as 1966 vs EMIS record 1965. Staff must verify identity before releasing results."
        ),
        "patient_record_note": (
            "JeffLocal triage 2026-06-08 10:05: Results enquiry — HbA1c/FBC/TFT. "
            "Partial identity match (DOB year discrepancy). Staff to verify before releasing."
        ),
        "open_details": "Results chase — partial identity match. Verify DOB before callback.",
        "call_duration_seconds": 227,
        "caller_sentiment": "calm",
        "caller_difficulty": "low",
        "transcript_quality": "good",
        "handoff_confidence": "medium",
        "extraction_confidence": "high",
        "staff_review_required": 1,
        "red_flags_present": 0,
        "status": "new",
        "assigned_to": None,
        "action_needed": "Confirm DOB before releasing results — call 07734 009182",
        "outcome_notes": "",
        "staff_action": "",
        "resolved_at": None,
        "resolved_by": None,
        "last_edited_at": None,
        "last_edited_by": None,
        "turnaround_minutes": None,
        "source_path": "outputs/handoff_json/demo_case_005.json",
        "_ts_base": _BASE,
        "_ts_offset": 65,
    },

    # ── DEMO-006 ─────────────────────────────────────────────────────────────────
    # URGENT — breathing difficulty, red flag. Patient: OSBORN Kristina, F, 29-Mar-1962
    # Verification: verified. Priority: urgent. Request: urgent_callback
    {
        "call_id": "DEMO-006",
        "request_type": "urgent_callback",
        "patient_name": "Kristina Osborn",
        "dob": "1962-03-29",
        "postcode": "PR8 1SX",
        "gender": "Female",
        "age": 64,
        "callback_number": "07519 337640",
        "verification_status": "verified",
        "verification_reason": "Name, DOB (29 Mar 1962), and NHS number confirmed against EMIS record.",
        "matched_patient_ref": "EMIS-299",
        "emis_number": "EMIS-299",
        "nhs_number": "478 697 4250",
        "top_candidate_name": "OSBORN Kristina",
        "priority": "urgent",
        "safe_to_queue": 1,
        "task_title": "URGENT — Worsening breathlessness in known asthmatic, blue inhaler not relieving",
        "task_body": (
            "Patient Kristina Osborn (64F) called reporting significant worsening of breathlessness "
            "over the past 4 hours. Known asthmatic on Seretide 250 and Salbutamol PRN. "
            "Salbutamol inhaler used 4 times this morning with minimal improvement. "
            "No fever, no chest pain, no new cough. Sitting upright. "
            "Peak flow not done. Husband present. "
            "Duty GP must call back immediately — consider 999 if no improvement."
        ),
        "staff_task_title": "URGENT — Asthma attack, Kristina Osborn, 07519 337640",
        "staff_task_body": (
            "Call Kristina Osborn on 07519 337640 immediately. "
            "64F known asthmatic. Worsening breathlessness x4 hours. "
            "Salbutamol used 4 times this morning — minimal relief. "
            "On Seretide 250 + Salbutamol PRN. "
            "Duty GP to assess — may need 999 or urgent A&E. EMIS: EMIS-299."
        ),
        "transcript": (
            "Jeff: Good morning, Churchtown Medical Centre. I am Jeff. How can I help?\n\n"
            "Caller: [breathless] I need a doctor. I am struggling to breathe.\n\n"
            "Jeff: I can hear you are having difficulty. Can you tell me your name?\n\n"
            "Caller: Kristina Osborn. O-S-B-O-R-N.\n\n"
            "Jeff: Date of birth?\n\n"
            "Caller: Twenty-ninth... March... nineteen sixty-two.\n\n"
            "Jeff: And NHS number?\n\n"
            "Caller: Four seven eight... six nine seven... four two five zero.\n\n"
            "Jeff: Thank you Kristina, your details are confirmed. "
            "Can you tell me — is this your asthma?\n\n"
            "Caller: Yes. I have been using my blue inhaler all morning. "
            "Four times. It is not helping much. I am on Seretide and Salbutamol.\n\n"
            "Jeff: Have you had any chest pain, or do you have a fever?\n\n"
            "Caller: No, just the breathing. My husband is here with me.\n\n"
            "Jeff: I am flagging this as urgent. The duty GP will call you back immediately. "
            "If your breathing gets significantly worse before then, please call 999. "
            "Do not wait. Do you understand?\n\n"
            "Caller: Yes, okay. Thank you.\n\n"
            "Jeff: Thank you Kristina. Help is on its way."
        ),
        "call_summary": "URGENT: 64F known asthmatic, worsening breathlessness x4 hours. Salbutamol x4 with minimal relief.",
        "ai_summary": (
            "64-year-old female with known asthma reporting worsening breathlessness for 4 hours. "
            "Medications: Seretide 250, Salbutamol PRN. Salbutamol used 4 times this morning "
            "with minimal relief. No chest pain, no fever. Husband present. "
            "Red flag: uncontrolled asthma with rescue inhaler failure in 64F."
        ),
        "patient_record_note": (
            "JeffLocal triage 2026-06-08 11:02: Worsening breathlessness x4 hours. "
            "Known asthmatic. Salbutamol x4 insufficient. Duty GP urgent callback. Red flag."
        ),
        "open_details": "Urgent — asthma, breathlessness unresponsive to Salbutamol. Red flag.",
        "call_duration_seconds": 187,
        "caller_sentiment": "distressed",
        "caller_difficulty": "low",
        "transcript_quality": "good",
        "handoff_confidence": "high",
        "extraction_confidence": "high",
        "staff_review_required": 1,
        "red_flags_present": 1,
        "status": "in_progress",
        "assigned_to": "Duty GP",
        "action_needed": "Immediate GP callback — 07519 337640",
        "outcome_notes": "",
        "staff_action": "",
        "resolved_at": None,
        "resolved_by": None,
        "last_edited_at": None,
        "last_edited_by": None,
        "turnaround_minutes": None,
        "source_path": "outputs/handoff_json/demo_case_006.json",
        "_ts_base": _BASE,
        "_ts_offset": 122,
    },

    # ── DEMO-007 ─────────────────────────────────────────────────────────────────
    # LOW — medication query. Patient: CAIN Lois, F, 14-Sep-1986
    # Verification: partial_match (name match, caller gave wrong NHS number digit)
    # Priority: low. Request: medication_query
    {
        "call_id": "DEMO-007",
        "request_type": "medication_query",
        "patient_name": "Lois Cain",
        "dob": "1986-09-14",
        "postcode": "PR9 8DT",
        "gender": "Female",
        "age": 39,
        "callback_number": "07803 116294",
        "verification_status": "partial_match",
        "verification_reason": (
            "Name and DOB confirmed. NHS number stated by caller (620 948 6119) "
            "differs by one digit from EMIS record (620 948 6118). "
            "Likely transcription error by caller. Staff to verify before discussing medication."
        ),
        "matched_patient_ref": "EMIS-300",
        "emis_number": "EMIS-300",
        "nhs_number": "620 948 6118",
        "top_candidate_name": "CAIN Lois",
        "priority": "low",
        "safe_to_queue": 1,
        "task_title": "Medication query — Sertraline 50mg side effects, partial identity match",
        "task_body": (
            "Patient Lois Cain (39F) calling with a query about side effects of Sertraline 50mg "
            "started 10 days ago. Reporting nausea and disturbed sleep. Wants to know if symptoms "
            "are expected and how long they will last. Identity partially matched — "
            "NHS number has one digit discrepancy. Staff to verify before advising."
        ),
        "staff_task_title": "Medication query — Sertraline side effects (Lois Cain, verify identity first)",
        "staff_task_body": (
            "Call Lois Cain on 07803 116294. Query: nausea and sleep disturbance on Sertraline 50mg "
            "started 10 days ago. Before advising, confirm NHS number — "
            "caller said 620 948 6119, EMIS shows 620 948 6118 (one digit off). "
            "Standard advice: nausea typically resolves within 2 weeks. "
            "Advise on sleep hygiene and when to contact GP if not improving."
        ),
        "transcript": (
            "Jeff: Good morning, Churchtown Medical Centre.\n\n"
            "Caller: Hi, I wanted to ask about a tablet I have just been prescribed.\n\n"
            "Jeff: Of course. Your name please?\n\n"
            "Caller: Lois Cain.\n\n"
            "Jeff: Date of birth?\n\n"
            "Caller: Fourteenth of September, nineteen eighty-six.\n\n"
            "Jeff: And your NHS number?\n\n"
            "Caller: Six two zero, nine four eight, six one one nine.\n\n"
            "Jeff: Thank you — there is a small discrepancy on the number I have on file. "
            "A member of the team will call you to verify before we can discuss your medication. "
            "What is your query?\n\n"
            "Caller: I started Sertraline fifty milligrams ten days ago and I feel quite sick "
            "in the mornings and I am not sleeping very well. I just wanted to check if that is normal.\n\n"
            "Jeff: I have noted that. Is this affecting your daily life significantly?\n\n"
            "Caller: A bit, yes. But I do not want to stop taking it, I just want to know if "
            "it will get better.\n\n"
            "Jeff: Understood. A member of the team will call you back today. "
            "Is 07803 116294 the best number?\n\n"
            "Caller: Yes, that is me.\n\n"
            "Jeff: Thank you Lois. Goodbye."
        ),
        "call_summary": "Medication query — Sertraline 50mg, nausea and sleep disturbance x10 days. Partial identity match.",
        "ai_summary": (
            "39-year-old female on Sertraline 50mg for 10 days, reporting nausea and "
            "disturbed sleep. Wants reassurance that side effects are expected and will resolve. "
            "Does not want to stop medication. NHS number one digit discrepancy — "
            "staff to verify before advising. Low priority clinical content."
        ),
        "patient_record_note": (
            "JeffLocal triage 2026-06-08 11:45: Sertraline 50mg side effect query "
            "(nausea, sleep disturbance x10 days). Partial identity match. Staff to verify and advise."
        ),
        "open_details": "Medication query — Sertraline. Partial identity match. Verify before callback.",
        "call_duration_seconds": 164,
        "caller_sentiment": "mildly_anxious",
        "caller_difficulty": "low",
        "transcript_quality": "good",
        "handoff_confidence": "medium",
        "extraction_confidence": "high",
        "staff_review_required": 1,
        "red_flags_present": 0,
        "status": "new",
        "assigned_to": None,
        "action_needed": "Verify NHS number then advise on Sertraline side effects — call 07803 116294",
        "outcome_notes": "",
        "staff_action": "",
        "resolved_at": None,
        "resolved_by": None,
        "last_edited_at": None,
        "last_edited_by": None,
        "turnaround_minutes": None,
        "source_path": "outputs/handoff_json/demo_case_007.json",
        "_ts_base": _BASE,
        "_ts_offset": 165,
    },

    # ── DEMO-008 ─────────────────────────────────────────────────────────────────
    # ADMIN — referral chase. Patient: CHONG Gavin, M, 19-Jun-1972
    # Verification: unverified (caller could not provide NHS number). Priority: admin.
    # Request: referral_chase
    {
        "call_id": "DEMO-008",
        "request_type": "referral_chase",
        "patient_name": "Gavin Chong",
        "dob": "1972-06-19",
        "postcode": "L37 4AR",
        "gender": "Male",
        "age": 53,
        "callback_number": "07700 881345",
        "verification_status": "unverified",
        "verification_reason": (
            "Name and DOB confirmed. Caller unable to provide NHS number — "
            "does not have card and could not recall number. "
            "Identity cannot be fully verified by automated triage. "
            "Staff must verify via EMIS before discussing referral details."
        ),
        "matched_patient_ref": "EMIS-346",
        "emis_number": "EMIS-346",
        "nhs_number": "620 918 8613",
        "top_candidate_name": "CHONG Gavin",
        "priority": "admin",
        "safe_to_queue": 0,
        "task_title": "Referral chase — cardiology, identity unverified",
        "task_body": (
            "Patient Gavin Chong (53M) calling to chase a cardiology referral submitted "
            "approximately 8 weeks ago following an abnormal ECG. Has not received appointment "
            "letter or contact from hospital. Identity unverified — NHS number not provided. "
            "Staff to look up in EMIS and verify before discussing referral details."
        ),
        "staff_task_title": "Referral chase — cardiology (Gavin Chong, verify identity, EMIS-346)",
        "staff_task_body": (
            "Call Gavin Chong on 07700 881345 re cardiology referral. "
            "First verify identity via EMIS-346 (NHS: 620 918 8613 — do not share until confirmed). "
            "Referral submitted ~8 weeks ago re abnormal ECG. Check eReferrals status. "
            "Do not discuss referral details until identity confirmed."
        ),
        "transcript": (
            "Jeff: Good afternoon, Churchtown Medical Centre.\n\n"
            "Caller: Hello, I am trying to find out what is happening with a referral "
            "the doctor made for me.\n\n"
            "Jeff: Of course. Can I take your name?\n\n"
            "Caller: Gavin Chong. C-H-O-N-G.\n\n"
            "Jeff: And your date of birth?\n\n"
            "Caller: Nineteenth of June, nineteen seventy-two.\n\n"
            "Jeff: Thank you. And your NHS number please?\n\n"
            "Caller: Ah, I do not have it to hand. I do not know it off the top of my head. "
            "I have never had to give it before.\n\n"
            "Jeff: That is okay. The team will be able to look you up. "
            "Without the NHS number I am not able to fully verify your identity, "
            "but someone will call you back. What is your referral for?\n\n"
            "Caller: It was to the heart clinic — cardiology. I had an ECG a couple of months ago "
            "and the GP said it was a bit abnormal and referred me. That was about eight weeks ago "
            "now and I have not heard anything.\n\n"
            "Jeff: I have noted that. A member of the reception team will call you back. "
            "Best number?\n\n"
            "Caller: Zero seven seven double oh, eight eight one three four five.\n\n"
            "Jeff: Thank you Gavin. Someone will be in touch today."
        ),
        "call_summary": "Referral chase — cardiology x8 weeks. Post abnormal ECG. Identity unverified (no NHS number).",
        "ai_summary": (
            "53-year-old male chasing cardiology referral submitted approximately 8 weeks ago "
            "following an abnormal ECG. No appointment letter or hospital contact received. "
            "Identity unverified — caller could not provide NHS number. "
            "Staff must verify via EMIS before discussing referral details. Admin priority."
        ),
        "patient_record_note": (
            "JeffLocal triage 2026-06-08 14:20: Cardiology referral chase — x8 weeks, post abnormal ECG. "
            "Identity unverified. Staff to look up EMIS-346 and call back."
        ),
        "open_details": "Referral chase — cardiology. Unverified identity. Verify before discussing.",
        "call_duration_seconds": 198,
        "caller_sentiment": "patient",
        "caller_difficulty": "low",
        "transcript_quality": "good",
        "handoff_confidence": "low",
        "extraction_confidence": "medium",
        "staff_review_required": 1,
        "red_flags_present": 0,
        "status": "new",
        "assigned_to": None,
        "action_needed": "Verify identity via EMIS then chase cardiology referral",
        "outcome_notes": "",
        "staff_action": "",
        "resolved_at": None,
        "resolved_by": None,
        "last_edited_at": None,
        "last_edited_by": None,
        "turnaround_minutes": None,
        "source_path": "outputs/handoff_json/demo_case_008.json",
        "_ts_base": _BASE,
        "_ts_offset": 260,
    },

    # ── DEMO-009 ─────────────────────────────────────────────────────────────────
    # LOW — admin callback. Patient: CAIN Steven, M, 15-Oct-1988
    # Verification: verified. Priority: low. Request: admin_callback
    {
        "call_id": "DEMO-009",
        "request_type": "admin_callback",
        "patient_name": "Steven Cain",
        "dob": "1988-10-15",
        "postcode": "PR9 8DT",
        "gender": "Male",
        "age": 37,
        "callback_number": "07803 115001",
        "verification_status": "verified",
        "verification_reason": "Name, DOB (15 Oct 1988), and NHS number confirmed against EMIS record.",
        "matched_patient_ref": "EMIS-301",
        "emis_number": "EMIS-301",
        "nhs_number": "620 929 4480",
        "top_candidate_name": "CAIN Steven",
        "priority": "low",
        "safe_to_queue": 1,
        "task_title": "Admin callback — request for GP letter for insurance purposes",
        "task_body": (
            "Patient Steven Cain (37M) requesting a GP letter confirming he is fit for "
            "travel insurance purposes. Planning travel in approximately 6 weeks. "
            "Mentions he has a history of type 2 diabetes — managed with Metformin 1g twice daily. "
            "Insurer has requested confirmation of current health status and no recent hospital admissions. "
            "Admin team to advise on private letter fee and process."
        ),
        "staff_task_title": "Admin — GP private letter request, Steven Cain (EMIS-301)",
        "staff_task_body": (
            "Call Steven Cain on 07803 115001 re GP private letter for travel insurance. "
            "T2DM on Metformin 1g BD. Travel in 6 weeks. "
            "Advise on private letter fee (standard £30), turnaround time, "
            "and what information the GP letter will contain. Arrange payment before drafting."
        ),
        "transcript": (
            "Jeff: Good afternoon, Churchtown Medical Centre.\n\n"
            "Caller: Hi, I need a letter from the GP for my travel insurance.\n\n"
            "Jeff: Of course, I can log that request. Your name please?\n\n"
            "Caller: Steven Cain.\n\n"
            "Jeff: Date of birth?\n\n"
            "Caller: Fifteenth of October, nineteen eighty-eight.\n\n"
            "Jeff: And NHS number?\n\n"
            "Caller: Six two zero, nine two nine, four four eight zero.\n\n"
            "Jeff: Thank you, all confirmed. Can you tell me a bit more about what the letter needs to cover?\n\n"
            "Caller: Yeah, the insurance company wants a letter saying I am fit to travel "
            "and that I have not been admitted to hospital recently. I am diabetic — type two — "
            "on Metformin. They just want a letter from the GP confirming my current status.\n\n"
            "Jeff: Understood. When are you travelling?\n\n"
            "Caller: About six weeks from now.\n\n"
            "Jeff: I have noted all of that. The admin team will call you back to discuss "
            "the letter, any associated fee, and the turnaround time. "
            "Is this number good to call back on?\n\n"
            "Caller: Yes, zero seven eight zero three, one one five zero zero one.\n\n"
            "Jeff: Perfect. Is there anything else today?\n\n"
            "Caller: No, that is it. Cheers.\n\n"
            "Jeff: Thank you Steven. Goodbye."
        ),
        "call_summary": "Admin request — GP private letter for travel insurance. T2DM on Metformin. Travel in 6 weeks.",
        "ai_summary": (
            "37-year-old male requesting GP private letter for travel insurance. "
            "Type 2 diabetes, managed with Metformin 1g twice daily. Travelling in approximately "
            "6 weeks. Insurer requires confirmation of current health status and no recent admissions. "
            "Low priority admin task — advise on fee and process."
        ),
        "patient_record_note": (
            "JeffLocal triage 2026-06-08 14:55: Private letter request for travel insurance. "
            "T2DM, Metformin 1g BD. Admin team to advise on fee and process."
        ),
        "open_details": "Admin — private GP letter for travel insurance. Fee discussion needed.",
        "call_duration_seconds": 174,
        "caller_sentiment": "friendly",
        "caller_difficulty": "low",
        "transcript_quality": "good",
        "handoff_confidence": "high",
        "extraction_confidence": "high",
        "staff_review_required": 0,
        "red_flags_present": 0,
        "status": "new",
        "assigned_to": None,
        "action_needed": "Admin team to advise on private letter fee and arrange",
        "outcome_notes": "",
        "staff_action": "",
        "resolved_at": None,
        "resolved_by": None,
        "last_edited_at": None,
        "last_edited_by": None,
        "turnaround_minutes": None,
        "source_path": "outputs/handoff_json/demo_case_009.json",
        "_ts_base": _BASE,
        "_ts_offset": 295,
    },

    # ── DEMO-010 ─────────────────────────────────────────────────────────────────
    # FAILED verification — no match found. Patient name not on register.
    # Patient: CLAYTON Daniel, M, 11-Dec-1984 — name not found in EMIS at time of call
    # (recently registered, record not yet active). Priority: routine. Request: appointment_request
    {
        "call_id": "DEMO-010",
        "request_type": "appointment_request",
        "patient_name": "Daniel Clayton",
        "dob": "1984-12-11",
        "postcode": "PR8 5GN",
        "gender": "Male",
        "age": 41,
        "callback_number": "07961 448820",
        "verification_status": "failed",
        "verification_reason": (
            "Name CLAYTON Daniel not found in EMIS register at time of call. "
            "DOB 11 Dec 1984 also produced no match. NHS number 620 947 1668 returned no record. "
            "Patient may have registered recently and EMIS record not yet active. "
            "Staff to check new registrations queue and verify manually."
        ),
        "matched_patient_ref": None,
        "emis_number": None,
        "nhs_number": "620 947 1668",
        "top_candidate_name": None,
        "priority": "routine",
        "safe_to_queue": 0,
        "task_title": "Appointment request — patient not found on register, possible new registration",
        "task_body": (
            "Daniel Clayton (41M) called requesting a routine GP appointment for recurring migraines. "
            "States he registered with the surgery 2 weeks ago. "
            "EMIS lookup returned no matching record — "
            "name, DOB, and NHS number all failed to match. "
            "Staff to check new patient registrations queue. "
            "If confirmed registered, book appointment; if not, advise on registration process."
        ),
        "staff_task_title": "Appointment request — patient not found on register (Daniel Clayton)",
        "staff_task_body": (
            "Call Daniel Clayton on 07961 448820. He wants a routine appointment for migraines. "
            "Not found in EMIS — check new registrations queue and NHS spine for NHS 620 947 1668. "
            "If registered but not yet active in EMIS, book appointment and update. "
            "If not registered, advise to complete registration form first."
        ),
        "transcript": (
            "Jeff: Good afternoon, Churchtown Medical Centre.\n\n"
            "Caller: Hi, I would like to book an appointment please.\n\n"
            "Jeff: Of course. Your name please?\n\n"
            "Caller: Daniel Clayton.\n\n"
            "Jeff: Date of birth?\n\n"
            "Caller: Eleventh of December, nineteen eighty-four.\n\n"
            "Jeff: And your NHS number?\n\n"
            "Caller: Six two zero, nine four seven, one six six eight.\n\n"
            "Jeff: Thank you. I am having difficulty finding your records on our system. "
            "Are you registered with Churchtown Medical Centre?\n\n"
            "Caller: Yes, I registered about two weeks ago. I sent the form in. "
            "I have not been to the surgery before though.\n\n"
            "Jeff: That may explain it — your registration may still be processing. "
            "I will log this as urgent for the reception team to check. "
            "A member of staff will call you back today. "
            "What is the appointment for?\n\n"
            "Caller: I get migraines quite regularly. I used to get medication for them "
            "at my last GP — Sumatriptan. I just need to get it sorted at this practice.\n\n"
            "Jeff: Understood. Is this number good for a callback?\n\n"
            "Caller: Yes, zero seven nine six one, four four eight eight two zero.\n\n"
            "Jeff: Thank you Daniel. The team will be in touch to get you sorted. Goodbye."
        ),
        "call_summary": "Appointment request — migraines, Sumatriptan. Patient not found on register — possible new registration still processing.",
        "ai_summary": (
            "41-year-old male requesting appointment for recurrent migraines. "
            "Previously on Sumatriptan at previous GP. Claims to have registered 2 weeks ago. "
            "EMIS lookup: no match on name, DOB, or NHS number. "
            "Likely new registration not yet active. Staff to check new registrations queue. "
            "Cannot verify identity or book appointment until record confirmed."
        ),
        "patient_record_note": (
            "JeffLocal triage 2026-06-08 15:10: Appointment request — migraines / Sumatriptan. "
            "Not found on EMIS register. States registered 2 weeks ago. "
            "Admin team to check new registrations and call back."
        ),
        "open_details": "Not on register — check new patient registration queue. Appointment for migraines.",
        "call_duration_seconds": 221,
        "caller_sentiment": "calm",
        "caller_difficulty": "low",
        "transcript_quality": "good",
        "handoff_confidence": "low",
        "extraction_confidence": "high",
        "staff_review_required": 1,
        "red_flags_present": 0,
        "status": "new",
        "assigned_to": None,
        "action_needed": "Check new registrations queue — confirm EMIS record before booking",
        "outcome_notes": "",
        "staff_action": "",
        "resolved_at": None,
        "resolved_by": None,
        "last_edited_at": None,
        "last_edited_by": None,
        "turnaround_minutes": None,
        "source_path": "outputs/handoff_json/demo_case_010.json",
        "_ts_base": _BASE,
        "_ts_offset": 310,
    },
]


def _apply_timestamps(cases: list[dict]) -> list[dict]:
    """Compute and attach all timestamp fields to each case dict."""
    now_iso = _now()
    result = []
    for case in cases:
        base = case.pop("_ts_base")
        offset = case.pop("_ts_offset")
        ts_iso, ts_sort = _ts_offset(base, offset)
        c = dict(case)
        c["timestamp"] = ts_iso
        c["call_timestamp_sort"] = ts_sort
        c["last_updated"] = ts_iso
        c["imported_at"] = now_iso
        c["created_at"] = ts_iso
        # source_file_mtime — simulate the JSON file write time (same as call timestamp)
        c["source_file_mtime"] = ts_iso
        # last_edited_at already set per case (None unless resolved)
        result.append(c)
    return result


# All columns in insertion order — must match cases table schema exactly
COLUMNS = [
    "call_id", "open_details", "timestamp", "call_timestamp_sort",
    "request_type", "patient_name", "dob", "postcode", "gender", "age",
    "callback_number", "verification_status", "verification_reason",
    "matched_patient_ref", "emis_number", "nhs_number", "top_candidate_name",
    "priority", "safe_to_queue",
    "task_title", "task_body", "staff_task_title", "staff_task_body",
    "transcript", "call_summary", "ai_summary", "patient_record_note",
    "call_duration_seconds", "caller_sentiment", "caller_difficulty",
    "transcript_quality", "handoff_confidence", "extraction_confidence",
    "staff_review_required", "red_flags_present",
    "status", "assigned_to", "action_needed", "outcome_notes",
    "staff_action", "resolved_at", "resolved_by",
    "last_updated", "last_edited_at", "last_edited_by",
    "turnaround_minutes", "source_path", "source_file_mtime",
    "imported_at", "created_at",
]


def seed(db_path: Path, clear: bool) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    existing_tables = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if "cases" not in existing_tables:
        print(
            "ERROR: 'cases' table not found. "
            "Run the dashboard at least once to initialise the DB schema."
        )
        conn.close()
        sys.exit(1)

    if clear:
        deleted = conn.execute(
            "DELETE FROM cases WHERE call_id LIKE ?",
            (f"{DEMO_PREFIX}%",),
        ).rowcount
        conn.commit()
        print(f"Cleared {deleted} existing demo row(s).")

    cases = _apply_timestamps(DEMO_CASES)

    placeholders = ", ".join(["?"] * len(COLUMNS))
    col_list = ", ".join(COLUMNS)
    sql = f"INSERT OR REPLACE INTO cases ({col_list}) VALUES ({placeholders})"  # noqa: S608

    inserted = 0
    for case in cases:
        values = [case.get(col) for col in COLUMNS]
        conn.execute(sql, values)
        inserted += 1

    conn.commit()
    conn.close()

    print(f"Done. {inserted} demo row(s) inserted/replaced.")
    print()
    print("Verification status breakdown:")
    for case in cases:
        print(
            f"  {case['call_id']}  {case['patient_name']:<22}"
            f"  {case['verification_status']:<14}"
            f"  priority={case['priority']:<8}"
            f"  status={case['status']}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed realistic demo triage cases into the JeffLocal dashboard DB."
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"Path to SQLite database (default: {DEFAULT_DB})",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Delete existing demo rows before inserting (idempotent re-seed).",
    )
    args = parser.parse_args()

    print(f"Target DB  : {args.db}")
    print(f"Clear first: {args.clear}")
    print()

    if not args.db.exists():
        print(
            f"WARNING: DB not found at {args.db}. "
            "It will be created, but schema must be initialised by running the dashboard first."
        )

    seed(args.db, args.clear)


if __name__ == "__main__":
    main()

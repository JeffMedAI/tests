"""
n8n_webhook_test_pack.py
Fixture module: synthetic test call payloads for /api/n8n/test-intake-batch tests.
Call IDs are plain unique identifiers — no prefix required.
No real patient data.
"""

from __future__ import annotations

_TEST_CALLS = [
    {
        "call_id": "TC-BATCH-001",
        "call_timestamp": "2026-05-28T09:00:00Z",
        "request_type": "prescription",
        "normalized_input": {
            "patient_name": "Alice Testington",
            "dob": "1965-03-14",
            "postcode": "PR9 7LT",
            "callback_number": "07111000001",
        },
        "verification_status": "matched",
        "verification_reason": "name+dob+postcode matched",
        "priority": "routine",
        "safe_to_queue": True,
        "staff_review_required": False,
        "red_flags_present": False,
        "task_title": "Repeat prescription request",
        "task_body": "Patient requests repeat prescription for simvastatin 40mg.",
        "call_summary": "Routine repeat prescription request.",
        "raw_transcript": "I need my repeat prescription for simvastatin please.",
        "status": "New",
    },
    {
        "call_id": "TC-BATCH-002",
        "call_timestamp": "2026-05-28T09:05:00Z",
        "request_type": "appointment_request",
        "normalized_input": {
            "patient_name": "Bob Mocksworth",
            "dob": "1978-07-22",
            "postcode": "PR8 1AB",
            "callback_number": "07111000002",
        },
        "verification_status": "matched",
        "verification_reason": "name+dob matched",
        "priority": "routine",
        "safe_to_queue": True,
        "staff_review_required": False,
        "red_flags_present": False,
        "task_title": "Appointment request",
        "task_body": "Patient requests GP appointment for back pain review.",
        "call_summary": "Routine appointment request for back pain.",
        "raw_transcript": "I'd like to make an appointment to see a doctor about my back.",
        "status": "New",
    },
    {
        "call_id": "TC-BATCH-003",
        "call_timestamp": "2026-05-28T09:10:00Z",
        "request_type": "sicknote",
        "normalized_input": {
            "patient_name": "Carol Dummyfield",
            "dob": "1990-11-05",
            "postcode": "PR9 0XY",
            "callback_number": "07111000003",
        },
        "verification_status": "matched",
        "verification_reason": "name+dob+postcode matched",
        "priority": "routine",
        "safe_to_queue": True,
        "staff_review_required": False,
        "red_flags_present": False,
        "task_title": "Sick note request",
        "task_body": "Patient requests sick note for 5 days, reason: viral illness.",
        "call_summary": "Patient requesting sick note for 5 days.",
        "raw_transcript": "I need a sick note for this week, I've had a virus.",
        "status": "New",
    },
    {
        "call_id": "TC-BATCH-004",
        "call_timestamp": "2026-05-28T09:15:00Z",
        "request_type": "callback_request",
        "normalized_input": {
            "patient_name": "David Placeholder",
            "dob": "1955-02-28",
            "postcode": "PR8 2CD",
            "callback_number": "07111000004",
        },
        "verification_status": "unverified",
        "verification_reason": "name not matched in system",
        "priority": "routine",
        "safe_to_queue": False,
        "staff_review_required": True,
        "red_flags_present": False,
        "task_title": "GP callback request — unverified",
        "task_body": "Patient not matched. Manual verification required before callback.",
        "call_summary": "Unverified patient requesting GP callback.",
        "raw_transcript": "Can a doctor call me back please? It's about my blood pressure medication.",
        "status": "New",
    },
    {
        "call_id": "TC-BATCH-005",
        "call_timestamp": "2026-05-28T09:20:00Z",
        "request_type": "appointment_redirect",
        "normalized_input": {
            "patient_name": "Geoffrey Mynne",
            "dob": "1941-02-21",
            "postcode": "PR9 9ZZ",
            "callback_number": "07111000005",
        },
        "verification_status": "matched",
        "verification_reason": "name+dob+postcode matched",
        "priority": "999 Emergency",
        "safe_to_queue": False,
        "staff_review_required": True,
        "red_flags_present": True,
        "task_title": "Emergency red flag — immediate review",
        "task_body": "Patient reports chest pain and breathlessness. Red flag: possible cardiac event.",
        "call_summary": "Chest pain and breathlessness. Immediate clinical review required.",
        "raw_transcript": "I've got really bad chest pain and I can't breathe properly.",
        "status": "New",
    },
]


def build_test_calls() -> list[dict]:
    """Return a list of 5 synthetic test call payloads (no real patient data)."""
    return list(_TEST_CALLS)

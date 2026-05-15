from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SENDER_PATH = ROOT / "tests" / "send_gp_demo_n8n_webhook_calls.py"


def load_sender_module():
    spec = importlib.util.spec_from_file_location("gp_demo_sender", SENDER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_powershell_handoff(handoff: dict) -> dict:
    payload = json.dumps(handoff, ensure_ascii=False)
    script = f"""
$ErrorActionPreference = 'Stop'
. 'C:\\JeffLocal\\app\\modules\\Jeff.StaffSummary.ps1'
. 'C:\\JeffLocal\\app\\modules\\Jeff.Emergency.ps1'
$handoff = @'
{payload}
'@ | ConvertFrom-Json
$null = Invoke-JeffEmergencyOverride -Handoff $handoff -ScanObjects @($handoff, $handoff.raw_transcript, $handoff.transcript_summary, $handoff.pathway_responses)
if (-not $handoff.PSObject.Properties['task_title']) {{
    $task = Get-JeffStaffTaskText -RequestType $handoff.request_type -RequestSubtype $handoff.request_subtype -PathwayResponses $handoff.pathway_responses -RawTranscript $handoff.raw_transcript -TranscriptSummary $handoff.transcript_summary -VerificationStatus $handoff.verification_status -VerificationReason $handoff.verification_reason -Priority $handoff.priority -SafeToQueue $handoff.safe_to_queue -StaffReviewRequired $handoff.staff_review_required -RedFlagsPresent $handoff.red_flags_present -NormalizedInput $handoff.normalized_input -MedicationsRequested @($handoff.normalized_input.medications_requested) -Pharmacy $handoff.normalized_input.pharmacy -CallbackNumber $handoff.normalized_input.callback_number
    $handoff | Add-Member -NotePropertyName task_title -NotePropertyValue $task.task_title -Force
    $handoff | Add-Member -NotePropertyName task_body -NotePropertyValue $task.task_body -Force
}}
$handoff | ConvertTo-Json -Depth 20 -Compress
"""
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            script,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout.strip())


def make_routine_prescription_handoff(raw_transcript: str, transcript_summary: str = "Caller reported no urgent symptoms.") -> dict:
    return {
        "call_id": "GPDEMO-20260513-TEST-001",
        "request_type": "prescription",
        "request_subtype": "prescription",
        "priority": "routine",
        "safe_to_queue": True,
        "staff_review_required": False,
        "red_flags_present": False,
        "verification_status": "matched",
        "verification_reason": "Exact normalized name and DOB match found in patient lookup.",
        "raw_transcript": raw_transcript,
        "transcript_summary": transcript_summary,
        "normalized_input": {
            "patient_name": "Jason Morrey",
            "dob": "1970-01-10",
            "postcode": "PR9 7LT",
            "callback_number": "07111000001",
            "medications_requested": ["atorvastatin 20mg"],
            "urgency_note": "routine",
            "pharmacy": "Demo Pharmacy",
            "caller_for": "self",
            "supplied_nhs_number": "",
        },
        "pathway_responses": {
            "consent_to_questions": "yes",
            "caller_for": "self",
            "selected_pathway": "prescription",
            "appointment_redirected": False,
            "identity": {
                "patient_name": "Jason Morrey",
                "dob": "1970-01-10",
                "postcode": "PR9 7LT",
                "callback_number_from_caller_id": "07111000001",
                "callback_confirmed": True,
            },
            "prescription": {
                "prescription_type": "repeat",
                "medications_requested": ["atorvastatin 20mg"],
                "pharmacy": "Demo Pharmacy",
                "run_out_status": "two tablets left",
            },
            "urgency_assessment": {
                "urgency_level": "routine",
                "red_flags_mentioned": [],
                "red_flag_followup_questions": [],
                "emergency_advice_given": False,
                "transfer_offered": False,
                "transfer_accepted": False,
            },
            "summary_confirmation": {
                "summary_read_back": transcript_summary,
                "caller_confirmed_correct": True,
                "anything_else": "no",
            },
        },
    }


def test_gp_demo_sender_uses_existing_lookup_patients():
    sender = load_sender_module()
    plain_calls = sender.build_plain_calls("GPDEMO-20260513-TESTBATCH")
    identities = [(call["normalized_input"]["patient_name"], call["normalized_input"]["dob"]) for call in plain_calls]

    assert identities == [
        ("Jason Morrey", "1970-01-10"),
        ("Mathew Morrey", "1978-09-15"),
        ("Peter Morrey", "1978-09-15"),
        ("Jayson Morrey", "1970-01-10"),
        ("Geoffrey Mynne", "1941-02-21"),
    ]
    assert plain_calls[0]["pathway_responses"]["urgency_assessment"]["urgency_level"] == "routine"
    assert plain_calls[3]["pathway_responses"]["caller_for"] == "third_party"
    assert plain_calls[4]["pathway_responses"]["urgency_assessment"]["red_flags_mentioned"] == [
        "chest pain",
        "breathlessness",
        "sweating",
    ]


def test_agent_question_does_not_trigger_red_flag():
    result = run_powershell_handoff(
        make_routine_prescription_handoff(
            "Agent: Have you had any chest pain, breathlessness, sweating, fainting, or any other urgent symptoms? "
            "Caller: No, nothing like that. I just need the prescription renewed in time."
        )
    )

    assert result["priority"] == "routine"
    assert result["red_flags_present"] is False
    assert result["safe_to_queue"] is True
    assert result["task_title"].startswith("Repeat prescription request")
    assert "POSSIBLE EMERGENCY" not in result["task_title"]
    assert "chest pain" not in result["task_body"].lower()
    assert "breathless" not in result["task_body"].lower()


def test_caller_denial_is_respected():
    result = run_powershell_handoff(
        make_routine_prescription_handoff(
            "Caller: No chest pain, no breathlessness, no sweating, no fainting. I only need my repeat prescription."
        )
    )

    assert result["priority"] == "routine"
    assert result["red_flags_present"] is False
    assert result["safe_to_queue"] is True
    assert "POSSIBLE EMERGENCY" not in result["task_title"]


def test_caller_affirmative_red_flag_triggers_override():
    result = run_powershell_handoff(
        make_routine_prescription_handoff(
            "Caller: I have chest pain and I am breathless. I feel sweaty and worse when I move. Agent: Please call 999 now."
        )
    )

    assert result["priority"] == "999 Emergency"
    assert result["red_flags_present"] is True
    assert result["safe_to_queue"] is False
    assert "POSSIBLE EMERGENCY" in result["task_title"]
    assert "chest pain" in result["task_body"].lower()
    assert "999/a&e" in result["task_body"].lower() or "999" in result["task_body"].lower()


def test_structured_red_flags_trigger_even_if_transcript_is_ambiguous():
    handoff = make_routine_prescription_handoff(
        "Agent: Have you had any chest pain or breathlessness? Caller: No, nothing like that."
    )
    handoff["pathway_responses"]["urgency_assessment"] = {
        "urgency_level": "999 Emergency",
        "red_flags_mentioned": ["chest pain", "breathlessness"],
        "red_flag_followup_questions": [],
        "emergency_advice_given": True,
        "transfer_offered": False,
        "transfer_accepted": False,
    }

    result = run_powershell_handoff(handoff)

    assert result["priority"] == "999 Emergency"
    assert result["red_flags_present"] is True
    assert result["safe_to_queue"] is False
    assert "POSSIBLE EMERGENCY" in result["task_title"]
    assert "chest pain" in result["task_body"].lower()

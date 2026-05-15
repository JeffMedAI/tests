Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$pythonCode = @'
import json
import re
import sys
from pathlib import Path

BASE = Path(r"C:\JeffLocal")
sys.path.insert(0, str(BASE / "app"))
sys.path.insert(0, str(BASE / "tests" / "fixtures"))

from build_raw_intake_row import build_raw_intake_row, load_mapping
import raw_intake_mock_pack as mock_pack

REQUIRED_HEADERS = [
    "Open Details",
    "Timestamp",
    "Call ID",
    "Status",
    "Request Type",
    "Patient Name",
    "DOB",
    "Postcode",
    "Callback Number",
    "Verification Status",
    "Verification Reason",
    "Matched Patient Ref",
    "EMIS Number",
    "NHS Number",
    "Top Candidate Name",
    "Priority",
    "Safe To Queue",
    "Task Title",
    "Task Body",
    "Transcript",
    "Assigned To",
    "Last Updated",
    "Action Needed",
    "Outcome Notes",
    "Staff Action",
    "Resolved At",
    "Resolved By",
    "Last Edited At",
    "Last Edited By",
    "Turnaround Minutes",
    "Call Summary",
    "Call Duration Seconds",
    "Caller Sentiment",
    "Caller Difficulty",
    "Transcript Quality",
    "Handoff Confidence",
    "Extraction Confidence",
    "Staff Review Required",
    "Red Flags Present",
]

OPTIONAL_BLANK_HEADERS = {
    "Assigned To",
    "Outcome Notes",
    "Staff Action",
    "Resolved At",
    "Resolved By",
    "Last Edited At",
    "Last Edited By",
    "Turnaround Minutes",
    "Matched Patient Ref",
    "EMIS Number",
    "NHS Number",
    "Top Candidate Name",
    "Callback Number",
    "DOB",
}


def fail(message):
    raise AssertionError(message)


columns = load_mapping(BASE / "config" / "raw_intake_columns.json")
headers = [column["header"] for column in columns]
if headers != REQUIRED_HEADERS:
    fail(f"Raw Intake header order mismatch.\nExpected: {REQUIRED_HEADERS}\nActual:   {headers}")

calls = mock_pack.build_mock_calls()
if len(calls) != 12:
    fail(f"Expected 12 mock calls, got {len(calls)}")

manifest_path = BASE / "tests" / "fixtures" / "expected_raw_intake_mock_outcomes.json"
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
call_ids = [call["call_id"] for call in calls]
if set(manifest.keys()) != set(call_ids):
    fail("Expected outcome manifest does not exactly cover the 12 mock calls.")

active_payload_text = json.dumps(calls, ensure_ascii=False)
for pattern in [r"n8n", r"webhook", r"script\.google", r"https?://", r"apps script"]:
    if re.search(pattern, active_payload_text, re.IGNORECASE):
        fail(f"Active mock payloads contain external sender/cloud reference: {pattern}")

if re.search(r"\b\d{3} \d{3} \d{4}\b", active_payload_text):
    fail("Active mock payloads contain NHS-number-shaped values.")

for call in calls:
    expected = manifest[call["call_id"]]
    ni = call["normalized_input"]
    for key, expected_key in [
        ("patient_name", "expected_patient_name"),
        ("dob", "expected_dob"),
        ("postcode", "expected_postcode"),
        ("callback_number", "expected_callback_number"),
    ]:
        if ni.get(key, "") != expected[expected_key]:
            fail(f"{call['call_id']} source {key} mismatch: {ni.get(key)} != {expected[expected_key]}")

    transcript = call.get("raw_transcript", "")
    if len(transcript) < 120:
        fail(f"{call['call_id']} transcript is too short to be realistic.")

    duration = call.get("call_duration_seconds", 0)
    if not isinstance(duration, int) or not (60 <= duration <= 600):
        fail(f"{call['call_id']} call duration is not numeric/realistic: {duration}")

handoffs = mock_pack.build_expected_handoffs()
if len(handoffs) != 12:
    fail(f"Expected 12 mock handoffs, got {len(handoffs)}")

for handoff in handoffs:
    call_id = handoff["call_id"]
    expected = manifest[call_id]
    row = build_raw_intake_row(handoff, BASE / "config" / "raw_intake_columns.json")
    row_keys = list(row.keys())

    if row_keys != REQUIRED_HEADERS:
        fail(f"{call_id} row keys/order mismatch.")
    if len(row) != 39:
        fail(f"{call_id} row should have 39 columns, got {len(row)}")

    for header in REQUIRED_HEADERS:
        if header in OPTIONAL_BLANK_HEADERS:
            continue
        value = row[header]
        if value is None or (isinstance(value, str) and not value.strip()):
            fail(f"{call_id} required staff-facing column is blank: {header}")

    for header in ["Safe To Queue", "Staff Review Required", "Red Flags Present"]:
        if not isinstance(row[header], bool):
            fail(f"{call_id} boolean column not normalized as bool: {header}={row[header]!r}")

    for header in ["Handoff Confidence", "Extraction Confidence"]:
        if not isinstance(row[header], (int, float)):
            fail(f"{call_id} confidence column is not numeric: {header}={row[header]!r}")

    if row["Request Type"] != expected["expected_request_type"]:
        fail(f"{call_id} request type mismatch.")
    if row["Patient Name"] != expected["expected_patient_name"]:
        fail(f"{call_id} patient name mismatch.")
    if row["DOB"] != expected["expected_dob"]:
        fail(f"{call_id} DOB mismatch.")
    if row["Postcode"] != expected["expected_postcode"]:
        fail(f"{call_id} postcode mismatch.")
    if row["Callback Number"] != expected["expected_callback_number"]:
        fail(f"{call_id} callback mismatch.")
    if row["Verification Status"] != expected["expected_verification_status"]:
        fail(f"{call_id} verification status mismatch.")
    if row["Priority"] != expected["expected_priority"]:
        fail(f"{call_id} priority mismatch.")
    if row["Safe To Queue"] != expected["expected_safe_to_queue"]:
        fail(f"{call_id} safe_to_queue mismatch.")
    if row["Staff Review Required"] != expected["expected_staff_review_required"]:
        fail(f"{call_id} staff_review_required mismatch.")
    if row["Red Flags Present"] != expected["expected_red_flags_present"]:
        fail(f"{call_id} red_flags_present mismatch.")
    if row["Transcript Quality"] != expected["expected_transcript_quality"]:
        fail(f"{call_id} transcript quality mismatch.")
    if row["Caller Sentiment"] != expected["expected_caller_sentiment"]:
        fail(f"{call_id} caller sentiment mismatch.")
    if row["Caller Difficulty"] != expected["expected_caller_difficulty"]:
        fail(f"{call_id} caller difficulty mismatch.")
    if row["Action Needed"] != expected["expected_action_needed"]:
        fail(f"{call_id} action needed mismatch.")

print("Raw Intake column contract passed.")
'@

$tempScript = Join-Path $env:TEMP ("jefflocal_raw_intake_contract_" + [guid]::NewGuid().ToString("N") + ".py")
try {
    $pythonCode | Set-Content -LiteralPath $tempScript -Encoding UTF8
    python $tempScript
}
finally {
    Remove-Item -LiteralPath $tempScript -Force -ErrorAction SilentlyContinue
}

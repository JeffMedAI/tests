"""
Fresh 5-call mixed-pathway test batch — 2026-05-21
Batch ID: N8NTEST-20260521-MIXEDVERIFY2

Covers: repeat_prescription, sick_note, test_result, referral (third-party), admin (no_match)
All transcripts follow Jeff prompt conversation flow (opening -> identity -> pathway -> summary -> close).
"""
import sys
import time
import json
import subprocess
from pathlib import Path

FIXTURE_DIR = Path(r"C:\JeffLocal\tests\fixtures")
sys.path.insert(0, str(FIXTURE_DIR))

import live_lookup_test_payloads as pack

LOCAL_ENCRYPTED_RAW_DIR = Path(r"C:\JeffLocal\queue\encrypted_raw")
SCHEDULED_TASK_NAME = "JeffLocal Encrypted Intake Cycle"


def write_envelope_to_local_queue(envelope):
    LOCAL_ENCRYPTED_RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_path = LOCAL_ENCRYPTED_RAW_DIR / f"{envelope['message_id']}.json"
    out_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    return out_path


def trigger_scheduled_task():
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
         f'Start-ScheduledTask -TaskName "{SCHEDULED_TASK_NAME}"'],
        check=False,
    )


PATIENTS = pack.PATIENTS
BATCH = "N8NTEST-20260521-MIXEDVERIFY2"


CALLS = [
    # --- Call 1: Repeat prescription, 2 meds, matched, DOB correct ---
    pack.make_call(
        BATCH, 1, "REPEAT-CORKHILL-KEVIN",
        PATIENTS["396"],
        workflow="prescription",
        request_type="repeat_prescription",
        transcript=(
            "Jeff: Good morning. I'll ask you a few quick questions so the practice team can review your request "
            "and contact you if needed. Is that okay? "
            "Caller: Yes, that's fine. "
            "Jeff: Are you calling about yourself or someone else? "
            "Caller: Myself. "
            "Jeff: Please say one of the following: Prescription, Sick note, Referral, Test result, or Admin. "
            "Caller: Prescription. "
            "Jeff: Is this for a repeat prescription or a new medication request? "
            "Caller: Repeat, please. I need two things actually. "
            "Jeff: No problem. Can I take your full name? "
            "Caller: Kevin Corkhill. "
            "Jeff: And your date of birth? "
            "Caller: Twenty-ninth June nineteen sixty-eight. "
            "Jeff: I can see a number ending in 0396 — is that the best number for the practice to reach you on? "
            "Caller: Yes, that's my mobile. "
            "Jeff: What are the medications you need? "
            "Caller: Metformin five hundred milligrams and bisoprolol two point five milligrams. "
            "Jeff: Have you run out, or are you about to run out? "
            "Caller: I've got about five days left on both. "
            "Jeff: Which pharmacy do you normally use? "
            "Caller: Boots on Lord Street, Southport. "
            "Jeff: Let me just check I've got that right. Repeat prescription for Kevin Corkhill, "
            "date of birth twenty-ninth June nineteen sixty-eight. Medications: metformin five hundred milligrams "
            "and bisoprolol two point five milligrams. Pharmacy: Boots, Lord Street. Callback number ending in 0396. "
            "Is that correct? "
            "Caller: Yes, that's all right. "
            "Jeff: Thank you. I've passed your request to the practice team, who will review it and contact you if needed. "
            "Is there anything else I can help you with today? "
            "Caller: No, that's everything, thanks. "
            "Jeff: We are always here to help. Thank you for calling Churchtown Medical Centre. Goodbye."
        ),
        meds=["metformin 500mg", "bisoprolol 2.5mg"],
        pharmacy="Boots Lord Street Southport",
        caller_id_number="07111000396",
        call_duration_seconds=248,
    ),

    # --- Call 2: New sick note, > 7 days, GP already seen, back pain, work use ---
    pack.make_call(
        BATCH, 2, "SICKNOTE-DANIEL-CLAYTON",
        PATIENTS["358"],
        workflow="admin",
        request_type="sick_note",
        transcript=(
            "Jeff: Good morning. I'll ask you a few quick questions so the practice team can review your request "
            "and contact you if needed. Is that okay? "
            "Caller: Yes. "
            "Jeff: Are you calling about yourself or someone else? "
            "Caller: For myself. "
            "Jeff: Please say one of the following: Prescription, Sick note, Referral, Test result, or Admin. "
            "Caller: Sick note. "
            "Jeff: Is this a new sick note request, or an extension of an existing sick note? "
            "Caller: New one. "
            "Jeff: Do you think you need the sick note for more than seven days? "
            "Caller: Yes, I think at least two weeks. "
            "Jeff: Can I take your full name? "
            "Caller: Daniel Clayton. "
            "Jeff: And your date of birth? "
            "Caller: Eleventh December nineteen eighty-four. "
            "Jeff: I can see a number ending in 0358 — is that the best number for the practice to reach you on? "
            "Caller: Yes. "
            "Jeff: What date do you need the sick note to start from? "
            "Caller: From this Monday, the nineteenth. "
            "Jeff: And how long do you think you will need to be signed off? "
            "Caller: Around two weeks, so until the second of June. "
            "Jeff: Is this for work, benefits, or personal use? "
            "Caller: Work. My employer needs it for their records. "
            "Jeff: Can you briefly describe the reason for the sick note request? "
            "Caller: I put my back out lifting at work. Lower back pain, I can barely sit down. "
            "Jeff: Have you spoken to a doctor about this? "
            "Caller: Yes, I saw the GP on Monday. She said I needed rest. "
            "Jeff: Would workplace adjustments such as reduced hours or lighter duties help you return to work? "
            "Caller: Possibly, yes — lighter duties would help once the pain eases. "
            "Jeff: Let me check I have that right. New sick note for Daniel Clayton, date of birth eleventh December "
            "nineteen eighty-four. Period requested: nineteenth May to second June twenty twenty-six, approximately "
            "two weeks. Reason: lower back pain following work injury. For work use. GP already consulted. "
            "Callback number ending in 0358. Is that correct? "
            "Caller: Yes, that's all right. "
            "Jeff: Thank you. I've passed your request to the practice team for review. A member of the team may "
            "contact you if any further review is needed. Is there anything else? "
            "Caller: No, that's everything. "
            "Jeff: Thank you for calling Churchtown Medical Centre. Goodbye."
        ),
        caller_id_number="07111000358",
        call_duration_seconds=312,
    ),

    # --- Call 3: Test result query, blood test, cholesterol, 4 days ago, matched ---
    pack.make_call(
        BATCH, 3, "RESULTS-COLETTE-COOKSON",
        PATIENTS["383"],
        workflow="admin",
        request_type="test_result",
        transcript=(
            "Jeff: Good morning. I'll ask you a few quick questions so the practice team can review your request "
            "and contact you if needed. Is that okay? "
            "Caller: Yes, of course. "
            "Jeff: Are you calling about yourself or someone else? "
            "Caller: Myself, yes. "
            "Jeff: Please say one of the following: Prescription, Sick note, Referral, Test result, or Admin. "
            "Caller: Test result. "
            "Jeff: What test are you asking about? "
            "Caller: I had a blood test done. I'm mainly asking about my cholesterol levels. "
            "Jeff: Can I take your full name? "
            "Caller: Colette Cookson. "
            "Jeff: And your date of birth? "
            "Caller: Seventeenth December nineteen sixty. "
            "Jeff: I can see a number ending in 0383 — is that the best number for the practice to reach you? "
            "Caller: Yes. "
            "Jeff: Around what date was the test taken? "
            "Caller: Last Friday morning — so that would be the sixteenth. "
            "Jeff: Do you have a reference number for it? "
            "Caller: No, I don't think I was given one. "
            "Jeff: That's fine. Let me check I have that right. Test result query for Colette Cookson, date of birth "
            "seventeenth December nineteen sixty. Blood test taken approximately sixteenth May, asking about cholesterol. "
            "No reference number. Callback number ending in 0383. Is that correct? "
            "Caller: Yes, that's right. "
            "Jeff: Thank you. I've passed your request to the practice team. Is there anything else? "
            "Caller: No, that's all. Thank you. "
            "Jeff: Thank you for calling Churchtown Medical Centre. Goodbye."
        ),
        caller_id_number="07111000383",
        supplied_nhs_number="480 196 3218",
        call_duration_seconds=221,
    ),

    # --- Call 4: Referral — third-party, wife calling for husband, chasing existing orthopaedics ---
    pack.make_call(
        BATCH, 4, "REFERRAL-3RDPARTY-WALTER-COOKSON",
        PATIENTS["387"],
        workflow="admin",
        request_type="referral",
        transcript=(
            "Jeff: Good morning. I'll ask you a few quick questions so the practice team can review your request "
            "and contact you if needed. Is that okay? "
            "Caller: Yes, I'll try. I'm actually calling for my husband. "
            "Jeff: Are you calling about yourself or someone else? "
            "Caller: Someone else — my husband. "
            "Jeff: What is the patient's date of birth? "
            "Caller: Twenty-sixth June nineteen seventy-two. "
            "Jeff: And the patient's full name? "
            "Caller: Walter Cookson. "
            "Jeff: Can I take your full name? "
            "Caller: Anne Cookson. "
            "Jeff: And your relationship to the patient? "
            "Caller: I'm his wife. "
            "Jeff: I can see a number ending in 0387 on this call — is that the best number for the practice to reach you? "
            "Caller: Yes, that's Walter's mobile but he's asked me to handle this. "
            "Jeff: Please say one of the following: Prescription, Sick note, Referral, Test result, or Admin. "
            "Caller: Referral. "
            "Jeff: Are you chasing an existing referral, or requesting a new referral? "
            "Caller: Chasing an existing one. He was referred to orthopaedics about three weeks ago and we've heard nothing. "
            "Jeff: Which hospital is this referral to? "
            "Caller: Southport and Formby, I believe. "
            "Jeff: Around what date was the referral submitted? "
            "Caller: The GP mentioned it on the second of May. "
            "Jeff: Let me check I have this right. Chasing an existing orthopaedics referral for Walter Cookson, "
            "date of birth twenty-sixth June nineteen seventy-two, submitted approximately second May twenty twenty-six "
            "to Southport and Formby. Third-party call placed by Anne Cookson, his wife. Callback number ending in 0387. "
            "Is that correct? "
            "Caller: Yes, that's all right. "
            "Jeff: Thank you. I've passed this to the practice team. Is there anything else today? "
            "Caller: No, thank you. "
            "Jeff: Thank you for calling Churchtown Medical Centre. Goodbye."
        ),
        caller_for="wife",
        caller_id_number="07111000387",
        call_duration_seconds=275,
    ),

    # --- Call 5: Admin query — unknown caller, no match expected ---
    pack.make_call(
        BATCH, 5, "ADMIN-NOMATCH-UNKNOWN",
        # Use a non-existent patient via name_override / dob_override
        PATIENTS["482"],  # Phillip Doherty as base (won't be in lookup with wrong name)
        workflow="admin",
        request_type="admin",
        transcript=(
            "Jeff: Good morning. I'll ask you a few quick questions so the practice team can review your request "
            "and contact you if needed. Is that okay? "
            "Caller: Yes. "
            "Jeff: Are you calling about yourself or someone else? "
            "Caller: Myself. "
            "Jeff: Please say one of the following: Prescription, Sick note, Referral, Test result, or Admin. "
            "Caller: Admin. "
            "Jeff: Please briefly describe how the admin team may be able to assist you. "
            "Caller: I need to update my address. I moved house about a month ago and want to make sure the practice "
            "has the right address on file. "
            "Jeff: I can take your details so the admin team can update your record. Can I take your full name? "
            "Caller: Marcus Thornton. "
            "Jeff: And your date of birth? "
            "Caller: Third August nineteen seventy-nine. "
            "Jeff: I can see a number ending in 0482 on this call — is that the best number for the practice to reach you? "
            "Caller: That's not my number actually — I'm calling from a shared office phone. My mobile is "
            "zero seven nine zero zero one two three four five six. "
            "Jeff: Thank you. Let me check I have that right. Admin request to update address for Marcus Thornton, "
            "date of birth third August nineteen seventy-nine. Callback number zero seven nine zero zero one two three "
            "four five six. Is that correct? "
            "Caller: Yes, that's right. "
            "Jeff: Thank you. I've passed your request to the admin team. Is there anything else? "
            "Caller: No, that's all. "
            "Jeff: Thank you for calling Churchtown Medical Centre. Goodbye."
        ),
        name_override="Marcus Thornton",
        dob_override="1979-08-03",
        caller_id_number="07900123456",
        call_duration_seconds=198,
    ),
]


def main():
    print(f"Fresh 5-call batch: {BATCH}")
    print(f"Writing to: {LOCAL_ENCRYPTED_RAW_DIR}")
    print()

    for i, call in enumerate(CALLS, start=1):
        envelope = pack.encrypt_envelope(call)
        out_path = write_envelope_to_local_queue(envelope)
        print(f"[{i}/5] {call['request_type']} — {call['normalized_input']['patient_name']}")
        print(f"  call_id : {call['call_id']}")
        print(f"  dob     : {call['normalized_input']['dob']}")
        print(f"  callback: {call['normalized_input']['callback_number'] or '(withheld)'}")
        print(f"  out     : {out_path}")
        print()
        time.sleep(0.3)

    print("All 5 written. Triggering scheduled intake cycle...")
    trigger_scheduled_task()
    print("Done.")


if __name__ == "__main__":
    main()

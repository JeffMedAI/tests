import base64
import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


KEYS_DIR = Path(r"C:\JeffLocal\config\security\keys")
PUBLIC_KEY_PATH = KEYS_DIR / "jefflocal_public.pem"
HMAC_SECRET_PATH = KEYS_DIR / "voice_agent_hmac_secret.txt"

KEY_ID = "jefflocal-rsa-test-001"
SENDER_ID = "voice-agent-test"
PROTOCOL = "JEIE-1"
ALG = "RSA-OAEP-256+A256GCM"


PATIENTS = {
    "230": {"name": "Abdel Boumnijel", "dob": "1952-12-18", "nhs": "626 283 3153"},
    "231": {"name": "Elizabeth Boumnijel", "dob": "1949-06-19", "nhs": "452 864 7400"},
    "237": {"name": "Kevin Bradbury", "dob": "1982-06-03", "nhs": "620 925 5116"},
    "242": {"name": "Dorothy Bridge", "dob": "1942-01-31", "nhs": "440 929 0460"},
    "243": {"name": "Julie Chadwick", "dob": "1965-03-16", "nhs": "620 934 6707"},
    "246": {"name": "William Bridge", "dob": "1942-02-14", "nhs": "440 927 5321"},
    "299": {"name": "Kristina Osborn", "dob": "1962-03-29", "nhs": "478 697 4250"},
    "300": {"name": "Lois Cain", "dob": "1986-09-14", "nhs": "620 948 6118"},
    "301": {"name": "Steven Cain", "dob": "1988-10-15", "nhs": "620 929 4480"},
    "302": {"name": "John Caines", "dob": "1942-12-28", "nhs": "420 162 8132"},
    "308": {"name": "Paul Callister", "dob": "1958-11-10", "nhs": "480 193 7349"},
    "346": {"name": "Gavin Chong", "dob": "1972-06-19", "nhs": "620 918 8613"},
    "351": {"name": "Michael Clarke", "dob": "1949-05-28", "nhs": "452 864 6552"},
    "358": {"name": "Daniel Clayton", "dob": "1984-12-11", "nhs": "620 947 1668"},
    "360": {"name": "Paula Clayton", "dob": "1961-08-28", "nhs": "628 706 9686"},
    "372": {"name": "Alexandra Cohen", "dob": "1987-05-19", "nhs": "620 928 5732"},
    "383": {"name": "Colette Cookson", "dob": "1960-12-17", "nhs": "480 196 3218"},
    "387": {"name": "Walter Cookson", "dob": "1972-06-26", "nhs": "614 289 3299"},
    "396": {"name": "Kevin Corkhill", "dob": "1968-06-29", "nhs": "620 916 1340"},
    "482": {"name": "Phillip Doherty", "dob": "1985-02-13", "nhs": "620 948 2600"},
}


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def encrypt_envelope(inner_json):
    public_key = serialization.load_pem_public_key(PUBLIC_KEY_PATH.read_bytes())
    hmac_secret = HMAC_SECRET_PATH.read_text(encoding="utf-8").strip().encode("utf-8")

    plaintext = json.dumps(inner_json, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    aes_key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(aes_key)
    iv = os.urandom(12)

    encrypted = aesgcm.encrypt(iv, plaintext, None)
    ciphertext = encrypted[:-16]
    tag = encrypted[-16:]

    encrypted_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    envelope = {
        "protocol": PROTOCOL,
        "alg": ALG,
        "key_id": KEY_ID,
        "sender_id": SENDER_ID,
        "message_id": inner_json["call_id"],
        "timestamp_utc": utc_now_iso(),
        "nonce": str(uuid.uuid4()),
        "encrypted_key": base64.b64encode(encrypted_key).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
        "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        "tag": base64.b64encode(tag).decode("ascii"),
        "signature_alg": "HMAC-SHA256",
    }

    canonical = ".".join([
        envelope["protocol"],
        envelope["sender_id"],
        envelope["message_id"],
        envelope["timestamp_utc"],
        envelope["nonce"],
        envelope["key_id"],
        envelope["alg"],
        envelope["encrypted_key"],
        envelope["iv"],
        envelope["ciphertext"],
        envelope["tag"],
    ])

    signature = hmac.new(hmac_secret, canonical.encode("utf-8"), hashlib.sha256).digest()
    envelope["signature"] = base64.b64encode(signature).decode("ascii")
    return envelope


def make_call(
    batch,
    index,
    suffix,
    patient,
    workflow,
    request_type,
    transcript,
    meds=None,
    urgency_note="",
    pharmacy="",
    caller_for="self",
    caller_id_number="",
    supplied_nhs_number="",
    dob_override=None,
    name_override=None,
    call_duration_seconds=180,
):
    if meds is None:
        meds = []

    call_id = f"RX-LIVELOOKUP20-{batch}-{index:02d}-{suffix}"
    patient_name = name_override or patient["name"]
    dob = dob_override or patient["dob"]

    return {
        "call_id": call_id,
        "call_timestamp": utc_now_iso(),
        "workflow": workflow,
        "request_type": request_type,
        "source": "voice_agent",
        "voice_agent": {
            "agent_name": "Jeff Voice Agent",
            "session_id": f"VA-{call_id}",
            "caller_channel": "phone",
            "call_direction": "inbound",
            "call_duration_seconds": call_duration_seconds,
            "language": "en-GB",
            "caller_id_captured": bool(caller_id_number),
            "scenario": suffix,
        },
        "normalized_input": {
            "patient_name": patient_name,
            "dob": dob,
            "callback_number": caller_id_number,
            "medications_requested": meds,
            "urgency_note": urgency_note,
            "pharmacy": pharmacy,
            "caller_for": caller_for,
            "supplied_nhs_number": supplied_nhs_number,
        },
        "raw_transcript": transcript,
        "transcript_summary": transcript[:280] + ("..." if len(transcript) > 280 else ""),
        "assigned_to": "",
        "outcome_notes": "",
        "staff_action": "",
        "resolved_at": "",
        "resolved_by": "",
        "last_edited_at": "",
        "last_edited_by": "",
        "turnaround_minutes": "",
        "extraction_confidence": {
            "patient_name": 0.92,
            "dob": 0.91,
            "callback_number": 0.98 if caller_id_number else 0.0,
            "request_type": 0.89,
            "medications_requested": 0.87 if meds else 0.0,
            "pharmacy": 0.84 if pharmacy else 0.0,
            "supplied_nhs_number": 0.95 if supplied_nhs_number else 0.0,
        },
        "voice_agent_flags": {
            "caller_confirmed_callback": bool(caller_id_number),
            "caller_for_someone_else": caller_for != "self",
            "possible_urgent_supply_issue": request_type in [
                "urgent_repeat_prescription",
                "urgent_appointment_request",
                "red_flag_medication_request",
            ],
            "call_quality": "good",
        },
    }


def build_calls():
    batch = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    return [
        make_call(batch, 1, "REPEAT-ABDEL", PATIENTS["230"], "prescription", "repeat_prescription",
            "Jeff: Good morning, prescription assistant speaking. Caller: Hello, I need to order my repeat prescription please. Jeff: Can I take your full name? Caller: Abdel Boumnijel. Jeff: Can you confirm your date of birth? Caller: Eighteenth December nineteen fifty two. Jeff: Which medicine do you need? Caller: Atorvastatin twenty milligrams. Jeff: Which pharmacy should this go to? Caller: Test Pharmacy. Jeff: I can see your caller ID ending in 0230; is this number okay for callback? Caller: Yes, that is fine. Jeff: Thank you, I will pass this to the practice team.",
            meds=["atorvastatin 20mg"], pharmacy="Test Pharmacy", caller_id_number="07111000230", call_duration_seconds=175),

        make_call(batch, 2, "SICKNOTE-ELIZABETH", PATIENTS["231"], "admin", "sick_note_request",
            "Jeff: How can I help today? Caller: I need a sick note for work. Jeff: I can take the details. What is your full name? Caller: Elizabeth Boumnijel. Jeff: Date of birth? Caller: Nineteenth June nineteen forty nine. Jeff: What period do you need covered? Caller: From Monday last week to this Friday after a chest infection. Jeff: Have you spoken to a clinician about this? Caller: Yes, last week. Jeff: I have captured your caller ID for callback. I will pass this to the admin team.",
            caller_id_number="07111000231", call_duration_seconds=215),

        make_call(batch, 3, "REFERRAL-KEVIN-BRADBURY", PATIENTS["237"], "admin", "referral_query",
            "Jeff: What can I help with? Caller: I am calling about a hospital referral. Jeff: Can I confirm your name and date of birth? Caller: Kevin Bradbury, third June nineteen eighty two. Jeff: What referral is this about? Caller: Orthopaedics for my shoulder. The GP mentioned it about three weeks ago but I have not heard anything. Jeff: I have your caller ID and will pass this to the referrals team.",
            caller_id_number="07111000237", supplied_nhs_number="620 925 5116", call_duration_seconds=230),

        make_call(batch, 4, "RESULTS-DOROTHY", PATIENTS["242"], "admin", "test_results_query",
            "Jeff: How can I help? Caller: I am calling for my blood test results. Jeff: Can I take your full name? Caller: Dorothy Bridge. Jeff: Date of birth? Caller: Thirty first January nineteen forty two. Jeff: When did you have the blood test? Caller: Last Thursday morning. I am mostly asking about kidney function. Jeff: I have captured your callback number from caller ID and will pass this to the results team.",
            caller_id_number="07111000242", call_duration_seconds=190),

        make_call(batch, 5, "ADMIN-JULIE", PATIENTS["243"], "admin", "admin_query",
            "Jeff: What can I help with today? Caller: I need to ask whether a letter from the hospital has arrived. Jeff: Can I take your full name? Caller: Julie Chadwick. Jeff: Date of birth? Caller: Sixteenth March nineteen sixty five. Jeff: Do you know which hospital department? Caller: Cardiology, I think. Jeff: I have the caller ID for callback. I will pass this to the admin team.",
            caller_id_number="07111000243", supplied_nhs_number="620 934 6707", call_duration_seconds=180),

        make_call(batch, 6, "HOUSEHOLD-BRIDGE-WILLIAM", PATIENTS["246"], "prescription", "repeat_prescription",
            "Jeff: Prescription assistant speaking. Caller: I need my repeat medication. Jeff: Can I take your full name? Caller: William Bridge. Jeff: Date of birth? Caller: Fourteenth February nineteen forty two. Jeff: Which medication? Caller: Amlodipine five milligrams. Jeff: Which pharmacy? Caller: Test Pharmacy. Jeff: I have captured the caller ID for callback. Caller: That is fine.",
            meds=["amlodipine 5mg"], pharmacy="Test Pharmacy", caller_id_number="07111000246", call_duration_seconds=185),

        make_call(batch, 7, "MEDQUERY-KRISTINA", PATIENTS["299"], "prescription", "medication_query",
            "Jeff: How can I help? Caller: I have a question about my tablets. Jeff: Can I confirm your name? Caller: Kristina Osborn. Jeff: Date of birth? Caller: Twenty ninth March nineteen sixty two. Jeff: What medication is this about? Caller: Sertraline fifty milligrams. I missed three doses and I am not sure whether to restart. Jeff: Are you feeling unsafe or at risk of harming yourself? Caller: No, I just need advice. Jeff: I will pass this medication query to the team.",
            meds=["sertraline 50mg"], caller_id_number="07111000299", call_duration_seconds=225),

        make_call(batch, 8, "APPT-LOIS-CAIN", PATIENTS["300"], "clinical_admin", "appointment_request",
            "Jeff: How can I help today? Caller: I would like to book an appointment. Jeff: Can I take your name? Caller: Lois Cain. Jeff: Date of birth? Caller: Fourteenth September nineteen eighty six. Jeff: What is the appointment about? Caller: Ongoing headaches, not severe today, but I would like to speak to a GP. Jeff: I have captured your callback number from caller ID. I will pass this request to the team.",
            caller_id_number="07111000300", call_duration_seconds=200),

        make_call(batch, 9, "URGENT-APPT-STEVEN-CAIN", PATIENTS["301"], "clinical_admin", "urgent_appointment_request",
            "Jeff: How can I help? Caller: I need urgent advice. I have chest tightness and I feel more breathless than usual. Jeff: If symptoms are severe or you feel unsafe, seek urgent medical help. I can pass this urgently to the practice team. Can I confirm your name and date of birth? Caller: Steven Cain, fifteenth October nineteen eighty eight. Jeff: I have captured your callback number from caller ID. I will mark this for urgent review.",
            caller_id_number="07111000301", call_duration_seconds=260),

        make_call(batch, 10, "SIMILAR-CAINES-JOHN", PATIENTS["302"], "admin", "admin_query",
            "Jeff: Can I take your full name? Caller: John Caines. Jeff: Date of birth? Caller: Twenty eighth December nineteen forty two. Jeff: How can I help? Caller: I need to ask about a form I dropped off. Jeff: I have captured your callback number. I will pass this to the admin team.",
            caller_id_number="07111000302", call_duration_seconds=160),

        make_call(batch, 11, "REPEAT-PAUL-CALLISTER", PATIENTS["308"], "prescription", "repeat_prescription",
            "Jeff: Prescription assistant. Caller: I need a repeat prescription. Jeff: Name please? Caller: Paul Callister. Jeff: Date of birth? Caller: Tenth November nineteen fifty eight. Jeff: Which medicine? Caller: Ramipril five milligrams. Jeff: Which pharmacy? Caller: Test Pharmacy. Jeff: I have captured the caller ID for callback.",
            meds=["ramipril 5mg"], pharmacy="Test Pharmacy", caller_id_number="07111000308", supplied_nhs_number="480 193 7349", call_duration_seconds=170),

        make_call(batch, 12, "REFERRAL-GAVIN", PATIENTS["346"], "admin", "referral_query",
            "Jeff: How can I help? Caller: I am chasing a dermatology referral. Jeff: Can I take your name? Caller: Gavin Chong. Jeff: Date of birth? Caller: Nineteenth June nineteen seventy two. Jeff: When was it discussed? Caller: Around two weeks ago. Jeff: I have your callback from caller ID and will ask the referrals team to check.",
            caller_id_number="07111000346", call_duration_seconds=210),

        make_call(batch, 13, "WRONG-DOB-MICHAEL-CLARKE", PATIENTS["351"], "prescription", "repeat_prescription",
            "Jeff: Can I take your name? Caller: Michael Clarke. Jeff: Date of birth? Caller: Twenty eighth May nineteen fifty, I think. Jeff: Which medication? Caller: Lansoprazole fifteen milligrams. Jeff: Pharmacy? Caller: Test Pharmacy. Jeff: I have captured your caller ID. I will pass this to the team for checking.",
            meds=["lansoprazole 15mg"], pharmacy="Test Pharmacy", caller_id_number="07111000351", dob_override="1950-05-28", call_duration_seconds=180),

        make_call(batch, 14, "NO-CALLBACK-DANIEL-CLAYTON", PATIENTS["358"], "prescription", "repeat_prescription",
            "Jeff: Can I take your name? Caller: Daniel Clayton. Jeff: Date of birth? Caller: Eleventh December nineteen eighty four. Jeff: Which medication do you need? Caller: Simvastatin forty milligrams. Jeff: I cannot see a caller ID on this call. Is there a callback number? Caller: I would rather not give one now. Jeff: The team may need to contact you if there is a query. Caller: I understand.",
            meds=["simvastatin 40mg"], pharmacy="Test Pharmacy", caller_id_number="", call_duration_seconds=185),

        make_call(batch, 15, "THIRD-PARTY-PAULA", PATIENTS["360"], "prescription", "third_party_repeat_prescription",
            "Jeff: Are you calling for yourself today? Caller: No, I am calling for my wife, Paula Clayton. Jeff: What is Paula's date of birth? Caller: Twenty eighth August nineteen sixty one. Jeff: Which medication does she need? Caller: Levothyroxine fifty micrograms. Jeff: Which pharmacy? Caller: Test Pharmacy. Jeff: I have captured the callback number from caller ID and will note this is a third-party call.",
            meds=["levothyroxine 50mcg"], pharmacy="Test Pharmacy", caller_for="husband", caller_id_number="07111000360", call_duration_seconds=225),

        make_call(batch, 16, "REGISTRATION-ALEXANDRA", PATIENTS["372"], "admin", "registration_query",
            "Jeff: How can I help? Caller: I want to check whether my registration has gone through. Jeff: Can I take your full name? Caller: Alexandra Cohen. Jeff: Date of birth? Caller: Nineteenth May nineteen eighty seven. Jeff: When did you submit the forms? Caller: Last week online. Jeff: I have captured your callback number and will pass this to registrations.",
            caller_id_number="07111000372", call_duration_seconds=190),

        make_call(batch, 17, "RESULTS-COLETTE", PATIENTS["383"], "admin", "test_results_query",
            "Jeff: How can I help today? Caller: I am calling about my urine test result. Jeff: Can I take your name? Caller: Colette Cookson. Jeff: Date of birth? Caller: Seventeenth December nineteen sixty. Jeff: When was the sample given? Caller: Monday morning. Jeff: I have captured your caller ID and will pass this to the results team.",
            caller_id_number="07111000383", supplied_nhs_number="480 196 3218", call_duration_seconds=185),

        make_call(batch, 18, "HOUSEHOLD-WALTER-COOKSON", PATIENTS["387"], "admin", "referral_query",
            "Jeff: Can I take your name? Caller: Walter Cookson. Jeff: Date of birth? Caller: Twenty sixth June nineteen seventy two. Jeff: How can I help? Caller: I am chasing a cardiology referral. My wife has also called about test results recently, so please make sure this is under my record. Jeff: I have captured your caller ID and will pass this to referrals.",
            caller_id_number="07111000387", call_duration_seconds=205),

        make_call(batch, 19, "RED-FLAG-KEVIN-CORKHILL", PATIENTS["396"], "clinical_admin", "urgent_appointment_request",
            "Jeff: How can I help? Caller: I need urgent advice. I have chest pain and feel sweaty. Jeff: If you have chest pain and feel unwell, you should seek urgent medical help now. I can also pass this urgently to the practice team. Can I confirm your name and date of birth? Caller: Kevin Corkhill, twenty ninth June nineteen sixty eight. Jeff: I have captured your caller ID. I will mark this as urgent.",
            caller_id_number="07111000396", call_duration_seconds=250),

        make_call(batch, 20, "NO-NHS-PHILLIP-DOHERTY", PATIENTS["482"], "admin", "admin_query",
            "Jeff: How can I help today? Caller: I need a copy of a letter from my records. Jeff: Can I take your full name? Caller: Phillip Doherty. Jeff: Date of birth? Caller: Thirteenth February nineteen eighty five. Jeff: Do you know your NHS number? Caller: No, I do not have it with me. Jeff: I have captured your callback number from caller ID and will pass this to admin.",
            caller_id_number="07111000482", supplied_nhs_number="", call_duration_seconds=175),
    ]


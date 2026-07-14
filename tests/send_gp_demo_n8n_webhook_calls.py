from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT_DIR / "tests" / "fixtures"
for path in (ROOT_DIR, FIXTURE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from live_lookup_test_payloads import encrypt_envelope  # noqa: E402

try:  # noqa: E402
    from app.decrypt_encrypted_raw import decrypt_envelope as local_decrypt_envelope  # type: ignore
except Exception:  # pragma: no cover - local fallback only
    local_decrypt_envelope = None

try:  # noqa: E402
    from n8n_webhook_test_pack import build_batch as build_n8ntest_batch  # type: ignore
except Exception:  # pragma: no cover - local fallback only
    build_n8ntest_batch = None


DEFAULT_WEBHOOK_URL = "http://localhost:5678/webhook/ava-live-intake"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
REQUIRED_ENVELOPE_FIELDS = {
    "protocol",
    "alg",
    "key_id",
    "sender_id",
    "message_id",
    "timestamp_utc",
    "nonce",
    "encrypted_key",
    "iv",
    "ciphertext",
    "tag",
    "signature_alg",
    "signature",
}


def is_local_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.hostname in LOCAL_HOSTS


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


_SLICE_OFFSET: int = 0
_SLICE_LIMIT: int | None = None


def transcript_blocks() -> list[dict[str, str]]:
    return [
        {
            "suffix": "001-PRESCRIPTION",
            "request_type": "prescription",
            "stated_request": "Repeat prescription requested for atorvastatin 20mg. Caller says there are two tablets left and asks for the prescription to be sent to the nominated pharmacy today.",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "staff_review_required": False,
            "red_flags_present": False,
            "patient_name": "Jason Morrey",
            "dob": "1970-01-10",
            "postcode": "PR9 7LT",
            "callback_number": "07111000001",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Routine repeat prescription request. Caller reported no urgent symptoms and provided a callback number.",
            "summary": "Routine repeat prescription request for atorvastatin 20mg. Caller reported two tablets left and no urgent symptoms.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I need my repeat "
                "prescription please, atorvastatin 20 milligrams. I have two tablets left and I am trying not to run "
                "out. Agent: Thank you. Have you had any chest pain, breathlessness, sweating, fainting, or any other "
                "urgent symptoms? Caller: No, nothing like that. I just need the medication renewed in time. Agent: "
                "Can I confirm your callback number and a couple of details so the practice can review the request? "
                "Caller: Yes, the callback is 07111000001 and my details are up to date. Agent: Thank you, I will "
                "pass this routine repeat prescription request to the practice team using the local demo workflow. "
                "Caller: Fine, thank you."
            ),
        },
        {
            "suffix": "002-SICKNOTE",
            "request_type": "sick_note",
            "stated_request": "Fit note requested after a viral illness absence. Caller says they need documentation for work and understands staff review is required before anything is issued.",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Mathew Morrey",
            "dob": "1978-09-15",
            "postcode": "PR9 7LT",
            "callback_number": "07111000002",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Fit note request. Caller understood the request will need staff review before completion.",
            "summary": "Fit note request after viral illness absence. Caller understands staff review is required before issue.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I need a fit note "
                "because I have been off work with a viral illness. Agent: I can help capture the request. Have your "
                "symptoms worsened or do you have any red flag symptoms such as chest pain or breathlessness? Caller: "
                "No, I just need the note because I am still not well enough to go back. Agent: Thank you. Please "
                "confirm a callback number and any relevant dates so the team can review the request. Caller: The "
                "callback is 07111000002 and I missed work from Monday. Agent: I will pass this fit note request to "
                "the practice team for staff review."
            ),
        },
        {
            "suffix": "003-REFERRAL",
            "request_type": "referral",
            "stated_request": "Referral follow-up requested for orthopaedics. Caller wants to know whether the referral has been sent and whether there is any update from the practice team.",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Peter Morrey",
            "dob": "1978-09-15",
            "postcode": "PR9 7LT",
            "callback_number": "07111000003",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Referral follow-up request. Staff review is required before any update is provided.",
            "summary": "Referral follow-up for orthopaedics. Caller is chasing whether the referral has been sent.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I am calling about "
                "a referral I was meant to have for orthopaedics. Agent: Thanks. Do you have any new symptoms or "
                "urgent problems today? Caller: No, I just want to know whether the referral has gone through. "
                "Agent: Can I confirm your callback number so the team can review the record and respond? Caller: "
                "Yes, it is 07111000003. Agent: I will pass this referral follow-up to the practice team for review "
                "using the local demo workflow."
            ),
        },
        {
            "suffix": "004-IDENTITY",
            "request_type": "admin",
            "stated_request": "Third-party caller gave partial details for another patient. Identity review is required before any discussion or processing can happen.",
            "verification_status": "possible_match",
            "priority": "review_required",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Jayson Morrey",
            "dob": "1970-01-10",
            "postcode": "PR9 7LT",
            "callback_number": "07111000004",
            "caller_for": "third_party",
            "caller_relationship": "third_party",
            "pathway_response": "Identity could not be confirmed from the transcript. Staff review required before processing.",
            "summary": "Third-party caller gave partial details only. Identity review is required before processing.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm who the request is for? Caller: It is for my brother, I "
                "think he is called Michael, but I am not sure of the full details. Agent: For safety, I need the "
                "patient's details or an authorised callback before the practice can discuss anything. Caller: I do "
                "not have all of that with me right now, I can call back later. Agent: That is fine, please leave a "
                "callback number and the practice will review the request. Caller: The callback is 07111000004. "
                "Agent: Thank you. I will mark this as an identity review case and pass it to staff."
            ),
        },
        {
            "suffix": "005-REDFLAG",
            "request_type": "appointment_redirect",
            "stated_request": "Possible emergency symptoms reported: chest pain, breathlessness and sweating. Caller was advised to call 999 immediately and not to wait for routine practice contact.",
            "verification_status": "matched",
            "priority": "999 Emergency",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": True,
            "patient_name": "Geoffrey Mynne",
            "dob": "1941-02-21",
            "postcode": "PR9 7LT",
            "callback_number": "07111000005",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Emergency symptoms identified. Caller advised to call 999 immediately.",
            "summary": "Possible emergency symptoms identified. Caller advised to call 999 immediately.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I am not feeling "
                "right, I have chest pain and I am short of breath. Agent: Are you alone, and are you feeling sweaty "
                "or faint as well? Caller: Yes, I am sweating and I feel worse when I move. Agent: This sounds "
                "urgent. Please call 999 now for emergency help and do not wait for a routine callback. Caller: "
                "Okay, I will call 999 right now. Agent: I am recording this as an emergency red-flag case for the "
                "practice record, but the immediate instruction is to seek emergency help first."
            ),
        },
        {
            "suffix": "006-MULTI-INTENT",
            "request_type": "needs_review",
            "stated_request": "Caller raised several things at once — a repeat prescription, chasing a referral, and a form for work — rambling and hard to follow.",
            "verification_status": "matched",
            "priority": "review_required",
            "safe_to_queue": True,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Neil Coulton",
            "dob": "1965-10-09",
            "postcode": "PR9 8AA",
            "callback_number": "07700900006",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Multiple unrelated requests in one call. Needs a human to untangle and route each item.",
            "summary": "Caller raised several requests at once. Staff review needed to separate and route each item.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: Right, a few things, "
                "sorry. I need my repeat tablets, and I also wanted to check on a referral, the one for my knee, and my "
                "wife said I should ask about a form for work as well. Agent: That is fine, I will capture all of it. "
                "First, can I confirm your name and date of birth? Caller: Neil Coulton, ninth of October nineteen "
                "sixty-five. Agent: Thank you. Have you had any urgent symptoms today, chest pain, breathlessness, "
                "anything like that? Caller: No, no, nothing like that, I am just juggling a lot. Agent: Understood. I "
                "will note the prescription, the knee referral query, and the work form request together and pass them "
                "to the team to sort out. Caller: Great, thanks, sorry it is all at once."
            ),
        },
        {
            "suffix": "007-UNKNOWN-PATHWAY",
            "request_type": "unknown",
            "stated_request": "Caller is vague and unsure what they need or who to speak to; no clear pathway.",
            "verification_status": "matched",
            "priority": "review_required",
            "safe_to_queue": True,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Colette Cookson",
            "dob": "1960-12-17",
            "postcode": "PR8 2BB",
            "callback_number": "07700900007",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Caller could not state a clear request. Unknown pathway, staff review required.",
            "summary": "Caller unsure what they needed. No clear pathway identified; staff to call back and clarify.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I am not really sure "
                "to be honest, someone told me to ring the surgery but I do not know who I am meant to speak to. Agent: "
                "That is alright, I can take some details and pass it on. Can I confirm your name and date of birth? "
                "Caller: Colette Cookson, seventeenth of December nineteen sixty. Agent: Thank you. Is there anything "
                "urgent or any symptoms worrying you today? Caller: No, nothing urgent, I just had a letter I think and "
                "I did not understand it. Agent: No problem. I will log this as a general query for the team to review "
                "and call you back to clarify what you need. Caller: Yes, that would be helpful, thank you."
            ),
        },
        {
            "suffix": "008-THIRD-PARTY",
            "request_type": "admin",
            "stated_request": "A brother is calling about a patient but cannot provide the date of birth; identity cannot be confirmed.",
            "verification_status": "insufficient_data",
            "priority": "review_required",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Paul Callister",
            "dob": "",
            "postcode": "PR9 7LT",
            "callback_number": "07700900008",
            "caller_for": "third_party",
            "caller_relationship": "third_party",
            "pathway_response": "Third-party caller without patient date of birth. Identity check required before anything is actioned.",
            "summary": "Brother calling on behalf of a patient but could not confirm date of birth. Identity review required.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm who the request is for? Caller: It is for my brother, Paul "
                "Callister, he asked me to ring on his behalf. Agent: Thank you. For safety I need to confirm his "
                "details. Can you give me his date of birth? Caller: Ah, I do not actually know it off the top of my "
                "head, sorry. He lives on the same road as me though. Agent: I understand, but without confirming his "
                "date of birth I cannot verify the record or discuss anything. Caller: That is fair enough. Can "
                "someone call him directly? Agent: Yes, I will record this as a third-party request that needs an "
                "identity check, and the team will contact the patient on a confirmed number. Caller: Okay, thank you."
            ),
        },
        {
            "suffix": "009-INSUFFICIENT-ID",
            "request_type": "prescription",
            "stated_request": "Caller wants a prescription but declines to give a date of birth, so identity cannot be verified.",
            "verification_status": "insufficient_data",
            "priority": "review_required",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Kristina Osborn",
            "dob": "",
            "postcode": "PR8 3CC",
            "callback_number": "07700900009",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Caller declined to provide date of birth. Insufficient identity details for safe matching.",
            "summary": "Caller requested a prescription but would not confirm date of birth. Cannot verify identity.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I need my usual "
                "prescription sorting out please. Agent: Of course. Can I take your name and date of birth to find the "
                "record? Caller: Kristina Osborn. I would rather not give my date of birth over the phone if that is "
                "alright. Agent: I understand the concern, but I am not able to verify the record or pass the request "
                "safely without confirming your date of birth. Caller: I really do not want to say it. Agent: That is "
                "your choice. I will log the request but mark that identity could not be confirmed, and the team will "
                "call you back to verify securely before anything is actioned. Caller: Fine, whatever is easiest."
            ),
        },
        {
            "suffix": "010-NO-MATCH",
            "request_type": "admin",
            "stated_request": "Caller gives full details but the patient is not found in the practice reference data.",
            "verification_status": "no_match",
            "priority": "review_required",
            "safe_to_queue": True,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Marcus Fenwick",
            "dob": "1990-03-03",
            "postcode": "PR9 9DD",
            "callback_number": "07700900010",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Full details supplied but no matching patient exists in the lookup. Possible wrong surgery.",
            "summary": "Caller provided full details but no matching patient record found. Staff to check registration.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I need to update my "
                "address on my record please. Agent: Certainly. Can I confirm your name and date of birth? Caller: "
                "Marcus Fenwick, third of March nineteen ninety. Agent: Thank you. And any urgent symptoms today? "
                "Caller: No, nothing like that, purely admin. Agent: Let me check the record. I am not finding a match "
                "for those details on our system. Are you definitely registered at this practice? Caller: I think so, "
                "I moved recently, maybe it has not gone through. Agent: That may be it. I will pass this to the team "
                "as an unmatched record so they can check your registration before updating anything. Caller: Okay."
            ),
        },
        {
            "suffix": "011-CARER-PROXY",
            "request_type": "sick_note",
            "stated_request": "A carer calls for an elderly parent, giving a nickname and the correct date of birth; name is close but not exact.",
            "verification_status": "possible_match",
            "priority": "review_required",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Dot Bridge",
            "dob": "1942-01-31",
            "postcode": "PR9 7LT",
            "callback_number": "07700900011",
            "caller_for": "carer",
            "caller_relationship": "carer",
            "pathway_response": "Carer for elderly parent. Date of birth matches but stated name is a nickname; not an exact match.",
            "summary": "Carer calling for elderly mother. DOB matches record but name is a nickname. Possible match, needs review.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm who the request is for? Caller: It is for my mum, I look "
                "after her. She needs a fit note renewing for her carer's allowance paperwork. Agent: Thank you. Can I "
                "confirm her name and date of birth? Caller: Everyone calls her Dot Bridge, and her date of birth is "
                "the thirty-first of January nineteen forty-two. Agent: Thank you. Any urgent symptoms or changes in "
                "her health today? Caller: No, she is her usual self, this is just paperwork. Agent: Understood. The "
                "date of birth matches a record but the name is slightly different, so I will mark this as a possible "
                "match for staff to verify before issuing anything. Caller: Yes, her proper name is Dorothy. Thank you."
            ),
        },
        {
            "suffix": "012-MISMATCH-NAME-DOB",
            "request_type": "prescription",
            "stated_request": "Caller's stated name matches a record but the date of birth they give does not agree with it.",
            "verification_status": "needs_review",
            "priority": "review_required",
            "safe_to_queue": True,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Steven Cain",
            "dob": "1990-01-01",
            "postcode": "PR8 4EE",
            "callback_number": "07700900012",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Name matches a record but the supplied date of birth conflicts with it. Identity not safe to auto-confirm.",
            "summary": "Caller name matches a record but stated date of birth conflicts. Needs staff verification.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I need a repeat of "
                "my inhaler please. Agent: Of course. Can I take your name and date of birth? Caller: Steven Cain, and "
                "I was born on the first of January nineteen ninety. Agent: Thank you. Any urgent symptoms today, "
                "breathlessness or wheeze that is worse than usual? Caller: No, it is just a routine top-up. Agent: "
                "Let me check. I can see a Steven Cain on the system but the date of birth you gave does not match what "
                "is on the record, so I am not able to confirm your identity automatically. Caller: Oh, maybe I said "
                "it wrong. Agent: No problem, I will mark this for staff to verify your details before processing the "
                "request. Caller: Alright, thank you."
            ),
        },
        {
            "suffix": "013-REDFLAG-CARDIAC",
            "request_type": "appointment_redirect",
            "stated_request": "Caller reports chest pain, breathlessness and sweating — possible cardiac emergency.",
            "verification_status": "matched",
            "priority": "999 Emergency",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": True,
            "patient_name": "William Bridge",
            "dob": "1942-02-14",
            "postcode": "PR9 7LT",
            "callback_number": "07700900013",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Cardiac red flags spoken: chest pain, breathlessness, sweating. Caller advised to call 999.",
            "summary": "Caller reported chest pain, breathlessness and sweating. Advised to call 999 immediately.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I have got a really "
                "bad pain in my chest and I cannot catch my breath. Agent: Can I confirm your name and date of birth? "
                "Caller: William Bridge, fourteenth of February nineteen forty-two. Agent: Thank you. Are you sweating "
                "or feeling faint as well? Caller: Yes, I am pouring with sweat and it is going into my left arm. "
                "Agent: This may be a medical emergency. Please hang up and call 999 now for an ambulance, do not wait "
                "for a callback. Caller: Alright, alright, I will ring them now. Agent: I am recording this as an "
                "emergency red-flag case for the practice record, but your priority is to call 999 immediately."
            ),
        },
        {
            "suffix": "014-REDFLAG-STROKE",
            "request_type": "appointment_redirect",
            "stated_request": "Caller describes facial droop, arm weakness and slurred speech — possible stroke (FAST).",
            "verification_status": "matched",
            "priority": "999 Emergency",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": True,
            "patient_name": "Daniel Clayton",
            "dob": "1984-12-11",
            "postcode": "PR8 5FF",
            "callback_number": "07700900014",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Stroke red flags spoken: face droop, arm weakness, slurred speech. Caller advised to call 999.",
            "summary": "Caller described facial droop, arm weakness and slurred speech. Advised to call 999 immediately.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: Something is wrong "
                "with my face, one side has dropped and my arm has gone weak. Agent: Can I confirm your name and date "
                "of birth? Caller: Daniel Clayton, eleventh of December nineteen eighty-four. My speech has gone funny "
                "too, I sound slurred. Agent: These are signs of a possible stroke. Please call 999 immediately, this "
                "is an emergency and time matters. Caller: Okay, my partner is dialling now. Agent: Good. I am logging "
                "this as an emergency red-flag case for the record, but the immediate action is emergency services on "
                "999 right now. Caller: They are ringing them, thank you."
            ),
        },
        {
            "suffix": "015-REDFLAG-SEPSIS",
            "request_type": "appointment_redirect",
            "stated_request": "Caller reports high fever, confusion, rapid breathing and mottled skin — possible sepsis.",
            "verification_status": "matched",
            "priority": "999 Emergency",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": True,
            "patient_name": "Paula Clayton",
            "dob": "1961-08-28",
            "postcode": "PR9 6GG",
            "callback_number": "07700900015",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Sepsis red flags spoken: high fever, confusion, rapid breathing, mottled skin. Advised 999.",
            "summary": "Caller reported high fever, confusion, rapid breathing and mottled skin. Advised to call 999.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I feel terrible, I "
                "am burning up with a fever and I keep getting confused about where I am. Agent: Can I confirm your "
                "name and date of birth? Caller: Paula Clayton, twenty-eighth of August nineteen sixty-one. My "
                "breathing is really fast and my skin has gone blotchy and mottled. Agent: These symptoms together can "
                "be very serious. Please call 999 now, this may be sepsis and needs emergency assessment. Caller: "
                "Okay, I did not realise it was that bad. Agent: Please ring 999 immediately. I am recording an "
                "emergency red-flag case for the record, but emergency services come first. Caller: I am calling now."
            ),
        },
        {
            "suffix": "016-REDFLAG-MHCRISIS",
            "request_type": "appointment_redirect",
            "stated_request": "Caller expresses active suicidal intent — mental health emergency.",
            "verification_status": "matched",
            "priority": "999 Emergency",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": True,
            "patient_name": "Emma Ball",
            "dob": "1981-09-02",
            "postcode": "PR8 7HH",
            "callback_number": "07700900016",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Mental-health red flag spoken: active suicidal intent. Caller advised to seek emergency help / call 999.",
            "summary": "Caller expressed active suicidal intent. Signposted to emergency help and 999 / crisis line.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: I do not think I "
                "can carry on, I have been thinking about ending my life and I have a plan. Agent: Thank you for "
                "telling me, I want to make sure you are safe. Can I confirm your name and date of birth? Caller: Emma "
                "Ball, second of September nineteen eighty-one. Agent: Emma, because you have told me you have a plan "
                "to harm yourself, this is an emergency. Please call 999 now, or I can stay with you while you contact "
                "the crisis team. Caller: I do not know. Agent: Your safety matters. Please ring 999 or the Samaritans "
                "on 116 123 right now. I am flagging this as an emergency for the team to follow up urgently as well. "
                "Caller: Okay, I will ring the crisis number."
            ),
        },
        {
            "suffix": "017-ANGRY-ABUSIVE",
            "request_type": "admin",
            "stated_request": "Hostile, demanding caller wants an urgent answer; abusive tone but request is captured calmly.",
            "verification_status": "matched",
            "priority": "routine",
            "safe_to_queue": True,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Kevin Corkhill",
            "dob": "1968-06-29",
            "postcode": "PR9 5JJ",
            "callback_number": "07700900017",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Angry, demanding caller. No clinical red flags. Captured calmly; flagged for staff handling.",
            "summary": "Hostile caller demanding an update. No red flags. Request captured; flagged for staff to handle.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: About time, I have "
                "been trying to get through for days, this is an absolute joke. Agent: I am sorry for the frustration. "
                "I can take the details now. Can I confirm your name and date of birth? Caller: Kevin Corkhill, "
                "twenty-ninth of June nineteen sixty-eight, and I want this sorted today, not next week. Agent: "
                "Understood. Are you having any urgent symptoms I should know about? Caller: No, I am just sick of "
                "being ignored about my paperwork. Agent: I hear you. I will log your admin request and flag that you "
                "would like a prompt callback. Caller: You had better, this is ridiculous. Agent: Noted, I have "
                "captured it for the team."
            ),
        },
        {
            "suffix": "018-CONFUSED-ELDERLY",
            "request_type": "prescription",
            "stated_request": "Elderly caller repeats themselves and gives a nickname with the correct date of birth; name not exact.",
            "verification_status": "possible_match",
            "priority": "review_required",
            "safe_to_queue": True,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Wally Cookson",
            "dob": "1972-06-26",
            "postcode": "PR8 6KK",
            "callback_number": "07700900018",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Elderly caller, loses thread and uses a nickname. DOB matches record but name is not exact.",
            "summary": "Confused elderly caller wanting tablets. DOB matches but name is a nickname. Possible match, needs review.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: Oh hello, yes, it "
                "is about my tablets, the little white ones, or are they the pink, I forget. Agent: That is alright. "
                "Can I take your name and date of birth? Caller: They call me Wally Cookson, and my birthday, let me "
                "think, twenty-sixth of June nineteen seventy-two. Agent: Thank you. Any urgent symptoms today? "
                "Caller: No, no, I just keep running low, I forget to order, you see. Agent: No problem. What was it "
                "you needed again? Caller: The tablets, for my blood pressure I think. Agent: I will note a "
                "prescription request. Your date of birth matches a record but the name is a little different, so I "
                "will mark it for staff to check. Caller: Righto, thank you dear."
            ),
        },
        {
            "suffix": "019-NON-NATIVE-EN",
            "request_type": "sick_note",
            "stated_request": "Caller with limited English, broken phrasing, asking for a sick note; details are parseable.",
            "verification_status": "matched",
            "priority": "review_required",
            "safe_to_queue": True,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Samantha Sunners",
            "dob": "1983-07-16",
            "postcode": "PR9 4LL",
            "callback_number": "07700900019",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Limited-English caller. Name and DOB parseable and matched. Staff review to confirm understanding.",
            "summary": "Caller with limited English requesting a sick note. Details matched. Staff review to confirm needs.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: Please, I need "
                "paper for my work, the sick paper, because I am not good to go. Agent: A fit note, I understand. Can "
                "I take your name and date of birth? Caller: Yes yes, name Samantha Sunners, birthday sixteen July "
                "nineteen eighty-three. Agent: Thank you. Do you have any urgent problem, pain in chest, hard to "
                "breathe? Caller: No no, no chest, only I am tired and my stomach not good many days. Agent: Okay. I "
                "note you would like a fit note. Because there are some details to confirm, I will pass this to the "
                "team to review and call you back. Caller: Thank you, thank you, you call me please. Agent: Yes, we "
                "will call you back."
            ),
        },
        {
            "suffix": "020-CHILD-CALLER",
            "request_type": "appointment_redirect",
            "stated_request": "A child is calling on behalf of a parent and cannot give a date of birth; safeguarding note applies.",
            "verification_status": "insufficient_data",
            "priority": "review_required",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Jean Cottrell",
            "dob": "",
            "postcode": "PR8 8MM",
            "callback_number": "07700900020",
            "caller_for": "third_party",
            "caller_relationship": "child",
            "pathway_response": "Minor calling for a parent, no date of birth. Third-party plus safeguarding consideration.",
            "summary": "Child calling for a parent without a date of birth. Identity review and safeguarding note required.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm who the request is for? Caller: It is for my mummy, she "
                "asked me to ring because she is poorly. Agent: Thank you for calling. How old are you, and is a "
                "grown-up there with you? Caller: I am nine. Mummy is lying down. Agent: Okay. Can you tell me your "
                "mummy's name? Caller: Jean, Jean Cottrell. Agent: Do you know her date of birth? Caller: No, I do "
                "not know that. Agent: That is alright, you have done well. I need to speak to an adult to confirm "
                "some details. Is there a grown-up who can come to the phone or a number we can call back? Caller: My "
                "auntie is coming later. Agent: Thank you. I will make sure a member of staff calls back to check "
                "your mummy is okay and speaks with an adult."
            ),
        },
        {
            "suffix": "021-TRUNCATED",
            "request_type": "unknown",
            "stated_request": "Recording cuts off mid-sentence; only partial details captured before the call drops.",
            "verification_status": "insufficient_data",
            "priority": "review_required",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "Julie",
            "dob": "",
            "postcode": "",
            "callback_number": "07700900021",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Call dropped before details completed. Only a first name captured. Safe fallback, staff review.",
            "summary": "Call cut off mid-sentence with only partial details. Cannot verify; staff review required.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: Hi yes I wanted to "
                "ask about, sorry the signal is terrible here, I am in the car park. Agent: No problem, take your "
                "time. Can I start with your name and date of birth? Caller: It is Julie, Julie, hang on, my date of "
                "birth is the, oh it is breaking up, can you hear me? Agent: You are breaking up a little, please go "
                "ahead with your date of birth. Caller: It is the twelfth of, no wait, it is, hello? Are you still "
                "there? I think I am losing you, the thing I actually needed was about my, hold on, it is the letter "
                "I got about the appoint—"
            ),
        },
        {
            "suffix": "022-GARBLED-ASR",
            "request_type": "unknown",
            "stated_request": "Heavy speech-recognition errors produce nonsense tokens; content is not reliably extractable.",
            "verification_status": "insufficient_data",
            "priority": "review_required",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "",
            "dob": "",
            "postcode": "",
            "callback_number": "07700900022",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Transcript heavily corrupted by mis-recognition. Low extraction confidence, safe fallback, staff review.",
            "summary": "Garbled transcript with nonsense tokens. Content not reliable; safe fallback and staff review.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: yerra the wossit "
                "for the thing innit the prezcrip no the uh appointmen brrr Agent: Sorry, the line is unclear, could "
                "you repeat that? Caller: naw naw the ting wit da nurse an da bloodz an da formy form for da werk yer "
                "know wa am sayin Agent: I am struggling to make out the details. Can I take your name slowly? Caller: "
                "iz uh sh sh krrk mmf da name iz uh krrrk hello hello da phone iz Agent: The audio is very broken. I "
                "will log this call so a member of staff can call you back on the number captured and take the details "
                "clearly. Caller: aye da werk form an da uh krrk cheers boss brrp."
            ),
        },
        {
            "suffix": "023-NEAR-SILENT",
            "request_type": "unknown",
            "stated_request": "Almost no intelligible speech; long silences with only faint background noise.",
            "verification_status": "insufficient_data",
            "priority": "review_required",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "",
            "dob": "",
            "postcode": "",
            "callback_number": "07700900023",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Near-silent call, no usable content. Processing output unavailable; staff review required.",
            "summary": "Near-silent call with no usable speech. Processing output unavailable; staff to call back.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: ... Agent: Hello, "
                "you are through to the surgery intake line, can you hear me? Caller: ... hm ... Agent: I can hear "
                "some background noise but I cannot make out any speech. If you can hear me, please speak now. Caller: "
                "... [faint rustling] ... Agent: I still cannot hear you clearly. Caller: ... [long pause] ... uh ... "
                "Agent: It seems we have a very poor connection and I cannot take any details. I will log this call "
                "against the number that came through so a member of staff can attempt to call you back. Caller: ... "
                "[silence] ... Agent: Thank you, take care, goodbye."
            ),
        },
        {
            "suffix": "024-LONG-RAMBLE",
            "request_type": "needs_review",
            "stated_request": "Very long, meandering call across many topics with a single red-flag symptom buried in the middle.",
            "verification_status": "matched",
            "priority": "999 Emergency",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": True,
            "patient_name": "John Caines",
            "dob": "1942-12-28",
            "postcode": "PR9 7LT",
            "callback_number": "07700900024",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Long multi-topic ramble; a cardiac red flag (crushing chest pain radiating to the arm) is buried mid-call and must be caught.",
            "summary": "Long rambling call with a buried cardiac red flag. Red flag must be detected and prioritised.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: Oh where do I "
                "start, it has been a week, first the bins were not collected and I know that is not you but it sets "
                "the tone, then my sister rang about the wedding, and I wanted to ask about my repeat tablets, the "
                "water ones, and also whether the physio letter ever came because my knee has been playing up since "
                "the garden, and the cat has been off its food which is a worry but again not your department. Agent: "
                "That is a lot, I will help where I can. Can I take your name and date of birth first? Caller: John "
                "Caines, twenty-eighth of December nineteen forty-two. Now, where was I, oh yes, and the other thing, "
                "and I did not want to make a fuss, is that this morning I had this crushing pain in my chest that "
                "spread down my left arm and I felt clammy, but it eased a bit so I carried on, anyway back to the "
                "prescription, and the receptionist last time was lovely. Agent: John, I need to stop you there. That "
                "chest pain spreading to your arm with clamminess is a serious red flag. Please call 999 now. Caller: "
                "Oh, do you think so, it is probably nothing. Agent: Please do not wait, ring 999 immediately. I am "
                "flagging this as an emergency for the team as well, but you must call 999 now. Caller: Alright, I "
                "will ring them, thank you for listening to my rambling."
            ),
        },
        {
            "suffix": "025-LANG-MIXED",
            "request_type": "unknown",
            "stated_request": "Caller mixes English with fragments of another language; only partial meaning is recoverable.",
            "verification_status": "insufficient_data",
            "priority": "review_required",
            "safe_to_queue": False,
            "staff_review_required": True,
            "red_flags_present": False,
            "patient_name": "",
            "dob": "",
            "postcode": "",
            "callback_number": "07700900025",
            "caller_for": "self",
            "caller_relationship": "self",
            "pathway_response": "Mixed-language call, partial English only. Safe fallback and staff review; consider interpreter.",
            "summary": "Caller switched between English and another language. Partial meaning only; staff review, interpreter may be needed.",
            "transcript": (
                "Agent: JeffLocal demo intake. Can I confirm what you need help with today? Caller: Bore da, sorry, "
                "hello, I need help with, dw i ddim yn gwybod sut i ddweud, the appointment, yr apwyntiad, for my "
                "check. Agent: I can help. Can I take your name and date of birth? Caller: Fy enw i yw, my name is, "
                "ah, it is hard, a fy nyddiad geni, my birthday, mae'n ddrwg gen i. Agent: No problem, take your "
                "time. Do you have any urgent symptoms, any pain? Caller: Na, dim poen, no pain, just the check up, y "
                "prawf, the blood test I think. Agent: I understand it is about a check or blood test. Because I could "
                "not capture all your details, I will pass this to the team and note that an interpreter may help "
                "when they call you back. Caller: Diolch, thank you, diolch yn fawr."
            ),
        },
    ]


def build_plain_calls(batch_id: str) -> list[dict]:
    batch_root = batch_id.rstrip("-")
    timestamp = utc_now_iso()
    calls: list[dict] = []
    _blocks = transcript_blocks()
    if _SLICE_LIMIT is not None:
        _blocks = _blocks[_SLICE_OFFSET : _SLICE_OFFSET + _SLICE_LIMIT]
    for item in _blocks:
        transcript = item["transcript"].strip()
        if len(transcript) <= 500:
            raise ValueError(f"Transcript too short for {item['suffix']}: {len(transcript)} chars")
        call_id = f"{batch_root}-{item['suffix']}"
        calls.append(
            {
                "call_id": call_id,
                "call_timestamp": timestamp,
                "workflow": "voice_agent_demo_batch",
                "request_type": item["request_type"],
                "source": "voice_agent",
                "voice_agent": {
                    "agent_name": "Jeff Voice Agent",
                    "session_id": f"VA-{call_id}",
                    "caller_channel": "phone",
                    "call_direction": "inbound",
                    "caller_id_captured": True,
                    "call_duration_seconds": 180,
                    "language": "en-GB",
                    "caller_sentiment": "demo",
                    "caller_difficulty": "demo",
                    "transcript_quality": "demo_realistic",
                },
                "normalized_input": {
                    "patient_name": item["patient_name"],
                    "dob": item["dob"],
                    "postcode": item["postcode"],
                    "callback_number": item["callback_number"],
                    "medications_requested": ["atorvastatin 20mg"] if item["request_type"] == "prescription" else [],
                    "urgency_note": item["priority"],
                    "pharmacy": "Demo Pharmacy" if item["request_type"] == "prescription" else "",
                    "caller_for": item["caller_for"],
                    "supplied_nhs_number": "",
                },
                "pathway_responses": {
                    "consent_to_questions": "yes",
                    "caller_for": item["caller_for"],
                    "selected_pathway": item["request_type"],
                    "appointment_redirected": item["request_type"] == "appointment_redirect",
                    "identity": {
                        "patient_name": item["patient_name"],
                        "dob": item["dob"],
                        "postcode": item["postcode"],
                        "callback_number_from_caller_id": item["callback_number"],
                        "callback_confirmed": True,
                    },
                    "prescription": {
                        "prescription_type": "repeat" if item["request_type"] == "prescription" else "",
                        "medications_requested": ["atorvastatin 20mg"] if item["request_type"] == "prescription" else [],
                        "pharmacy": "Demo Pharmacy" if item["request_type"] == "prescription" else "",
                        "run_out_status": "two tablets left" if item["request_type"] == "prescription" else "",
                    },
                    "sick_note": {
                        "request_type": "new" if item["request_type"] == "sick_note" else "",
                        "purpose": "work" if item["request_type"] == "sick_note" else "",
                        "requested_duration": "one week" if item["request_type"] == "sick_note" else "",
                        "reason": "viral illness" if item["request_type"] == "sick_note" else "",
                    },
                    "referral": {
                        "referral_type": "chasing" if item["request_type"] == "referral" else "",
                        "specialty": "orthopaedics" if item["request_type"] == "referral" else "",
                        "approx_submission_date": "about four weeks ago" if item["request_type"] == "referral" else "",
                    },
                    "admin": {
                        "caller_relationship": item["caller_relationship"],
                        "needs_identity_check": item["request_type"] == "admin",
                    },
                    "urgency_assessment": {
                        "urgency_level": item["priority"],
                        "red_flags_mentioned": ["chest pain", "breathlessness", "sweating"] if item["red_flags_present"] else [],
                        "red_flag_followup_questions": [],
                        "emergency_advice_given": item["red_flags_present"],
                        "transfer_offered": False,
                        "transfer_accepted": False,
                    },
                    "summary_confirmation": {
                        "summary_read_back": item["summary"],
                        "caller_confirmed_correct": True,
                        "anything_else": "no",
                    },
                },
                "raw_transcript": transcript,
                "transcript_summary": item["summary"],
                "call_duration_seconds": 180,
                "caller_sentiment": "demo",
                "caller_difficulty": "demo",
                "transcript_quality": "demo_realistic",
                "handoff_confidence": 0.91,
                "extraction_confidence": 0.88,
                "staff_review_required": item["staff_review_required"],
                "red_flags_present": item["red_flags_present"],
                "assigned_to": "",
                "outcome_notes": "",
                "staff_action": "",
                "resolved_at": "",
                "resolved_by": "",
                "last_edited_at": "",
                "last_edited_by": "",
                "turnaround_minutes": "",
            }
        )
    return calls


def encrypt_calls(batch_id: str) -> list[dict]:
    return [encrypt_envelope(call) for call in build_plain_calls(batch_id)]


def build_batch(batch_id: str) -> dict:
    batch_root = batch_id.rstrip("-")
    return {
        "test_mode": True,
        "disable_google_push": True,
        "refresh_artifacts": True,
        "batch_id": batch_root,
        "source": "voice_agent_demo",
        "calls": encrypt_calls(batch_root),
    }


def assert_envelope_shape(envelope: dict) -> None:
    missing = REQUIRED_ENVELOPE_FIELDS.difference(envelope.keys())
    if missing:
        raise ValueError(f"Envelope missing fields: {', '.join(sorted(missing))}")
    if envelope["protocol"] != "JEIE-1":
        raise ValueError(f"Unexpected protocol: {envelope['protocol']}")
    if envelope["alg"] != "RSA-OAEP-256+A256GCM":
        raise ValueError(f"Unexpected alg: {envelope['alg']}")
    if envelope["key_id"] != "jefflocal-rsa-test-001":
        raise ValueError(f"Unexpected key_id: {envelope['key_id']}")
    if envelope["signature_alg"] != "HMAC-SHA256":
        raise ValueError(f"Unexpected signature_alg: {envelope['signature_alg']}")


def local_self_check(batch_id: str, batch: dict) -> None:
    sample = batch["calls"][0]
    assert_envelope_shape(sample)
    if local_decrypt_envelope is not None:
        plain = build_plain_calls(batch_id)[0]
        decrypted = local_decrypt_envelope(sample)
        if decrypted.get("call_id") != plain["call_id"]:
            raise ValueError("Local decrypt check failed: call_id mismatch")
        if decrypted.get("source") != "voice_agent":
            raise ValueError("Local decrypt check failed: source mismatch")
        if decrypted.get("raw_transcript") != plain["raw_transcript"]:
            raise ValueError("Local decrypt check failed: transcript mismatch")
        return
    if build_n8ntest_batch is not None:
        working_shape = set(build_n8ntest_batch("N8NTEST-LOCAL-SHAPE")["calls"][0].keys())
        if set(sample.keys()) != working_shape:
            raise ValueError("Envelope shape mismatch against working N8NTEST fixture")


def print_summary(target_url: str, batch_id: str, calls: list[dict], dry_run: bool) -> None:
    summary = {
        "target_url": target_url,
        "batch_id": batch_id,
        "call_ids": [item["message_id"] for item in calls],
        "num_calls": len(calls),
        "mode": "dry-run" if dry_run else "send",
    }
    print(json.dumps(summary, indent=2))


def report_deadletter_issue(batch_id: str) -> None:
    deadletter_dir = ROOT_DIR / "queue" / "deadletter"
    if not deadletter_dir.exists():
        return
    matches = sorted(deadletter_dir.glob(f"*{batch_id}*.json"))
    if matches:
        print("Likely decrypt format mismatch: JeffLocal created decrypt_failed files for this batch.")
        for path in matches:
            print(f"  {path.name}")


def send_batch(target_url: str, payload: dict) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        target_url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Send one encrypted GPDEMO batch to a local n8n webhook.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-send", action="store_true")
    parser.add_argument("--prefix", default="")
    parser.add_argument("--url", default=DEFAULT_WEBHOOK_URL)
    parser.add_argument("--offset", type=int, default=0, help="slice start index into transcript_blocks()")
    parser.add_argument("--limit", type=int, default=None, help="max calls to send (endpoint cap is 5)")
    args = parser.parse_args()

    global _SLICE_OFFSET, _SLICE_LIMIT
    _SLICE_OFFSET = args.offset
    _SLICE_LIMIT = args.limit

    if not args.url.strip():
        print("ERROR: --url is required", file=sys.stderr)
        return 2
    if not is_local_url(args.url):
        print("ERROR: refusing non-local webhook URL", file=sys.stderr)
        return 2

    batch_id = args.prefix.strip() or f"GPDEMO-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    batch = build_batch(batch_id)
    plain_calls = build_plain_calls(batch_id)
    print_summary(args.url, batch_id, batch["calls"], dry_run=args.dry_run)
    print(json.dumps({"plaintext_transcripts_over_500": all(len(call["raw_transcript"]) > 500 for call in plain_calls)}, indent=2))

    local_self_check(batch_id, batch)

    if args.dry_run:
        return 0
    if not args.confirm_send:
        print("Refusing to send without --confirm-send.", file=sys.stderr)
        return 2

    status, body = send_batch(args.url, batch)
    print(json.dumps({"batch_id": batch_id, "status": status}, indent=2))
    if status == 404:
        print(
            "n8n webhook not found. Check that the 'JeffLocal - 06 Test Intake Webhook' workflow is active in n8n "
            "and that n8n is running on port 5678."
        )
    if status in {400, 500}:
        print(body)
    if 200 <= status < 300:
        time.sleep(1)
        report_deadletter_issue(batch_id)
    return 0 if 200 <= status < 300 else 1


if __name__ == "__main__":
    raise SystemExit(main())

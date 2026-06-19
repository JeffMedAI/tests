Set-StrictMode -Version Latest

function Invoke-JeffOllamaExtraction {
    param(
        [string]$Model,
        [object]$Call,
        [string]$OutputsDir
    )

    $prompt = @"
You are assisting a UK GP practice reception workflow by reading a phone call transcript and extracting structured data for a local workflow processor called JeffLocal.
Return strict JSON only. Do not include markdown, comments, or explanatory text.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSIBILITY SPLIT — READ CAREFULLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YOU MAY:
- Read the raw transcript and extract draft structured fields
- Draft transcript_summary, task_title, task_body
- Suggest request_type and selected_pathway
- Flag uncertain or missing information

YOU MUST NOT:
- Make final routing, priority, or queueing decisions
- Decide verification_status or patient identity
- Make clinical decisions of any kind
- Invent information not present in the transcript
- Confirm patient identity from the call alone

All final decisions on safety, identity, routing, priority, safe_to_queue, and patient matching are made by deterministic JeffLocal code after you return.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WRITING RULES FOR transcript_summary, task_title, task_body
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Write for busy reception staff who need to understand the request in under 3 seconds.
- transcript_summary: max 22 words. Patient name + request type + key detail + any issue.
- task_title: max 9 words. Format: [Type] - [Patient Name or Unknown] - [Key Status].
- task_body: max 45 words. Short direct sentences. Only what staff need to act.
- Base only on the transcript. Never invent missing details.
- Do not make clinical decisions or confirm identity.
- If a detail is unknown, say so explicitly (e.g. "medication unclear", "DOB missing").

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GOOD transcript_summary EXAMPLES (by pathway)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
prescription:
  GOOD: "Jason Morrey requests repeat prescription for atorvastatin 20mg; callback confirmed."
  GOOD: "Dorothy Bridge's daughter requests repeat prescription; caller acting on patient's behalf."
  GOOD: "Julie Chadwick requests prescription but callback number not confirmed."
  BAD:  "Patient called about medication." (too vague — medication and name are known)
  BAD:  "Repeat prescription request." (missing patient name and medication)

sick_note:
  GOOD: "Maria Santos requests 5-day sick note for viral illness; has not yet seen GP."
  GOOD: "Robert Lee requests extension to existing sick note; reason: back pain, started 12 May."
  BAD:  "Patient wants sick note." (missing duration, reason, and whether GP seen)

referral:
  GOOD: "Anne Hughes chasing cardiology referral to Southport Hospital; submitted approx 6 weeks ago."
  GOOD: "David Park requests new orthopaedic referral; knee pain, GP not yet seen."
  BAD:  "Patient asking about referral." (no specialty, hospital, or context)

test_result:
  GOOD: "Patricia Kite requesting blood test result from 20 May; has not spoken to GP."
  GOOD: "Marcus Obi calling about urine sample result; concerned it has not arrived."
  BAD:  "Patient wants test result." (no test type or date)

appointment_redirect:
  GOOD: "Colin Webb requests same-day appointment for chest infection; callback 07911 123456."
  GOOD: "Emma Rashid requests routine GP appointment for medication review; no preference."
  BAD:  "Patient wants appointment." (no reason or urgency)

admin:
  GOOD: "Sarah Booth requests copy of medical records for insurance; callback confirmed."
  GOOD: "Unknown caller asking about online access; no patient details provided."
  BAD:  "Admin query." (no reason or patient name)

unknown:
  GOOD: "Caller did not state request clearly; possible repeat prescription or callback. Transcript unclear."
  BAD:  "Unknown request." (no detail from transcript at all)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REQUEST TYPE DEFINITIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
prescription        — any medication, repeat or new, inhaler, cream, tablet, pharmacy query
sick_note           — sick note, fit note, Med3, doctor's note, signed-off request, certificate
referral            — new referral, chasing referral, Choose & Book, hospital or consultant query
test_result         — blood test, scan, x-ray, urine, swab, any lab or imaging result
appointment_redirect — booking an appointment, requesting to see GP/nurse/pharmacist
admin               — address change, records, registration, forms, online access, letters, complaints
unknown             — cannot determine from transcript; flag for staff review

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT JSON SCHEMA — return exactly this structure, no extra fields
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{
  "patient_name": "",
  "dob": "",
  "callback_number": "",
  "caller_name": "",
  "caller_relationship": "self | third_party | carer | family | unknown",
  "request_type": "prescription | sick_note | referral | test_result | appointment_redirect | admin | unknown",
  "selected_pathway": "",
  "transcript_summary": "",
  "task_title": "",
  "task_body": "",
  "transcript_quality_flag": "clear | unclear | incomplete | noisy",
  "uncertain_fields": [],
  "missing_fields": [],
  "identity": {
    "callback_confirmed": false,
    "name_stated": false,
    "dob_stated": false,
    "postcode_stated": false,
    "nhs_number_stated": false
  },
  "urgency_assessment": {
    "urgency_level": "routine | urgent | emergency",
    "red_flags_mentioned": [],
    "red_flag_followup_questions": [],
    "emergency_advice_given": false,
    "transfer_offered": false,
    "transfer_accepted": false
  },
  "red_flags": [],
  "appointment_redirected": false,
  "pathway_responses": {
    "prescription": {
      "prescription_type": "repeat | acute | new | unknown",
      "medications_requested": [],
      "pharmacy": "",
      "run_out_status": "has_supply | running_low | run_out | unknown"
    },
    "sick_note": {
      "request_type": "new | extension | duplicate | unknown",
      "purpose": "employment | personal | benefits | other | unknown",
      "start_date": "",
      "requested_duration": "",
      "reason": "",
      "already_spoken_to_doctor": false,
      "workplace_adjustments_discussed": false
    },
    "referral": {
      "referral_type": "new | chase | urgent | unknown",
      "hospital_name": "",
      "specialty": "",
      "approx_submission_date": "",
      "choose_and_book_code": ""
    },
    "test_result": {
      "test_type": "",
      "approx_test_date": "",
      "reference_number": "",
      "gp_seen_about_result": false,
      "urgency_concern": false
    },
    "appointment_redirect": {
      "appointment_reason": "",
      "preferred_timeframe": "same_day | routine | specific_date | unknown",
      "who_for": "self | third_party | unknown",
      "urgency": "",
      "clinician_preference": "",
      "previous_appointment_declined": false
    },
    "admin": {
      "admin_reason": "",
      "caller_relationship": "self | third_party | carer | family | unknown",
      "needs_identity_check": false,
      "website_answer_available": false,
      "callback_needed": false
    },
    "unknown": {
      "caller_stated_reason": "",
      "suggested_pathway": ""
    }
  }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FIELD NOTES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
identity.callback_confirmed     — true only if caller explicitly confirmed the callback number during the call
identity.name_stated            — true if patient name was spoken (even if unclear)
identity.dob_stated             — true if any date of birth was spoken
identity.postcode_stated        — true if any postcode was spoken
identity.nhs_number_stated      — true if an NHS number was spoken

urgency_assessment              — always complete this section for every call, regardless of pathway
urgency_assessment.urgency_level — routine: no urgency stated. urgent: caller expressed concern. emergency: life-threatening symptoms mentioned.
red_flags                       — list any: chest pain, difficulty breathing, collapse, severe bleeding, stroke symptoms, suicidal ideation, safeguarding concern. Empty array if none.
appointment_redirected          — true if caller was advised to book an appointment rather than the stated request being fulfilled

sick_note.already_spoken_to_doctor       — true if caller states they have already seen or spoken to a GP about this condition
sick_note.workplace_adjustments_discussed — true if caller mentions employer, workplace, or adjustments in same call

test_result.gp_seen_about_result — true if caller says they have already spoken to a doctor about this result
test_result.urgency_concern      — true if caller expresses worry or urgency about the result

appointment_redirect.previous_appointment_declined — true if caller says they were previously turned away or told there were no appointments

admin.needs_identity_check — true if the request (e.g. records, letters) requires reception to verify identity before proceeding

Only populate the pathway_responses section matching request_type. Leave other sections empty/false/[].
Do not use callback_number for identity matching — that is done by deterministic code.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
call_id: $($Call.call_id)
request_type_hint: $($Call.request_type)
patient_name_raw: $($Call.patient_name_raw)
dob_raw: $($Call.dob_raw)
callback_number_raw: $($Call.callback_number_raw)
medications_raw: $($Call.medications_raw)
urgency_note_raw: $($Call.urgency_note_raw)
pharmacy_raw: $($Call.pharmacy_raw)
caller_for_raw: $($Call.caller_for_raw)
raw_transcript: $($Call.raw_transcript)
call_transcript_summary: $($Call.call_transcript_summary)
"@

    $body = @{
        model = $Model
        format = "json"
        stream = $false
        messages = @(
            @{
                role = "user"
                content = $prompt
            }
        )
    } | ConvertTo-Json -Depth 10

    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)

    $ollamaResponse = Invoke-RestMethod `
        -Uri "http://localhost:11434/api/chat" `
        -Method Post `
        -ContentType "application/json; charset=utf-8" `
        -Body $bodyBytes

    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $rawOutPath = Join-Path $OutputsDir "$($Call.call_id)-ollama-response-$timestamp.json"
    $ollamaResponse | ConvertTo-Json -Depth 10 | Set-Content -Path $rawOutPath -Encoding UTF8

    $contentText = $ollamaResponse.message.content
    $llmData = $contentText | ConvertFrom-Json

    return [pscustomobject]@{
        llm_data = $llmData
        raw_output_path = $rawOutPath
    }
}

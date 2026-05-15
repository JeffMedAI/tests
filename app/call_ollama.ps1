Set-StrictMode -Version Latest

function Invoke-JeffOllamaExtraction {
    param(
        [string]$Model,
        [object]$Call,
        [string]$OutputsDir
    )

    $prompt = @"
You are assisting a GP practice reception workflow by reading a GP surgery phone call transcript for a local workflow processor.
Return strict JSON only. Do not include markdown, comments, or explanatory text.

Responsibility split:
- You may read the raw transcript, extract draft structured fields, and draft transcript_summary.
- You may suggest request_type and selected_pathway.
- Deterministic JeffLocal code makes final routing, required-field validation, patient matching, verification_status, verification_reason, priority, safe_to_queue, review flags, safety flags, candidate matches, matched patient details, final handoff JSON construction, and final staff-facing summary/title/body after verification.
- Do not make final safety, identity, matching, verification, or queueing decisions. The rules layer decides.

Draft writing rules for transcript_summary, task_title, and task_body:
- Write for busy reception/admin staff who need to understand the request within 3 seconds.
- Output must be factual, brief, and based only on the transcript.
- Maximum 22 words.
- Include patient name if stated, request type, medication/item/request detail if stated, and important issue such as urgent, callback refused, caller acting for someone else, unclear DOB, or missing details.
- Do not invent missing details.
- Do not make clinical decisions.
- Do not confirm patient identity.
- Do not decide whether the request is safe.
- Do not use vague phrases like "patient called about medication" if the medication/request is known.
- Do not include unnecessary politeness, filler, or long explanations.

Good transcript_summary examples:
"Abdel Boumnijel requests repeat prescription for amlodipine; callback number provided."
"Dorothy Bridge's daughter requests repeat prescription; caller is acting on patient's behalf."
"Julie Chadwick requests repeat prescription but callback number was not confirmed."
"Caller requests prescription but patient identity details are incomplete."

Bad transcript_summary examples:
"The caller contacted the surgery regarding a prescription request and provided some information."
"Patient needs help with medication."
"Repeat prescription request."

If medication is unclear, write "medication unclear".
If DOB is missing or unclear, write "DOB missing" or "DOB unclear".
If patient name is missing, write "Unknown patient".
If callback number is missing, write "callback missing".
If caller is requesting for someone else, state that clearly.
If transcript is messy or uncertain, state the specific uncertainty.
Never include information that is not present in the transcript.
- task_title maximum 9 words. Format: [Request Type] - [Patient Name or Unknown Patient] - [Key Status].
- task_body maximum 45 words. Use short, direct sentences with only what staff need to act.

Use this exact JSON shape:
{
  "patient_name": "",
  "dob": "",
  "callback_number": "",
  "caller_name": "",
  "caller_relationship": "",
  "request_type": "",
  "selected_pathway": "",
  "transcript_summary": "",
  "task_title": "",
  "task_body": "",
  "transcript_quality_flag": "",
  "uncertain_fields": [],
  "missing_fields": [],
  "urgency_assessment": {
    "urgency_level": "",
    "red_flags_mentioned": [],
    "red_flag_followup_questions": [],
    "emergency_advice_given": false,
    "transfer_offered": false,
    "transfer_accepted": false
  },
  "red_flags": [],
  "pathway_responses": {
    "prescription": {
      "prescription_type": "",
      "medications_requested": [],
      "pharmacy": "",
      "run_out_status": ""
    },
    "sick_note": {
      "request_type": "",
      "purpose": "",
      "start_date": "",
      "requested_duration": "",
      "reason": ""
    },
    "referral": {
      "referral_type": "",
      "hospital_name": "",
      "approx_submission_date": "",
      "specialty": ""
    },
    "test_result": {
      "test_type": "",
      "approx_test_date": "",
      "reference_number": ""
    },
    "appointment_redirect": {
      "appointment_reason": "",
      "preferred_timeframe": ""
    },
    "admin": {
      "admin_reason": "",
      "website_answer_available": false,
      "callback_needed": false
    }
  }
}

request_type and selected_pathway may be suggested by the model, but deterministic local code makes final routing, validation, and patient verification decisions.
Do not decide verification_status. Do not infer a patient match. Do not use callback number for identity matching.

Input:
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

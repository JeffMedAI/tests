# Codex Build Prompt — JeffLocal End-to-End Upgrade

You are working on the JeffLocal reception workflow/dashboard project.

Project context:
JeffLocal is a local GP practice workflow system. It receives voice-agent call transcripts, sends transcript content to a local Ollama model for structured extraction, applies deterministic matching and safety rules, builds staff handoff JSON, and pushes staff-facing output to Google Sheets.

Important:
Do not remove or weaken the existing deterministic matching, verification, safety, queueing, or Google push behaviour.

Core principle:
Ollama/local LLM may extract and draft.
Deterministic JeffLocal code must verify, match, validate, post-process, and finalize.
LLM output must never override verified EMIS/NHS/patient lookup data.

## Task 1 — Dashboard redesign

Redesign the JeffLocal reception dashboard to use a clean fixed left-side navigation panel.

Sidebar must include:
- JeffLocal logo/brand
- Dashboard
- Requests
- Patients
- Staff
- Reports
- Settings
- Help/support
- Logged-in user/role indicator

Dashboard page should show only operational overview:
- Urgent attention banner
- Red flags
- Staff review count
- Identity checks
- Open cases
- Processed today
- System health
- Live workload summary
- Request mix summary
- Staff workload summary

Move detailed information into separate pages:
- Requests: full request table, filters, status, type, date range, request detail drawer
- Patients: patient lookup, match status, verification history, candidate matches
- Staff: staff workload, assignments, resolved/in-progress counts, alerts acknowledged
- Reports: daily/weekly metrics, pathway volumes, failed queue trends, safety queue trends
- Settings: model settings, routing settings, Google push/webhook settings, pathway configuration, monitoring thresholds
- System/Admin if needed: queue status, deadletter files, audit logs, raw transcripts, debug output

Functional behaviour:
- Sidebar controls active page/view.
- Dashboard cards link to filtered views where appropriate.
- “View Critical” opens red flag / failed safety / urgent review items.
- “View All Alerts” opens alerts or requests with alert filters applied.
- Keep filters on Requests page, not the main dashboard.
- Do not remove existing workflow logic.

## Task 2 — Ollama vs deterministic responsibility

Ollama/local LLM is responsible for:
- Reading the raw transcript.
- Extracting draft structured fields.
- Drafting transcript_summary, task_title, and task_body.

Deterministic JeffLocal code is responsible for:
- Required-field validation
- Patient matching
- verification_status
- verification_reason
- priority
- safe_to_queue
- review flags
- safety flags
- candidate matches
- matched patient details
- final handoff JSON construction
- final staff-facing summary/title/body after verification

Do not allow the LLM to make final safety, identity, matching, or queueing decisions.

## Task 3 — Strengthen Ollama prompt

Find the prompt/config file or prompt construction logic used by call_ollama.ps1 / generate_staff_summary.ps1 / build_handoff.ps1.

Update it so Ollama creates highly precise draft fields.

Prompt requirements:

You are assisting a GP practice reception workflow.

Your job is to read a raw call transcript and produce a concise staff handoff draft.

Write for busy reception/admin staff who need to understand the request within 3 seconds.

Output must be factual, brief, and based only on the transcript.

Rules:
- Do not invent missing details.
- Do not make clinical decisions.
- Do not confirm patient identity.
- Do not decide whether the request is safe.
- Do not use vague phrases like “patient called about medication” if the medication/request is known.
- Do not include unnecessary politeness, filler, or long explanations.

Create:

### transcript_summary
One sentence.
Maximum 22 words.
Include patient name if stated, request type, medication/item/request detail if stated, and important issue if relevant.

Good examples:
- "Abdel Boumnijel requests repeat prescription for amlodipine; callback number provided."
- "Dorothy Bridge’s daughter requests repeat prescription; caller is acting on patient’s behalf."
- "Julie Chadwick requests repeat prescription but callback number was not confirmed."
- "Caller requests prescription but patient identity details are incomplete."

Bad examples:
- "The caller contacted the surgery regarding a prescription request and provided some information."
- "Patient needs help with medication."
- "Repeat prescription request."

### task_title
Short staff-facing title.
Maximum 9 words where possible.

Draft format:
[Request Type] - [Patient Name or Unknown Patient] - [Key Status]

Examples:
- "Prescription - Abdel Boumnijel - Draft"
- "Prescription - Julie Chadwick - Callback Not Confirmed"
- "Prescription - Unknown Patient - Missing DOB"
- "Prescription - Dorothy Bridge - Caller Acting For Patient"

### task_body
Compact staff instruction.
Maximum 45 words.
Use short, direct sentences.
Include only what staff need to act:
- request
- patient details stated
- medication/item
- callback status
- caller relationship if relevant
- uncertainty or missing fields

Good examples:
- "Repeat prescription requested for amlodipine. Patient: Abdel Boumnijel, DOB stated. Callback number provided. Check matched record before processing."
- "Caller says they are Dorothy Bridge’s daughter and requests a repeat prescription. Patient DOB stated. Treat as caller-for-patient and review identity before processing."
- "Repeat prescription requested for Julie Chadwick. Callback number was not confirmed. Review before contacting or processing."

Return valid JSON only:

{
  "transcript_summary": "",
  "task_title": "",
  "task_body": ""
}

Additional rules:
- If medication is unclear, write "medication unclear".
- If DOB is missing or unclear, write "DOB missing" or "DOB unclear".
- If patient name is missing, write "Unknown patient".
- If callback number is missing, write "callback missing".
- If caller is requesting for someone else, state that clearly.
- If transcript is messy or uncertain, state the specific uncertainty.
- Never include information that is not present in the transcript.

## Task 4 — Deterministic post-processing after verification

After Ollama drafts transcript_summary, task_title, and task_body, JeffLocal must run deterministic post-processing before final handoff JSON.

Pipeline order:
1. Ollama extracts draft structured fields from transcript.
2. Deterministic code performs patient matching and verification.
3. Deterministic post-processing normalizes patient identifiers using verified lookup data.
4. Final transcript_summary, task_title, and task_body are generated or corrected using verified EMIS/NHS identifiers.
5. Final handoff JSON is built and pushed to staff handoff.

Rules:

### matched
If verification_status = matched:
- Replace transcript-spelled patient name with verified matched_patient_name.
- Use matched EMIS Number and/or matched NHS Number as the primary identifier in transcript_summary and task_body.
- Prefer “EMIS: [matched_patient_ref]” or “NHS: [matched_nhs_number]”.
- Do not use caller-spelled or LLM-inferred name spelling once a verified match exists.

### possible_match / possible_match_weak
If verification_status = possible_match or possible_match_weak:
- Do not rewrite the caller-stated name as confirmed.
- Use candidate identifiers cautiously:
  "Possible match: EMIS [top_candidate_ref] / NHS [top_candidate_nhs_number if available]"
- State staff review is required.
- Do not treat as fully safe without review.

### no_match / insufficient_data
If verification_status = no_match or insufficient_data:
- Do not insert EMIS or NHS number.
- Use "Unknown patient" or caller-stated details only.
- Clearly state missing identifiers such as DOB missing, name unclear, callback missing.

Final field rules:
- transcript_summary: one sentence, maximum 22 words.
- task_title: short, clear, include verification status.
- task_body: maximum 45 words.
- For matched patients, use verified EMIS/NHS identifiers.
- Include patient name only as a secondary display label if useful, never as the only identifier.
- Never allow Ollama text to override verified lookup data.
- Never allow transcript spelling to override matched_patient_name, EMIS number, NHS number, DOB, age, or gender.
- If safe_to_queue is false, task_body must include "Staff review required."
- If callback_number is missing or unconfirmed, task_body must state "Callback missing." or "Callback not confirmed."
- If caller_for is not the patient, task_body must state "Caller acting for patient."

Reject or rewrite vague outputs:
- "Patient called about medication"
- "Prescription request"
- "Caller needs help"
- "Medication issue"

## Task 5 — Preserve matching tiers

Do not break the existing locked matching tiers:
- matched = exact full name + exact DOB
- possible_match = same surname + same DOB + first 3 letters of first name match
- possible_match_weak = same DOB + first 3 letters of first name match + high surname similarity / one-character surname difference
- no_match = nothing reliable found
- insufficient_data = required details missing

Preserve:
- Callback number is captured for handoff but not used for patient matching.
- False transliteration flag remains removed.
- Staff-facing matched names are cleaned for display.
- Callback-not-confirmed cases show clean wording.
- Spoken DOB parsing supports forms like "2nd of May, 71".
- possible_match_weak remains cautious and review-based.

## Task 6 — Tests

Add or update tests for:
- matched patient with misspelled transcript name
- possible_match
- possible_match_weak
- no_match
- insufficient_data
- caller acting for patient
- callback not confirmed
- messy transcript
- queue movement
- handoff JSON schema
- Google push mock mode
- model monitoring
- dashboard navigation

Tests must confirm:
- matched final summary/body use EMIS/NHS identifiers
- transcript misspellings do not override verified lookup data
- possible matches are cautious and require review
- no_match/insufficient_data do not insert EMIS/NHS
- summary is under 22 words
- task body is under 45 words
- vague LLM output is rejected or rewritten

## Task 7 — End-to-end validation before handover

Before handing over:
- Run existing smoke tests.
- Run new post-processing tests.
- Run UI tests/build checks.
- Run queue processing test.
- Run Google push in test/mock mode unless live credentials are intentionally configured.
- Confirm no regression in intake, queue movement, failed/deadletter handling, model monitoring, handoff JSON, Google Sheet mapping, or dashboard navigation.

If any test fails:
- Fix it.
- Re-run the failed test.
- Re-run the full affected flow.
- Do not hand over until end-to-end validation passes.

Final handover must include:
1. Files changed.
2. Summary of UI changes.
3. Summary of prompt changes.
4. Summary of post-processing changes.
5. Test commands run.
6. Test results.
7. Known limitations or skipped tests, with reasons.
8. Confirmation that existing workflow logic was preserved.

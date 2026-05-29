# Claude Code / Cursor Review Prompt — JeffLocal

You are reviewing and debugging Codex’s implementation of JeffLocal.

Do not rebuild the project from scratch.
Do not replace the architecture unless absolutely necessary.
Your job is to review, test, debug, and harden the implementation.

Context:
JeffLocal is a local GP reception workflow. It processes voice-agent transcripts, sends transcript content to local Ollama for structured extraction, performs deterministic patient matching, generates staff handoff JSON, and pushes staff-facing output to Google Sheets.

Key safety rule:
Ollama may extract and draft, but deterministic JeffLocal code must decide and finalize.

## Review areas

### 1. Pipeline order
Confirm the pipeline is:
- intake transcript
- Ollama extraction/draft summary/title/body
- deterministic patient matching
- deterministic post-processing
- final staff-facing summary/title/body
- handoff JSON
- queue movement
- Google push or mock push
- monitoring/evaluation

Flag any place where Ollama output bypasses deterministic verification.

### 2. Patient identity safety
Check that verified patient lookup data overrides transcript spelling and LLM guesses.

For matched patients:
- final summary/task body use EMIS/NHS identifiers
- transcript misspellings do not survive into final identifiers
- LLM cannot overwrite matched_patient_name, EMIS, NHS number, DOB, age, or gender

For possible_match and possible_match_weak:
- wording is cautious
- candidate is not presented as confirmed
- staff review is required

For no_match or insufficient_data:
- no EMIS/NHS number is inserted
- missing details are clearly stated

### 3. Staff-facing text quality
Check transcript_summary, task_title, and task_body.

They must be:
- precise
- readable within 3 seconds
- non-vague
- operationally useful for reception staff

Limits:
- transcript_summary: max 22 words
- task_body: max 45 words
- task_title: short and clear

Reject vague output like:
- “Patient called about medication”
- “Prescription request”
- “Caller needs help”
- “Medication issue”

### 4. Matching logic regression check
Confirm these tiers are preserved:
- matched = exact full name + exact DOB
- possible_match = same surname + same DOB + first 3 letters of first name match
- possible_match_weak = same DOB + first 3 letters of first name match + high surname similarity / one-character surname difference
- no_match
- insufficient_data

Confirm callback number is not used for patient matching.

### 5. Queue and handoff safety
Check:
- incoming -> processing -> processed movement
- failed handling
- deadletter handling if implemented
- audit logs
- error logs
- handoff JSON schema
- Google Sheet payload mapping
- mock Google push mode for tests

### 6. Dashboard review
Check the new sidebar dashboard:
- Dashboard only shows overview cards
- Requests page has filters/table/detail view
- Patients, Staff, Reports, Settings are reachable
- Critical alert buttons route to filtered review/critical items
- UI does not expose raw clutter on the main dashboard

### 7. Tests
Run or inspect tests for:
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

If tests are missing, add them.
If tests fail, fix the code and rerun them.

### 8. End-to-end validation
Run an end-to-end test using mock Ollama and mock Google push if live services are unavailable.

The E2E test must prove:
- transcript goes in
- extraction draft is created
- matching runs
- post-processing rewrites final staff fields
- final handoff JSON is produced
- queue movement works
- monitoring runs
- Google push mock payload is correct

## Final response required

Provide:
1. Issues found.
2. Files changed.
3. Tests added or updated.
4. Commands run.
5. Test results.
6. Remaining risks.
7. Confirmation whether JeffLocal is safe to hand back to Codex/user.

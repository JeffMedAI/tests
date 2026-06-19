# LLM vs Rules Responsibility — JeffLocal

JeffLocal uses a strict responsibility split.

## Core rule

Ollama/local LLM may extract and draft.
Deterministic JeffLocal code must verify, match, validate, post-process, and finalize.

LLM output must never override verified EMIS/NHS/patient lookup data.

## Ollama is allowed to

- Read the raw transcript.
- Extract draft structured fields.
- Draft transcript_summary.
- Draft task_title.
- Draft task_body.
- Suggest unclear or missing fields.

## Ollama is not allowed to

- Confirm patient identity.
- Decide verification_status.
- Decide safe_to_queue.
- Decide clinical urgency.
- Decide final staff task safety.
- Override patient lookup data.
- Override matched_patient_name.
- Override EMIS number.
- Override NHS number.
- Override DOB, age, or gender.
- Insert identifiers not found through deterministic lookup.

## Deterministic JeffLocal code must decide

- Required-field validation.
- Patient matching.
- verification_status.
- verification_reason.
- candidate_matches.
- matched_patient_ref / EMIS number.
- matched_nhs_number.
- matched_patient_name.
- priority.
- safe_to_queue.
- review flags.
- safety flags.
- final transcript_summary.
- final task_title.
- final task_body.
- final handoff JSON.
- Google Sheet payload.

## Required pipeline order

1. Raw transcript is received.
2. Ollama extracts draft structured data and draft staff text.
3. Deterministic patient matching runs.
4. Verification status is assigned.
5. Deterministic post-processing normalizes identifiers.
6. Final staff-facing fields are generated.
7. Handoff JSON is created.
8. Queue movement, monitoring, and Google push run.

## Matched patient rule

If verification_status = matched:
- Use verified EMIS/NHS identifiers in final staff-facing text.
- Correct transcript-spelled names using verified lookup data.
- Never rely on the caller’s spelling as the final identifier.

## Possible match rule

If verification_status = possible_match or possible_match_weak:
- Candidate must be described as possible only.
- Staff review is required.
- Do not present candidate as confirmed.

## No match / insufficient data rule

If verification_status = no_match or insufficient_data:
- Do not insert EMIS or NHS numbers.
- Clearly state missing or unclear details.
- Require staff review.

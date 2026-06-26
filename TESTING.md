# TESTING.md — Avamed (JeffLocal) End-to-End Test Protocol & Call Template
# Source of truth for how we test the live intake pipeline. Read before any test run.
# Last updated: 2026-06-16

---

## PLAIN ENGLISH (for Saeed)

This file is the recipe book for testing the system the way a real patient call would flow.

When you say **"run tests"**, the team does this, every time:

1. Builds a fresh batch of pretend patient calls — easy ones, hard ones, emergencies, messy
   recordings, people calling about someone else, etc. — so **every kind of case the reception
   dashboard can show gets filled in**.
2. Sends them in the **real way a live call arrives**: encrypted, through n8n, through the AI
   (Jeff/Ollama), through the safety checks, and onto the dashboard. Nothing is faked or skipped.
3. A reception worker's actions are then **simulated on every case** — opening it, reviewing it,
   resolving it — exactly as Churchtown staff would do it.
4. While all that runs, **separate watchdog agents watch the whole thing at the same time** and
   write down every problem and every improvement idea.
5. You get **one plain-English report per test run** in `docs/reports/` telling you what passed,
   what broke, and what to fix.

No real patient data is ever used. Every name, number and NHS number below is invented for testing.

---

## WHAT THIS TESTS — THE FULL PIPELINE (no shortcuts)

```
Test driver (encrypts each call, JEIE-1 envelope)
   → POST batch to n8n  http://localhost:5678/webhook-test/ava-live-intake
      → n8n decrypts + drops raw into  queue/encrypted_raw → queue/incoming
         → PowerShell pipeline + Ollama/Gemma (gemma4:e2b)   [LIVE model — extract + draft only]
            → deterministic patient matching (EMIS/NHS reference)   [sets identity + safety fields]
               → safety rules (red flags, safe_to_queue, priority)
                  → handoff JSON written to  outputs/handoff_json/<call_id>_handoff.json
                     → dashboard importer polls + upserts into SQLite (cases table)
                        → case appears on dashboard (https://dashboard.app-avamed.uk → :8765)
                           → STAFF ACTION simulated (review / resolve) via dashboard endpoints
```

**Entry point is the real n8n webhook. Ollama runs live. No stage is bypassed.** This is the
agreed mode (set 2026-06-16). The handoff-JSON-inject shortcut and pinned-LLM mode are NOT used
for a normal "run tests" request — they are debugging fallbacks only, and must be called out
explicitly in the run report if ever used.

### CORE SAFETY INVARIANT — must hold on every run

Per CLAUDE.md, the LLM may extract and draft, but **deterministic code alone** sets:
`verification_status, safe_to_queue, priority, matched_patient_name, emis_number, nhs_number,
dob, clinical urgency, any patient-identity field`.

Therefore in every test case below, those fields are **EXPECTED OUTCOMES we assert**, never inputs
we feed. The test driver supplies only the call signals (transcript, normalised input, pathway
answers, red-flag mentions). If a run shows an identity/safety field that tracks the LLM's wording
instead of the deterministic rule, that is a **critical failure — stop and flag to Saeed.**

---

## HOW TO RUN A BATCH

**Harness:** `tests/send_gp_demo_n8n_webhook_calls.py` (the encrypted-envelope driver).
**Keys:** `config/keys/jefflocal_public.pem` + `config/keys/voice_agent_hmac_secret.txt`
(`key_id = jefflocal-rsa-test-001`, `alg = RSA-OAEP-256+A256GCM`, `signature_alg = HMAC-SHA256`).

Pre-flight (all must be up — watchdog manages all three; check via `scripts/service_control`):
- n8n on `:5678` with "JeffLocal - 06 Test Intake Webhook" workflow **active**.
- Ollama on `:11434` with `gemma4:e2b` pulled.
- Dashboard on `:8765`.

Dry run first (builds + encrypts + self-checks decrypt, sends nothing):
```powershell
python tests\send_gp_demo_n8n_webhook_calls.py --dry-run --prefix TEST-<YYYYMMDD-HHMMSS>
```

Send for real (requires the explicit flag; refuses non-local URLs):
```powershell
python tests\send_gp_demo_n8n_webhook_calls.py --confirm-send --prefix TEST-<YYYYMMDD-HHMMSS>
```

After send, the driver waits 1s and reports any `queue/deadletter/*<batch_id>*.json` — a deadletter
hit means a decrypt/format mismatch; treat as a failure, do not ignore.

> **Expanding the call set:** the driver's `transcript_blocks()` currently ships 5 demo calls.
> The full matrix in this file (below) is the agreed coverage target. To run the full matrix,
> extend `transcript_blocks()` with the rows in **§ TEST CALL MATRIX** (same field shape), or
> generate them from this file at run time. Adding test fixtures is not a production-code change,
> but the driver lives under `tests/` — keep edits inside `tests/` and never point `--url` off
> localhost.

---

## CALL PARAMETER CONTRACT (one row per test call)

Each call in `transcript_blocks()` is defined by these fields. The driver wraps them into the
voice-agent payload (`normalized_input`, `pathway_responses`, `voice_agent`, `raw_transcript`)
and then encrypts. Transcript must be **> 500 chars** (driver enforces this).

| Field | Meaning | Notes |
|-------|---------|-------|
| `suffix` | call_id tail, e.g. `001-PRESCRIPTION` | unique within batch |
| `request_type` | one of: `prescription, sick_note, referral, test_result, appointment_redirect, admin, unknown, needs_review` | from `config/pathways.json` |
| `stated_request` | one-line what the caller wants | |
| `patient_name`, `dob`, `postcode`, `callback_number` | caller-supplied identity signals | **invented data only** |
| `caller_for` / `caller_relationship` | `self`, `third_party`, `carer`, `parent` | drives identity path |
| `pathway_response` | the pathway-specific answer block summary | |
| `summary` | the read-back summary the agent gave | |
| `transcript` | full dialogue (> 500 chars) | the only thing Ollama actually reads |
| `red_flags_present` *(signal)* | whether emergency symptoms were spoken | drives red-flag mentions in payload; final flag is re-derived deterministically |
| `staff_review_required` *(signal)* | whether the call obviously needs human review | final value re-derived |

**EXPECTED (assert after import — NOT fed in):** `verification_status`, `priority`,
`safe_to_queue`, `red_flags_present` (final), `staff_review_required` (final), target dashboard
filter, and the staff-resolution path.

---

## TEST CALL MATRIX — every case/category the dashboard can show

IDs use prefix `TEST-<batch>-NNN-<TAG>`. "Filter" = where it must land in the dashboard worklist
(`filter_clause`: `all, urgent_red_flags, needs_review, identity_issues, open, resolved,
resolved_today`). Free-text (summary/task body) is asserted as **contains key facts**, since
Ollama output varies run-to-run; the deterministic fields are asserted **exactly**.

### A. Happy-path verified requests (land in `open`, resolvable cleanly)

| # | Tag | request_type | Caller | Expect verification | Expect priority | safe_to_queue | Filter |
|---|-----|--------------|--------|--------------------|-----------------|---------------|--------|
| 001 | PRESCRIPTION-MATCH | prescription | self, clear | matched | routine | true | open |
| 002 | TESTRESULT-MATCH | test_result | self, clear | matched | routine | true | open |
| 003 | APPT-REDIRECT | appointment_redirect | self, clear | matched | routine | true | open |

### B. Verified but needs human review (land in `needs_review`)

| # | Tag | request_type | Caller | Expect verification | Expect priority | staff_review | Filter |
|---|-----|--------------|--------|--------------------|-----------------|--------------|--------|
| 004 | SICKNOTE-REVIEW | sick_note | self, clear | matched | routine | true | needs_review |
| 005 | REFERRAL-CHASE | referral | self, clear | matched | routine | true | needs_review |
| 006 | MULTI-INTENT | needs_review | self, rambling | matched | review_required | true | needs_review |
| 007 | UNKNOWN-PATHWAY | unknown | self, vague | matched | review_required | true | needs_review |

### C. Identity / verification problems (land in `identity_issues`)

| # | Tag | request_type | Caller | Expect verification | safe_to_queue | Filter |
|---|-----|--------------|--------|--------------------|---------------|--------|
| 008 | THIRD-PARTY | admin | third_party (brother), partial details | possible_match | false | identity_issues |
| 009 | INSUFFICIENT-ID | prescription | self, refuses/forgets DOB+postcode | insufficient_id (review_required) | false | identity_issues |
| 010 | NO-MATCH | admin | self, details not in reference data | no_match | false | identity_issues |
| 011 | CARER-PROXY | sick_note | carer for elderly parent | possible_match | false | identity_issues |
| 012 | MISMATCH-NAME-DOB | prescription | self, name and DOB disagree with record | possible_match | false | identity_issues |

### D. Red-flag emergencies (land in `urgent_red_flags`, priority `999 Emergency`)

| # | Tag | request_type | Symptom spoken | Expect red_flags | Expect priority | safe_to_queue | Filter |
|---|-----|--------------|----------------|------------------|-----------------|---------------|--------|
| 013 | REDFLAG-CARDIAC | appointment_redirect | chest pain + breathlessness + sweating | true | 999 Emergency | false | urgent_red_flags |
| 014 | REDFLAG-STROKE | appointment_redirect | face droop, arm weakness, slurred speech (FAST) | true | 999 Emergency | false | urgent_red_flags |
| 015 | REDFLAG-SEPSIS | appointment_redirect | high fever, confusion, rapid breathing, mottled skin | true | 999 Emergency | false | urgent_red_flags |
| 016 | REDFLAG-MHCRISIS | appointment_redirect | active suicidal intent | true | 999 Emergency | false | urgent_red_flags |

### E. Difficult callers (verify the pipeline copes; placement depends on content)

| # | Tag | request_type | Difficulty | Expect | Filter |
|---|-----|--------------|-----------|--------|--------|
| 017 | ANGRY-ABUSIVE | admin | hostile, swearing, demanding | matched, captured calmly, review_required | needs_review |
| 018 | CONFUSED-ELDERLY | prescription | repeats self, loses thread | matched if details given, else possible_match | needs_review / identity_issues |
| 019 | NON-NATIVE-EN | sick_note | limited English, broken phrasing | matched if parseable, staff_review true | needs_review |
| 020 | CHILD-CALLER | appointment_redirect | minor calling for a parent | possible_match (third-party/safeguarding note) | identity_issues |

### F. Bad / degraded transcripts (robustness — must NEVER crash the importer)

| # | Tag | request_type | Transcript defect | Expect | Filter |
|---|-----|--------------|-------------------|--------|--------|
| 021 | TRUNCATED | unknown | cuts off mid-sentence | safe fallback task, staff_review true | needs_review |
| 022 | GARBLED-ASR | unknown | heavy mis-recognition, nonsense tokens | safe fallback, low extraction_confidence, staff_review true | needs_review |
| 023 | NEAR-SILENT | unknown | almost no speech, padded to >500 chars | "Processing output unavailable - staff review required" fallback | needs_review |
| 024 | LONG-RAMBLE | needs_review | 1500+ chars, multiple topics, one buried red flag | red flag caught → urgent; else review_required | urgent_red_flags / needs_review |
| 025 | LANG-MIXED | unknown | English + other-language fragments | safe fallback, staff_review true | needs_review |

> **Coverage check:** matrix above exercises all 8 request types, all 4 verification states
> (matched / possible_match / no_match / insufficient_id), all 4 priority bands
> (routine / review_required / urgent_review-equivalent / 999 Emergency), and all 6 dashboard
> filters. If a request adds a new pathway or filter, add a row here in the same run.

---

## STAFF RESOLUTION — simulate a real reception worker on every case

After import, each case is actioned exactly as Churchtown reception would, via the live dashboard
endpoints (FastAPI, `:8765`). Locked fields must be rejected silently; staff fields must persist.

**Endpoints:**

- **Full update** — `POST /case/<call_id>/update`
  Body: `status, assigned_to, action_needed, outcome_notes, staff_action, resolved_by,
  last_edited_by, mark_resolved=yes` (+ `priority`, `verification_status`, `safe_to_queue` which
  MUST be ignored — they are locked). Success = `303` redirect; one `audit_events` row written.

- **Quick action** — `POST /case/<call_id>/quick_action`
  Body: `action ∈ {start_review, flag_issue, resolve}`, `assigned_to`, `edited_by`/`resolved_by`.
  `start_review` → status `Needs Review`; `flag_issue` → `action_needed = "Issue flagged by staff"`.

**Resolution script per category:**

| Category | Staff steps to simulate | Must-pass assertions |
|----------|------------------------|----------------------|
| A (happy path) | open → assign → `update` with `mark_resolved=yes`, outcome notes | status `Resolved`, `resolved_at` + `turnaround_minutes` set, locked fields unchanged |
| B (needs review) | `quick_action start_review` → assign → `update` resolve with notes | status transitions New→Needs Review→Resolved; staff fields persist on re-import |
| C (identity) | `quick_action start_review` → attempt `resolve` **without** notes → then with notes | resolve without notes returns **400** ("Outcome notes are required before resolving an identity issue."), succeeds with notes |
| D (red flag) | attempt `quick_action resolve` **without** notes → then full `update` resolve with escalation notes | resolve without notes returns **400** ("...before resolving a red-flag case."); priority stays `999 Emergency` |
| E (difficult) | `quick_action flag_issue` → assign → resolve with notes | action_needed = "Issue flagged by staff"; no crash; audit row per action |
| F (bad transcript) | `quick_action start_review` → resolve with notes | fallback task_title/body present; case resolvable; importer never errored on the file |

**Locked-field probe (run on at least one case per batch):** send an `update` that also tries to
change `priority=999 Emergency`, `verification_status=no_match`, `safe_to_queue=false`. Assert the
three locked fields are **unchanged** from their imported values while staff fields update.

---

## INDEPENDENT MONITORING AGENTS (run concurrently with the batch)

Every test run is watched in real time by independent agents (spawn via the `Agent` tool;
one per lane, running simultaneously, each blind to the others so issues aren't masked):

1. **Pipeline monitor** — watches `queue/` stages + `outputs/handoff_json/` + importer log; flags
   stuck items, deadletter hits, decrypt failures, files that never reach the dashboard.
2. **Safety monitor** — asserts the CORE SAFETY INVARIANT on every imported case: confirms
   identity/priority/verification/safe_to_queue match the deterministic rule, not the LLM wording.
   Any drift = critical, stop the run.
3. **Dashboard/UX monitor** — confirms each case lands in its EXPECTED filter, renders without raw
   JSON leaking, and the staff-action endpoints behave (status codes, audit rows, locked fields).
4. **Data-integrity monitor** — checks no duplicate cases on re-import, staff fields preserved,
   GDPR fields (no real PII), timestamps parse, turnaround computed.

Each agent returns: issues found (severity), and improvement suggestions. The Lead Agent
consolidates.

### Per-run report file (required artifact)

Write one file per run: `docs/reports/test-run-<YYYYMMDD-HHMMSS>.md`, plain English (caveman),
committed at session close. Structure:

```
# TEST RUN — <batch_id> — <date> <time>
## RESULT: PASS / FAIL (X of Y cases correct)
## WHAT WE TESTED: <one line — how many calls, what kinds>
## WHAT PASSED: <bullets>
## WHAT FAILED: <bullets, each with case id + what was expected vs seen + severity>
## SAFETY CHECK: <invariant held? yes/no — if no, this is a STOP>
## IMPROVEMENT SUGGESTIONS: <from monitoring agents>
## PENDING SAEED: <anything needing sign-off>
```

A FAIL on any red-flag case, any identity case, or the safety invariant is a hard stop — escalate
to Saeed in the same run report, do not auto-resolve.

---

## PASS / FAIL CRITERIA (whole run)

- **PASS** = every case lands in its expected filter; all deterministic fields match expectations;
  all staff-resolution assertions hold; locked fields unchanged; no deadletter; safety invariant
  held; importer never errored.
- **FAIL** = any of the above breaks. Red-flag, identity, or safety failures are **critical**.

Free-text variance (summary/task wording differs between Ollama runs) is **not** a failure as long
as the key facts are present and the deterministic fields are correct.

---

## TEMPLATE NOTE

This file is the reusable template. When Saeed says **"run tests"**: build a fresh batch from the
TEST CALL MATRIX (new `TEST-<timestamp>` prefix), send it the real way (n8n → live Ollama →
dashboard), simulate staff resolution on every case, run the four monitoring agents concurrently,
and produce the per-run report. Do not invent a lighter process; if you must shortcut a stage,
say so in the report and get Saeed's sign-off.

# TEST AGENT BRIEF — E2E CALL FLOW TEST
# Status: PENDING IMPLEMENTATION — do not build until Saeed gives go-ahead
# Created: 2026-05-29
# Author: Lead Agent (Saeed directive)
# Last updated: 2026-05-29

---

## OBJECTIVE

Build a commanded E2E call flow test that exercises the entire JeffLocal system
end-to-end: simulated patient calls → n8n webhook → pipeline → handoff JSON →
dashboard import → case verification → watchdog health check.

Run on command only. Not part of CI. Not run automatically.

---

## CALL SUITE — 10 mixed cases

All call IDs are unique per run using timestamp:
`E2E-{YYYYMMDD-HHMMSS}-{seq:02d}-{LABEL}`
e.g. `E2E-20260530-143022-01-PRESCRIPTION`

| # | Label | Pathway | Special conditions |
|---|---|---|---|
| 1 | PRESCRIPTION | prescription | Routine repeat, clean identity, high confidence |
| 2 | SICKNOTE | sick_note | New fit note, staff_review_required=True |
| 3 | REFERRAL | referral | Referral chase, medium confidence |
| 4 | TEST-RESULT | test_result | Chasing blood results |
| 5 | REDFLAG | appointment_redirect | Chest pain + breathlessness, 999 advice given, red_flags_present=True |
| 6 | IDENTITY-MISMATCH | prescription | Third-party call, name mismatch, staff_review_required=True |
| 7 | ADMIN | admin | Address change request |
| 8 | LOW-CONFIDENCE | unknown | Unclear intent, confidence=0.68 (below 0.72 floor → fallback flag expected) |
| 9 | MULTI-INTENT | prescription | Caller asks for prescription AND sick note — messy transcript, needs review |
| 10 | EMERGENCY-ESCALATION | appointment_redirect | Stroke symptoms, 999 escalation, priority=Critical |

Requirements:
- Full realistic transcripts for every case (not placeholder text)
- All 8 pathways covered across the 10 cases
- Unique call IDs every run — no collision with existing cases in DB

---

## TEST STAGES

### Stage 1 — Pre-flight
- Watchdog health: all 5 services responding
  - Production dashboard (8765) — HTTP /api/health
  - Sandbox dashboard (5000) — HTTP /api/health
  - n8n (5678) — HTTP /healthz
  - Ollama (11434) — HTTP /api/tags
  - Cloudflare tunnel — cloudflared.exe process present
- Dashboard /api/health returns ok=True
- Config files present: model_settings.json, routing_rules.json, pathways.json, model_monitoring.json

### Stage 2 — Inject calls
- POST all 10 payloads to n8n webhook
- Record batch_id and all 10 call_ids
- Wait for pipeline (configurable, default 30s via --wait-seconds)

### Stage 3 — Dashboard verification
- POST /api/sync to import handoffs
- Assert all 10 call_ids appear as cases on dashboard
- Assert case 5 (REDFLAG): red_flags_present=True, priority=Urgent
- Assert case 6 (IDENTITY): staff_review_required=True
- Assert case 8 (LOW-CONFIDENCE): flagged for review (confidence below floor)
- Assert case 10 (EMERGENCY): priority=Critical

### Stage 4 — Watchdog re-check
- All 5 services still healthy after load
- No unexpected restart events in logs/service_control/watchdog.log during test window

### Stage 5 — Report
- Print pass/fail per case and per stage to stdout
- Write JSON report to: logs/e2e_callflow_{timestamp}.json
- Exit code 0 = all pass, Exit code 1 = any failure

---

## FILES TO CREATE

```
tests/run_e2e_callflow_test.py        — Main test runner (Python, cross-platform)
tests/fixtures/e2e_callflow_pack.py   — 10 call payloads with unique ID generation
tests/E2E_CALLFLOW_README.md          — How to run, what each case tests, expected output
```

---

## COMMAND-LINE INTERFACE

```
python tests/run_e2e_callflow_test.py \
  [--webhook-url http://localhost:5678/webhook/jeff-intake] \
  [--dashboard-url http://localhost:8765] \
  [--wait-seconds 30] \
  [--cleanup]           # auto-purge E2E test cases from DB after run
  [--stage 1-5]         # run a single stage only (default: all)
```

Defaults:
- webhook-url: http://localhost:5678/webhook/jeff-intake
- dashboard-url: http://localhost:8765
- wait-seconds: 30

---

## CONSTRAINTS

- Must not touch production patient data
- Test cases auto-purge on --cleanup flag (DELETE FROM cases WHERE call_id LIKE 'E2E-%')
- Payload format must match existing n8n_webhook_test_pack.py structure
- Use existing fixture helpers from tests/fixtures/ where possible
- Security Agent review required before any PR

---

## CALL ID FORMAT

```python
from datetime import datetime, timezone
ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
call_id = f"E2E-{ts}-{seq:02d}-{label}"
# e.g. E2E-20260530-143022-05-REDFLAG
```

---

## STATUS NOTES

- [ ] NOT YET BUILT — awaiting Saeed go-ahead
- [ ] Saeed may add or edit requirements before implementation
- [ ] Auth fix (conftest.py session fixture) must be done first —
      test runner makes authenticated dashboard requests
- [ ] Security Agent review required before PR

---

*Saved by Lead Agent 2026-05-29. Do not implement without Saeed instruction.*

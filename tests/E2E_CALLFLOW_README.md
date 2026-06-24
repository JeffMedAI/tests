# JeffLocal — E2E Call Flow Test

Tests the full JeffLocal system end-to-end on command.  
Not part of CI. Run manually when you want a full system verification.

---

## What it tests

```
Patient call payloads
  → POST to n8n webhook (localhost:5678)
    → Pipeline processes (run_intake.ps1 → Ollama → build_handoff.ps1)
      → Handoff JSON written to outputs/handoff_json/
        → Dashboard imports cases (/api/sync)
          → Cases verified via /api/cases/{call_id}
            → Watchdog health re-checked across all 5 services
```

---

## Quick start

```bash
# All 5 stages, default URLs
python tests/run_e2e_callflow_test.py

# Custom webhook URL
python tests/run_e2e_callflow_test.py --webhook-url http://localhost:5678/webhook/jeff-intake

# Longer pipeline wait (if Ollama is slow)
python tests/run_e2e_callflow_test.py --wait-seconds 60

# Run and clean up test cases afterwards
python tests/run_e2e_callflow_test.py --cleanup

# Single stage only
python tests/run_e2e_callflow_test.py --stage 1   # pre-flight only
python tests/run_e2e_callflow_test.py --stage 3   # verify only (cases must already exist)
```

---

## Arguments

| Argument | Default | Description |
|---|---|---|
| `--webhook-url` | `http://localhost:5678/webhook/ava-live-intake` | n8n webhook endpoint |
| `--dashboard-url` | `http://localhost:8765` | Dashboard base URL |
| `--wait-seconds` | `30` | Seconds to wait after injection before verifying |
| `--timeout` | `120` | HTTP timeout for the webhook POST |
| `--stage` | all | Run a single stage (1-5) |
| `--cleanup` | off | Delete E2E cases from dashboard DB after run |
| `--no-colour` | off | Disable ANSI colour output |

---

## The 10 test cases

Every run generates unique call IDs: `E2E-{YYYYMMDD-HHMMSS}-{seq:02d}-{LABEL}`  
No collision with existing cases. Clean run every time.

| # | Label | Pathway | What it tests |
|---|---|---|---|
| 01 | PRESCRIPTION | prescription | Routine repeat, clean identity, high confidence (0.96) |
| 02 | SICKNOTE | sick_note | New fit note, staff_review_required=True |
| 03 | REFERRAL | referral | Referral chase, medium confidence (0.88) |
| 04 | TEST-RESULT | test_result | Chasing blood results (kidney + thyroid) |
| 05 | REDFLAG | appointment_redirect | Chest pain, sweating, breathlessness — 999 advised, red_flags_present verified |
| 06 | IDENTITY-MISMATCH | prescription | Third-party call, name unclear — staff_review_required verified |
| 07 | ADMIN | admin | Address change request |
| 08 | LOW-CONFIDENCE | unknown | Unclear intent, confidence=0.65 — below 0.72 floor, verified |
| 09 | MULTI-INTENT | prescription | Prescription + sick note in same call — messy transcript |
| 10 | EMERGENCY-ESCALATION | appointment_redirect | Stroke symptoms (FAST criteria), 999 escalation, red_flags_present verified |

---

## Stages

| Stage | Name | What happens |
|---|---|---|
| 1 | Pre-flight | Checks all 5 services are healthy, config files present |
| 2 | Inject | POSTs all 10 calls to n8n, waits for pipeline |
| 3 | Verify | Syncs dashboard, checks each case exists, validates flags |
| 4 | Watchdog | Re-checks all services, scans watchdog log for CRITICALs |
| 5 | Report | Prints pass/fail summary, writes JSON to logs/ |

---

## Output

Pass/fail printed to stdout with colour indicators:
```
✓ Production dashboard /api/health
✓ n8n port 5678 responding
✓ Ollama /api/tags responding
✓ Case found: E2E-20260530-143022-01-PRESCRIPTION
✓   E2E-20260530-143022-05-REDFLAG: red_flags_present=True
✗   E2E-20260530-143022-08-LOW-CONFIDENCE: confidence below floor  [confidence=0.71]
```

JSON report written to: `logs/e2e_callflow_{run_ts}.json`  
Exit code: `0` = all pass, `1` = any failure

---

## Requirements

- All 5 services running: production dashboard (8765), n8n (5678), Ollama (11434), Cloudflare tunnel
- n8n webhook configured to accept `jeff-intake` batch payloads
- Config files present in `config/`
- Python 3.10+, no extra packages required (stdlib only)

---

## Cleanup

Test cases are prefixed `E2E-` so they're easy to identify.  
To remove them from the dashboard DB after a test run:

```bash
python tests/run_e2e_callflow_test.py --cleanup
```

Or manually in SQLite:
```sql
DELETE FROM cases WHERE call_id LIKE 'E2E-%';
```

---

## Files

```
tests/run_e2e_callflow_test.py        — Main test runner
tests/fixtures/e2e_callflow_pack.py   — 10 call payloads
tests/E2E_CALLFLOW_README.md          — This file
logs/e2e_callflow_{ts}.json           — Per-run JSON reports
```

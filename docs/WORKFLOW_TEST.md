# WORKFLOW_TEST.md — Avamed Test Pipeline Map

> Source of truth for running test calls through the Avamed pipeline.
> Read this before creating or running any test. Last updated: 2026-06-16.

---

## 1. Current test assets (latest)

| Asset | Path | Purpose |
|-------|------|---------|
| **Fixture (latest)** | `tests/fixtures/rich_mixed_pack.py` | Builds **12** rich test calls covering all dashboard fields and scenarios. |
| **Sender (direct)** | `tests/send_rich_mixed_test_calls.py` | Writes finished handoff JSON straight to `outputs/handoff_json/`. **Bypasses n8n** — dashboard-import test only. |
| **n8n webhook fixture** | `tests/fixtures/n8n_webhook_test_pack.py` | Older `n8ntest`-prefix pack (DEFUNCT — kept for reference only). |

**Defunct prefixes — do NOT reuse for new tests:** `rawmock`, `n8ntest`, `gpdemo`.

**Latest pack call_id format:** `RICH-{yyyyMMdd-HHmmss}-{NN}-{LABEL}` (e.g. `RICH-20260616-141500-01-ROUTINE-PRESCRIPTION`).

The 12 rich_mixed scenarios:

| # | Type | Scenario |
|---|------|----------|
| 1 | prescription | Routine, clean/easy (Margaret Holden) |
| 2 | sick_note | Anxious caller |
| 3 | referral | Dermatology |
| 4 | test_result | Frustrated caller |
| 5 | appointment_redirect | Chest-pain emergency (red flag) |
| 6 | appointment_redirect | Confused elderly, poor audio |
| 7 | admin | Address change |
| 8 | prescription | Missing info, low confidence |
| 9 | appointment_redirect | Parent calling for child |
| 10 | prescription | Duplicate-meds alert |
| 11 | prescription | Comprehensive clear call |
| 12 | (see fixture) | — |

---

## 2. The full pipeline (entry → dashboard)

```
[1] Jeff (Hostcomm voice AI) captures call reason
        │
        ▼
[2] queue/encrypted_raw/   ──poll──►  queue/incoming/
        │   app/poll_encrypted_intake_queue.ps1
        ▼
[3] process_queue.ps1  →  Ollama/Gemma extraction (model gemma4:e2b, temp 0.1)
        │                  app/run_intake.ps1 / run_encrypted_intake_cycle.ps1
        ▼
[4] DETERMINISTIC matching + safety fields
        │   (verification_status, safe_to_queue, priority, matched_patient_name,
        │    EMIS/NHS/DOB, clinical urgency — NEVER set by the LLM)
        ▼
[5] outputs/handoff_json/{call_id}_handoff.json
        │
        ▼
[6] n8n routes intake  (port 5678)
        │   Workflow "06 Test Intake Webhook"
        ▼
[7] Dashboard importer  →  SQLite (dashboard/data/dashboard.sqlite)
        │   import_handoffs(conn, pattern="*_handoff.json")
        ▼
[8] Staff dashboard (port 8765, C:\JeffLocal\dashboard\)
```

**Queue stages:** `encrypted_raw → incoming → processing → processed / failed / deadletter`

---

## 3. The n8n webhook path (how a test runs through the FULL pipeline)

**Workflow:** `JeffLocal - 06 Test Intake Webhook`
- **n8n ID:** `0pRmm3xCHP4wsVyy` (active)
- **Webhook (entry):** `POST http://localhost:5678/webhook/ava-live-intake`
- **Nodes:** Webhook → HTTP Request → Respond to Webhook
- **HTTP Request node** wraps each incoming call into a batch envelope and POSTs to the dashboard:

```
POST http://127.0.0.1:8765/api/n8n/test-intake-batch
{
  "batch_id": "<from payload.body.batch_id or yyyyMMdd-HHmmss>",
  "test_mode": true,
  "disable_google_push": true,
  "source": "n8n_test_webhook",
  "calls": [ <the call body> ]
}
```

**Dashboard endpoint `/api/n8n/test-intake-batch` (main.py:3737):**
- Requires `test_mode=true` AND `disable_google_push=true` (else HTTP 400).
- `calls` must be an array of **1 to 5** objects, with **unique** call_ids.
- HMAC-protected via `JEFF_WEBHOOK_SECRET` when set (`verify_webhook_hmac`).
- It then: archives prior n8ntest artifacts → writes envelopes → **runs the real encrypted intake cycle (Ollama extraction + matching)** → imports fresh handoffs into SQLite.
- This endpoint is SANDBOX/TEST ONLY and will be removed before production.

> Because n8n wraps **one call per webhook POST**, run the 12 rich_mixed calls by POSTing each call individually to the webhook.

---

## 4. How to run a NEW test through the full n8n pipeline

**Pre-flight (services must be up):**
- Ollama (port 11434, model `gemma4:e2b`)
- n8n (port 5678) — workflow 06 active
- Dashboard (port 8765)

**Steps:**
1. Build the calls from the latest fixture:
   ```python
   from tests.fixtures.rich_mixed_pack import build_rich_calls
   calls = build_rich_calls()   # 12 calls, fresh RICH- timestamp
   ```
2. POST each call to the n8n webhook (one at a time):
   ```
   POST http://localhost:5678/webhook/ava-live-intake
   Content-Type: application/json
   <single call object>
   ```
3. Verify each batch response: `ok: true`, `batch_processed`, `batch_handoffs`, `batch_failed: 0`, `batch_deadletter: 0`.
4. Confirm cases in the dashboard at `http://localhost:8765/requests`.

**To run the DIRECT (dashboard-only, no n8n) path instead:**
```
python tests/send_rich_mixed_test_calls.py   # writes handoff JSON → importer picks up
```

---

## 5. n8n maintenance / fix scripts

| Script | Purpose |
|--------|---------|
| `scripts/fix_wf06_jsonbody.py` | Rewrites workflow 06's HTTP Request `jsonBody` expression (correct `={{ }}` delimiters, passes `batch_id`/`call_id` through, wraps call into batch envelope). Deactivate → PUT update → reactivate via n8n API. |
| `scripts/service_control/fix_n8n_workflows.py` | Broader n8n workflow repair. |

n8n API key is read from `C:\Users\s5256\.n8n\database.sqlite` (`user_api_keys` table).

---

## 6. All n8n workflows (current)

| ID | Name | Active |
|----|------|--------|
| `0pRmm3xCHP4wsVyy` | 06 Test Intake Webhook | ✅ |
| `M8z6HI401t8GUl1f` | 05 Daily Summary | ✅ |
| `gW3L08bbmr744aKh` | 04 Overdue Scan | ✅ |
| `wuHsIjBf3pkNEMpa` | 03 Red Flag Scan | ✅ |
| `ZYmUGt1lmT4XASNL` | 02 Dashboard Sync | ❌ |
| `uDfd2t1gz6PCU1qi` | 01 Health Check | ❌ |

---

## 7. Safety rules for tests (non-negotiable)

- **No real patient data** in fixtures, commits, or examples. Use synthetic names/NHS numbers only.
- **Google push must stay disabled** for all test runs (`disable_google_push: true`).
- Deterministic fields (verification_status, priority, safe_to_queue, identity) must come from pipeline code, never from the LLM or hand-edited into fixtures as "expected" production values.
- ENI (EMIS/NHS integration) is INACTIVE (Phase 2). Do not trigger it in tests.

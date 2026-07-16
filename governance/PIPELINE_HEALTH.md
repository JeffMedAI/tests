# PIPELINE HEALTH — Monitoring Reference
**Owner:** DevOps Agent  
**Last updated:** 2026-06-18

---

## Pipeline Stages and Health Indicators

```
Jeff voice AI → queue/encrypted_raw/ → queue/incoming/ → processing → queue/processed/
                                                       ↘ queue/deadletter/ (failures)
         Ollama/Gemma (gemma4:e2b)
              ↓
         Deterministic patient matching + safety rules
              ↓
         outputs/handoff_json/<call_id>_handoff.json
              ↓
         Dashboard importer → SQLite cases table
```

---

## Health Metrics

| Metric | How to check | Green | Amber | Red |
|--------|-------------|-------|-------|-----|
| queue/incoming/ file count | `(ls C:\JeffLocal\queue\incoming\).Count` | 0 (between calls) | 1–3 (processing) | > 3 for > 5 min |
| queue/deadletter/ count | `(ls C:\JeffLocal\queue\deadletter\).Count` | 0 | 1–5 (investigate) | > 5 (stop and fix) |
| Ollama response time | Pipeline log: `encrypted_intake_cycle_YYYY-MM-DD.log` | < 60s | 60–120s | > 120s |
| Cases in DB today | See health_check.md quick check | Matches expected call volume | — | 0 when calls expected |
| Handoff inbox (waiting to import) | `(ls C:\JeffLocal\outputs\handoff_json\ -File).Count` | 0 (between calls) | 1–5 (mid-import) | Files persisting > 5 min (import failing, or retire blocked by a file lock) |
| Handoff JSON files (imported) | `(ls C:\JeffLocal\outputs\handoff_json\processed\ -File).Count` | Matches case count in DB | — | Fewer than DB rows (files removed outside the purge) |

---

## Log Locations

| Component | Log path |
|-----------|---------|
| Pipeline (PS) | `C:\JeffLocal\logs\app\encrypted_intake_cycle_YYYY-MM-DD.log` |
| Dashboard (uvicorn) | `C:\JeffLocal\logs\dashboard\` |
| Backup | `C:\JeffLocal\logs\backup\backup_YYYY-MM-DD.log` |
| n8n | Task Scheduler history for `JeffLocal - n8n Watchdog` |

---

## Dead-Letter Causes and Fixes

| Cause | How to identify | Fix |
|-------|----------------|-----|
| JEIE-1 decrypt failure | File in deadletter/, log shows "HMAC" or "decrypt" error | Check keys in config/keys/ match those used by n8n |
| Wrong payload shape | n8n sends wrong JSON structure | Check WF06 HTTP Request node body expression |
| Missing required field | Log shows KeyError or missing field | Check voice agent payload format |
| DB write error | Log shows SQLite error | Check dashboard is running; check DB not locked |

---

## Current Known Issues (2026-06-18)

- 5 items in deadletter queue from pre-pipeline-fix era (WF06 bug). These are historical — do not replay without Saeed's instruction. No replay tooling exists yet.

---

## Baseline Metrics (record after Churchtown go-live)

| Metric | Baseline (first week) |
|--------|----------------------|
| Calls/day | — |
| Processing time avg | — |
| Dead-letter rate | — |
| Ollama model | gemma4:e2b |
| Fallback model | gemma4:e4b (if monitoring score < 0.72) |

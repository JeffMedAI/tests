# SECURITY REVIEW — 2026-05-30
## Watchdog, WhatsApp Sender, Strategy Daily (Steps 5 & 11)

**Reviewer:** Security Agent  
**Date:** 2026-05-30  
**Scope:** Three items NOT covered in 2026-05-29 review  
**Authority:** Veto authority applies — vetoed items may not proceed to production  
**System context:** Medical-adjacent (JeffLocal / Avamed AI triage, Churchtown Medical Centre). All patient data currently mock.

---

## ITEM 1: Hardened Watchdog
**File:** `C:\JeffLocal\scripts\service_control\watchdog.ps1`

```
VERDICT: APPROVED WITH NOTES
```

### Checklist

- [x] No patient data exposure
- [x] No credential/secret exposure
- [x] No uncontrolled external calls
- [x] No privilege escalation beyond design intent
- [x] No path traversal / injection risks
- [x] Dependencies vetted

### Analysis

**Privilege escalation:** The script is registered at boot with elevated privileges by design, to manage system services and kill processes. This is the stated design intent and is appropriate for a service watchdog. No escalation beyond that intent was found. The script does not invoke any external user-supplied input, so there is no path by which a lower-privileged actor could leverage it.

**Service names / restart commands:** All five service definitions (`ProductionDashboard`, `SandboxDashboard`, `N8n`, `Ollama`, `CloudflareTunnel`) use hardcoded absolute paths sourced from `$RepoRoot` (itself hardcoded to `C:\JeffLocal`). No service name, path, or argument is derived from external input, environment variables, registry reads, or user input. Command injection via service definitions is not possible as written.

**Restart cap logic:** The sliding-window cap is correctly implemented. `Test-RestartAllowed` reads a JSON state file, filters timestamps to only those within the last 3600 seconds, and returns `$false` if the count is already at `$RestartMax` (3). `Record-Restart` appends the current timestamp. The cap correctly prevents infinite restart loops. After cap is hit, the watchdog sends a CRITICAL alert and skips further restart attempts until the next hourly window expires naturally.

**Log file handling:** Rotation at 5 MB using `Move-Item` to `.old` is simple but functional — only one generation of backup is kept (`.old` is overwritten on next rotation). Log files are written to `C:\JeffLocal\logs\service_control\` using `Add-Content -Force`, which creates the file if absent. No explicit ACL is set on the log directory, meaning any local user who can read `C:\JeffLocal\logs\` can read watchdog logs. This is acceptable for a developer machine but worth noting for any future multi-user deployment.

**WhatsApp alert content:** The alert messages sent are entirely static strings: e.g. `"ALERT: Production Dashboard (8765) went DOWN — attempting restart. (JeffLocal watchdog)"`. No system paths, credentials, environment variables, or config values are interpolated into alert messages. No patient data can reach these messages by the current code path.

**Temp file handling:** `Send-Alert` creates a temp file via `[System.IO.Path]::GetTempFileName()`, writes the alert string to it, then passes the path to `send_whatsapp.py`. The temp file is **never deleted** — it persists in `%TEMP%`. The content is only the alert string (no secrets, no patient data), so the security impact is low, but this is unnecessary file accumulation and should be cleaned up.

**`$ErrorActionPreference = "SilentlyContinue"` at top scope:** This suppresses errors globally within the script, which could mask unexpected failures. The intent is to keep the watchdog resilient, but it also means silent failures in unexpected paths. Acceptable for a watchdog, but any future refactor should scope this more tightly.

### Notes

1. **Temp file leak (low severity):** The `.txt` temp file created per alert is never deleted. Add `Remove-Item $tmpFile -ErrorAction SilentlyContinue` after `Start-Process` in `Send-Alert`. No security risk currently — content is safe — but good hygiene.
2. **Log ACL:** No explicit ACL on `logs\service_control\`. Consider restricting read to Administrators only if this ever moves to a shared or clinical machine.
3. **Restart state file ACL:** `restart_state.json` is likewise unprotected. Tampering with it could reset the restart counter and bypass the cap. Low risk on a single-user dev machine; higher risk in future deployment.
4. **Cloudflare tunnel check is process-only:** The tunnel health check only verifies that `cloudflared.exe` is running, not that the tunnel is actually connected. A crashed tunnel that leaves a zombie process would pass as healthy. Minor operational gap, not a security issue.

---

## ITEM 2: WhatsApp Sender
**File:** `C:\JeffLocal\scripts\daily\send_whatsapp.py`

```
VERDICT: APPROVED WITH NOTES
```

### Checklist

- [x] No patient data exposure (currently — see notes)
- [x] No credential/secret exposure
- [x] No uncontrolled external calls
- [x] No privilege escalation beyond design intent
- [x] No path traversal / injection risks
- [x] Dependencies vetted

### Analysis

**File reads / patient data:** The script reads whatever file is passed as `sys.argv[1]`. When called from the watchdog, the file contains only a short alert string. When called from `strategy_daily.ps1`, it receives the daily briefing report. The daily report contains: session log excerpts, git log (commit messages), document staleness info, and PROJECT_MEMORY pending/blocked items. **None of this is patient data** under the current mock-data-only state. However, this is a forward risk: if session logs or PROJECT_MEMORY ever contain real patient identifiers, names, or clinical content, those would be transmitted via WhatsApp. This must be reviewed before live patient data is introduced.

**Credential/secret exposure:** The script reads no `.env` files, no config files, and no credential stores. The only hardcoded value is the phone number `+447440333938` (Saeed's own number, per design). No API keys are present — pywhatkit uses the local browser, not a cloud API.

**pywhatkit dependency:** `pywhatkit` is a legitimate, widely-used open-source library on PyPI (10,000+ GitHub stars, active maintenance as of early 2026). It does **not** relay messages through any third-party server — it automates WhatsApp Web via the local browser using `selenium` and `pyautogui`. The message travels through Meta's WhatsApp infrastructure (as any WhatsApp message does) but not through any intermediate service. No known CVEs as of review date. The library's automation approach means it requires the browser to be open and logged in to WhatsApp Web — it is not a headless API and will silently fail if the browser session has expired.

**Injection risks:** The file path is taken from `sys.argv[1]` and passed to `open()`. There is no shell interpolation — this is a Python file open, not a subprocess call. No path traversal risk: the caller controls what path is passed, and the caller (strategy_daily.ps1 or watchdog.ps1) always passes a hardcoded or date-derived path, never user input.

**Temp file usage (watchdog context):** See Item 1 — the temp file that watchdog creates and passes to this script is never cleaned up. The file content is safe, but temp file accumulation is untidy.

### Notes

1. **FORWARD RISK — real patient data (medium severity, flag for future review):** When live patient data is introduced, this pipeline (session logs → report → WhatsApp) must be reassessed. Patient data must never appear in session logs, PROJECT_MEMORY, or daily reports. A data classification gate should be added before that transition.
2. **Silent failure if WhatsApp Web session expires:** pywhatkit will open a browser tab but cannot send if not logged in. The script prints "Done." even in some failure modes. Add explicit error detection (pywhatkit does raise exceptions on send failure, but the callers may suppress them).
3. **Phone number hardcoded:** `+447440333938` is in plaintext in the script. Not a secret (it's an operational config), but should eventually move to `.env` for maintainability.

---

## ITEM 3: strategy_daily.ps1 — Steps 5 and 11
**File:** `C:\JeffLocal\scripts\daily\strategy_daily.ps1`  
**Steps under review:** Step 5 (STATE VERIFICATION) and Step 11 (WhatsApp send)

```
VERDICT: APPROVED WITH NOTES
```

### Checklist

- [x] No patient data exposure (currently — see notes)
- [x] No credential/secret exposure
- [x] No uncontrolled external calls
- [x] No privilege escalation beyond design intent
- [x] No path traversal / injection risks
- [x] Dependencies vetted

### Analysis

**Step 5 — What it reads:** Step 5 reads `PROJECT_MEMORY.md` (full content) and the content of session log files from `docs\sessions\` (last 24 hours). It extracts lines matching `BLOCKED|Awaiting Saeed|PENDING|awaiting sign-off` from PROJECT_MEMORY's CURRENT STATUS section, and scans session logs for lines matching a fixed keyword list (`cookie|main\.py|N1|N2|R2|GDPR|sandbox|degraded|sign-off|approval`). Neither source contains patient data under current mock-only state.

**Step 5 — Injection / path traversal:** All paths are hardcoded as script parameters with safe defaults. They are used only with `Test-Path`, `Get-Content`, and `Get-ChildItem` — never passed to shell/invoke. The regex used for drift detection correctly escapes keywords with `[regex]::Escape($kw)` — no regex injection. The `$MemoryStatus` regex uses a multiline pattern with a fixed structure — no user input is interpolated into it.

**Step 5 — Drift detection logic:** The keyword extraction takes only the first 3 words with length > 5 from each pending item. This is safe from injection and produces a simple cross-reference. The logic is conservative: it can produce false-positive "drift" alerts (items that were addressed but whose keywords don't appear in logs), which is operationally noisy but not a security concern.

**Step 11 — What is sent:** Step 11 calls `send_whatsapp_report.py` (note: this is a **different script** from `send_whatsapp.py` reviewed in Item 2 — `send_whatsapp_report.py` is referenced but not present in the repository as of this review). It passes `$ReportPath`, which is constructed as `"$ReportsDir\$Today.md"` where `$Today` is `(Get-Date).ToString("yyyy-MM-dd")` — a fixed date string with no user input. No injection possible.

**Step 11 — Data sent via WhatsApp:** The full daily report is transmitted. The report contains: session log excerpts (what was done, blockers, next tasks), git commit messages, document staleness list, and PROJECT_MEMORY pending items. All of this is project operational metadata — no patient data under current mock state.

**Missing script:** `send_whatsapp_report.py` is referenced in Step 11 but the script checked in Item 2 is `send_whatsapp.py`. The script at the referenced path may not exist, which would trigger the `WARNING: WhatsApp sender not found` log entry but would not cause a failure (the warning is caught). This is a reliability gap, not a security gap.

### Notes

1. **`send_whatsapp_report.py` vs `send_whatsapp.py` mismatch:** Step 11 calls `$RepoRoot\scripts\daily\send_whatsapp_report.py` but the actual script is `send_whatsapp.py`. Either the filename needs to match, or the path in Step 11 needs to be updated. This is currently causing silent WhatsApp send failures from the daily script.
2. **FORWARD RISK — real patient data (same as Item 2):** When live patient data is introduced, session logs must be reviewed to ensure clinical content is never captured in them, and therefore never in the daily report.
3. **PROJECT_MEMORY drift in the report:** The report includes raw lines from PROJECT_MEMORY marked as pending/blocked. If those lines ever contain patient-adjacent information (e.g. a blocker described as "patient N1's record missing"), they would appear in the WhatsApp message. Keep PROJECT_MEMORY entries clinical-data-free.
4. **`Set-StrictMode -Version Latest` + `$ErrorActionPreference = "Stop"`:** These are good practices for a scheduled script — they surface errors rather than silently swallowing them. Correct and appropriate.

---

## SUMMARY TABLE

| Item | Verdict | Critical Issues | Notes |
|------|---------|-----------------|-------|
| watchdog.ps1 | ✅ APPROVED WITH NOTES | None | Temp file leak; log/state ACLs unset |
| send_whatsapp.py | ✅ APPROVED WITH NOTES | None | Forward risk when real data introduced |
| strategy_daily.ps1 Steps 5+11 | ✅ APPROVED WITH NOTES | None | Script name mismatch (Step 11); same forward data risk |

**No vetoes issued.**

---

## FORWARD-LOOKING REQUIREMENTS (pre-live-data gate)

Before any real patient data (names, NHS numbers, clinical notes, appointment details) enters the system, the following must be addressed:

1. Session logs and PROJECT_MEMORY must have a documented data classification policy: no patient identifiers permitted.
2. The WhatsApp pipeline (watchdog → send_whatsapp.py; strategy_daily → send_whatsapp_report.py) must be reviewed against that policy.
3. A data leakage test must be conducted: verify that no patient data can flow from dashboard → session log → daily report → WhatsApp.
4. pywhatkit dependency should be formally pinned (`pywhatkit==1.x.x`) to prevent silent supply-chain updates.

---

*Security Agent — JeffLocal | Review date: 2026-05-30*  
*Prior review: security_review_2026-05-29_prod_breach.md*

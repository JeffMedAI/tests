# JeffLocal Staff Dashboard

Local-only FastAPI dashboard for reviewing JeffLocal handoff JSON files.

## Run

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\dashboard\run_dashboard.ps1
```

Open:

```text
http://127.0.0.1:8765
```

## Import Handoff JSON

The dashboard imports handoff files from:

```text
C:\JeffLocal\outputs\handoff_json\*_handoff.json
```

Import runs on dashboard startup. The `Import Handoffs` button can be used to re-run the import. Cases are upserted by `call_id`, so repeated imports do not duplicate cases.

## Locked Fields

JeffLocal remains the source of truth for request type, patient identity matching, verification status/reason, matched patient details, priority, safe-to-queue, red flags, staff-review flag, task title/body, transcript, call summary, and confidence fields.

The dashboard stores these fields as read-only case data and does not expose form inputs for them.

## Staff Editable Fields

Staff may update only:

- Status
- Assigned To
- Action Needed
- Outcome Notes
- Staff Action
- Resolved By
- Mark Resolved

The dashboard sets `Last Updated`, `Last Edited At`, `Resolved At`, and `Turnaround Minutes` automatically.

## Local-Only Safety

The dashboard does not call Ollama, perform patient matching, run the queue processor, post to Google Sheets, call Apps Script, or use external URLs. It only reads local handoff JSON and writes local SQLite/audit files.

SQLite data is stored at:

```text
C:\JeffLocal\dashboard\data\dashboard.sqlite
```

Dashboard staff updates are audited in SQLite and also appended to:

```text
C:\JeffLocal\logs\audits\dashboard_audit_YYYY-MM-DD.jsonl
```

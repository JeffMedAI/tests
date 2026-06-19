"""
Fix all n8n workflow bugs and activate scheduled workflows.
Run once: python fix_n8n_workflows.py
"""
import sqlite3
import json
import urllib.request
import urllib.error

N8N_BASE = "http://localhost:5678/api/v1"
DB_PATH = r"C:\Users\s5256\.n8n\database.sqlite"


def get_api_key():
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT apiKey FROM user_api_keys LIMIT 1").fetchone()
    conn.close()
    return row[0]


def n8n_request(method, path, body=None, api_key=None):
    url = N8N_BASE + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "X-N8N-API-KEY": api_key,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()


def put_workflow(wf_id, body, api_key):
    result, err = n8n_request("PUT", f"/workflows/{wf_id}", body, api_key)
    if err:
        print(f"  PUT error: {err}")
        return False
    print(f"  PUT OK — versionId: {result.get('versionId')}")
    return True


def activate_workflow(wf_id, api_key):
    result, err = n8n_request("POST", f"/workflows/{wf_id}/activate", {}, api_key)
    if err:
        print(f"  Activate error: {err}")
    else:
        print(f"  Activated — activeVersionId: {result.get('activeVersionId')}")


def deactivate_workflow(wf_id, api_key):
    result, err = n8n_request("POST", f"/workflows/{wf_id}/deactivate", {}, api_key)
    if err:
        print(f"  Deactivate error: {err}")
    else:
        print(f"  Deactivated")


def get_workflow(wf_id, api_key):
    result, err = n8n_request("GET", f"/workflows/{wf_id}", None, api_key)
    if err:
        print(f"  GET error: {err}")
    return result


def main():
    api_key = get_api_key()
    print(f"API key loaded ({api_key[:8]}...)\n")

    # ──────────────────────────────────────────────────────────────────────────
    # WORKFLOW 06 — Test Intake Webhook
    # The deactivate/reactivate already fixed the activeVersionId.
    # Verify and re-confirm the active version now has the batch wrapper.
    # ──────────────────────────────────────────────────────────────────────────
    print("=== Workflow 06 — Test Intake Webhook ===")
    wf06 = get_workflow("0pRmm3xCHP4wsVyy", api_key)
    if wf06:
        # Confirm the HTTP Request node has the batch wrapper
        http_node = next((n for n in wf06["nodes"] if n["name"] == "HTTP Request"), None)
        if http_node:
            body_val = http_node["parameters"].get("jsonBody", "")
            has_test_mode = "test_mode" in body_val
            has_calls = '"calls"' in body_val or "calls:" in body_val
            print(f"  test_mode in body: {has_test_mode}")
            print(f"  calls wrapper in body: {has_calls}")
            if not has_test_mode or not has_calls:
                print("  FIXING: updating jsonBody with correct batch wrapper")
                http_node["parameters"]["jsonBody"] = (
                    '={{\n'
                    '  {\n'
                    '    batch_id: "N8NTEST-" + $now.toFormat("yyyyMMdd-HHmmss"),\n'
                    '    test_mode: true,\n'
                    '    disable_google_push: true,\n'
                    '    source: "n8n_test_webhook",\n'
                    '    calls: [\n'
                    '      {\n'
                    '        ...$json.body,\n'
                    '        call_id: "N8NTEST-" + ($json.body.call_id || "CALL") + "-" + $now.toFormat("HHmmss")\n'
                    '      }\n'
                    '    ]\n'
                    '  }\n'
                    '}}'
                )
                put_body = {
                    "name": wf06["name"],
                    "nodes": wf06["nodes"],
                    "connections": wf06["connections"],
                    "settings": {"executionOrder": "v1"},
                    "staticData": None,
                    "pinData": {},
                }
                if put_workflow("0pRmm3xCHP4wsVyy", put_body, api_key):
                    deactivate_workflow("0pRmm3xCHP4wsVyy", api_key)
                    activate_workflow("0pRmm3xCHP4wsVyy", api_key)
            else:
                print("  batch wrapper already correct — active version confirmed OK")
    print()

    # ──────────────────────────────────────────────────────────────────────────
    # WORKFLOW 03 — Red Flag Scan: add schedule trigger (every 5 min), fix
    # ──────────────────────────────────────────────────────────────────────────
    print("=== Workflow 03 — Red Flag Scan ===")
    wf03_body = {
        "name": "JeffLocal - 03 Red Flag Scan",
        "nodes": [
            {
                "parameters": {"rule": {"interval": [{"field": "minutes", "minutesInterval": 5}]}},
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [0, 0],
                "id": "910b4c27-a20a-4a5a-b481-bd01a4431a22",
                "name": "Every 5 minutes",
            },
            {
                "parameters": {
                    "url": "http://127.0.0.1:8765/api/red-flags",
                    "options": {"response": {"response": {"responseFormat": "json"}}},
                },
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.4,
                "position": [208, 0],
                "id": "b4910194-ed1f-4565-b2cf-74afc50b38ed",
                "name": "HTTP Request",
            },
            {
                "parameters": {
                    "conditions": {
                        "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 3},
                        "conditions": [{"id": "7959a31f-4c13-487a-9cea-220566bd4450", "leftValue": "={{$json.count}}", "rightValue": 0, "operator": {"type": "number", "operation": "gt"}}],
                        "combinator": "and",
                    },
                    "options": {},
                },
                "type": "n8n-nodes-base.if",
                "typeVersion": 2.3,
                "position": [416, 0],
                "id": "b364f34f-fb42-4012-8102-35a0d651d874",
                "name": "If",
            },
            {
                "parameters": {
                    "assignments": {
                        "assignments": [
                            {"id": "a0bcad59", "name": "alert_type", "value": "JeffLocal Red Flag", "type": "string"},
                            {"id": "3da20d2f", "name": "count", "value": "={{$json.count}}", "type": "number"},
                            {"id": "11e646dc", "name": "first_call_id", "value": "={{$json.cases[0].call_id}}", "type": "string"},
                            {"id": "f4c36183", "name": "first_patient", "value": "={{$json.cases[0].patient_name}}", "type": "string"},
                            {"id": "5a3e3b87", "name": "first_priority", "value": "={{$json.cases[0].priority}}", "type": "string"},
                            {"id": "5fb1a1a6", "name": "message", "value": '={{"JeffLocal has " + $json.count + " unresolved red-flag case(s). First: " + $json.cases[0].call_id + " - " + $json.cases[0].patient_name + " (" + $json.cases[0].priority + ")"}}'  , "type": "string"},
                        ]
                    },
                    "options": {},
                },
                "type": "n8n-nodes-base.set",
                "typeVersion": 3.4,
                "position": [624, -96],
                "id": "90392e01-e668-43a1-899c-8c4ec2deaf32",
                "name": "Build Red Flag Alert",
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": "http://127.0.0.1:8765/api/alerts/log",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": '={\n  "alert_type": "{{$json.alert_type}}",\n  "severity": "critical",\n  "count": {{$json.count}},\n  "message": "{{$json.message}}",\n  "first_call_id": "{{$json.first_call_id}}",\n  "first_patient": "{{$json.first_patient}}",\n  "first_priority": "{{$json.first_priority}}",\n  "source_workflow": "JeffLocal - 03 Red Flag Scan"\n}',
                    "options": {"response": {"response": {"responseFormat": "json"}}},
                },
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.4,
                "position": [832, -96],
                "id": "09a04bd3-2f6c-4565-bff8-5cf9617f1628",
                "name": "Log Red Flag Alert",
            },
        ],
        "connections": {
            "Every 5 minutes": {"main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]},
            "HTTP Request": {"main": [[{"node": "If", "type": "main", "index": 0}]]},
            "If": {"main": [[{"node": "Build Red Flag Alert", "type": "main", "index": 0}]]},
            "Build Red Flag Alert": {"main": [[{"node": "Log Red Flag Alert", "type": "main", "index": 0}]]},
        },
        "settings": {"executionOrder": "v1"},
        "staticData": None,
        "pinData": {},
    }
    if put_workflow("wuHsIjBf3pkNEMpa", wf03_body, api_key):
        activate_workflow("wuHsIjBf3pkNEMpa", api_key)
    print()

    # ──────────────────────────────────────────────────────────────────────────
    # WORKFLOW 04 — Overdue Scan: fix double ==, add 30-min schedule
    # ──────────────────────────────────────────────────────────────────────────
    print("=== Workflow 04 — Overdue Scan ===")
    wf04_body = {
        "name": "JeffLocal - 04 Overdue Scan",
        "nodes": [
            {
                "parameters": {"rule": {"interval": [{"field": "minutes", "minutesInterval": 30}]}},
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [0, 0],
                "id": "bab0dea3-5839-46f8-812f-72f8aa33e603",
                "name": "Every 30 minutes",
            },
            {
                "parameters": {
                    "url": "http://127.0.0.1:8765/api/overdue?threshold_hours=24",
                    "options": {"response": {"response": {"responseFormat": "json"}}},
                },
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.4,
                "position": [208, 0],
                "id": "fd5b865d-5e32-4f57-97d1-6c6d9f5fab19",
                "name": "HTTP Request",
            },
            {
                "parameters": {
                    "conditions": {
                        "options": {"caseSensitive": True, "leftValue": "", "typeValidation": "strict", "version": 3},
                        "conditions": [{"id": "f85e834e-db70-4ad2-919d-da4a70795566", "leftValue": "={{$json.count}}", "rightValue": 0, "operator": {"type": "number", "operation": "gt"}}],
                        "combinator": "and",
                    },
                    "options": {},
                },
                "type": "n8n-nodes-base.if",
                "typeVersion": 2.3,
                "position": [416, 0],
                "id": "81a1554a-39bc-40d2-881b-a8c4948eee84",
                "name": "If",
            },
            {
                "parameters": {
                    "assignments": {
                        "assignments": [
                            {"id": "e80aee14", "name": "alert_type", "value": "JeffLocal Overdue Cases", "type": "string"},
                            {"id": "3fcdc743", "name": "count", "value": "={{$json.count}}", "type": "string"},
                            {"id": "657cf111", "name": "first_call_id", "value": "={{$json.cases[0].call_id}}", "type": "string"},
                            {"id": "cad833e6", "name": "first_patient", "value": "={{$json.cases[0].patient_name}}", "type": "string"},
                            {"id": "f04eccca", "name": "first_priority", "value": "={{$json.cases[0].priority}}", "type": "string"},
                            # FIX: was "=={{...}}" (double ==), now correctly "={{...}}"
                            {"id": "d62a2a97", "name": "message", "value": '={{"JeffLocal has " + $json.count + " overdue unresolved case(s). First: " + $json.cases[0].call_id + " - " + $json.cases[0].patient_name + " (" + $json.cases[0].priority + ")"}}'  , "type": "string"},
                        ]
                    },
                    "options": {},
                },
                "type": "n8n-nodes-base.set",
                "typeVersion": 3.4,
                "position": [624, -96],
                "id": "b7c47f4f-90ce-44d5-878a-d5032ff2549b",
                "name": "Build Overdue Alert",
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": "http://127.0.0.1:8765/api/alerts/log",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": '={\n  "alert_type": "{{$json.alert_type}}",\n  "severity": "warning",\n  "count": {{$json.count}},\n  "message": "{{$json.message}}",\n  "first_call_id": "{{$json.first_call_id}}",\n  "first_patient": "{{$json.first_patient}}",\n  "first_priority": "{{$json.first_priority}}",\n  "source_workflow": "JeffLocal - 04 Overdue Scan"\n}',
                    "options": {"response": {"response": {"responseFormat": "json"}}},
                },
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.4,
                "position": [832, -96],
                "id": "b4a695ef-4b7d-4cf1-a820-becbe18fca10",
                "name": "Log Overdue Alert",
            },
        ],
        "connections": {
            "Every 30 minutes": {"main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]},
            "HTTP Request": {"main": [[{"node": "If", "type": "main", "index": 0}]]},
            "If": {"main": [[{"node": "Build Overdue Alert", "type": "main", "index": 0}]]},
            "Build Overdue Alert": {"main": [[{"node": "Log Overdue Alert", "type": "main", "index": 0}]]},
        },
        "settings": {"executionOrder": "v1"},
        "staticData": None,
        "pinData": {},
    }
    if put_workflow("gW3L08bbmr744aKh", wf04_body, api_key):
        activate_workflow("gW3L08bbmr744aKh", api_key)
    print()

    # ──────────────────────────────────────────────────────────────────────────
    # WORKFLOW 05 — Daily Summary: fix corrupted field names, add 07:00 cron
    # ──────────────────────────────────────────────────────────────────────────
    print("=== Workflow 05 — Daily Summary ===")
    wf05_body = {
        "name": "JeffLocal - 05 Daily Summary",
        "nodes": [
            {
                "parameters": {"rule": {"interval": [{"field": "cronExpression", "expression": "0 7 * * *"}]}},
                "type": "n8n-nodes-base.scheduleTrigger",
                "typeVersion": 1.2,
                "position": [0, 0],
                "id": "01d3d534-671d-4a12-b276-b265e4d34f64",
                "name": "Daily at 07:00",
            },
            {
                "parameters": {
                    "url": "http://127.0.0.1:8765/api/daily-summary",
                    "options": {"response": {"response": {"responseFormat": "json"}}},
                },
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.4,
                "position": [208, 0],
                "id": "dd2b7033-0bd3-4c5b-8fd1-91ce349c201e",
                "name": "HTTP Request",
            },
            {
                "parameters": {
                    "assignments": {
                        "assignments": [
                            # FIX: removed leading = and trailing spaces from all field names
                            {"id": "cd70ce66", "name": "summary_type", "value": "JeffLocal Daily Summary", "type": "string"},
                            {"id": "896b4007", "name": "total", "value": "={{$json.total}}", "type": "number"},
                            {"id": "d4d8f845", "name": "unresolved", "value": "={{$json.unresolved}}", "type": "number"},
                            {"id": "8199218f", "name": "resolved", "value": "={{$json.resolved}}", "type": "number"},
                            {"id": "0b8971a9", "name": "red_flags", "value": "={{$json.red_flags}}", "type": "number"},
                            {"id": "cf8d4666", "name": "identity_issues", "value": "={{$json.identity_issues}}", "type": "number"},
                            {"id": "25189390", "name": "avg_turnaround_minutes", "value": "={{$json.avg_turnaround_minutes}}", "type": "number"},
                            {"id": "6e507a61", "name": "message", "value": '={{"JeffLocal daily summary: " + $json.total + " total, " + $json.unresolved + " unresolved, " + $json.resolved + " resolved, " + $json.red_flags + " red flag(s), " + $json.identity_issues + " identity issue(s). Avg turnaround: " + $json.avg_turnaround_minutes + " min."}}', "type": "string"},
                        ]
                    },
                    "options": {},
                },
                "type": "n8n-nodes-base.set",
                "typeVersion": 3.4,
                "position": [416, 0],
                "id": "6488f506-a1d3-46b7-828b-6a9d7fc10126",
                "name": "Build Daily Summary",
            },
            {
                "parameters": {
                    "method": "POST",
                    "url": "http://127.0.0.1:8765/api/alerts/log",
                    "sendBody": True,
                    "specifyBody": "json",
                    "jsonBody": '={\n  "alert_type": "{{$json.summary_type}}",\n  "severity": "info",\n  "count": "{{$json.total}}",\n  "message": "{{$json.message}}",\n  "first_call_id": "",\n  "first_patient": "",\n  "first_priority": "",\n  "source_workflow": "JeffLocal - 05 Daily Summary"\n}',
                    "options": {"response": {"response": {"responseFormat": "json"}}},
                },
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.4,
                "position": [624, 0],
                "id": "c4938741-4ea5-470b-90a4-f3ccbdd41b35",
                "name": "Log Daily Summary",
            },
        ],
        "connections": {
            "Daily at 07:00": {"main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]},
            "HTTP Request": {"main": [[{"node": "Build Daily Summary", "type": "main", "index": 0}]]},
            "Build Daily Summary": {"main": [[{"node": "Log Daily Summary", "type": "main", "index": 0}]]},
        },
        "settings": {"executionOrder": "v1"},
        "staticData": None,
        "pinData": {},
    }
    if put_workflow("M8z6HI401t8GUl1f", wf05_body, api_key):
        activate_workflow("M8z6HI401t8GUl1f", api_key)
    print()

    # ──────────────────────────────────────────────────────────────────────────
    # WORKFLOW 02 — Dashboard Sync: remove rawmock_only=true from URL
    # Keep as manual-only (used on demand, not scheduled)
    # ──────────────────────────────────────────────────────────────────────────
    print("=== Workflow 02 — Dashboard Sync ===")
    wf02_body = {
        "name": "JeffLocal - 02 Dashboard Sync",
        "nodes": [
            {
                "parameters": {},
                "type": "n8n-nodes-base.manualTrigger",
                "typeVersion": 1,
                "position": [0, 0],
                "id": "38830aae-391b-48fe-9b96-86011f1ac1aa",
                "name": "When clicking 'Execute workflow'",
            },
            {
                "parameters": {
                    "method": "POST",
                    # FIX: removed rawmock_only=true — was only importing TC-* test files
                    "url": "http://127.0.0.1:8765/api/sync",
                    "options": {"response": {"response": {"responseFormat": "json"}}},
                },
                "type": "n8n-nodes-base.httpRequest",
                "typeVersion": 4.4,
                "position": [208, 0],
                "id": "1895a137-8e32-446e-bb0e-cd62047503ab",
                "name": "HTTP Request",
            },
        ],
        "connections": {
            "When clicking 'Execute workflow'": {"main": [[{"node": "HTTP Request", "type": "main", "index": 0}]]}
        },
        "settings": {"executionOrder": "v1"},
        "staticData": None,
        "pinData": {},
    }
    put_workflow("ZYmUGt1lmT4XASNL", wf02_body, api_key)
    print("  (kept manual-only — used on demand)")
    print()

    print("=== All fixes applied. Verifying active workflows ===")
    result, err = n8n_request("GET", "/workflows", None, api_key)
    if result:
        for wf in result.get("data", []):
            status = "ACTIVE" if wf["active"] else "inactive"
            print(f"  [{status}] {wf['name']}")


if __name__ == "__main__":
    main()

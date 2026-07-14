"""
Fix workflows 03 + 04: update HTTP Request URLs from /api/red-flags and /api/overdue
to /api/n8n/red-flags and /api/n8n/overdue so n8n bypasses login auth.
Run once: python fix_n8n_auth_urls.py
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
        url, data=data, method=method,
        headers={"X-N8N-API-KEY": api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode()


def get_workflow(wf_id, api_key):
    result, err = n8n_request("GET", f"/workflows/{wf_id}", None, api_key)
    if err:
        print(f"  GET error: {err}")
    return result


def put_workflow(wf_id, body, api_key):
    result, err = n8n_request("PUT", f"/workflows/{wf_id}", body, api_key)
    if err:
        print(f"  PUT error: {err}")
        return False
    print(f"  PUT OK — versionId: {result.get('versionId')}")
    return True


def toggle_active(wf_id, activate, api_key):
    action = "activate" if activate else "deactivate"
    result, err = n8n_request("POST", f"/workflows/{wf_id}/{action}", {}, api_key)
    if err:
        print(f"  {action} error: {err}")
    else:
        print(f"  {action}d OK")


def fix_workflow_url(wf_id, old_url, new_url, api_key):
    wf = get_workflow(wf_id, api_key)
    if not wf:
        return False

    changed = False
    for node in wf["nodes"]:
        url = node.get("parameters", {}).get("url", "")
        if old_url in url:
            node["parameters"]["url"] = url.replace(old_url, new_url)
            changed = True
            print(f"  Updated node '{node['name']}': {url} -> {node['parameters']['url']}")

    if not changed:
        print(f"  No URL match found for '{old_url}' — already fixed?")
        return True

    body = {
        "name": wf["name"],
        "nodes": wf["nodes"],
        "connections": wf["connections"],
        "settings": {"executionOrder": "v1"},
        "staticData": None,
        "pinData": {},
    }
    if put_workflow(wf_id, body, api_key):
        toggle_active(wf_id, False, api_key)
        toggle_active(wf_id, True, api_key)
        return True
    return False


def main():
    api_key = get_api_key()
    print(f"API key loaded ({api_key[:8]}...)\n")

    print("=== Workflow 03 — Red Flag Scan ===")
    fix_workflow_url(
        "wuHsIjBf3pkNEMpa",
        "/api/red-flags",
        "/api/n8n/red-flags",
        api_key,
    )
    print()

    print("=== Workflow 04 — Overdue Scan ===")
    fix_workflow_url(
        "gW3L08bbmr744aKh",
        "/api/overdue",
        "/api/n8n/overdue",
        api_key,
    )
    print()

    print("=== Verifying ===")
    for wf_id, name in [("wuHsIjBf3pkNEMpa", "03 Red Flag"), ("gW3L08bbmr744aKh", "04 Overdue")]:
        wf = get_workflow(wf_id, api_key)
        if wf:
            for node in wf["nodes"]:
                url = node.get("parameters", {}).get("url", "")
                if url:
                    print(f"  [{name}] {node['name']}: {url}")


if __name__ == "__main__":
    main()

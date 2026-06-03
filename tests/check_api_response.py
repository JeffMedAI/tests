"""Check that /api/cases/{call_id} returns valid JSON for RICH cases."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(r"C:\JeffLocal\sandbox\dashboard")))

from httpx import Client
from fastapi.testclient import TestClient
from app.main import app
from app.db import connect, init_db, DB_PATH
from app.auth import hash_password
from unittest.mock import patch

# Bypass auth for this test
def _always_public(path):
    return True

issues = []

with patch("app.main._is_public_path", _always_public):
    client = TestClient(app, raise_server_exceptions=True)
    with connect() as conn:
        rows = conn.execute("SELECT call_id FROM cases WHERE call_id LIKE 'RICH%'").fetchall()

    print(f"Testing {len(rows)} RICH cases via /api/cases/{{call_id}}...")
    for row in rows:
        call_id = row["call_id"]
        try:
            r = client.get(f"/api/cases/{call_id}")
            if r.status_code != 200:
                issues.append(f"  HTTP {r.status_code}: {call_id}")
                continue
            data = r.json()
            # Check key fields JS depends on
            for field in ["patient_name", "request_type_label", "ai_summary", "suggested_actions", "pathway_items"]:
                if field not in data:
                    issues.append(f"  Missing field '{field}' in {call_id}")
            print(f"  OK  {call_id[:50]} | patient={data.get('patient_name','?')} | summary={len(data.get('ai_summary',''))} chars")
        except Exception as e:
            issues.append(f"  EXCEPTION {call_id}: {e}")

print()
if issues:
    print(f"ISSUES FOUND ({len(issues)}):")
    for i in issues:
        print(i)
else:
    print(f"All {len(rows)} RICH cases return valid JSON from API — no issues")

"""E2E: test both the inline panel API and full case detail page for all RICH cases."""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(r"C:\JeffLocal\sandbox\dashboard")))

from fastapi.testclient import TestClient
from app.main import app

def always_public(path): return True

issues = []

with patch("app.main._is_public_path", always_public):
    client = TestClient(app, raise_server_exceptions=False)

    from app.db import connect
    with connect() as conn:
        rows = conn.execute("SELECT call_id FROM cases WHERE call_id LIKE 'RICH%' ORDER BY call_id").fetchall()

    print(f"=== E2E test: {len(rows)} RICH cases ===\n")

    for row in rows:
        cid = row["call_id"]
        label = cid[28:]  # trim timestamp prefix for readability

        # 1. Inline panel API
        r1 = client.get(f"/api/cases/{cid}")
        api_ok = r1.status_code == 200
        try:
            d = r1.json()
            has_name = bool(d.get("patient_name"))
            has_summary = bool(d.get("ai_summary"))
            has_actions = isinstance(d.get("suggested_actions"), list)
        except Exception as e:
            api_ok = False
            has_name = has_summary = has_actions = False
            issues.append(f"[API JSON parse] {cid}: {e}")

        # 2. Full case detail page
        r2 = client.get(f"/case/{cid}")
        page_ok = r2.status_code == 200
        has_banner = "ns-banner" in r2.text if page_ok else False
        has_stepper = "cd-stepper" in r2.text if page_ok else False
        has_patient = (d.get("patient_name","") in r2.text) if page_ok and api_ok else False

        if not api_ok:
            issues.append(f"[API {r1.status_code}] {cid}")
        if not page_ok:
            issues.append(f"[PAGE {r2.status_code}] {cid}")
            # Print the actual error for debugging
            if r2.status_code == 500:
                err_snippet = r2.text[:300] if r2.text else "(empty)"
                issues.append(f"  500 body: {err_snippet}")

        api_sym  = "OK" if api_ok  else "FAIL"
        page_sym = "OK" if page_ok else "FAIL"
        banner_sym  = "Y" if has_banner  else "N"
        stepper_sym = "Y" if has_stepper else "N"
        name_sym    = "Y" if has_name    else "N"
        summary_sym = "Y" if has_summary else "N"

        print(f"  API:{api_sym} PAGE:{page_sym} banner:{banner_sym} stepper:{stepper_sym} "
              f"name:{name_sym} summary:{summary_sym}  {label[:35]}")

print()
if issues:
    print(f"=== ISSUES ({len(issues)}) ===")
    for i in issues: print(i)
else:
    print("=== ALL CHECKS PASSED ===")

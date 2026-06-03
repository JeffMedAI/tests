"""Test-render case_detail.html with a RICH emergency case to catch template errors."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r"C:\JeffLocal\sandbox\dashboard")))

from jinja2 import Environment, FileSystemLoader, Undefined, DebugUndefined
from app.db import connect, row_to_dict
from app.main import prepare_case

env = Environment(loader=FileSystemLoader(r"C:\JeffLocal\sandbox\dashboard\templates"))
env.undefined = DebugUndefined  # surface missing vars instead of silent empty

# Pull the emergency RICH case
with connect() as conn:
    row = conn.execute(
        "SELECT * FROM cases WHERE call_id LIKE 'RICH%' AND red_flags_present = 1 LIMIT 1"
    ).fetchone()
    if not row:
        row = conn.execute("SELECT * FROM cases WHERE call_id LIKE 'RICH%' LIMIT 1").fetchone()

if not row:
    print("ERROR: No RICH cases found")
    sys.exit(1)

case = prepare_case(row_to_dict(row))
print(f"Testing with: {case['call_id']}")

# Minimal context that main.py would pass
ctx = {
    "case": case,
    "return_url": "/requests",
    "current_user": {"display_name": "Test User", "role": "staff", "id": 1},
    "request": None,
    "is_mobile": False,
}

try:
    t = env.get_template("case_detail.html")
    rendered = t.render(**ctx)
    print(f"case_detail.html rendered OK — {len(rendered)} chars")
    for marker in ["ns-banner", "cd-stepper", "jl-gap-toast"]:
        print(f"  {'FOUND' if marker in rendered else 'MISSING'}: {marker}")
except Exception as e:
    import traceback
    print("RENDER FAILED:")
    traceback.print_exc()

# Also test index.html with minimal context
try:
    t2 = env.get_template("index.html")
    ctx2 = {
        "cases": [case],
        "show_requests": True,
        "urgent_attention": {"red_flags": 1, "staff_review": 0, "identity_checks": 0, "latest": None},
        "queue_status_card": {"open": 1, "overdue": 0, "resolved_today": 0, "red_flags": 1},
        "staff_workload_list": [],
        "filter_links": [{"url": "/", "label": "All", "count": 1, "active": False}],
        "active_filter": "all",
        "active_date_range": "today",
        "current_list_url": "/requests",
        "current_user": {"display_name": "Test", "role": "staff"},
        "total_count": 1,
        "page": 1,
        "page_size": 20,
    }
    rendered2 = t2.render(**ctx2)
    print(f"\nindex.html rendered OK — {len(rendered2)} chars")
    for marker in ["attn-badge", "CALL NOW", "jl-gap-toast"]:
        print(f"  {'FOUND' if marker in rendered2 else 'MISSING'}: {marker}")
except Exception as e:
    import traceback
    print("index.html RENDER FAILED:")
    traceback.print_exc()

"""Quick test: does prepare_case + api_case_get work for RICH cases?"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r"C:\JeffLocal\sandbox\dashboard")))

from app.db import connect, init_db, row_to_dict

with connect() as conn:
    rows = conn.execute("SELECT * FROM cases WHERE call_id LIKE 'RICH%'").fetchall()

print(f"RICH cases in DB: {len(rows)}")
if not rows:
    print("ERROR: No RICH cases found — import didn't work")
    sys.exit(1)

# Test prepare_case on each
from app.main import prepare_case, build_suggested_actions, pathway_question_responses
errors = []
for row in rows:
    call_id = row["call_id"]
    try:
        case = prepare_case(row_to_dict(row))
        build_suggested_actions(case)
        pathway_question_responses(case)
    except Exception as e:
        errors.append(f"  {call_id}: {e}")

if errors:
    print(f"FAILURES ({len(errors)}):")
    for e in errors:
        print(e)
else:
    print(f"All {len(rows)} RICH cases pass prepare_case OK")

# Also check test suite delta

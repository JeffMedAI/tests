"""Mark remaining E2E test cases as resolved to clean up dashboard."""
import sys, os
os.environ["JEFFLOCAL_ROOT_DIR"] = r"C:\JeffLocal"
sys.path.insert(0, r"C:\JeffLocal\sandbox\dashboard")
from app.db import connect
from datetime import datetime, timezone

now = datetime.now(timezone.utc).isoformat()

with connect() as conn:
    # Find all non-resolved E2E test cases
    rows = conn.execute("""
        SELECT call_id, status FROM cases
        WHERE (call_id LIKE 'E2E-%' OR call_id LIKE 'N8NTEST-%' OR call_id LIKE 'GPDEMO-%')
        AND status NOT IN ('Resolved', 'Unable to Complete')
    """).fetchall()

    print(f"Found {len(rows)} stale test cases to clean up:")
    for r in rows:
        print(f"  {r[0]} — {r[1]}")

    if rows:
        conn.execute("""
            UPDATE cases
            SET status='Resolved',
                resolved_by='System (test cleanup)',
                resolved_at=?,
                outcome_notes='Auto-resolved: stale E2E test data cleanup',
                last_updated=?,
                last_edited_at=?,
                last_edited_by='System (test cleanup)'
            WHERE (call_id LIKE 'E2E-%' OR call_id LIKE 'N8NTEST-%' OR call_id LIKE 'GPDEMO-%')
            AND status NOT IN ('Resolved', 'Unable to Complete')
        """, (now, now, now))
        conn.commit()
        print(f"\nResolved {len(rows)} cases.")
    else:
        print("Nothing to clean up.")

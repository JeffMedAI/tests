import sys, os
os.environ["JEFFLOCAL_ROOT_DIR"] = r"C:\JeffLocal"
sys.path.insert(0, r"C:\JeffLocal\sandbox\dashboard")
from app.db import connect
with connect() as conn:
    rows = conn.execute("""
        SELECT COALESCE(request_type,'(null)') as rt, COUNT(*) as cnt
        FROM cases
        WHERE date(timestamp) = date('now')
        GROUP BY rt ORDER BY cnt DESC
    """).fetchall()
    total = sum(r[1] for r in rows)
    print(f"Total today: {total}")
    for r in rows:
        print(f"  '{r[0]}': {r[1]}")

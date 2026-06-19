import sqlite3, sys, os
os.environ.setdefault("JEFFLOCAL_ROOT_DIR", r"C:\JeffLocal")
sys.path.insert(0, r"C:\JeffLocal\sandbox\dashboard")
from app.db import connect
with connect() as conn:
    total = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    e2e = conn.execute("SELECT COUNT(*) FROM cases WHERE call_id LIKE '%E2E%'").fetchone()[0]
    print(f"Total cases: {total}  |  E2E cases: {e2e}")
    rows = conn.execute("SELECT call_id, status FROM cases WHERE call_id LIKE '%E2E%' ORDER BY rowid DESC LIMIT 15").fetchall()
    for r in rows:
        print(" ", r)

import sqlite3, os
os.environ["JEFFLOCAL_ROOT_DIR"] = r"C:\JeffLocal"
import sys; sys.path.insert(0, r"C:\JeffLocal\sandbox\dashboard")
from app.db import connect

with connect() as conn:
    # Staff workload breakdown
    print("=== Staff workload query ===")
    rows = conn.execute("""
        SELECT assigned_to,
               COUNT(CASE WHEN status NOT IN ('Resolved','Unable to Complete') THEN 1 END) as open_count,
               COUNT(CASE WHEN status = 'In Progress' THEN 1 END) as in_progress,
               COUNT(CASE WHEN status = 'Resolved' THEN 1 END) as resolved_total
        FROM cases
        WHERE assigned_to IS NOT NULL AND assigned_to != ''
        GROUP BY assigned_to
        ORDER BY open_count DESC
    """).fetchall()
    for r in rows:
        print(f"  {r[0]}: open={r[1]}, in_progress={r[2]}, resolved_total={r[3]}")

    print("\n=== Total cases by status ===")
    statuses = conn.execute("SELECT status, COUNT(*) FROM cases GROUP BY status ORDER BY COUNT(*) DESC").fetchall()
    for s in statuses:
        print(f"  {s[0]}: {s[1]}")

    total = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
    print(f"\nTotal cases in DB: {total}")

    print("\n=== Saeed 1 cases sample ===")
    saeed = conn.execute("SELECT call_id, status, assigned_to FROM cases WHERE assigned_to='Saeed 1' LIMIT 10").fetchall()
    for c in saeed:
        print(f"  {c}")
    saeed_total = conn.execute("SELECT COUNT(*) FROM cases WHERE assigned_to='Saeed 1'").fetchone()[0]
    print(f"Total assigned to Saeed 1: {saeed_total}")

    print("\n=== Unassigned open cases ===")
    unassigned = conn.execute("SELECT COUNT(*) FROM cases WHERE (assigned_to IS NULL OR assigned_to='') AND status NOT IN ('Resolved','Unable to Complete')").fetchone()[0]
    print(f"Unassigned open: {unassigned}")

    print("\n=== Quick status expected values ===")
    open_total = conn.execute("SELECT COUNT(*) FROM cases WHERE status NOT IN ('Resolved','Unable to Complete')").fetchone()[0]
    overdue = conn.execute("SELECT COUNT(*) FROM cases WHERE status='Overdue'").fetchone()[0]
    resolved_today = conn.execute("SELECT COUNT(*) FROM cases WHERE status='Resolved' AND date(resolved_at)=date('now')").fetchone()[0]
    critical = conn.execute("SELECT COUNT(*) FROM cases WHERE red_flags_present=1 AND status NOT IN ('Resolved','Unable to Complete')").fetchone()[0]
    print(f"  Open: {open_total} | Overdue: {overdue} | Resolved today: {resolved_today} | Critical (red flags): {critical}")

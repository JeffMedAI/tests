import sqlite3

db = sqlite3.connect('dashboard/data/dashboard.sqlite')
cur = db.cursor()

rows = cur.execute(
    "SELECT call_id, status, priority, verification_status, created_at FROM cases ORDER BY created_at DESC LIMIT 15"
).fetchall()
print(f"Total recent cases: {len(rows)}")
for r in rows:
    print(r)

fresh = cur.execute(
    "SELECT call_id, status FROM cases WHERE call_id LIKE 'CSV-FRESH%'"
).fetchall()
print(f"\nCSV-FRESH cases: {len(fresh)}")
for r in fresh:
    print(r)

total = cur.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
print(f"\nTotal cases in DB: {total}")
db.close()

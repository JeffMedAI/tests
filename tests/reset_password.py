"""Reset saeed1 password and clear failed attempts."""
import sys, os
os.environ["JEFFLOCAL_ROOT_DIR"] = r"C:\JeffLocal"
sys.path.insert(0, r"C:\JeffLocal\sandbox\dashboard")
from app.auth import hash_password
from app.db import connect

new_password = "Saeed1Test"
hashed = hash_password(new_password)

with connect() as conn:
    conn.execute(
        "UPDATE staff_users SET password_hash=?, failed_attempts=0, locked_until=NULL WHERE username=?",
        (hashed, "saeed1")
    )
    conn.commit()
    row = conn.execute("SELECT id, display_name, username, failed_attempts FROM staff_users WHERE username='saeed1'").fetchone()
    print(f"Updated: id={row[0]} name={row[1]} username={row[2]} failed_attempts={row[3]}")
    print(f"New password set to: {new_password}")

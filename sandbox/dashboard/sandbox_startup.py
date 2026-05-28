"""
sandbox_startup.py
──────────────────
Sandbox launcher for the JeffLocal dashboard.

Loads .env.sandbox, injects practice config into every Jinja2 template,
then starts uvicorn. main.py and db.py are NOT modified — all
practice-specific config lives here and in .env.sandbox.

Usage (via launch_sandbox.ps1):
    python sandbox_startup.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ── 1. Load .env.sandbox before anything else ──────────────────────────
_here = Path(__file__).resolve().parent
_env_file = _here / ".env.sandbox"

if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _val = _line.split("=", 1)
            os.environ.setdefault(_key.strip(), _val.strip())
    print(f"✓ Loaded environment from {_env_file.name}")
else:
    print(f"⚠ {_env_file.name} not found — using system environment variables")

# ── 2. Resolve config values ────────────────────────────────────────────
PRACTICE_NAME       = os.environ.get("PRACTICE_NAME",       "JeffLocal")
PRACTICE_SHORT_CODE = os.environ.get("PRACTICE_SHORT_CODE", "JL")
PRACTICE_ACCENT     = os.environ.get("PRACTICE_ACCENT",     "#005EB8")
ENVIRONMENT         = os.environ.get("ENVIRONMENT",         "sandbox")
PORT                = int(os.environ.get("PORT",            "5000"))

print(f"  Practice : {PRACTICE_NAME}")
print(f"  Mode     : {ENVIRONMENT}")
print(f"  Port     : {PORT}")

# ── 3. Import app and patch template globals ────────────────────────────
#    We import AFTER setting env vars so any os.environ.get() calls
#    in main.py at module level will also pick up the correct values.
sys.path.insert(0, str(_here))
from app.main import app, templates  # noqa: E402

templates.env.globals.update({
    "practice_name":       PRACTICE_NAME,
    "practice_short_code": PRACTICE_SHORT_CODE,
    "practice_accent":     PRACTICE_ACCENT,
    "environment":         ENVIRONMENT,
})
print("✓ Template globals injected")

# ── 4. Start uvicorn ────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    print(f"\nStarting sandbox dashboard → http://localhost:{PORT}\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT, reload=False)

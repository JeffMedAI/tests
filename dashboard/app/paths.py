from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = Path(os.environ["JEFFLOCAL_ROOT_DIR"]) if os.environ.get("JEFFLOCAL_ROOT_DIR") else BASE_DIR.parent
ALERT_DIR = ROOT_DIR / "logs" / "alerts"
SERVICE_START_SCRIPT = ROOT_DIR / "scripts" / "service_control" / "start_jefflocal_services.ps1"

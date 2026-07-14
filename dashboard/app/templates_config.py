"""
Shared Jinja2Templates singleton.

Imported by routers so they can render templates without importing main.py.
The nav_alert_count global is registered by main.py after startup (it needs
a live DB connection) — this module only sets up the static filter.
"""
from __future__ import annotations

from pathlib import Path

from fastapi.templating import Jinja2Templates

from .models import format_display_timestamp

_BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(directory=_BASE_DIR / "templates")
templates.env.filters["display_ts"] = format_display_timestamp

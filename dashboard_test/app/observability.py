"""
Observability module for Avamed / JeffLocal dashboard.

Provides:
- HealthStatus enum and build_health_response() for the /health endpoint
- Lightweight in-process metric counters (record_pipeline_event, get_metrics)
- StructuredFormatter: JSON log formatter for structured logging
"""

from __future__ import annotations

import datetime
import enum
import json
import logging
import threading
from typing import Any

log = logging.getLogger(__name__)

_START_TIME = datetime.datetime.now(datetime.timezone.utc)


# ---------------------------------------------------------------------------
# Health status
# ---------------------------------------------------------------------------

class HealthStatus(enum.Enum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


def build_health_response(
    services: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Build a health-check response dict suitable for /health endpoint JSON.

    services: optional dict mapping service name → "up" | "down" | "unknown"
    Overall status is DEGRADED if any service is not "up", OK otherwise.
    """
    if services is None:
        services = {}

    overall = HealthStatus.OK
    for state in services.values():
        if state != "up":
            overall = HealthStatus.DEGRADED
            break

    now = datetime.datetime.now(datetime.timezone.utc)
    uptime_seconds = (now - _START_TIME).total_seconds()

    return {
        "status": overall.value,
        "version": "1.0.0",
        "timestamp": now.isoformat(),
        "uptime_seconds": uptime_seconds,
        "services": services,
    }


# ---------------------------------------------------------------------------
# Lightweight metric counters (in-process, reset on restart)
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_counters: dict[str, int] = {}


def record_pipeline_event(event_type: str) -> None:
    """
    Increment counters for a named pipeline event.

    event_type examples: "intake", "safety_violation", "matched", "failed"
    """
    with _lock:
        _counters["pipeline_events_total"] = _counters.get("pipeline_events_total", 0) + 1
        key = f"pipeline_{event_type}_total"
        _counters[key] = _counters.get(key, 0) + 1
    log.debug("pipeline_event type=%s totals=%s", event_type, _counters)


def get_metrics() -> dict[str, int]:
    """Return a snapshot of current counters."""
    with _lock:
        return dict(_counters)


def reset_metrics() -> None:
    """Reset all counters to zero. Intended for tests only."""
    with _lock:
        _counters.clear()


# ---------------------------------------------------------------------------
# Structured JSON log formatter
# ---------------------------------------------------------------------------

class StructuredFormatter(logging.Formatter):
    """
    Emits each log record as a single-line JSON object.

    Keys: timestamp, level, logger, message, [exc_info if present]
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.datetime.fromtimestamp(
                record.created, datetime.timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

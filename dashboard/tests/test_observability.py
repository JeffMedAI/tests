"""
TDD tests for the observability module.

Covers:
- Health check response structure
- Structured log record format
- Metric counters (pipeline events)
"""
import json
import logging
import pytest
from app.observability import (
    HealthStatus,
    build_health_response,
    get_metrics,
    record_pipeline_event,
    reset_metrics,
    StructuredFormatter,
)


class TestHealthStatus:
    def test_ok_is_truthy(self):
        assert HealthStatus.OK

    def test_degraded_is_truthy(self):
        assert HealthStatus.DEGRADED

    def test_down_is_truthy(self):
        assert HealthStatus.DOWN

    def test_values_are_strings(self):
        assert isinstance(HealthStatus.OK.value, str)


class TestBuildHealthResponse:
    def test_returns_dict(self):
        result = build_health_response()
        assert isinstance(result, dict)

    def test_has_status_field(self):
        result = build_health_response()
        assert "status" in result

    def test_has_version_field(self):
        result = build_health_response()
        assert "version" in result

    def test_has_services_field(self):
        result = build_health_response()
        assert "services" in result

    def test_services_is_dict(self):
        result = build_health_response()
        assert isinstance(result["services"], dict)

    def test_default_status_is_ok(self):
        result = build_health_response()
        assert result["status"] == HealthStatus.OK.value

    def test_accepts_service_statuses(self):
        result = build_health_response(services={"ollama": "up", "n8n": "down"})
        assert result["services"]["ollama"] == "up"
        assert result["services"]["n8n"] == "down"

    def test_degraded_when_any_service_down(self):
        result = build_health_response(services={"ollama": "down"})
        assert result["status"] == HealthStatus.DEGRADED.value

    def test_ok_when_all_services_up(self):
        result = build_health_response(services={"ollama": "up", "n8n": "up"})
        assert result["status"] == HealthStatus.OK.value

    def test_has_uptime_or_timestamp(self):
        result = build_health_response()
        assert "timestamp" in result or "uptime_seconds" in result

    def test_json_serialisable(self):
        result = build_health_response()
        serialised = json.dumps(result)
        assert isinstance(serialised, str)


class TestMetrics:
    def setup_method(self):
        reset_metrics()

    def test_get_metrics_returns_dict(self):
        assert isinstance(get_metrics(), dict)

    def test_initial_pipeline_events_zero(self):
        m = get_metrics()
        assert m.get("pipeline_events_total", 0) == 0

    def test_record_intake_increments_counter(self):
        record_pipeline_event("intake")
        m = get_metrics()
        assert m["pipeline_events_total"] >= 1

    def test_record_multiple_events(self):
        record_pipeline_event("intake")
        record_pipeline_event("intake")
        record_pipeline_event("safety_violation")
        m = get_metrics()
        assert m["pipeline_events_total"] >= 3

    def test_events_tracked_by_type(self):
        record_pipeline_event("intake")
        record_pipeline_event("safety_violation")
        m = get_metrics()
        assert m.get("pipeline_intake_total", 0) >= 1
        assert m.get("pipeline_safety_violation_total", 0) >= 1

    def test_reset_clears_counters(self):
        record_pipeline_event("intake")
        reset_metrics()
        m = get_metrics()
        assert m.get("pipeline_events_total", 0) == 0

    def test_metrics_are_json_serialisable(self):
        record_pipeline_event("intake")
        serialised = json.dumps(get_metrics())
        assert isinstance(serialised, str)


class TestStructuredFormatter:
    def test_is_logging_formatter(self):
        assert issubclass(StructuredFormatter, logging.Formatter)

    def test_formats_record_as_json(self):
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="hello world",
            args=(),
            exc_info=None,
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_json_has_message_field(self):
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None,
        )
        parsed = json.loads(formatter.format(record))
        assert parsed.get("message") == "test message"

    def test_json_has_level_field(self):
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="error",
            args=(),
            exc_info=None,
        )
        parsed = json.loads(formatter.format(record))
        assert "level" in parsed
        assert parsed["level"] == "ERROR"

    def test_json_has_timestamp_field(self):
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="ts test",
            args=(),
            exc_info=None,
        )
        parsed = json.loads(formatter.format(record))
        assert "timestamp" in parsed or "time" in parsed

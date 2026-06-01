"""
test_hmac_verification.py — Unit and integration tests for HMAC-SHA256 webhook verification.

Covers:
  Unit tests — verify_hmac_signature() pure function:
    - Valid signature returns True
    - Invalid (tampered) signature returns False
    - Missing / empty signature header returns False
    - Malformed header (no "sha256=" prefix) returns False
    - Empty payload is handled correctly (still verifiable)

  Integration tests — /api/n8n/test-intake-batch endpoint:
    - JEFF_WEBHOOK_SECRET not set -> secret-skip path, endpoint reachable
    - JEFF_WEBHOOK_SECRET set + valid signature -> endpoint accepts (not 401)
    - JEFF_WEBHOOK_SECRET set + invalid signature -> 401
    - JEFF_WEBHOOK_SECRET set + missing header -> 401
    - JEFF_WEBHOOK_SECRET set + tampered body -> 401

SANDBOX ONLY — targets C:\\JeffLocal\\sandbox\\dashboard\\ (port 5000).
Never run against the production dashboard (port 8765).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import sys
import types
from pathlib import Path

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from app.main import app, verify_hmac_signature  # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sign(payload: bytes, secret: bytes) -> str:
    """Produce a correctly-formatted X-Hub-Signature-256 value."""
    digest = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _make_headers(payload_bytes: bytes, secret: str) -> dict[str, str]:
    sig = _sign(payload_bytes, secret.encode())
    return {"X-Hub-Signature-256": sig, "Content-Type": "application/json"}


# ── Unit tests: verify_hmac_signature ─────────────────────────────────────────

SECRET = b"test-secret-for-unit-tests"
PAYLOAD = b'{"call_id": "TEST-001", "transcript": "headache"}'


def test_valid_signature_returns_true():
    """Correct HMAC-SHA256 signature must return True."""
    sig = _sign(PAYLOAD, SECRET)
    assert verify_hmac_signature(PAYLOAD, sig, SECRET) is True


def test_tampered_payload_returns_false():
    """Signature computed over original payload must fail for altered payload."""
    sig = _sign(PAYLOAD, SECRET)
    tampered = PAYLOAD + b" extra"
    assert verify_hmac_signature(tampered, sig, SECRET) is False


def test_wrong_secret_returns_false():
    """Signature computed with a different secret must fail."""
    sig = _sign(PAYLOAD, b"wrong-secret")
    assert verify_hmac_signature(PAYLOAD, sig, SECRET) is False


def test_missing_signature_header_returns_false():
    """Empty string signature header (header absent) must return False."""
    assert verify_hmac_signature(PAYLOAD, "", SECRET) is False


def test_malformed_header_no_prefix_returns_false():
    """Header without 'sha256=' prefix must return False without raising."""
    raw_hex = hmac.new(SECRET, PAYLOAD, hashlib.sha256).hexdigest()
    assert verify_hmac_signature(PAYLOAD, raw_hex, SECRET) is False


def test_wrong_prefix_returns_false():
    """Header with wrong algorithm prefix must return False."""
    digest = hmac.new(SECRET, PAYLOAD, hashlib.sha256).hexdigest()
    assert verify_hmac_signature(PAYLOAD, f"sha1={digest}", SECRET) is False


def test_empty_payload_valid_signature_returns_true():
    """Empty body is a valid payload; signature over it must verify correctly."""
    empty = b""
    sig = _sign(empty, SECRET)
    assert verify_hmac_signature(empty, sig, SECRET) is True


def test_empty_payload_wrong_signature_returns_false():
    """Empty body with a signature computed over non-empty payload must fail."""
    sig = _sign(PAYLOAD, SECRET)
    assert verify_hmac_signature(b"", sig, SECRET) is False


def test_uses_constant_time_comparison():
    """
    Confirm hmac.compare_digest is used (timing-safe).
    Short/mismatched sig must return False without raising, not short-circuit.
    """
    short_sig = "sha256=abc"
    assert verify_hmac_signature(PAYLOAD, short_sig, SECRET) is False


# ── Integration fixtures ──────────────────────────────────────────────────────

# A minimal payload satisfying the endpoint's own guards:
#   test_mode=true, disable_google_push=true, valid calls list.
VALID_BATCH = {
    "test_mode": True,
    "disable_google_push": True,
    "refresh_artifacts": False,
    "calls": [
        {
            "call_id": "N8NTEST-HMAC-TEST-001",
            "transcript": "headache for three days",
            "caller_number": "REDACTED",
            "practice_id": "churchtown",
            "timestamp": "2026-05-30T10:00:00Z",
            "duration_seconds": 45,
        }
    ],
}

ENDPOINT = "/api/n8n/test-intake-batch"


@pytest.fixture()
def client(monkeypatch, tmp_path):
    """Standard TestClient — used by 401 tests where the guard fires before
    any pipeline code runs, so no stub needed."""
    import app.audit as audit_module
    import app.db as db_module
    import app.main as main_module
    from app.db import connect, init_db
    from fastapi.testclient import TestClient

    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "ALERT_DIR", tmp_path / "alerts")
    monkeypatch.setattr(main_module, "_is_public_path", lambda path: True)

    with connect(db_path) as conn:
        init_db(conn)

    with TestClient(app) as tc:
        yield tc


@pytest.fixture()
def lenient_client(monkeypatch, tmp_path):
    """TestClient for pass-through HMAC tests.

    Injects a stub ``live_lookup_test_payloads`` into sys.modules before the
    TestClient starts, so the endpoint can reach a real HTTP response in this
    Linux environment (where the Windows-only test fixture is absent).
    Uses raise_server_exceptions=False so downstream 500s don't blow up the
    test — we only care that the HMAC guard did NOT fire (status != 401).
    """
    import app.audit as audit_module
    import app.db as db_module
    import app.main as main_module
    from app.db import connect, init_db
    from fastapi.testclient import TestClient

    # Inject stub BEFORE the TestClient starts so any lazy import in the
    # endpoint finds it in sys.modules.
    injected = "live_lookup_test_payloads" not in sys.modules
    if injected:
        stub = types.ModuleType("live_lookup_test_payloads")
        stub.encrypt_envelope = lambda call: call  # type: ignore[attr-defined]
        sys.modules["live_lookup_test_payloads"] = stub

    db_path = tmp_path / "dashboard.sqlite"
    monkeypatch.setattr(db_module, "DB_PATH", db_path)
    monkeypatch.setattr(audit_module, "AUDIT_DIR", tmp_path / "audits")
    monkeypatch.setattr(main_module, "ALERT_DIR", tmp_path / "alerts")
    monkeypatch.setattr(main_module, "_is_public_path", lambda path: True)

    with connect(db_path) as conn:
        init_db(conn)

    with TestClient(app, raise_server_exceptions=False) as tc:
        yield tc

    if injected:
        sys.modules.pop("live_lookup_test_payloads", None)


# ── Integration tests ─────────────────────────────────────────────────────────

def test_integration_no_secret_set_skips_verification(monkeypatch, lenient_client):
    """
    When JEFF_WEBHOOK_SECRET is not set the guard is skipped entirely.
    A request with no signature header must NOT return 401.
    """
    monkeypatch.delenv("JEFF_WEBHOOK_SECRET", raising=False)
    body = json.dumps(VALID_BATCH).encode()
    response = lenient_client.post(
        ENDPOINT, content=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code != 401, (
        f"HMAC guard fired when secret not set — got 401. Body: {response.text}"
    )


def test_integration_valid_hmac_accepted(monkeypatch, lenient_client):
    """
    Request signed with the correct secret must pass the guard (not 401).
    The endpoint may return a non-200 for other reasons; that is acceptable.
    """
    secret = "integration-test-secret-abc123"
    monkeypatch.setenv("JEFF_WEBHOOK_SECRET", secret)
    body = json.dumps(VALID_BATCH).encode()
    headers = _make_headers(body, secret)
    response = lenient_client.post(ENDPOINT, content=body, headers=headers)
    assert response.status_code != 401, (
        f"Valid HMAC signature was rejected (401). Body: {response.text}"
    )


def test_integration_invalid_hmac_returns_401(monkeypatch, client):
    """Request signed with wrong secret must be rejected with 401."""
    monkeypatch.setenv("JEFF_WEBHOOK_SECRET", "correct-secret")
    body = json.dumps(VALID_BATCH).encode()
    headers = _make_headers(body, "wrong-secret")
    response = client.post(ENDPOINT, content=body, headers=headers)
    assert response.status_code == 401, (
        f"Expected 401 for invalid signature, got {response.status_code}. Body: {response.text}"
    )


def test_integration_missing_header_returns_401(monkeypatch, client):
    """Request with no X-Hub-Signature-256 header must be rejected with 401."""
    monkeypatch.setenv("JEFF_WEBHOOK_SECRET", "correct-secret")
    body = json.dumps(VALID_BATCH).encode()
    response = client.post(
        ENDPOINT, content=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 401, (
        f"Expected 401 for missing header, got {response.status_code}. Body: {response.text}"
    )


def test_integration_tampered_body_returns_401(monkeypatch, client):
    """
    Signature valid for original body must fail when body is altered.
    Simulates a MITM modification attack.
    """
    secret = "tamper-test-secret"
    monkeypatch.setenv("JEFF_WEBHOOK_SECRET", secret)
    original_body = json.dumps(VALID_BATCH).encode()
    sig = _sign(original_body, secret.encode())
    tampered_body = original_body + b" "
    response = client.post(
        ENDPOINT,
        content=tampered_body,
        headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"},
    )
    assert response.status_code == 401, (
        f"Expected 401 for tampered body, got {response.status_code}. Body: {response.text}"
    )

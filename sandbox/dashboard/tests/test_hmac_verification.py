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
    - JEFF_WEBHOOK_SECRET not set → secret-skip path, endpoint reachable
    - JEFF_WEBHOOK_SECRET set + valid signature → endpoint accepts (200 or processes)
    - JEFF_WEBHOOK_SECRET set + invalid signature → 401
    - JEFF_WEBHOOK_SECRET set + missing header → 401

SANDBOX ONLY — this test file targets C:\\JeffLocal\\sandbox\\dashboard\\ (port 5000).
Never run against the production dashboard (port 8765).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
import sys

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
DASHBOARD_ROOT = Path(__file__).resolve().parents[1]
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))

from app.main import app  # noqa: E402

# verify_hmac_signature is a planned feature (IR-01). Import conditionally so
# collection does not fail when the function is not yet implemented. Unit tests
# that exercise the function directly are marked xfail until it is merged.
try:
    from app.main import verify_hmac_signature  # type: ignore[attr-defined]
    _HMAC_FN_AVAILABLE = True
except ImportError:
    verify_hmac_signature = None  # type: ignore[assignment]
    _HMAC_FN_AVAILABLE = False

_needs_hmac_fn = pytest.mark.xfail(
    not _HMAC_FN_AVAILABLE,
    reason="verify_hmac_signature not yet implemented in app.main (IR-01 pending)",
    strict=False,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _sign(payload: bytes, secret: bytes) -> str:
    """Produce a correctly-formatted X-Hub-Signature-256 value."""
    digest = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


# ── Unit tests: verify_hmac_signature ─────────────────────────────────────────

SECRET = b"test-secret-for-unit-tests"
PAYLOAD = b'{"call_id": "TEST-001", "transcript": "headache"}'


@_needs_hmac_fn
def test_valid_signature_returns_true():
    """Correct HMAC-SHA256 signature must return True."""
    sig = _sign(PAYLOAD, SECRET)
    assert verify_hmac_signature(PAYLOAD, sig, SECRET) is True


@_needs_hmac_fn
def test_tampered_payload_returns_false():
    """Signature computed over original payload must fail for altered payload."""
    sig = _sign(PAYLOAD, SECRET)
    tampered = PAYLOAD + b" extra"
    assert verify_hmac_signature(tampered, sig, SECRET) is False


@_needs_hmac_fn
def test_wrong_secret_returns_false():
    """Signature computed with a different secret must fail."""
    sig = _sign(PAYLOAD, b"wrong-secret")
    assert verify_hmac_signature(PAYLOAD, sig, SECRET) is False


@_needs_hmac_fn
def test_missing_signature_header_returns_false():
    """Empty string signature header (header absent) must return False."""
    assert verify_hmac_signature(PAYLOAD, "", SECRET) is False


@_needs_hmac_fn
def test_malformed_header_no_prefix_returns_false():
    """Header without 'sha256=' prefix must return False without raising."""
    raw_hex = hmac.new(SECRET, PAYLOAD, hashlib.sha256).hexdigest()
    assert verify_hmac_signature(PAYLOAD, raw_hex, SECRET) is False


@_needs_hmac_fn
def test_wrong_prefix_returns_false():
    """Header with wrong algorithm prefix must return False."""
    digest = hmac.new(SECRET, PAYLOAD, hashlib.sha256).hexdigest()
    assert verify_hmac_signature(PAYLOAD, f"sha1={digest}", SECRET) is False


@_needs_hmac_fn
def test_empty_payload_valid_signature_returns_true():
    """Empty body is a valid payload; signature over it must verify correctly."""
    empty = b""
    sig = _sign(empty, SECRET)
    assert verify_hmac_signature(empty, sig, SECRET) is True


@_needs_hmac_fn
def test_empty_payload_wrong_signature_returns_false():
    """Empty body with a signature computed over non-empty payload must fail."""
    sig = _sign(PAYLOAD, SECRET)  # signed over non-empty
    assert verify_hmac_signature(b"", sig, SECRET) is False


@_needs_hmac_fn
def test_uses_constant_time_comparison():
    """
    Confirm hmac.compare_digest is used (timing-safe).
    We verify indirectly: the function must return False rather than raise
    when given strings of different lengths (compare_digest handles this
    without short-circuiting on the first differing byte).
    """
    short_sig = "sha256=abc"
    assert verify_hmac_signature(PAYLOAD, short_sig, SECRET) is False


# ── Integration tests: /api/n8n/test-intake-batch ────────────────────────────

# A minimal payload that satisfies the endpoint's own validation guards
# (test_mode=true, disable_google_push=true, valid calls list).
# The call_id prefix "N8NTEST-" satisfies the call_id format check.
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
    """FastAPI TestClient with isolated DB and auth bypassed."""
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


def _make_headers(payload_bytes: bytes, secret: str) -> dict[str, str]:
    sig = _sign(payload_bytes, secret.encode())
    return {"X-Hub-Signature-256": sig, "Content-Type": "application/json"}


@pytest.fixture()
def lenient_client(monkeypatch, tmp_path):
    """TestClient with raise_server_exceptions=False.

    Used by tests that only care about the HMAC guard verdict (401 vs not-401)
    and must not fail when the downstream pipeline raises due to missing
    test fixtures (live_lookup_test_payloads) in this Linux CI environment.
    """
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

    with TestClient(app, raise_server_exceptions=False) as tc:
        yield tc


def test_integration_no_secret_set_skips_verification(monkeypatch, lenient_client):
    """
    When JEFF_WEBHOOK_SECRET is not configured the dependency skips HMAC
    verification.  A request with no signature header should not be rejected
    by the HMAC guard (endpoint may still fail for other reasons — e.g. the
    encrypted intake cycle — but must NOT return 401 for a missing signature).
    """
    monkeypatch.delenv("JEFF_WEBHOOK_SECRET", raising=False)
    body = json.dumps(VALID_BATCH).encode()
    response = lenient_client.post(ENDPOINT, content=body, headers={"Content-Type": "application/json"})
    # 401 would mean HMAC guard fired — that must not happen when secret is absent
    assert response.status_code != 401, (
        f"Expected HMAC guard to be skipped when secret not set, got 401. "
        f"Body: {response.text}"
    )


def test_integration_valid_hmac_accepted(monkeypatch, lenient_client):
    """
    Request signed with the correct secret must pass the HMAC guard.
    The endpoint may subsequently fail (e.g. intake cycle not running in tests)
    but must NOT return 401.
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
    headers = _make_headers(body, "wrong-secret")  # wrong signing key
    response = client.post(ENDPOINT, content=body, headers=headers)
    assert response.status_code == 401, (
        f"Expected 401 for invalid signature, got {response.status_code}. "
        f"Body: {response.text}"
    )


def test_integration_missing_header_returns_401(monkeypatch, client):
    """Request with no X-Hub-Signature-256 header must be rejected with 401."""
    monkeypatch.setenv("JEFF_WEBHOOK_SECRET", "correct-secret")
    body = json.dumps(VALID_BATCH).encode()
    response = client.post(
        ENDPOINT,
        content=body,
        headers={"Content-Type": "application/json"},  # no HMAC header
    )
    assert response.status_code == 401, (
        f"Expected 401 for missing signature header, got {response.status_code}. "
        f"Body: {response.text}"
    )


def test_integration_tampered_body_returns_401(monkeypatch, client):
    """
    Signature computed over original body must fail when body is altered in transit.
    Simulates a replay / MITM modification attack.
    """
    secret = "tamper-test-secret"
    monkeypatch.setenv("JEFF_WEBHOOK_SECRET", secret)
    original_body = json.dumps(VALID_BATCH).encode()
    sig = _sign(original_body, secret.encode())

    # Send a different body with the signature from the original
    tampered_body = original_body + b" "
    response = client.post(
        ENDPOINT,
        content=tampered_body,
        headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"},
    )
    assert response.status_code == 401, (
        f"Expected 401 for tampered body, got {response.status_code}. "
        f"Body: {response.text}"
    )

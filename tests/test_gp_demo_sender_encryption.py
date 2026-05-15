from __future__ import annotations

import base64
import importlib.util
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT_DIR / "tests" / "fixtures"
SENDER_PATH = ROOT_DIR / "tests" / "send_gp_demo_n8n_webhook_calls.py"
DECRYPT_PATH = ROOT_DIR / "app" / "decrypt_encrypted_raw.py"

for path in (ROOT_DIR, FIXTURE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from live_lookup_test_payloads import encrypt_envelope as working_encrypt_envelope  # noqa: E402
from n8n_webhook_test_pack import build_batch as build_n8ntest_batch  # noqa: E402


def load_sender_module():
    spec = importlib.util.spec_from_file_location("gp_demo_sender", SENDER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_decrypt_envelope():
    spec = importlib.util.spec_from_file_location("gp_demo_decrypt", DECRYPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.decrypt_envelope


def test_gp_demo_sender_reuses_working_encrypt_helper():
    sender = load_sender_module()
    assert sender.encrypt_envelope is working_encrypt_envelope


def test_gp_demo_batch_has_five_encrypted_calls_and_long_transcripts():
    sender = load_sender_module()
    batch_id = "GPDEMO-20260513-TESTBATCH"
    plain_calls = sender.build_plain_calls(batch_id)
    batch = sender.build_batch(batch_id)

    assert len(plain_calls) == 5
    assert all(len(call["raw_transcript"]) > 500 for call in plain_calls)
    assert batch["test_mode"] is True
    assert batch["disable_google_push"] is True
    assert batch["refresh_artifacts"] is True
    assert batch["batch_id"] == batch_id
    assert batch["source"] == "voice_agent_demo"
    assert len(batch["calls"]) == 5
    assert all(sender.REQUIRED_ENVELOPE_FIELDS.issubset(call.keys()) for call in batch["calls"])
    assert build_n8ntest_batch is not None
    assert set(batch["calls"][0].keys()) == set(build_n8ntest_batch("N8NTEST-LOCAL-BATCH")["calls"][0].keys())


def test_gp_demo_envelope_decrypts_locally_and_uses_separate_tag():
    sender = load_sender_module()
    decrypt_envelope = load_decrypt_envelope()
    plain_call = sender.build_plain_calls("GPDEMO-20260513-TESTBATCH")[0]
    envelope = sender.encrypt_envelope(plain_call)

    assert envelope["protocol"] == "JEIE-1"
    assert envelope["alg"] == "RSA-OAEP-256+A256GCM"
    assert envelope["key_id"] == "jefflocal-rsa-test-001"
    assert envelope["signature_alg"] == "HMAC-SHA256"
    assert "tag" in envelope
    assert "ciphertext" in envelope
    assert len(base64.b64decode(envelope["tag"])) == 16

    decrypted = decrypt_envelope(envelope)
    assert decrypted["call_id"] == plain_call["call_id"]
    assert decrypted["source"] == "voice_agent"
    assert decrypted["raw_transcript"] == plain_call["raw_transcript"]


def test_gp_demo_dry_run_and_confirm_send_gate(monkeypatch, capsys):
    sender = load_sender_module()
    calls = []

    def fake_send_batch(*args, **kwargs):
        calls.append((args, kwargs))
        return 200, "{}"

    monkeypatch.setattr(sender, "send_batch", fake_send_batch)
    monkeypatch.setattr(sender, "report_deadletter_issue", lambda batch_id: None)

    monkeypatch.setattr(sys, "argv", ["send_gp_demo_n8n_webhook_calls.py", "--dry-run"])
    assert sender.main() == 0
    assert not calls
    dry_output = capsys.readouterr().out
    assert '"mode": "dry-run"' in dry_output

    monkeypatch.setattr(sys, "argv", ["send_gp_demo_n8n_webhook_calls.py"])
    assert sender.main() == 2
    assert not calls

    monkeypatch.setattr(sys, "argv", ["send_gp_demo_n8n_webhook_calls.py", "--confirm-send"])
    assert sender.main() == 0
    assert calls

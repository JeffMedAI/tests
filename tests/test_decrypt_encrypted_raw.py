from __future__ import annotations

import json
import importlib.util
import base64
import hashlib
import hmac
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT_DIR / "tests" / "fixtures"
for path in (ROOT_DIR, FIXTURE_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from live_lookup_test_payloads import encrypt_envelope, make_call, PATIENTS  # noqa: E402


def load_decryptor():
    spec = importlib.util.spec_from_file_location("jefflocal_decrypt_encrypted_raw", ROOT_DIR / "app" / "decrypt_encrypted_raw.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


decryptor = load_decryptor()


def make_inner(call_id: str) -> dict:
    return make_call(
        "DECRYPTOR",
        1,
        call_id,
        PATIENTS["230"],
        "prescription",
        "repeat_prescription",
        "Jeff: Can I help? Caller: I need my repeat prescription please. Jeff: Thank you, I will pass it to the practice team.",
        meds=["atorvastatin 20mg"],
        pharmacy="Test Pharmacy",
        caller_id_number="07111000230",
    )


def make_config_file(tmp_path: Path) -> Path:
    source = json.loads((ROOT_DIR / "config" / "security" / "jeie_v1.config.json").read_text(encoding="utf-8"))
    source.update(
        {
            "queue_encrypted_raw_path": str(tmp_path / "encrypted_raw"),
            "queue_incoming_path": str(tmp_path / "incoming"),
            "queue_encrypted_processed_path": str(tmp_path / "encrypted_processed"),
            "deadletter_path": str(tmp_path / "deadletter"),
            "audit_log_path": str(tmp_path / "audits"),
            "security_log_path": str(tmp_path / "security"),
            "nonce_store_path": str(tmp_path / "security" / "runtime" / "nonce_store.json"),
        }
    )
    config_path = tmp_path / "jeie_v1.config.json"
    config_path.write_text(json.dumps(source), encoding="utf-8")
    return config_path


def make_config(tmp_path: Path) -> decryptor.SecurityConfig:
    config = decryptor.load_config(make_config_file(tmp_path))
    decryptor.ensure_directories(config)
    return config


def write_envelope(config: decryptor.SecurityConfig, envelope: dict, name: str = "envelope.json") -> Path:
    path = config.queue_encrypted_raw_path / name
    path.write_text(json.dumps(envelope), encoding="utf-8")
    return path


def latest_jsonl(directory: Path) -> list[dict]:
    files = sorted(directory.glob("*.jsonl"))
    assert files
    return [json.loads(line) for line in files[-1].read_text(encoding="utf-8").splitlines()]


def utc_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resign_envelope(envelope: dict) -> dict:
    secret = (ROOT_DIR / "config" / "security" / "keys" / "voice_agent_hmac_secret.txt").read_text(encoding="utf-8").strip().encode("utf-8")
    canonical = ".".join(
        [
            envelope["protocol"],
            envelope["sender_id"],
            envelope["message_id"],
            envelope["timestamp_utc"],
            envelope["nonce"],
            envelope["key_id"],
            envelope["alg"],
            envelope["encrypted_key"],
            envelope["iv"],
            envelope["ciphertext"],
            envelope["tag"],
        ]
    )
    envelope["signature"] = base64.b64encode(hmac.new(secret, canonical.encode("utf-8"), hashlib.sha256).digest()).decode("ascii")
    return envelope


def stale_envelope(call_id: str) -> dict:
    envelope = encrypt_envelope(make_inner(call_id))
    envelope["timestamp_utc"] = utc_iso(datetime.now(timezone.utc) - timedelta(hours=2))
    return resign_envelope(envelope)


def future_envelope(call_id: str) -> dict:
    envelope = encrypt_envelope(make_inner(call_id))
    envelope["timestamp_utc"] = utc_iso(datetime.now(timezone.utc) + timedelta(hours=2))
    return resign_envelope(envelope)


def invalid_inner_envelope() -> dict:
    inner = {
        "call_id": "PREVIEW-INNER",
        "patient_name": "Abdel Boumnijel",
        "dob": "1952-12-18",
        "medication": "atorvastatin 20mg",
        "message": "Caller asked for a repeat prescription.",
        "payload": {
            "callback_number": "07111000230",
            "nhs_number": "626 283 3153",
            "raw_transcript": "Jeff: Hello. Caller: I need medication.",
        },
        "items": [{"name": "Abdel Boumnijel"}, "atorvastatin 20mg", 7, None],
    }
    return encrypt_envelope(inner)


def request_wrapped_inner() -> dict:
    return {
        "call_id": "WRAPPED-INNER",
        "call_timestamp": decryptor.now_iso(),
        "environment": "test",
        "event_type": "voice_intake",
        "payload_status": "ready",
        "source": "voice_agent",
        "voice_agent": {
            "provider": "demo",
            "call_direction": "inbound",
            "caller_number": "07111000230",
        },
        "request": {
            "workflow": "prescription",
            "request_type": "repeat_prescription",
            "raw_transcript": "Jeff: Hello. Caller: I need my repeat prescription.",
            "patient": {
                "name": "Abdel Boumnijel",
                "dob": "1952-12-18",
                "postcode": "PR1 1AA",
                "nhs_number": "626 283 3153",
            },
            "caller": {
                "relationship": "self",
            },
            "details": {
                "medication": "atorvastatin 20mg",
                "urgency": "routine",
                "pharmacy": "Test Pharmacy",
            },
        },
    }


def wrapped_envelope(overrides: dict | None = None) -> dict:
    inner = request_wrapped_inner()
    if overrides:
        inner.update(overrides)
    return encrypt_envelope(inner)


def test_decryptor_has_no_hardcoded_security_paths_except_config_path():
    source = (ROOT_DIR / "app" / "decrypt_encrypted_raw.py").read_text(encoding="utf-8")
    assert source.count(r"C:\JeffLocal") == 1
    assert "CONFIG_PATH" in source


def test_success_writes_incoming_moves_processed_and_audits(tmp_path):
    config = make_config(tmp_path)
    inner = make_inner("SUCCESS")
    envelope = encrypt_envelope(inner)
    source_path = write_envelope(config, envelope)

    assert decryptor.process_with_failure_handling(source_path, config, dry_run=False) is True
    incoming_path = config.queue_incoming_path / f"{inner['call_id']}.json"
    assert incoming_path.exists()
    assert not source_path.exists()
    assert (config.encrypted_processed_path / source_path.name).exists()

    events = latest_jsonl(config.audit_log_path)
    assert events[-1]["event"] == "encrypted_envelope_decrypted"
    assert events[-1]["message_id"] == inner["call_id"]
    assert events[-1]["sender_id"] == "voice-agent-test"
    assert events[-1]["key_id"] == "jefflocal-rsa-test-001"
    assert events[-1]["envelope_sha256"]


def test_dry_run_does_not_write_or_move(tmp_path):
    config = make_config(tmp_path)
    inner = make_inner("DRYRUN")
    source_path = write_envelope(config, encrypt_envelope(inner))

    assert decryptor.process_with_failure_handling(source_path, config, dry_run=True) is True
    assert source_path.exists()
    assert not (config.queue_incoming_path / f"{inner['call_id']}.json").exists()
    assert not list(config.encrypted_processed_path.glob("*.json"))


def test_invalid_base64_fails_stage_and_moves_deadletter(tmp_path):
    config = make_config(tmp_path)
    envelope = encrypt_envelope(make_inner("BADB64"))
    envelope["tag"] = "not valid base64!"
    source_path = write_envelope(config, envelope, "badb64.json")

    assert decryptor.process_with_failure_handling(source_path, config, dry_run=False) is False
    assert not source_path.exists()
    deadletters = list(config.deadletter_path.glob("decrypt_failed_badb64*.json"))
    assert len(deadletters) == 1

    events = latest_jsonl(config.security_log_path)
    assert events[-1]["event"] == "decrypt_failed"
    assert events[-1]["stage"] == "validate_base64_fields"
    assert events[-1]["encrypted_key_sha256_prefix"]
    assert events[-1]["ciphertext_sha256_prefix"]
    assert events[-1]["signature_sha256_prefix"]
    assert "atorvastatin" not in json.dumps(events[-1]).lower()


def test_nonce_replay_detected_after_success(tmp_path):
    config = make_config(tmp_path)
    envelope = encrypt_envelope(make_inner("REPLAY"))
    first_path = write_envelope(config, envelope, "first.json")
    second_path = write_envelope(config, envelope, "second.json")

    assert decryptor.process_with_failure_handling(first_path, config, dry_run=False) is True
    assert decryptor.process_with_failure_handling(second_path, config, dry_run=False) is False

    events = latest_jsonl(config.security_log_path)
    assert events[-1]["stage"] == "validate_envelope_metadata"
    assert "replay_detected" in events[-1]["sanitized_reason"]
    assert events[-1]["safe_to_replay"] is False


def test_stale_envelope_rejected_by_default(tmp_path):
    config = make_config(tmp_path)
    source_path = write_envelope(config, stale_envelope("STALEDEFAULT"), "replay_stale_default.json")

    assert decryptor.process_with_failure_handling(source_path, config, dry_run=True) is False
    assert source_path.exists()
    events = latest_jsonl(config.security_log_path)
    assert events[-1]["stage"] == "validate_envelope_metadata"
    assert events[-1]["stale_replay_override"] is False
    assert events[-1]["timestamp_age_seconds"] > config.timestamp_skew_seconds
    assert events[-1]["safe_to_replay"] is False


def test_stale_envelope_allowed_with_file_allow_stale_replay(tmp_path):
    config = make_config(tmp_path)
    source_path = write_envelope(config, stale_envelope("STALEALLOW"), "replay_stale_allow.json")

    assert decryptor.process_with_failure_handling(source_path, config, dry_run=True, allow_stale_replay=True) is True
    assert source_path.exists()
    audits = latest_jsonl(config.audit_log_path)
    assert audits[-1]["event"] == "encrypted_envelope_decrypted"
    assert audits[-1]["stale_replay_override"] is True
    assert audits[-1]["dry_run"] is True
    assert audits[-1]["timestamp_age_seconds"] > config.timestamp_skew_seconds
    assert audits[-1]["nonce_replay_check_bypassed"] is True


def test_allow_stale_replay_cli_rejected_without_file(tmp_path):
    config_path = make_config_file(tmp_path)

    assert decryptor.main(["--config", str(config_path), "--allow-stale-replay"]) == 2


def test_allow_stale_replay_cli_rejected_for_normal_batch_target(tmp_path):
    config = make_config(tmp_path)
    config_path = tmp_path / "jeie_v1.config.json"
    source_path = write_envelope(config, stale_envelope("STALENORMAL"), "normal_stale.json")

    assert decryptor.main(["--config", str(config_path), "--file", str(source_path), "--allow-stale-replay", "--dry-run"]) == 2


def test_future_timestamp_rejected_even_with_stale_replay_override(tmp_path):
    config = make_config(tmp_path)
    source_path = write_envelope(config, future_envelope("FUTURE"), "replay_future.json")

    assert decryptor.process_with_failure_handling(source_path, config, dry_run=True, allow_stale_replay=True) is False
    events = latest_jsonl(config.security_log_path)
    assert events[-1]["stage"] == "validate_envelope_metadata"
    assert "future" in events[-1]["sanitized_reason"]
    assert events[-1]["stale_replay_override"] is True
    assert events[-1]["safe_to_replay"] is False


def test_preview_inner_schema_rejected_without_dry_run(tmp_path):
    config_path = make_config_file(tmp_path)
    assert decryptor.main(["--config", str(config_path), "--preview-inner-schema"]) == 2


def test_preview_inner_schema_contains_keys_and_types_not_values(tmp_path, capsys):
    config = make_config(tmp_path)
    source_path = write_envelope(config, invalid_inner_envelope(), "preview_inner.json")

    assert decryptor.process_with_failure_handling(source_path, config, dry_run=True, preview_inner_schema=True) is False
    output = capsys.readouterr().out
    events = latest_jsonl(config.security_log_path)
    preview = events[-1]["inner_schema_preview"]

    assert events[-1]["stage"] == "validate_inner_json"
    assert "Safe inner schema preview" in output
    assert "patient_name" in preview["top_level_keys"]
    assert preview["fields"]["payload"]["type"] == "dict"
    assert set(preview["fields"]["payload"]["child_keys"]) == {"callback_number", "nhs_number", "raw_transcript"}
    assert preview["fields"]["items"]["type"] == "list"
    assert preview["fields"]["items"]["length"] == 4
    assert set(preview["fields"]["items"]["item_types"]) == {"dict", "int", "null", "str"}

    rendered = json.dumps(events[-1]) + output
    assert "Abdel Boumnijel" not in rendered
    assert "1952-12-18" not in rendered
    assert "07111000230" not in rendered
    assert "atorvastatin" not in rendered.lower()
    assert "626 283 3153" not in rendered
    assert "Jeff: Hello" not in rendered


def test_request_wrapped_payload_maps_and_passes_validate_inner_json(tmp_path):
    config = make_config(tmp_path)
    envelope = wrapped_envelope()
    source_path = write_envelope(config, envelope, "wrapped.json")

    assert decryptor.process_with_failure_handling(source_path, config, dry_run=True) is True
    decrypted = decryptor.decrypt_envelope(envelope, config)
    assert decrypted["workflow"] == "prescription"
    assert decrypted["request_type"] == "repeat_prescription"
    assert decrypted["raw_transcript"]
    assert decrypted["normalized_input"]["patient_name"] == "Abdel Boumnijel"
    assert decrypted["normalized_input"]["dob"] == "1952-12-18"
    assert decrypted["normalized_input"]["postcode"] == "PR1 1AA"
    assert decrypted["normalized_input"]["nhs_number"] == "626 283 3153"
    assert decrypted["normalized_input"]["callback_number"] == "07111000230"
    assert decrypted["normalized_input"]["caller_for"] == "self"
    assert decrypted["normalized_input"]["medications_requested"] == ["atorvastatin 20mg"]
    assert decrypted["normalized_input"]["urgency_note"] == "routine"
    assert decrypted["normalized_input"]["pharmacy"] == "Test Pharmacy"


def test_request_wrapper_transport_source_is_preserved_and_source_normalized(tmp_path):
    config = make_config(tmp_path)
    inner = request_wrapped_inner()
    inner["source"] = "n8n_e2e_batch"
    envelope = encrypt_envelope(inner)
    source_path = write_envelope(config, envelope, "transport_wrapped.json")

    assert decryptor.process_with_failure_handling(source_path, config, dry_run=True) is True
    decrypted = decryptor.decrypt_envelope(envelope, config)
    assert decrypted["source"] == "voice_agent"
    assert decrypted["transport_source"] == "n8n_e2e_batch"


def test_arbitrary_source_without_voice_agent_dict_still_fails(tmp_path):
    config = make_config(tmp_path)
    inner = request_wrapped_inner()
    inner["source"] = "n8n_e2e_batch"
    inner.pop("voice_agent")
    source_path = write_envelope(config, encrypt_envelope(inner), "no_voice_agent.json")

    assert decryptor.process_with_failure_handling(source_path, config, dry_run=True, preview_inner_schema=True) is False
    events = latest_jsonl(config.security_log_path)
    assert events[-1]["stage"] == "validate_inner_json"
    assert "Unsupported source" in events[-1]["sanitized_reason"]


def test_source_voice_agent_remains_unchanged(tmp_path):
    config = make_config(tmp_path)
    decrypted = decryptor.decrypt_envelope(wrapped_envelope(), config)
    assert decrypted["source"] == "voice_agent"
    assert "transport_source" not in decrypted


def test_audit_success_log_includes_transport_source_when_present(tmp_path):
    config = make_config(tmp_path)
    inner = request_wrapped_inner()
    inner["source"] = "n8n_e2e_batch"
    source_path = write_envelope(config, encrypt_envelope(inner), "transport_audit_real.json")

    assert decryptor.process_with_failure_handling(source_path, config, dry_run=False, allow_stale_replay=False) is True
    audits = latest_jsonl(config.audit_log_path)
    assert audits[-1]["transport_source"] == "n8n_e2e_batch"
    rendered = json.dumps(audits[-1])
    assert "Abdel Boumnijel" not in rendered
    assert "1952-12-18" not in rendered
    assert "07111000230" not in rendered
    assert "atorvastatin" not in rendered.lower()


def test_request_wrapper_does_not_overwrite_existing_top_level_fields(tmp_path):
    config = make_config(tmp_path)
    inner = request_wrapped_inner()
    inner["workflow"] = "top_workflow"
    inner["request_type"] = "top_request"
    inner["raw_transcript"] = "Top-level transcript."
    envelope = encrypt_envelope(inner)

    decrypted = decryptor.decrypt_envelope(envelope, config)
    assert decrypted["workflow"] == "top_workflow"
    assert decrypted["request_type"] == "top_request"
    assert decrypted["raw_transcript"] == "Top-level transcript."


def test_voice_agent_caller_number_fallback_only_when_callback_missing(tmp_path):
    config = make_config(tmp_path)
    fallback = decryptor.decrypt_envelope(wrapped_envelope(), config)
    assert fallback["normalized_input"]["callback_number"] == "07111000230"

    inner = request_wrapped_inner()
    inner["request"]["caller"]["callback_number"] = "07111000999"
    explicit = decryptor.decrypt_envelope(encrypt_envelope(inner), config)
    assert explicit["normalized_input"]["callback_number"] == "07111000999"


def test_request_wrapper_missing_useful_fields_still_fails_cleanly(tmp_path):
    config = make_config(tmp_path)
    inner = request_wrapped_inner()
    del inner["request"]["workflow"]
    del inner["request"]["request_type"]
    del inner["request"]["raw_transcript"]
    source_path = write_envelope(config, encrypt_envelope(inner), "bad_wrapped.json")

    assert decryptor.process_with_failure_handling(source_path, config, dry_run=True, preview_inner_schema=True) is False
    events = latest_jsonl(config.security_log_path)
    assert events[-1]["stage"] == "validate_inner_json"
    rendered = json.dumps(events[-1])
    assert "Abdel Boumnijel" not in rendered
    assert "1952-12-18" not in rendered
    assert "07111000230" not in rendered
    assert "atorvastatin" not in rendered.lower()

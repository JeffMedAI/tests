import argparse
import base64
import binascii
import hashlib
import hmac
import json
import os
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


CONFIG_PATH = Path(r"C:\JeffLocal\config\security\jeie_v1.config.json")
SIGNATURE_ALG = "HMAC-SHA256"
REQUIRED_ENVELOPE_FIELDS = [
    "protocol",
    "alg",
    "key_id",
    "sender_id",
    "message_id",
    "timestamp_utc",
    "nonce",
    "encrypted_key",
    "iv",
    "ciphertext",
    "tag",
    "signature_alg",
    "signature",
]
BASE64_FIELDS = ["encrypted_key", "iv", "ciphertext", "tag", "signature"]
REQUIRED_INNER_FIELDS = [
    "call_id",
    "call_timestamp",
    "workflow",
    "request_type",
    "source",
    "normalized_input",
    "raw_transcript",
]


def first_present(mapping: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return None


class DecryptStageError(Exception):
    def __init__(
        self,
        stage: str,
        reason: str,
        *,
        envelope: dict[str, Any] | None = None,
        source_file: Path | None = None,
        original_exception: BaseException | None = None,
        inner_schema_preview: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(reason)
        self.stage = stage
        self.message_id = safe_metadata(envelope, "message_id") if envelope else ""
        self.key_id = safe_metadata(envelope, "key_id") if envelope else ""
        self.sender_id = safe_metadata(envelope, "sender_id") if envelope else ""
        self.alg = safe_metadata(envelope, "alg") if envelope else ""
        self.signature_alg = safe_metadata(envelope, "signature_alg") if envelope else ""
        self.source_file = str(source_file) if source_file else ""
        self.original_exception_type = type(original_exception).__name__ if original_exception else ""
        self.sanitized_reason = sanitize_reason(reason)
        self.inner_schema_preview = inner_schema_preview


@dataclass(frozen=True)
class TimestampValidation:
    age_seconds: float | None
    stale_override_used: bool


@dataclass(frozen=True)
class SecurityConfig:
    protocol: str
    allowed_alg: str
    allowed_senders: set[str]
    active_key_id: str
    timestamp_skew_seconds: int
    nonce_retention_hours: int
    max_body_bytes: int
    queue_encrypted_raw_path: Path
    queue_incoming_path: Path
    encrypted_processed_path: Path
    deadletter_path: Path
    audit_log_path: Path
    security_log_path: Path
    private_key_path: Path
    public_key_path: Path
    hmac_secret_path: Path
    nonce_store_path: Path
    private_key_passphrase: bytes | None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def now_iso() -> str:
    return utc_now().isoformat()


def sanitize_reason(reason: str) -> str:
    text = str(reason)
    text = re.sub(r"[A-Za-z0-9+/=_-]{48,}", "[redacted-token]", text)
    text = re.sub(r"\b\d{10}\b", "[redacted-number]", text)
    text = re.sub(r"\b\d{3}\s?\d{3}\s?\d{4}\b", "[redacted-number]", text)
    return text[:500]


def safe_metadata(envelope: dict[str, Any] | None, field: str) -> str:
    if not envelope:
        return ""
    value = envelope.get(field, "")
    if value is None:
        return ""
    return sanitize_reason(str(value))[:160]


def sha256_hex(data: bytes | str) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8", "replace")
    return hashlib.sha256(data).hexdigest()


def optional_field_hash_prefix(envelope: dict[str, Any] | None, field: str) -> str:
    if not envelope or field not in envelope:
        return ""
    return sha256_hex(str(envelope[field]))[:16]


def safe_filename(value: str) -> str:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in value)
    return safe or "unknown"


def load_config(config_path: Path = CONFIG_PATH) -> SecurityConfig:
    raw = config_path.read_text(encoding="utf-8-sig")
    data = json.loads(raw)

    required_paths = [
        "queue_encrypted_raw_path",
        "queue_incoming_path",
        "deadletter_path",
        "audit_log_path",
        "security_log_path",
        "private_key_path",
        "public_key_path",
        "hmac_secret_path",
    ]
    missing = [field for field in required_paths if not data.get(field)]
    if missing:
        raise DecryptStageError(
            "validate_envelope_metadata",
            f"Security config missing fields: {', '.join(missing)}",
            original_exception=None,
        )

    encrypted_raw = Path(data["queue_encrypted_raw_path"])
    processed_path = Path(data.get("queue_encrypted_processed_path") or encrypted_raw.parent / "encrypted_processed")
    security_log = Path(data["security_log_path"])
    nonce_store = Path(data.get("nonce_store_path") or security_log / "runtime" / "jeie_nonce_store.json")

    return SecurityConfig(
        protocol=str(data["protocol"]),
        allowed_alg=str(data["allowed_alg"]),
        allowed_senders={str(item) for item in data.get("allowed_senders", [])},
        active_key_id=str(data["active_key_id"]),
        timestamp_skew_seconds=int(data.get("timestamp_skew_seconds", 300)),
        nonce_retention_hours=int(data.get("nonce_retention_hours", 24)),
        max_body_bytes=int(data.get("max_body_bytes", 262144)),
        queue_encrypted_raw_path=encrypted_raw,
        queue_incoming_path=Path(data["queue_incoming_path"]),
        encrypted_processed_path=processed_path,
        deadletter_path=Path(data["deadletter_path"]),
        audit_log_path=Path(data["audit_log_path"]),
        security_log_path=security_log,
        private_key_path=Path(data["private_key_path"]),
        public_key_path=Path(data["public_key_path"]),
        hmac_secret_path=Path(data["hmac_secret_path"]),
        nonce_store_path=nonce_store,
        private_key_passphrase=data["private_key_passphrase"].encode("utf-8") if data.get("private_key_passphrase") else None,
    )


def ensure_directories(config: SecurityConfig) -> None:
    for path in [
        config.queue_incoming_path,
        config.queue_encrypted_raw_path,
        config.encrypted_processed_path,
        config.deadletter_path,
        config.audit_log_path,
        config.security_log_path,
        config.nonce_store_path.parent,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def jsonl_append(directory: Path, prefix: str, event: dict[str, Any]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    log_file = directory / f"{prefix}_{utc_now().date()}.jsonl"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def audit(config: SecurityConfig, event: dict[str, Any]) -> None:
    jsonl_append(config.audit_log_path, "decrypt_encrypted_raw", event)


def security(config: SecurityConfig, event: dict[str, Any]) -> None:
    jsonl_append(config.security_log_path, "decrypt_encrypted_raw_security", event)


def read_file(path: Path, config: SecurityConfig) -> str:
    try:
        size = path.stat().st_size
        if size > config.max_body_bytes:
            raise DecryptStageError("read_file", f"Envelope exceeds max_body_bytes: {size}", source_file=path)
        return path.read_text(encoding="utf-8-sig")
    except DecryptStageError:
        raise
    except Exception as exc:
        raise DecryptStageError("read_file", "Could not read envelope file", source_file=path, original_exception=exc)


def parse_envelope(raw: str, source_file: Path) -> dict[str, Any]:
    try:
        envelope = json.loads(raw)
    except Exception as exc:
        raise DecryptStageError("parse_json", "Envelope is not valid JSON", source_file=source_file, original_exception=exc)
    if not isinstance(envelope, dict):
        raise DecryptStageError("parse_json", "Envelope JSON must be an object", source_file=source_file)
    return envelope


def require_envelope_fields(envelope: dict[str, Any], source_file: Path) -> None:
    missing = [field for field in REQUIRED_ENVELOPE_FIELDS if envelope.get(field) in (None, "")]
    if missing:
        raise DecryptStageError(
            "required_envelope_fields",
            f"Missing required envelope fields: {', '.join(missing)}",
            envelope=envelope,
            source_file=source_file,
        )


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def timestamp_age_seconds(envelope: dict[str, Any]) -> float | None:
    try:
        timestamp = parse_timestamp(str(envelope["timestamp_utc"]))
    except Exception:
        return None
    return (utc_now() - timestamp).total_seconds()


def validate_envelope_metadata(
    envelope: dict[str, Any],
    config: SecurityConfig,
    source_file: Path,
    allow_stale_replay: bool = False,
) -> TimestampValidation:
    checks = [
        (envelope["protocol"] == config.protocol, f"Invalid protocol: {envelope['protocol']}"),
        (envelope["alg"] == config.allowed_alg, f"Invalid alg: {envelope['alg']}"),
        (envelope["key_id"] == config.active_key_id, f"Invalid key_id: {envelope['key_id']}"),
        (envelope["sender_id"] in config.allowed_senders, f"Sender not allowed: {envelope['sender_id']}"),
        (envelope["signature_alg"] == SIGNATURE_ALG, f"Invalid signature_alg: {envelope['signature_alg']}"),
    ]
    for ok, reason in checks:
        if not ok:
            raise DecryptStageError("validate_envelope_metadata", reason, envelope=envelope, source_file=source_file)

    try:
        timestamp = parse_timestamp(str(envelope["timestamp_utc"]))
    except Exception as exc:
        raise DecryptStageError(
            "validate_envelope_metadata",
            "Invalid timestamp_utc",
            envelope=envelope,
            source_file=source_file,
            original_exception=exc,
        )

    age_seconds = (utc_now() - timestamp).total_seconds()
    skew = config.timestamp_skew_seconds
    if age_seconds < -skew:
        raise DecryptStageError(
            "validate_envelope_metadata",
            "Envelope timestamp is too far in the future",
            envelope=envelope,
            source_file=source_file,
        )
    if age_seconds > skew:
        if allow_stale_replay:
            return TimestampValidation(age_seconds=age_seconds, stale_override_used=True)
        raise DecryptStageError(
            "validate_envelope_metadata",
            "Envelope timestamp is outside allowed freshness window",
            envelope=envelope,
            source_file=source_file,
        )
    return TimestampValidation(age_seconds=age_seconds, stale_override_used=False)


def validate_base64_fields(envelope: dict[str, Any], source_file: Path) -> dict[str, bytes]:
    decoded: dict[str, bytes] = {}
    for field in BASE64_FIELDS:
        try:
            decoded[field] = base64.b64decode(str(envelope[field]), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise DecryptStageError(
                "validate_base64_fields",
                f"Invalid base64 field: {field}",
                envelope=envelope,
                source_file=source_file,
                original_exception=exc,
            )
    if len(decoded["iv"]) != 12:
        raise DecryptStageError("validate_base64_fields", "Invalid iv length", envelope=envelope, source_file=source_file)
    if len(decoded["tag"]) != 16:
        raise DecryptStageError("validate_base64_fields", "Invalid AES-GCM tag length", envelope=envelope, source_file=source_file)
    return decoded


def hmac_canonical(envelope: dict[str, Any]) -> str:
    return ".".join(
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


def verify_hmac_signature(
    envelope: dict[str, Any],
    decoded: dict[str, bytes],
    config: SecurityConfig,
    source_file: Path,
) -> None:
    try:
        secret = config.hmac_secret_path.read_text(encoding="utf-8").strip().encode("utf-8")
        expected = hmac.new(secret, hmac_canonical(envelope).encode("utf-8"), hashlib.sha256).digest()
    except Exception as exc:
        raise DecryptStageError(
            "verify_hmac_signature",
            "Could not calculate HMAC signature",
            envelope=envelope,
            source_file=source_file,
            original_exception=exc,
        )
    if not hmac.compare_digest(expected, decoded["signature"]):
        raise DecryptStageError("verify_hmac_signature", "Invalid HMAC signature", envelope=envelope, source_file=source_file)


def load_private_key(config: SecurityConfig, envelope: dict[str, Any], source_file: Path) -> Any:
    try:
        return serialization.load_pem_private_key(config.private_key_path.read_bytes(), password=config.private_key_passphrase)
    except Exception as exc:
        raise DecryptStageError(
            "load_private_key",
            "Could not load configured private key",
            envelope=envelope,
            source_file=source_file,
            original_exception=exc,
        )


def rsa_unwrap_aes_key(
    private_key: Any,
    encrypted_key: bytes,
    envelope: dict[str, Any],
    source_file: Path,
) -> bytes:
    try:
        return private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except Exception as exc:
        raise DecryptStageError(
            "rsa_unwrap_aes_key",
            "Could not unwrap AES key with configured RSA private key",
            envelope=envelope,
            source_file=source_file,
            original_exception=exc,
        )


def aes_gcm_decrypt(aes_key: bytes, decoded: dict[str, bytes], envelope: dict[str, Any], source_file: Path) -> bytes:
    try:
        return AESGCM(aes_key).decrypt(decoded["iv"], decoded["ciphertext"] + decoded["tag"], None)
    except InvalidTag as exc:
        raise DecryptStageError(
            "aes_gcm_decrypt",
            "AES-GCM authentication failed",
            envelope=envelope,
            source_file=source_file,
            original_exception=exc,
        )
    except Exception as exc:
        raise DecryptStageError(
            "aes_gcm_decrypt",
            "Could not decrypt ciphertext",
            envelope=envelope,
            source_file=source_file,
            original_exception=exc,
        )


def parse_inner_json(plaintext: bytes, envelope: dict[str, Any], source_file: Path) -> dict[str, Any]:
    try:
        inner = json.loads(plaintext.decode("utf-8"))
    except Exception as exc:
        raise DecryptStageError(
            "parse_inner_json",
            "Decrypted plaintext is not valid inner JSON",
            envelope=envelope,
            source_file=source_file,
            original_exception=exc,
        )
    if not isinstance(inner, dict):
        raise DecryptStageError("parse_inner_json", "Inner JSON must be an object", envelope=envelope, source_file=source_file)
    return inner


def type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, dict):
        return "dict"
    if isinstance(value, list):
        return "list"
    if isinstance(value, str):
        return "str"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    return type(value).__name__


def safe_inner_schema_preview(inner: dict[str, Any]) -> dict[str, Any]:
    preview: dict[str, Any] = {
        "top_level_keys": sorted(str(key) for key in inner.keys()),
        "fields": {},
    }
    fields: dict[str, Any] = preview["fields"]
    for key in sorted(inner.keys(), key=str):
        value = inner[key]
        field_preview: dict[str, Any] = {"type": type_name(value)}
        if isinstance(value, dict):
            field_preview["child_keys"] = sorted(str(child_key) for child_key in value.keys())
        elif isinstance(value, list):
            item_types = sorted({type_name(item) for item in value})
            field_preview["length"] = len(value)
            field_preview["item_types"] = item_types
        fields[str(key)] = field_preview
    return preview


def validate_inner(inner: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_INNER_FIELDS if field not in inner]
    if missing:
        raise ValueError(f"Inner JSON missing fields: {', '.join(missing)}")

    if inner["source"] != "voice_agent":
        raise ValueError(f"Unsupported source: {inner['source']}")

    if not isinstance(inner["normalized_input"], dict):
        raise ValueError("normalized_input must be an object")


def validate_inner_json(
    inner: dict[str, Any],
    envelope: dict[str, Any],
    source_file: Path,
    preview_inner_schema: bool = False,
) -> None:
    try:
        validate_inner(inner)
    except Exception as exc:
        preview = safe_inner_schema_preview(inner) if preview_inner_schema else None
        raise DecryptStageError(
            "validate_inner_json",
            str(exc),
            envelope=envelope,
            source_file=source_file,
            original_exception=exc,
            inner_schema_preview=preview,
        )


def normalize_medications(value: Any) -> Any:
    if value in (None, ""):
        return None
    if isinstance(value, list):
        return value
    return [value]


def normalize_inbound_voice_payload(inner: dict[str, Any]) -> dict[str, Any]:
    request = inner.get("request")
    if not isinstance(request, dict):
        return inner

    normalized = dict(inner)
    patient = request.get("patient") if isinstance(request.get("patient"), dict) else {}
    caller = request.get("caller") if isinstance(request.get("caller"), dict) else {}
    details = request.get("details") if isinstance(request.get("details"), dict) else {}
    voice_agent = normalized.get("voice_agent") if isinstance(normalized.get("voice_agent"), dict) else {}

    if normalized.get("workflow") in (None, "") and request.get("workflow") not in (None, ""):
        normalized["workflow"] = request["workflow"]
    if normalized.get("request_type") in (None, "") and request.get("request_type") not in (None, ""):
        normalized["request_type"] = request["request_type"]
    if normalized.get("raw_transcript") in (None, "") and request.get("raw_transcript") not in (None, ""):
        normalized["raw_transcript"] = request["raw_transcript"]
    source = normalized.get("source")
    if isinstance(voice_agent, dict) and voice_agent:
        if source not in (None, "", "voice_agent") and normalized.get("transport_source") in (None, ""):
            normalized["transport_source"] = source
        normalized["source"] = "voice_agent"
    elif normalized.get("source") in (None, ""):
        normalized["source"] = "voice_agent"

    normalized_input = normalized.get("normalized_input")
    if not isinstance(normalized_input, dict):
        normalized_input = {}
    else:
        normalized_input = dict(normalized_input)

    patient_name = first_present(patient, ["name", "patient_name", "full_name"])
    if normalized_input.get("patient_name") in (None, "") and patient_name not in (None, ""):
        normalized_input["patient_name"] = patient_name

    dob = first_present(patient, ["dob", "date_of_birth"])
    if normalized_input.get("dob") in (None, "") and dob not in (None, ""):
        normalized_input["dob"] = dob

    postcode = first_present(patient, ["postcode"])
    if normalized_input.get("postcode") in (None, "") and postcode not in (None, ""):
        normalized_input["postcode"] = postcode

    nhs_number = first_present(patient, ["nhs_number"])
    if normalized_input.get("nhs_number") in (None, "") and nhs_number not in (None, ""):
        normalized_input["nhs_number"] = nhs_number

    callback = first_present(caller, ["callback_number", "phone", "phone_number", "caller_number"])
    if callback in (None, ""):
        callback = first_present(voice_agent, ["caller_number"])
    if normalized_input.get("callback_number") in (None, "") and callback not in (None, ""):
        normalized_input["callback_number"] = callback

    caller_for = first_present(caller, ["caller_for", "relationship", "calling_for"])
    if normalized_input.get("caller_for") in (None, "") and caller_for not in (None, ""):
        normalized_input["caller_for"] = caller_for

    meds = first_present(details, ["medication", "medications", "medications_requested"])
    if normalized_input.get("medications_requested") in (None, "", []) and meds not in (None, ""):
        normalized_input["medications_requested"] = normalize_medications(meds)

    urgency_note = first_present(details, ["urgency_note", "urgency", "notes"])
    if normalized_input.get("urgency_note") in (None, "") and urgency_note not in (None, ""):
        normalized_input["urgency_note"] = urgency_note

    pharmacy = first_present(details, ["pharmacy"])
    if normalized_input.get("pharmacy") in (None, "") and pharmacy not in (None, ""):
        normalized_input["pharmacy"] = pharmacy

    normalized["normalized_input"] = normalized_input
    return normalized


def normalize_inbound_payload(inner: dict[str, Any], envelope: dict[str, Any], source_file: Path) -> dict[str, Any]:
    try:
        return normalize_inbound_voice_payload(inner)
    except Exception as exc:
        raise DecryptStageError(
            "normalize_inbound_payload",
            "Could not normalize inbound voice payload wrapper",
            envelope=envelope,
            source_file=source_file,
            original_exception=exc,
        )


def ensure_mixed_workflow_compatibility(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = payload.get("normalized_input") or {}

    payload.setdefault("workflow", payload.get("workflow", "unknown"))
    payload.setdefault("request_type", payload.get("request_type", "unknown_request"))

    payload.setdefault("patient_name_raw", normalized.get("patient_name", ""))
    payload.setdefault("dob_raw", normalized.get("dob", ""))
    payload.setdefault("postcode_raw", normalized.get("postcode", ""))
    payload.setdefault("callback_number_raw", normalized.get("callback_number", ""))

    meds = normalized.get("medications_requested", "")
    if isinstance(meds, list):
        meds_text = ", ".join(str(x) for x in meds)
    else:
        meds_text = str(meds or "")

    payload.setdefault("medications_raw", meds_text)
    payload.setdefault("medication_raw", meds_text)
    payload.setdefault("medications_requested_raw", meds_text)
    payload.setdefault("medications_requested", meds)

    payload.setdefault("urgency_note_raw", normalized.get("urgency_note", ""))
    payload.setdefault("urgency_note", normalized.get("urgency_note", ""))

    payload.setdefault("pharmacy_raw", normalized.get("pharmacy", ""))
    payload.setdefault("pharmacy", normalized.get("pharmacy", ""))

    payload.setdefault("caller_for_raw", normalized.get("caller_for", ""))
    payload.setdefault("caller_for", normalized.get("caller_for", ""))

    payload.setdefault("raw_transcript", payload.get("raw_transcript", ""))
    payload.setdefault("transcript_summary", payload.get("transcript_summary", payload.get("call_summary", "")))

    return payload


def compatibility_normalization(inner: dict[str, Any], envelope: dict[str, Any], source_file: Path) -> dict[str, Any]:
    try:
        return ensure_mixed_workflow_compatibility(inner)
    except Exception as exc:
        raise DecryptStageError(
            "compatibility_normalization",
            "Could not apply mixed workflow compatibility normalization",
            envelope=envelope,
            source_file=source_file,
            original_exception=exc,
        )


def load_nonce_store(config: SecurityConfig) -> dict[str, str]:
    if not config.nonce_store_path.exists():
        return {}
    try:
        data = json.loads(config.nonce_store_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items()}


def prune_nonce_store(store: dict[str, str], config: SecurityConfig) -> dict[str, str]:
    cutoff_seconds = config.nonce_retention_hours * 3600
    now = utc_now()
    pruned: dict[str, str] = {}
    for key, value in store.items():
        try:
            seen_at = parse_timestamp(value)
        except Exception:
            continue
        if (now - seen_at).total_seconds() <= cutoff_seconds:
            pruned[key] = value
    return pruned


def nonce_key(envelope: dict[str, Any]) -> str:
    return f"{envelope['sender_id']}:{envelope['nonce']}"


def check_nonce_replay(envelope: dict[str, Any], config: SecurityConfig, source_file: Path) -> None:
    store = prune_nonce_store(load_nonce_store(config), config)
    if nonce_key(envelope) in store:
        raise DecryptStageError(
            "validate_envelope_metadata",
            "replay_detected: sender_id and nonce already seen within retention window",
            envelope=envelope,
            source_file=source_file,
        )


def record_nonce(envelope: dict[str, Any], config: SecurityConfig) -> None:
    store = prune_nonce_store(load_nonce_store(config), config)
    store[nonce_key(envelope)] = now_iso()
    config.nonce_store_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = config.nonce_store_path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(store, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(temp_path, config.nonce_store_path)


def collision_safe_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    timestamp = utc_now().strftime("%Y%m%dT%H%M%SZ")
    for index in range(1, 1000):
        next_candidate = directory / f"{stem}_{timestamp}_{index}{suffix}"
        if not next_candidate.exists():
            return next_candidate
    raise RuntimeError("Could not allocate collision-safe filename")


def write_incoming(inner: dict[str, Any], config: SecurityConfig, envelope: dict[str, Any], source_file: Path, dry_run: bool) -> Path:
    safe_call_id = safe_filename(str(inner["call_id"]))
    incoming_path = config.queue_incoming_path / f"{safe_call_id}.json"
    if dry_run:
        return incoming_path
    try:
        incoming_path.write_text(json.dumps(inner, indent=2, ensure_ascii=False), encoding="utf-8")
        return incoming_path
    except Exception as exc:
        raise DecryptStageError(
            "write_incoming",
            "Could not write decrypted inner JSON to incoming queue",
            envelope=envelope,
            source_file=source_file,
            original_exception=exc,
        )


def move_to_encrypted_processed(path: Path, config: SecurityConfig, envelope: dict[str, Any], dry_run: bool) -> Path:
    processed_path = collision_safe_path(config.encrypted_processed_path, path.name)
    if dry_run:
        return processed_path
    try:
        shutil.move(str(path), str(processed_path))
        return processed_path
    except Exception as exc:
        raise DecryptStageError(
            "move_to_encrypted_processed",
            "Could not move encrypted envelope to processed queue",
            envelope=envelope,
            source_file=path,
            original_exception=exc,
        )


def decrypt_envelope(envelope: dict[str, Any], config: SecurityConfig | None = None) -> dict[str, Any]:
    config = config or load_config()
    source_file = Path("<memory>")
    require_envelope_fields(envelope, source_file)
    validate_envelope_metadata(envelope, config, source_file)
    decoded = validate_base64_fields(envelope, source_file)
    verify_hmac_signature(envelope, decoded, config, source_file)
    private_key = load_private_key(config, envelope, source_file)
    aes_key = rsa_unwrap_aes_key(private_key, decoded["encrypted_key"], envelope, source_file)
    plaintext = aes_gcm_decrypt(aes_key, decoded, envelope, source_file)
    inner = parse_inner_json(plaintext, envelope, source_file)
    inner = normalize_inbound_voice_payload(inner)
    return inner


def process_file(
    path: Path,
    config: SecurityConfig,
    dry_run: bool = False,
    allow_stale_replay: bool = False,
    preview_inner_schema: bool = False,
) -> tuple[dict[str, Any], Path, Path, TimestampValidation, bool]:
    raw = read_file(path, config)
    envelope = parse_envelope(raw, path)
    require_envelope_fields(envelope, path)
    timestamp_validation = validate_envelope_metadata(envelope, config, path, allow_stale_replay=allow_stale_replay)
    decoded = validate_base64_fields(envelope, path)
    verify_hmac_signature(envelope, decoded, config, path)
    nonce_replay_check_bypassed = bool(timestamp_validation.stale_override_used)
    if not nonce_replay_check_bypassed:
        check_nonce_replay(envelope, config, path)
    private_key = load_private_key(config, envelope, path)
    aes_key = rsa_unwrap_aes_key(private_key, decoded["encrypted_key"], envelope, path)
    plaintext = aes_gcm_decrypt(aes_key, decoded, envelope, path)
    inner = parse_inner_json(plaintext, envelope, path)
    inner = normalize_inbound_payload(inner, envelope, path)
    validate_inner_json(inner, envelope, path, preview_inner_schema=preview_inner_schema)
    inner = compatibility_normalization(inner, envelope, path)
    incoming_path = write_incoming(inner, config, envelope, path, dry_run)
    processed_path = move_to_encrypted_processed(path, config, envelope, dry_run)
    if not dry_run:
        try:
            record_nonce(envelope, config)
        except Exception as exc:
            security(
                config,
                {
                    "timestamp_utc": now_iso(),
                    "event": "nonce_record_failed",
                    "message_id": envelope["message_id"],
                    "sender_id": envelope["sender_id"],
                    "key_id": envelope["key_id"],
                    "error_type": type(exc).__name__,
                    "sanitized_reason": sanitize_reason(str(exc)),
                },
            )
        try:
            audit(
                config,
                {
                    "timestamp_utc": now_iso(),
                    "event": "encrypted_envelope_decrypted",
                    "message_id": envelope["message_id"],
                    "sender_id": envelope["sender_id"],
                    "key_id": envelope["key_id"],
                    "call_id": inner.get("call_id", ""),
                    "workflow": inner.get("workflow", ""),
                    "request_type": inner.get("request_type", ""),
                    "transport_source": inner.get("transport_source", ""),
                    "incoming_path": str(incoming_path),
                    "encrypted_processed_path": str(processed_path),
                    "envelope_sha256": sha256_hex(raw),
                    "stale_replay_override": bool(timestamp_validation.stale_override_used),
                    "dry_run": False,
                    "timestamp_age_seconds": timestamp_validation.age_seconds,
                    "timestamp_skew_seconds": config.timestamp_skew_seconds,
                    "nonce_replay_check_bypassed": nonce_replay_check_bypassed,
                },
            )
        except Exception as exc:
            security(
                config,
                {
                    "timestamp_utc": now_iso(),
                    "event": "decrypt_audit_write_failed",
                    "message_id": envelope["message_id"],
                    "sender_id": envelope["sender_id"],
                    "key_id": envelope["key_id"],
                    "error_type": type(exc).__name__,
                    "sanitized_reason": sanitize_reason(str(exc)),
                },
            )
    elif timestamp_validation.stale_override_used:
        audit(
            config,
            {
                "timestamp_utc": now_iso(),
                "event": "encrypted_envelope_decrypted",
                "message_id": envelope["message_id"],
                "sender_id": envelope["sender_id"],
                "key_id": envelope["key_id"],
                "call_id": inner.get("call_id", ""),
                "workflow": inner.get("workflow", ""),
                "request_type": inner.get("request_type", ""),
                "transport_source": inner.get("transport_source", ""),
                "incoming_path": str(incoming_path),
                "encrypted_processed_path": str(processed_path),
                "envelope_sha256": sha256_hex(raw),
                "stale_replay_override": True,
                "dry_run": True,
                "timestamp_age_seconds": timestamp_validation.age_seconds,
                "timestamp_skew_seconds": config.timestamp_skew_seconds,
                "nonce_replay_check_bypassed": nonce_replay_check_bypassed,
            },
        )
    return inner, incoming_path, processed_path, timestamp_validation, nonce_replay_check_bypassed


def is_stale_envelope(envelope: dict[str, Any] | None, config: SecurityConfig) -> bool:
    if not envelope:
        return False
    age = timestamp_age_seconds(envelope)
    return age is not None and age > config.timestamp_skew_seconds


def safe_to_replay(error: DecryptStageError, envelope: dict[str, Any] | None, config: SecurityConfig) -> bool:
    if "replay_detected" in error.sanitized_reason:
        return False
    if "timestamp" in error.sanitized_reason.lower():
        return False
    if is_stale_envelope(envelope, config):
        return False
    return error.stage not in {
        "parse_json",
        "required_envelope_fields",
        "validate_envelope_metadata",
        "validate_base64_fields",
        "verify_hmac_signature",
    }


def security_event(
    error: DecryptStageError,
    *,
    raw: str,
    envelope: dict[str, Any] | None,
    source_file: Path,
    deadletter_path: Path | None,
    config: SecurityConfig,
    stale_replay_override: bool,
) -> dict[str, Any]:
    age = timestamp_age_seconds(envelope) if envelope else None
    event = {
        "timestamp_utc": now_iso(),
        "event": "decrypt_failed",
        "stage": error.stage,
        "source_file": str(source_file),
        "deadletter_path": str(deadletter_path) if deadletter_path else "",
        "message_id": error.message_id or safe_metadata(envelope, "message_id"),
        "sender_id": error.sender_id or safe_metadata(envelope, "sender_id"),
        "key_id": error.key_id or safe_metadata(envelope, "key_id"),
        "alg": error.alg or safe_metadata(envelope, "alg"),
        "signature_alg": error.signature_alg or safe_metadata(envelope, "signature_alg"),
        "error_type": error.original_exception_type or error.__class__.__name__,
        "sanitized_reason": error.sanitized_reason,
        "safe_to_replay": safe_to_replay(error, envelope, config),
        "stale_replay_override": bool(stale_replay_override),
        "timestamp_age_seconds": age,
        "timestamp_skew_seconds": config.timestamp_skew_seconds,
        "envelope_sha256": sha256_hex(raw) if raw else "",
        "encrypted_key_sha256_prefix": optional_field_hash_prefix(envelope, "encrypted_key"),
        "ciphertext_sha256_prefix": optional_field_hash_prefix(envelope, "ciphertext"),
        "signature_sha256_prefix": optional_field_hash_prefix(envelope, "signature"),
    }
    if error.inner_schema_preview is not None:
        event["inner_schema_preview"] = error.inner_schema_preview
    return event


def move_to_deadletter(path: Path, config: SecurityConfig, dry_run: bool) -> Path | None:
    failed_path = collision_safe_path(config.deadletter_path, f"decrypt_failed_{path.name}")
    if dry_run:
        return None
    try:
        shutil.move(str(path), str(failed_path))
        return failed_path
    except Exception as exc:
        security(
            config,
            {
                "timestamp_utc": now_iso(),
                "event": "decrypt_deadletter_move_failed",
                "source_file": str(path),
                "intended_deadletter_path": str(failed_path),
                "error_type": type(exc).__name__,
                "sanitized_reason": sanitize_reason(str(exc)),
            },
        )
        return None


def handle_failure(
    path: Path,
    config: SecurityConfig,
    error: DecryptStageError,
    *,
    raw: str,
    envelope: dict[str, Any] | None,
    dry_run: bool,
    stale_replay_override: bool,
) -> None:
    failed_path = move_to_deadletter(path, config, dry_run)
    security(
        config,
        security_event(
            error,
            raw=raw,
            envelope=envelope,
            source_file=path,
            deadletter_path=failed_path,
            config=config,
            stale_replay_override=stale_replay_override,
        ),
    )
    print(f"FAILED: {path.name}")
    print(f"Stage: {error.stage}")
    print(f"Reason: {error.sanitized_reason}")
    if error.inner_schema_preview is not None:
        print("Safe inner schema preview:")
        print(json.dumps(error.inner_schema_preview, indent=2, sort_keys=True))
    if failed_path:
        print(f"Moved to: {failed_path}")
    elif dry_run:
        print("Dry run: original file was not moved.")
    else:
        print("Original file was not moved; see security log.")


def process_with_failure_handling(
    path: Path,
    config: SecurityConfig,
    dry_run: bool,
    allow_stale_replay: bool = False,
    preview_inner_schema: bool = False,
) -> bool:
    raw = ""
    envelope: dict[str, Any] | None = None
    try:
        raw = read_file(path, config)
        envelope = parse_envelope(raw, path)
        inner, incoming_path, processed_path, timestamp_validation, nonce_replay_check_bypassed = process_file(
            path,
            config,
            dry_run=dry_run,
            allow_stale_replay=allow_stale_replay,
            preview_inner_schema=preview_inner_schema,
        )
        mode = "DRY RUN decrypted" if dry_run else "Decrypted"
        print(f"{mode}: {path.name}")
        print(f"Incoming: {incoming_path}")
        print(f"Encrypted processed: {processed_path}")
        print(f"Call ID: {inner.get('call_id', '')}")
        if timestamp_validation.stale_override_used:
            print("Stale replay override: true")
            if nonce_replay_check_bypassed:
                print("Nonce replay check bypassed for stale replay diagnostic.")
        return True
    except DecryptStageError as error:
        handle_failure(
            path,
            config,
            error,
            raw=raw,
            envelope=envelope,
            dry_run=dry_run,
            stale_replay_override=allow_stale_replay,
        )
        return False
    except Exception as exc:
        error = DecryptStageError(
            "read_file" if not raw else "validate_envelope_metadata",
            "Unexpected decrypt pipeline failure",
            envelope=envelope,
            source_file=path,
            original_exception=exc,
        )
        handle_failure(
            path,
            config,
            error,
            raw=raw,
            envelope=envelope,
            dry_run=dry_run,
            stale_replay_override=allow_stale_replay,
        )
        return False


def select_files(config: SecurityConfig, file_path: str | None) -> list[Path]:
    if file_path:
        return [Path(file_path)]
    return sorted(config.queue_encrypted_raw_path.glob("*.json"))


def is_allowed_stale_replay_target(path: Path) -> bool:
    name_ok = path.name.lower().startswith("replay_")
    parts_ok = any(part.lower() == "deadletter" for part in path.parts)
    return name_ok or parts_ok


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Decrypt JEIE-1 encrypted_raw envelopes into JeffLocal incoming queue.")
    parser.add_argument("--file", help="Process one encrypted envelope JSON file.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and decrypt without writing incoming or moving files.")
    parser.add_argument(
        "--allow-stale-replay",
        action="store_true",
        help="Allow stale timestamp only for intentional single-file replay/deadletter diagnostics.",
    )
    parser.add_argument(
        "--preview-inner-schema",
        action="store_true",
        help="Dry-run diagnostic: print/log safe decrypted inner JSON keys and value types on inner validation failure.",
    )
    parser.add_argument("--config", default=str(CONFIG_PATH), help="Security config path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = load_config(Path(args.config))
        ensure_directories(config)
    except DecryptStageError as exc:
        print(f"FAILED: config")
        print(f"Stage: {exc.stage}")
        print(f"Reason: {exc.sanitized_reason}")
        return 1

    if args.allow_stale_replay:
        if not args.file:
            print("ERROR: --allow-stale-replay requires --file.", file=os.sys.stderr)
            return 2
        target = Path(args.file)
        if not is_allowed_stale_replay_target(target):
            print("ERROR: --allow-stale-replay only accepts replay_* files or paths containing deadletter.", file=os.sys.stderr)
            return 2
    if args.preview_inner_schema and not args.dry_run:
        print("ERROR: --preview-inner-schema requires --dry-run.", file=os.sys.stderr)
        return 2

    files = select_files(config, args.file)
    if not files:
        print("No encrypted_raw files found.")
        return 0

    successes = 0
    failures = 0
    for path in files:
        if process_with_failure_handling(
            path,
            config,
            dry_run=args.dry_run,
            allow_stale_replay=args.allow_stale_replay,
            preview_inner_schema=args.preview_inner_schema,
        ):
            successes += 1
        else:
            failures += 1

    print(
        json.dumps(
            {
                "processed": len(files),
                "decrypted": successes,
                "failed": failures,
                "dry_run": bool(args.dry_run),
                "allow_stale_replay": bool(args.allow_stale_replay),
            }
        )
    )
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

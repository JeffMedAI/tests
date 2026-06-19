import base64
import json
import hmac
import hashlib
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

base = Path(r"C:\JeffLocal")
keys_dir = base / "config" / "security" / "keys"
out_dir = base / "queue" / "encrypted_raw"
out_dir.mkdir(parents=True, exist_ok=True)

PROTOCOL = "JEIE-1"
ALG = "RSA-OAEP-256+A256GCM"
KEY_ID = "jefflocal-rsa-test-001"
SENDER_ID = "voice-agent-test"

public_key_path = keys_dir / "jefflocal_public.pem"
hmac_secret_path = keys_dir / "voice_agent_hmac_secret.txt"

public_key = serialization.load_pem_public_key(public_key_path.read_bytes())
hmac_secret = hmac_secret_path.read_text(encoding="utf-8").strip().encode("utf-8")

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
timestamp_utc = datetime.now(timezone.utc).isoformat()
message_id = f"FRESH-N8N-E2E-{stamp}"
call_id = f"FRESH-RX-{stamp}"

inner = {
    "call_id": call_id,
    "call_timestamp": timestamp_utc,
    "environment": "local_test",
    "event_type": "voice_intake",
    "payload_status": "fresh_test",
    "source": "n8n_e2e_batch",
    "voice_agent": {
        "provider": "local_test_sender",
        "call_direction": "inbound",
        "caller_number": "07123456789"
    },
    "request": {
        "workflow": "prescription",
        "request_type": "repeat_prescription",
        "patient": {
            "patient_name": "Test Patient",
            "dob": "1971-05-02",
            "postcode": "AB12 3CD"
        },
        "caller": {
            "callback_number": "07123456789",
            "caller_for": "self"
        },
        "details": {
            "medications_requested": ["test medication"],
            "urgency_note": "routine",
            "pharmacy": "usual pharmacy"
        },
        "raw_transcript": "Test caller requests a routine repeat prescription. This is a synthetic local test transcript."
    }
}

plaintext = json.dumps(inner, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

aes_key = AESGCM.generate_key(bit_length=256)
iv = os.urandom(12)
aesgcm = AESGCM(aes_key)
ciphertext_with_tag = aesgcm.encrypt(iv, plaintext, None)
ciphertext = ciphertext_with_tag[:-16]
tag = ciphertext_with_tag[-16:]

encrypted_key = public_key.encrypt(
    aes_key,
    padding.OAEP(
        mgf=padding.MGF1(algorithm=hashes.SHA256()),
        algorithm=hashes.SHA256(),
        label=None
    )
)

def b64(data):
    return base64.b64encode(data).decode("ascii")

envelope = {
    "protocol": PROTOCOL,
    "alg": ALG,
    "key_id": KEY_ID,
    "sender_id": SENDER_ID,
    "message_id": message_id,
    "timestamp_utc": timestamp_utc,
    "nonce": str(uuid.uuid4()),
    "encrypted_key": b64(encrypted_key),
    "iv": b64(iv),
    "ciphertext": b64(ciphertext),
    "tag": b64(tag),
    "signature_alg": "HMAC-SHA256"
}

canonical = ".".join([
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
])

signature = hmac.new(
    hmac_secret,
    canonical.encode("utf-8"),
    hashlib.sha256
).digest()

envelope["signature"] = b64(signature)

out_path = out_dir / f"{message_id}.json"
out_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")

print(f"Wrote fresh encrypted test:")
print(out_path)
print(f"call_id={call_id}")
print(f"message_id={message_id}")

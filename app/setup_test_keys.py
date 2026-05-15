from pathlib import Path
import secrets
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

base = Path(r"C:\JeffLocal\config\security\keys")
base.mkdir(parents=True, exist_ok=True)

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

public_key = private_key.public_key()

(base / "jefflocal_private.pem").write_bytes(
    private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
)

(base / "jefflocal_public.pem").write_bytes(
    public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
)

(base / "voice_agent_hmac_secret.txt").write_text(
    secrets.token_urlsafe(48),
    encoding="utf-8"
)

print("Test keys created.")
print("Give this public key to the fake voice agent:")
print((base / "jefflocal_public.pem").read_text())
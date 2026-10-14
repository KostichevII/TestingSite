import base64
import json
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Та же фраза, что и в JS-шифровании. В проде — из переменной окружения.
PASSPHRASE = os.environ.get(
    "QUIZ_PASSPHRASE", "TestIt::v1::change-me-please"
).encode()
ITERATIONS = 100_000


def derive_key(salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    return kdf.derive(PASSPHRASE)


def decrypt_value(payload: dict, key: bytes):
    """payload = {'iv': base64, 'ct': base64} -> исходный JSON-объект."""
    iv = base64.b64decode(payload["iv"])
    ct = base64.b64decode(payload["ct"])
    plaintext = AESGCM(key).decrypt(iv, ct, None)
    return json.loads(plaintext)
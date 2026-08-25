import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-insecure-secret-change-me")
TOKEN_TTL_SECONDS = 60 * 60 * 12
PBKDF2_ITERATIONS = 200_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, digest_hex = stored.split("$")
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    expected = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return hmac.compare_digest(expected.hex(), digest_hex)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def create_token(email: str) -> str:
    payload_b64 = _b64url_encode(json.dumps({"email": email, "exp": int(time.time()) + TOKEN_TTL_SECONDS}).encode())
    sig_b64 = _b64url_encode(hmac.new(SESSION_SECRET.encode(), payload_b64.encode(), hashlib.sha256).digest())
    return f"{payload_b64}.{sig_b64}"


def verify_token(token: str) -> Optional[str]:
    try:
        payload_b64, sig_b64 = token.split(".")
    except ValueError:
        return None
    expected_sig = _b64url_encode(hmac.new(SESSION_SECRET.encode(), payload_b64.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(expected_sig, sig_b64):
        return None
    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except (ValueError, UnicodeDecodeError):
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload.get("email")

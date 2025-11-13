# electronic_records/encryption.py
"""
PHI Encryption Utility
----------------------
Encrypts and decrypts Protected Health Information (PHI) using Fernet
(symmetric AES encryption). Uses an environment variable key for security.
"""

import os
from cryptography.fernet import Fernet, InvalidToken

ENV_KEY = "HCRM_ENCRYPTION_KEY"


def get_key() -> bytes:
    """Fetch or generate a valid Fernet encryption key."""
    key = os.getenv(ENV_KEY)
    if key:
        if isinstance(key, str):
            key_bytes = key.encode()
        else:
            key_bytes = key
        # Validate that it's a proper Fernet key
        try:
            Fernet(key_bytes)
            return key_bytes
        except Exception:
            raise ValueError(
                f"Invalid {ENV_KEY} format. Must be a 32-byte base64-encoded string."
            )
    # Generate a temporary key if not set
    temp = Fernet.generate_key()
    os.environ[ENV_KEY] = temp.decode()
    # Warn without exposing the actual key
    print("⚠️  No encryption key found — generated a temporary one for dev use.")
    return temp


_KEY = get_key()
_FERNET = Fernet(_KEY)


def encrypt(plaintext: str) -> str:
    """Encrypt plaintext and return token."""
    if plaintext is None:
        raise ValueError("plaintext cannot be None")
    if plaintext == "":
        return ""
    if isinstance(plaintext, str):
        plaintext = plaintext.encode("utf-8")
    token = _FERNET.encrypt(plaintext)
    return token.decode("utf-8")


def decrypt(token: str) -> str:
    """Decrypt token and return plaintext."""
    if token is None:
        raise ValueError("token cannot be None")
    if token == "":
        return ""
    if isinstance(token, str):
        token = token.encode("utf-8")
    try:
        plain = _FERNET.decrypt(token)
    except InvalidToken as e:
        raise ValueError("Invalid token or key") from e
    return plain.decode("utf-8")


def _self_test():
    """Quick round-trip test for development."""
    sample = "hello world"
    token = encrypt(sample)
    assert decrypt(token) == sample
    print("Encryption self-test passed.")
# electronic_records/encryption.py
"""
PHI Encryption Utility
----------------------
Encrypts and decrypts Protected Health Information (PHI) using Fernet
(symmetric AES encryption). Uses an environment variable key for security.

This version preserves the same public functions as before but:
- Fails fast if the key is missing/invalid (no temporary key generation)
- Uses one validated Fernet instance for all operations
- Reads key from django settings.HCRM_ENCRYPTION_KEY first (if settings available),
  falling back to the environment variable HCRM_ENCRYPTION_KEY
"""

import os
from cryptography.fernet import Fernet, InvalidToken

# keep same env var name you used before
ENV_KEY = "HCRM_ENCRYPTION_KEY"


def _read_key_from_settings_or_env():
    """
    Prefer settings.HCRM_ENCRYPTION_KEY (if Django settings are imported elsewhere),
    otherwise fall back to environment variable. Always return bytes.
    """
    # try to import settings lazily so module can be imported in non-Django contexts (tests)
    try:
        from django.conf import settings  # local import
        maybe = getattr(settings, "HCRM_ENCRYPTION_KEY", None)
    except Exception:
        maybe = None

    if not maybe:
        maybe = os.getenv(ENV_KEY, "")

    if not maybe:
        # Fail fast: do not auto-generate a temporary key
        raise RuntimeError(
            f"Missing {ENV_KEY}. Set it in environment or settings.HCRM_ENCRYPTION_KEY. "
            "Generate a key with: from cryptography.fernet import Fernet; Fernet.generate_key().decode()"
        )

    # ensure bytes
    if isinstance(maybe, str):
        maybe = maybe.strip().encode()
    return maybe


def get_key() -> bytes:
    """
    Fetch the active Fernet key as bytes.
    This keeps the previous public function name but no longer generates a temporary key.
    """
    key_bytes = _read_key_from_settings_or_env()
    # validate
    try:
        Fernet(key_bytes)
    except Exception:
        raise ValueError(f"Invalid {ENV_KEY} format. Must be a 32-byte url-safe base64-encoded string.")
    return key_bytes


# create a single Fernet instance for the module (validated at import time)
_KEY = get_key()
_FERNET = Fernet(_KEY)


def encrypt(plaintext: str) -> str:
    """Encrypt plaintext string and return token (string)."""
    if plaintext is None:
        raise ValueError("plaintext cannot be None")
    if plaintext == "":
        return ""
    if isinstance(plaintext, str):
        plaintext = plaintext.encode("utf-8")
    token = _FERNET.encrypt(plaintext)
    return token.decode("utf-8")


def decrypt(token: str) -> str:
    """Decrypt token string and return plaintext string."""
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


def encrypt_file(file_data: bytes) -> bytes:
    """Encrypt file bytes and return encrypted bytes."""
    if file_data is None:
        raise ValueError("file_data cannot be None")
    if not isinstance(file_data, (bytes, bytearray)):
        raise ValueError("file_data must be bytes")
    return _FERNET.encrypt(bytes(file_data))


def decrypt_file(encrypted_data: bytes) -> bytes:
    """Decrypt file bytes and return original bytes."""
    if encrypted_data is None:
        raise ValueError("encrypted_data cannot be None")
    if not isinstance(encrypted_data, (bytes, bytearray)):
        raise ValueError("encrypted_data must be bytes")
    try:
        return _FERNET.decrypt(bytes(encrypted_data))
    except InvalidToken as e:
        raise ValueError("Invalid encrypted data or wrong key") from e

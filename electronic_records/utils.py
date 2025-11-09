# electronic_records/utils.py
from cryptography.fernet import Fernet
from django.conf import settings

def _get_fernet():
    key = getattr(settings, "MY_FERNET_KEY", None)
    if not key:
        raise RuntimeError("Fernet key not configured in settings.MY_FERNET_KEY")
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)

def decrypt_field(value):
    """
    Decrypts a Fernet-encrypted value (stored as bytes or str).
    Returns plaintext string on success, otherwise returns original value.
    """
    if value is None:
        return None
    try:
        f = _get_fernet()
        if isinstance(value, str):
            value = value.encode()
        return f.decrypt(value).decode("utf-8")
    except Exception:
        # fallback: try to decode bytes -> str or return raw value
        try:
            if isinstance(value, (bytes, bytearray)):
                return value.decode("utf-8", errors="ignore")
        except Exception:
            pass
        return value

def encrypt_field(plaintext):
    """
    Encrypt plaintext string (or bytes) to Fernet bytes.
    Returns bytes. Caller can store as bytes or decode to str as needed.
    """
    if plaintext is None:
        return None
    f = _get_fernet()
    if isinstance(plaintext, str):
        plaintext = plaintext.encode("utf-8")
    return f.encrypt(plaintext)

import os
from django.core.exceptions import ImproperlyConfigured
from cryptography.fernet import Fernet

# Accept either HCRM_ENCRYPTION_KEY (preferred) or MY_FERNET_KEY for backward compatibility
_key = os.getenv("HCRM_ENCRYPTION_KEY", "").strip() or os.getenv("MY_FERNET_KEY", "").strip()

if not _key:
    raise ImproperlyConfigured(
        "Missing HCRM_ENCRYPTION_KEY or MY_FERNET_KEY environment variable. "
        "Generate one with: from cryptography.fernet import Fernet; Fernet.generate_key().decode() "
        "and add it to your .env for local development."
    )

try:
    Fernet(_key)
except Exception as exc:
    raise ImproperlyConfigured(
        "Provided Fernet key (HCRM_ENCRYPTION_KEY or MY_FERNET_KEY) is not valid. "
        "It must be a 32-byte url-safe base64-encoded string."
    ) from exc

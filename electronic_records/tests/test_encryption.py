import os
import pytest
from django.test import SimpleTestCase
from electronic_records.utils import encrypt_field, decrypt_field


# -------------------------
#  Unit / functional tests
# -------------------------

def test_encrypt_decrypt_roundtrip():
    """Ensure encrypt_field + decrypt_field work for normal text."""
    original = "This is sensitive PHI: patient 123, allergy penicillin."
    token = encrypt_field(original)
    assert token != original, "Encrypted text should differ from original"
    result = decrypt_field(token)
    assert result == original, "Decrypted text should match original"


def test_encrypt_empty_string():
    """Empty string should return empty string (no encryption)."""
    assert encrypt_field("") == ""
    assert decrypt_field("") == ""


def test_encrypt_raises_on_none():
    """Passing None should raise ValueError (invalid input)."""
    with pytest.raises(ValueError):
        encrypt_field(None)
    with pytest.raises(ValueError):
        decrypt_field(None)


def test_ciphertext_randomness():
    """Each encryption of the same text should produce different ciphertexts."""
    text = "same input"
    c1 = encrypt_field(text)
    c2 = encrypt_field(text)
    assert c1 != c2, "Encryptions should be non-deterministic"
    assert decrypt_field(c1) == text
    assert decrypt_field(c2) == text


# -------------------------
#  Django compatibility test
# -------------------------

class EncryptionUtilsTests(SimpleTestCase):
    """Django test discovery compatibility + basic key sanity check."""

    def test_environment_key_present(self):
        """Ensure encryption key is present or warn if missing."""
        key = os.environ.get("HCRM_ENCRYPTION_KEY") or os.environ.get("MY_FERNET_KEY")
        self.assertIsNotNone(key, "MY_FERNET_KEY must be set for encryption")

    def test_encrypt_and_decrypt_consistency(self):
        """Check basic consistency using Django's SimpleTestCase."""
        plain = "Backend Django test encryption"
        token = encrypt_field(plain)
        self.assertNotEqual(token, plain)
        decrypted = decrypt_field(token)
        self.assertEqual(decrypted, plain)

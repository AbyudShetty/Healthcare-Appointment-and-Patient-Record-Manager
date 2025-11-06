# electronic_records/tests/test_encryption.py
import pytest
from electronic_records import encryption

def test_encrypt_decrypt_roundtrip():
    original = "This is sensitive PHI: patient 123, allergy penicillin."
    token = encryption.encrypt(original)
    assert token != original
    result = encryption.decrypt(token)
    assert result == original

def test_encrypt_empty_string():
    assert encryption.encrypt("") == ""
    assert encryption.decrypt("") == ""

def test_encrypt_raises_on_none():
    with pytest.raises(ValueError):
        encryption.encrypt(None)
    with pytest.raises(ValueError):
        encryption.decrypt(None)

def test_ciphertext_randomness():
    text = "same input"
    c1 = encryption.encrypt(text)
    c2 = encryption.encrypt(text)
    assert c1 != c2
    assert encryption.decrypt(c1) == text
    assert encryption.decrypt(c2) == text

import base64

import pytest
from cryptography.exceptions import InvalidTag

from jalada.adapters.security.evidence_cipher import EvidenceCipher

KEY = b"k" * 32


def test_encrypted_bytes_decrypt_back_to_the_original() -> None:
    cipher = EvidenceCipher(KEY)

    sealed = cipher.encrypt(b"receipt bytes", b"evidence/u/1")

    assert b"receipt bytes" not in sealed
    assert cipher.decrypt(sealed, b"evidence/u/1") == b"receipt bytes"


def test_the_same_bytes_encrypt_differently_each_time() -> None:
    cipher = EvidenceCipher(KEY)

    assert cipher.encrypt(b"same", b"x") != cipher.encrypt(b"same", b"x")


def test_ciphertext_moved_to_another_object_will_not_decrypt() -> None:
    cipher = EvidenceCipher(KEY)
    sealed = cipher.encrypt(b"receipt", b"evidence/u/1")

    with pytest.raises(InvalidTag):
        cipher.decrypt(sealed, b"evidence/u/2")


def test_tampered_ciphertext_will_not_decrypt() -> None:
    cipher = EvidenceCipher(KEY)
    sealed = bytearray(cipher.encrypt(b"receipt", b"x"))
    sealed[-1] ^= 1

    with pytest.raises(InvalidTag):
        cipher.decrypt(bytes(sealed), b"x")


def test_another_key_cannot_decrypt() -> None:
    sealed = EvidenceCipher(KEY).encrypt(b"receipt", b"x")

    with pytest.raises(InvalidTag):
        EvidenceCipher(b"o" * 32).decrypt(sealed, b"x")


def test_keys_must_be_32_bytes_and_get_a_stable_id() -> None:
    with pytest.raises(ValueError):
        EvidenceCipher(b"short")
    encoded = base64.b64encode(KEY).decode()

    assert EvidenceCipher.from_base64(encoded).key_id == EvidenceCipher(KEY).key_id
    assert len(EvidenceCipher(KEY).key_id) == 12

import base64
import hashlib
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_BYTES = 12


class EvidenceCipher:
    """AES-256-GCM. Each object gets a fresh random nonce, stored in front of the ciphertext."""

    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("The evidence key must be 32 bytes")
        self._aead = AESGCM(key)
        # Saved with each object, so objects can be read after the key is rotated.
        self.key_id = hashlib.sha256(key).hexdigest()[:12]

    @classmethod
    def from_base64(cls, encoded: str) -> "EvidenceCipher":
        return cls(base64.b64decode(encoded, validate=True))

    def encrypt(self, plaintext: bytes, bound_to: bytes) -> bytes:
        """`bound_to` must match on decrypt, so ciphertext cannot be swapped between objects."""
        nonce = os.urandom(NONCE_BYTES)
        return nonce + self._aead.encrypt(nonce, plaintext, bound_to)

    def decrypt(self, sealed: bytes, bound_to: bytes) -> bytes:
        return self._aead.decrypt(sealed[:NONCE_BYTES], sealed[NONCE_BYTES:], bound_to)

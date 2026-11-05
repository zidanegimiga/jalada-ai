import hashlib
import secrets

# No 0, O, 1, I or L: easy to read off a screen and type.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8
CODE_MINUTES = 10


def new_link_code() -> str:
    """A one-time code that ties a Telegram account to a Jalada AI account."""
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def hash_link_code(code: str) -> str:
    """Codes are stored hashed, like session tokens."""
    return hashlib.sha256(code.strip().upper().encode()).hexdigest()

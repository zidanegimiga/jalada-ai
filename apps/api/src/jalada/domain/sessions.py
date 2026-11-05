import hashlib
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Session:
    token_hash: str
    user_id: UUID
    expires_at: datetime


def hash_session_token(token: str) -> str:
    """Only this hash is stored, so a copy of the database cannot be used to sign in."""
    return hashlib.sha256(token.encode()).hexdigest()

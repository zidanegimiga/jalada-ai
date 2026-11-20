import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID


@dataclass(frozen=True)
class Session:
    token_hash: str
    user_id: UUID
    expires_at: datetime


def hash_session_token(token: str) -> str:
    """Only this hash is stored, so a copy of the database cannot be used to sign in."""
    return hashlib.sha256(token.encode()).hexdigest()


def new_session(user_id: UUID, now: datetime, lifetime: timedelta) -> tuple[str, Session]:
    """A fresh session: the token for the person, and what is stored, its hash."""
    token = secrets.token_urlsafe(32)
    return token, Session(hash_session_token(token), user_id, now + lifetime)

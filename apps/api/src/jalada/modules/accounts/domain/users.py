from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

MIN_PASSWORD_LENGTH = 10
MAX_PASSWORD_LENGTH = 128


@dataclass(frozen=True)
class User:
    id: UUID
    email: str
    display_name: str
    created_at: datetime


def normalize_email(raw: str) -> str:
    """Emails are compared case-insensitively, so they are stored in one form."""
    return raw.strip().lower()


def is_acceptable_password(password: str) -> bool:
    """Length is the rule that matters most. Very long inputs are refused to keep hashing cheap."""
    return MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH

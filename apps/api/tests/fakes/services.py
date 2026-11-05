"""Fakes for the clock, hashing, Google, storage, text reading and the language model."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from jalada.application.errors import GoogleSignInFailed
from jalada.application.ports import (
    GoogleProfile,
)
from jalada.pipeline.model import ImageInput, ModelReply, ModelUsage


class FakeHasher:
    def __init__(self) -> None:
        self.verified: list[str] = []

    def hash(self, password: str) -> str:
        return f"hashed:{password}"

    def verify(self, password_hash: str, password: str) -> bool:
        self.verified.append(password_hash)
        return password_hash == f"hashed:{password}"


class FixedClock:
    def __init__(self, now: datetime = datetime(2026, 11, 5, 9, 0, tzinfo=UTC)) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current


class FakeGoogle:
    """Returns a preset profile for the code "good-code" and fails for anything else."""

    def __init__(self) -> None:
        self.profile = GoogleProfile("google-123", "jane@example.com", True, "Jane Doe")
        self.exchanged: list[tuple[str, str, str]] = []

    def authorization_url(self, state: str, nonce: str, code_verifier: str) -> str:
        return f"https://accounts.example.com/auth?state={state}"

    def exchange(self, code: str, nonce: str, code_verifier: str) -> GoogleProfile:
        self.exchanged.append((code, nonce, code_verifier))
        if code != "good-code":
            raise GoogleSignInFailed
        return self.profile


class FakeEvidenceStore:
    """Keeps evidence in memory, keyed by user and id."""

    key_id = "test-key"

    def __init__(self) -> None:
        self.objects: dict[tuple[UUID, UUID], bytes] = {}

    def put(self, evidence_id: UUID, user_id: UUID, data: bytes) -> None:
        self.objects[(user_id, evidence_id)] = data

    def get(self, evidence_id: UUID, user_id: UUID, key_id: str) -> bytes:
        return self.objects[(user_id, evidence_id)]

    def delete(self, evidence_id: UUID, user_id: UUID) -> None:
        self.objects.pop((user_id, evidence_id), None)


class FakeTextReader:
    """Plain text is decoded. Anything else reads as the text given for it, or nothing."""

    def __init__(self, pdf_text: str | None = None) -> None:
        self.pdf_text = pdf_text

    def read(self, content_type: str, data: bytes) -> str | None:
        if content_type.startswith("text/"):
            return data.decode()
        return self.pdf_text if content_type == "application/pdf" else None


def later(clock: FixedClock, minutes: int) -> datetime:
    return clock.now() + timedelta(minutes=minutes)


class ScriptedModel:
    """Answers with prepared replies, in order, and remembers what it was asked."""

    name = "scripted"

    def __init__(self, *replies: dict[str, Any] | Exception, tokens: int = 100) -> None:
        self._replies = list(replies)
        self._tokens = tokens
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        instructions: str,
        content: str,
        schema: dict[str, Any],
        image: ImageInput | None = None,
    ) -> ModelReply:
        self.calls.append({"content": content, "schema": schema, "image": image})
        reply = self._replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        usage = ModelUsage(self._tokens, self._tokens // 2, Decimal("0.001"))
        return ModelReply(reply, usage)


class FakeChat:
    """Records what the bot would send, and serves files from a dict."""

    def __init__(self, files: dict[str, bytes] | None = None) -> None:
        self.sent: list[tuple[int, str]] = []
        self.files = files or {}

    def send(self, chat_id: int, text: str) -> None:
        self.sent.append((chat_id, text))

    def download(self, file_id: str, max_bytes: int) -> bytes | None:
        data = self.files[file_id]
        return data if len(data) <= max_bytes else None

import hashlib
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

MAX_FILE_BYTES = 10 * 1024 * 1024
MAX_TEXT_CHARACTERS = 5000
TEXT_CONTENT_TYPE = "text/plain; charset=utf-8"

# File signatures: the first bytes that identify each accepted type.
SIGNATURES: list[tuple[bytes, int, str]] = [
    (b"\xff\xd8\xff", 0, "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", 0, "image/png"),
    (b"WEBP", 8, "image/webp"),
    (b"%PDF-", 0, "application/pdf"),
]


class EvidenceSource(StrEnum):
    WEB_UPLOAD = "web_upload"
    WEB_PASTE = "web_paste"
    TELEGRAM = "telegram"


class EvidenceKind(StrEnum):
    UNKNOWN = "unknown"
    MPESA_MESSAGE = "mpesa_message"
    STATEMENT = "statement"
    RECEIPT = "receipt"
    WITHHOLDING_CERTIFICATE = "withholding_certificate"
    PAYSLIP = "payslip"
    FREE_TEXT = "free_text"


class EvidenceStatus(StrEnum):
    RECEIVED = "received"
    PROCESSING = "processing"
    PROPOSED = "proposed"
    NEEDS_REVIEW = "needs_review"
    CONFIRMED = "confirmed"
    DUPLICATE = "duplicate"
    FAILED = "failed"


@dataclass(frozen=True)
class Evidence:
    id: UUID
    user_id: UUID
    source: EvidenceSource
    kind: EvidenceKind
    status: EvidenceStatus
    content_type: str
    size_bytes: int
    sha256: str
    encryption_key_id: str
    received_at: datetime


def detect_file_type(data: bytes) -> str | None:
    """The content type from the file's own bytes. Names and declared types are never trusted."""
    for signature, offset, content_type in SIGNATURES:
        if data[offset: offset + len(signature)] == signature:
            if content_type == "image/webp" and not data.startswith(b"RIFF"):
                continue
            return content_type
    return None


def fingerprint(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

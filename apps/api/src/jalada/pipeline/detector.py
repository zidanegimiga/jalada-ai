import re

from jalada.domain.evidence import EvidenceKind

MPESA_CONFIRMATION = re.compile(r"^\s*[A-Z0-9]{10}\s+Confirmed\b")
MPESA_CODE = re.compile(r"\b[A-Z0-9]{10}\b")


def detect(text: str | None, content_type: str) -> EvidenceKind:
    """What kind of evidence this is, from its text. Rules only; unknown when unsure."""
    if not text or not text.strip():
        return EvidenceKind.UNKNOWN
    lowered = text.lower()
    if MPESA_CONFIRMATION.match(text):
        return EvidenceKind.MPESA_MESSAGE
    if "withholding certificate" in lowered and "certificate serial number" in lowered:
        return EvidenceKind.WITHHOLDING_CERTIFICATE
    if "m-pesa statement" in lowered or "mpesa statement" in lowered:
        return EvidenceKind.STATEMENT
    if "payslip" in lowered or "pay slip" in lowered or "net pay" in lowered:
        return EvidenceKind.PAYSLIP
    if content_type.startswith("text/"):
        return EvidenceKind.FREE_TEXT
    if content_type.startswith("image/"):
        return EvidenceKind.RECEIPT
    return EvidenceKind.UNKNOWN

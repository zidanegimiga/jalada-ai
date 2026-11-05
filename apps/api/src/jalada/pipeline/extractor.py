from jalada.domain.evidence import EvidenceKind
from jalada.domain.extraction import Extraction
from jalada.pipeline.certificates import parse_certificate
from jalada.pipeline.mpesa import parse_mpesa


def extract_with_rules(kind: EvidenceKind, text: str | None) -> Extraction | None:
    """Fixed formats are parsed with rules. Anything else returns None for the model to try."""
    if not text:
        return None
    if kind == EvidenceKind.MPESA_MESSAGE:
        return parse_mpesa(text)
    if kind == EvidenceKind.WITHHOLDING_CERTIFICATE:
        return parse_certificate(text)
    return None

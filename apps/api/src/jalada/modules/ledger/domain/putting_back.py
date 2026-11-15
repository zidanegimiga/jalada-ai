"""Taking back "Not a transaction": the record goes back to the status it had before it was
rejected, as the audit trail kept it."""

from collections.abc import Sequence

from jalada.modules.evidence.domain.evidence import EvidenceStatus
from jalada.modules.ledger.domain.audit import AuditAction, AuditEvent

# What the evidence shows once its record is back, by the record's status.
EVIDENCE_STATUS = {
    "candidate": EvidenceStatus.CANDIDATE,
    "proposed": EvidenceStatus.PROPOSED,
    "needs_review": EvidenceStatus.NEEDS_REVIEW,
}
# For a record whose earlier status is not known, and for evidence with no record.
WAITING = "needs_review"


def status_before_rejection(events: Sequence[AuditEvent]) -> str:
    """The status the record had before its latest rejection. Anything that cannot be put
    back as it was, such as a missing event, comes back as waiting for a look."""
    rejections = [e for e in events if e.action == AuditAction.REJECTED and e.before]
    if not rejections:
        return WAITING
    before = rejections[-1].before or {}
    status = before.get("status")
    return status if status in EVIDENCE_STATUS else WAITING

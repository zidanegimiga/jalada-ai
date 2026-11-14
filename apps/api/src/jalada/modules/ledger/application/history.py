"""Writing the audit trail: one event for each change to a payment or a certificate."""

from datetime import datetime

from jalada.modules.ledger.application.transaction_mirror import Mirrored
from jalada.modules.ledger.domain.audit import Actor, AuditAction, SubjectType, event
from jalada.modules.ledger.domain.entries import Entry
from jalada.unit_of_work import UnitOfWork


def record(
    work: UnitOfWork,
    before: Entry | None,
    after: Entry,
    mirrored: Mirrored,
    actor: Actor,
    action: AuditAction,
    at: datetime,
) -> None:
    """Payments are recorded as transactions. Certificates, still entries, as entries."""
    was, now = mirrored
    if now is not None:
        trail = event(after.user_id, SubjectType.TRANSACTION, now.id, actor, action, was, now, at)
    else:
        trail = event(after.user_id, SubjectType.ENTRY, after.id, actor, action, before, after, at)
    work.audit_for(after.user_id).add(trail)

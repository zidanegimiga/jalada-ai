"""Writing the audit trail: one event for each change to a payment or a certificate."""

from datetime import datetime

from jalada.modules.ledger.application.transaction_mirror import Mirrored
from jalada.modules.ledger.domain.audit import Actor, AuditAction, SubjectType, event
from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.ledger.domain.transactions import Transaction
from jalada.unit_of_work import UnitOfWork


def record_transaction(
    work: UnitOfWork,
    before: Transaction | None,
    after: Transaction,
    actor: Actor,
    action: AuditAction,
    at: datetime,
) -> None:
    work.audit_for(after.user_id).add(
        event(after.user_id, SubjectType.TRANSACTION, after.id, actor, action, before, after, at)
    )


def record_entry(
    work: UnitOfWork,
    before: Entry | None,
    after: Entry,
    actor: Actor,
    action: AuditAction,
    at: datetime,
) -> None:
    """For withholding certificates, which are still entries."""
    work.audit_for(after.user_id).add(
        event(after.user_id, SubjectType.ENTRY, after.id, actor, action, before, after, at)
    )


def record(
    work: UnitOfWork,
    before: Entry | None,
    after: Entry,
    mirrored: Mirrored,
    actor: Actor,
    action: AuditAction,
    at: datetime,
) -> None:
    """For an entry written with its mirrored transaction: the transaction is recorded when
    there is one, the entry otherwise."""
    was, now = mirrored
    if now is not None:
        record_transaction(work, was, now, actor, action, at)
    else:
        record_entry(work, before, after, actor, action, at)

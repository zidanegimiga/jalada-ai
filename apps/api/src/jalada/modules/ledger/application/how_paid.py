"""Answering "Paid in cash or by card?" for a receipt whose payment never arrived."""

import uuid
from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.evidence.domain.evidence import EvidenceStatus
from jalada.modules.ledger.application import history
from jalada.modules.ledger.domain.audit import Actor, AuditAction
from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.ledger.domain.how_paid import ACCOUNTS, PaidWith, paid_from
from jalada.modules.ledger.domain.money_accounts import MoneyAccount
from jalada.modules.ledger.domain.transactions import TransactionStatus, as_entry
from jalada.shared.errors import EntryNotFound, InvalidEntry
from jalada.unit_of_work import UnitOfWork


class HowPaid:
    def __init__(self, unit_of_work: Callable[[], UnitOfWork], clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def answer(self, user_id: UUID, candidate_id: UUID, paid_with: PaidWith) -> Entry:
        """Puts the receipt on the cash or card account as a payment to confirm."""
        now = self._clock.now()
        with self._unit_of_work() as work:
            candidate = work.transactions_for(user_id).get(candidate_id)
            if candidate is None:
                raise EntryNotFound
            if candidate.status != TransactionStatus.CANDIDATE:
                raise InvalidEntry("This receipt already has its payment.")
            payment = paid_from(candidate, _account(work, user_id, paid_with, now))
            work.transactions_for(user_id).update(payment)
            history.record_transaction(
                work, candidate, payment, Actor.USER, AuditAction.ANSWERED, now
            )
            for link in payment.evidence:
                work.evidence_for(user_id).set_status(link.evidence_id, EvidenceStatus.NEEDS_REVIEW)
            work.commit()
        return as_entry(payment)


def _account(work: UnitOfWork, user_id: UUID, paid_with: PaidWith, now: datetime) -> UUID:
    """The user's account for the answer, opened the first time it is needed."""
    kind, name = ACCOUNTS[paid_with]
    accounts = work.money_accounts_for(user_id)
    found = next((a for a in accounts.all() if a.kind == kind), None)
    if found:
        return found.id
    opened = MoneyAccount(uuid.uuid4(), user_id, kind, name, True, now)
    accounts.add(opened)
    return opened.id

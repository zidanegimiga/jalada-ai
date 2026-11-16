"""Answering "Is this your own account?" for a payment to a paybill or from a business."""

import uuid
from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.ledger.application import history
from jalada.modules.ledger.domain.audit import Actor, AuditAction
from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.ledger.domain.money_accounts import MoneyAccount, MoneyAccountKind
from jalada.modules.ledger.domain.transactions import Transaction, TransactionStatus, as_entry
from jalada.modules.ledger.domain.transfers import (
    account_name,
    as_transfer,
    own_account_for,
    own_identifiers,
)
from jalada.shared.errors import EntryNotFound, InvalidEntry
from jalada.unit_of_work import UnitOfWork

WAITING = (TransactionStatus.PROPOSED, TransactionStatus.NEEDS_REVIEW)
# The most waiting payments looked at for the same account, as many as To check shows.
LIMIT = 100


class OwnAccounts:
    def __init__(self, unit_of_work: Callable[[], UnitOfWork], clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def say_mine(self, user_id: UUID, payment_id: UUID) -> Entry:
        """The account on the other side is the user's own. This payment, and any other
        waiting payment to or from the same account, become transfers to confirm."""
        now = self._clock.now()
        with self._unit_of_work() as work:
            payment = work.transactions_for(user_id).get(payment_id)
            if payment is None:
                raise EntryNotFound
            if payment.status not in WAITING or own_identifiers(payment) is None:
                raise InvalidEntry("This payment was not to or from a business account.")
            account = _account(work, payment, now)
            transfer = _make_transfer(work, payment, account, now)
            for other in work.transactions_for(user_id).pending(LIMIT):
                if other.id != payment.id and own_account_for(other, [account]):
                    _make_transfer(work, other, account, now)
            work.commit()
        return as_entry(transfer)


def _account(work: UnitOfWork, payment: Transaction, now: datetime) -> MoneyAccount:
    """The account, opened the first time. It is known only by how messages name it."""
    accounts = work.money_accounts_for(payment.user_id)
    found = own_account_for(payment, accounts.all())
    if found:
        return found
    named = own_identifiers(payment) or {}
    name = account_name(named, payment.counterparty or "")
    opened = MoneyAccount(
        uuid.uuid4(), payment.user_id, MoneyAccountKind.BANK, name, False, now, named
    )
    accounts.add(opened)
    return opened


def _make_transfer(
    work: UnitOfWork, payment: Transaction, account: MoneyAccount, now: datetime
) -> Transaction:
    transfer = as_transfer(payment, account)
    work.transactions_for(payment.user_id).update(transfer)
    history.record_transaction(work, payment, transfer, Actor.USER, AuditAction.ANSWERED, now)
    return transfer

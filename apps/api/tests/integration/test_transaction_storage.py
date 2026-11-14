import uuid
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker
from test_ledger_storage import make_entry, setup_evidence

from jalada.modules.ledger.domain.categories import Purpose
from jalada.modules.ledger.domain.money_accounts import default_accounts
from jalada.modules.ledger.domain.transactions import (
    EvidenceLink,
    EvidenceRole,
    LinkedBy,
    Transaction,
    TransactionLine,
    TransactionStatus,
    from_entry,
)
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)


def saved(session_factory: sessionmaker[DbSession], code: str = "UK5AB1CD23") -> Transaction:
    """A proposed M-Pesa payment for a new user, saved with its M-Pesa account."""
    user, evidence, run = setup_evidence(session_factory)
    [mpesa, _] = default_accounts(user.id, NOW)
    transaction = from_entry(
        make_entry(user, evidence, run, code), mpesa.id, EvidenceRole.PAYMENT_PROOF
    )
    with SqlUnitOfWork(session_factory) as work:
        work.money_accounts_for(user.id).add(mpesa)
        work.transactions_for(user.id).add(transaction)
        work.commit()
    return transaction


def test_a_transaction_comes_back_with_its_lines_and_evidence(
    session_factory: sessionmaker[DbSession],
) -> None:
    transaction = saved(session_factory)

    with SqlUnitOfWork(session_factory) as work:
        assert work.transactions_for(transaction.user_id).get(transaction.id) == transaction
        assert work.transactions_for(uuid.uuid4()).get(transaction.id) is None


def test_updating_replaces_the_lines_and_keeps_every_link(
    session_factory: sessionmaker[DbSession],
) -> None:
    transaction = saved(session_factory)
    _, receipt, _ = setup_evidence(session_factory)
    receipt_link = EvidenceLink(receipt.id, EvidenceRole.RECEIPT, LinkedBy.SUGGESTED, NOW)
    split = (
        TransactionLine(10000, "personal_food", Purpose.PERSONAL),
        TransactionLine(5000, "business_stock", Purpose.BUSINESS),
    )
    changed = replace(
        transaction,
        status=TransactionStatus.CONFIRMED,
        confirmed_at=NOW,
        lines=split,
        evidence=(receipt_link,),
    )
    with SqlUnitOfWork(session_factory) as work:
        work.transactions_for(transaction.user_id).update(changed)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        found = work.transactions_for(transaction.user_id).get(transaction.id)
    assert found is not None
    assert found.status == TransactionStatus.CONFIRMED
    assert found.lines == split
    assert found.evidence == (*transaction.evidence, receipt_link)


def test_payment_codes_are_unique_per_user(session_factory: sessionmaker[DbSession]) -> None:
    first = saved(session_factory, "UK5AB1CD99")
    saved(session_factory, "UK5AB1CD99")  # another user may have the same code

    with SqlUnitOfWork(session_factory) as work, pytest.raises(IntegrityError):
        work.transactions_for(first.user_id).add(replace(first, id=uuid.uuid4(), evidence=()))


def test_nobody_else_can_change_a_transaction(session_factory: sessionmaker[DbSession]) -> None:
    transaction = saved(session_factory)
    stranger = uuid.uuid4()

    with SqlUnitOfWork(session_factory) as work:
        with pytest.raises(PermissionError):
            work.transactions_for(stranger).add(transaction)
        with pytest.raises(LookupError):
            work.transactions_for(stranger).update(replace(transaction, user_id=stranger))

    with SqlUnitOfWork(session_factory) as work:
        assert work.transactions_for(transaction.user_id).get(transaction.id) == transaction


def test_only_proposed_and_doubtful_transactions_are_pending(
    session_factory: sessionmaker[DbSession],
) -> None:
    waiting = saved(session_factory)
    confirmed = replace(
        waiting,
        id=uuid.uuid4(),
        payment_code=None,
        status=TransactionStatus.CONFIRMED,
        evidence=(),
    )
    with SqlUnitOfWork(session_factory) as work:
        work.transactions_for(waiting.user_id).add(confirmed)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.transactions_for(waiting.user_id).pending(10) == [waiting]
        assert work.transactions_for(uuid.uuid4()).pending(10) == []


def test_all_lists_every_transaction_of_one_user(
    session_factory: sessionmaker[DbSession],
) -> None:
    first = saved(session_factory)
    later = replace(first, id=uuid.uuid4(), payment_code=None, created_at=NOW, evidence=())
    saved(session_factory, "UK5AB1CD77")  # someone else's
    with SqlUnitOfWork(session_factory) as work:
        work.transactions_for(first.user_id).add(later)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        assert work.transactions_for(first.user_id).all() == [first, later]


def test_a_payment_code_is_found_only_for_its_owner(
    session_factory: sessionmaker[DbSession],
) -> None:
    transaction = saved(session_factory, "UK5AB1CD55")

    with SqlUnitOfWork(session_factory) as work:
        assert work.transactions_for(transaction.user_id).has_payment_code("UK5AB1CD55")
        assert not work.transactions_for(transaction.user_id).has_payment_code("UK5AB1CD56")
        assert not work.transactions_for(uuid.uuid4()).has_payment_code("UK5AB1CD55")

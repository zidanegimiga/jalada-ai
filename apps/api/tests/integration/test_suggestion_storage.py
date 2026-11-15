import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DbSession
from sqlalchemy.orm import sessionmaker
from test_transaction_storage import saved

from jalada.modules.ledger.domain.suggestions import (
    MatchSuggestion,
    SuggestionKind,
    SuggestionStatus,
)
from jalada.modules.ledger.domain.transactions import Transaction, TransactionStatus
from jalada.sql_unit_of_work import SqlUnitOfWork

pytestmark = pytest.mark.integration

NOW = datetime(2026, 11, 15, 9, 0, tzinfo=UTC)


def pair(session_factory: sessionmaker[DbSession]) -> tuple[Transaction, Transaction]:
    """A saved payment and a receipt waiting as a candidate, for the same user."""
    payment = saved(session_factory)
    candidate = replace(
        payment,
        id=uuid.uuid4(),
        account_id=None,
        status=TransactionStatus.CANDIDATE,
        payment_code=None,
        run_id=None,
    )
    with SqlUnitOfWork(session_factory) as work:
        work.transactions_for(payment.user_id).add(candidate)
        work.commit()
    return payment, candidate


def suggestion(payment: Transaction, candidate: Transaction) -> MatchSuggestion:
    return MatchSuggestion(
        id=uuid.uuid4(),
        user_id=payment.user_id,
        kind=SuggestionKind.SAME_PURCHASE,
        payment_id=payment.id,
        candidate_id=candidate.id,
        score=1.0,
        reasons=("same amount", "same day"),
        status=SuggestionStatus.OPEN,
        created_at=NOW,
    )


def test_a_suggestion_comes_back_from_either_side_for_its_user_only(
    session_factory: sessionmaker[DbSession],
) -> None:
    payment, candidate = pair(session_factory)
    offered = suggestion(payment, candidate)
    with SqlUnitOfWork(session_factory) as work:
        work.suggestions_for(payment.user_id).add(offered)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        mine = work.suggestions_for(payment.user_id)
        assert mine.get(offered.id) == offered
        assert mine.involving(payment.id) == mine.involving(candidate.id) == [offered]
        assert mine.open() == mine.all() == [offered]
        assert work.suggestions_for(uuid.uuid4()).get(offered.id) is None


def test_a_decision_is_saved_and_the_suggestion_is_no_longer_open(
    session_factory: sessionmaker[DbSession],
) -> None:
    payment, candidate = pair(session_factory)
    offered = suggestion(payment, candidate)
    declined = replace(
        offered, status=SuggestionStatus.DECLINED, decided_at=NOW + timedelta(hours=1)
    )
    with SqlUnitOfWork(session_factory) as work:
        work.suggestions_for(payment.user_id).add(offered)
        work.suggestions_for(payment.user_id).decide(declined)
        work.commit()

    with SqlUnitOfWork(session_factory) as work:
        mine = work.suggestions_for(payment.user_id)
        assert mine.open() == []
        assert mine.get(offered.id) == declined


def test_the_same_pair_is_never_suggested_twice(
    session_factory: sessionmaker[DbSession],
) -> None:
    payment, candidate = pair(session_factory)
    with SqlUnitOfWork(session_factory) as work:
        work.suggestions_for(payment.user_id).add(suggestion(payment, candidate))
        with pytest.raises(IntegrityError):
            work.suggestions_for(payment.user_id).add(suggestion(payment, candidate))


def test_a_suggestion_for_another_user_is_refused(
    session_factory: sessionmaker[DbSession],
) -> None:
    payment, candidate = pair(session_factory)
    stranger = replace(suggestion(payment, candidate), user_id=uuid.uuid4())
    with SqlUnitOfWork(session_factory) as work, pytest.raises(PermissionError):
        work.suggestions_for(payment.user_id).add(stranger)


def test_receipts_still_waiting_come_back_once_they_are_old_enough(
    session_factory: sessionmaker[DbSession],
) -> None:
    payment, candidate = pair(session_factory)
    with SqlUnitOfWork(session_factory) as work:
        transactions = work.transactions_for(payment.user_id)
        assert transactions.candidates(candidate.created_at, 10) == [candidate]
        assert transactions.candidates(candidate.created_at - timedelta(seconds=1), 10) == []
        assert work.transactions_for(uuid.uuid4()).candidates(NOW, 10) == []

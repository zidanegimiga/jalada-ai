import uuid
from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any

import pytest

from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.ready import ready_to_confirm
from jalada.modules.ledger.domain.transactions import (
    EvidenceLink,
    EvidenceRole,
    LinkedBy,
    Transaction,
    TransactionKind,
    TransactionLine,
    TransactionStatus,
)

NOW = datetime(2026, 11, 7, 12, tzinfo=UTC)
LINE = TransactionLine(15000, "personal_family_support", Purpose.PERSONAL)


def proposed() -> Transaction:
    return Transaction(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        account_id=uuid.uuid4(),
        kind=TransactionKind.PAYMENT,
        status=TransactionStatus.PROPOSED,
        occurred_on=date(2026, 11, 5),
        direction=Direction.OUT,
        amount_cents=15000,
        counterparty="JANE WANJIKU",
        reference=None,
        payment_code="UK5AB1CD23",
        confidence=0.95,
        run_id=uuid.uuid4(),
        created_at=NOW,
        confirmed_at=None,
        lines=(LINE,),
        evidence=(EvidenceLink(uuid.uuid4(), EvidenceRole.PAYMENT_PROOF, LinkedBy.PIPELINE, NOW),),
    )


def test_a_proposed_payment_with_a_category_is_ready() -> None:
    assert ready_to_confirm(proposed(), open_question=False)


def test_an_open_question_holds_it_back() -> None:
    assert not ready_to_confirm(proposed(), open_question=True)


@pytest.mark.parametrize(
    "changes",
    [
        {"status": TransactionStatus.NEEDS_REVIEW},
        {"status": TransactionStatus.CONFIRMED},
        {"status": TransactionStatus.CANDIDATE},
        {"lines": (replace(LINE, suggested=True),)},
        {"lines": (replace(LINE, category=None),)},
        {"lines": (replace(LINE, category="business_sales"),)},
        {"lines": (replace(LINE, amount_cents=10000),)},
        {"occurred_on": None},
    ],
)
def test_anything_that_needs_a_look_is_not_ready(changes: dict[str, Any]) -> None:
    assert not ready_to_confirm(replace(proposed(), **changes), open_question=False)

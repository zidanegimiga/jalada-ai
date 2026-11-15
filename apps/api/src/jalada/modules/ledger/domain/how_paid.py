"""Asking how a receipt was paid when no payment for it has arrived (design 03,
"Candidates"). Cash or card turns the candidate into a payment on that account, which the
user then confirms like any other."""

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum
from uuid import UUID

from jalada.modules.ledger.domain.money_accounts import MoneyAccountKind
from jalada.modules.ledger.domain.transactions import Transaction, TransactionStatus


class PaidWith(StrEnum):
    CASH = "cash"
    CARD = "card"


# The account each answer puts the payment on, found by kind or opened with this name.
ACCOUNTS = {
    PaidWith.CASH: (MoneyAccountKind.CASH, "Cash"),
    PaidWith.CARD: (MoneyAccountKind.CARD, "Card"),
}


@dataclass(frozen=True)
class AskingRules:
    # How long a receipt waits for its payment message before the user is asked.
    wait: timedelta = timedelta(days=3)


DEFAULT_ASKING = AskingRules()


def time_to_ask(
    candidate: Transaction,
    now: datetime,
    has_open_question: bool,
    rules: AskingRules = DEFAULT_ASKING,
) -> bool:
    """True for a candidate that has waited long enough with nothing offered for it. An
    open suggested match is asked first."""
    return (
        candidate.status == TransactionStatus.CANDIDATE
        and not has_open_question
        and now - candidate.created_at >= rules.wait
    )


def paid_from(candidate: Transaction, account_id: UUID) -> Transaction:
    """The candidate as a payment from the account the user named, waiting for them to
    confirm it."""
    if candidate.status != TransactionStatus.CANDIDATE:
        raise ValueError("Only a candidate is waiting to be told how it was paid")
    return replace(candidate, account_id=account_id, status=TransactionStatus.NEEDS_REVIEW)

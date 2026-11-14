import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class MoneyAccountKind(StrEnum):
    MPESA = "mpesa"
    BANK = "bank"
    CASH = "cash"
    CARD = "card"
    LOAN = "loan"


@dataclass(frozen=True)
class MoneyAccount:
    """Somewhere the user's money sits. Transactions move money in, out or between these."""

    id: UUID
    user_id: UUID
    kind: MoneyAccountKind
    name: str
    # False for an account known only by name, such as a bank the user never sends
    # statements for. Transfers to it are still transfers.
    tracked: bool
    created_at: datetime


DEFAULT_ACCOUNTS = ((MoneyAccountKind.MPESA, "M-Pesa"), (MoneyAccountKind.CASH, "Cash"))


def default_accounts(user_id: UUID, now: datetime) -> list[MoneyAccount]:
    """The accounts every user starts with."""
    return [
        MoneyAccount(uuid.uuid4(), user_id, kind, name, True, now)
        for kind, name in DEFAULT_ACCOUNTS
    ]

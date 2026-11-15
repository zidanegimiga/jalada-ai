"""Transfers to the user's own accounts, such as M-Pesa to a bank through its paybill.

The first payment to a paybill that looks like a bank or a savings account is asked about:
is it the user's own account? Once they say yes, every payment to that paybill and
account number is a transfer, which is neither money in nor money out (design 03, "Moved
M-Pesa to the bank")."""

import re
from dataclasses import dataclass, replace

from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.entries import counterparty_key
from jalada.modules.ledger.domain.money_accounts import MoneyAccount
from jalada.modules.ledger.domain.transactions import (
    Transaction,
    TransactionKind,
    TransactionLine,
)

OWN_TRANSFER_OUT = "own_transfer_out"


@dataclass(frozen=True)
class OwnAccountSigns:
    # Words in a paybill name that say the user may be paying into their own account.
    words: frozenset[str] = frozenset(
        {
            "bank",
            "sacco",
            "mmf",
            "money market",
            "fund",
            "savings",
            "investment",
            "equity",
            "kcb",
            "co-op",
            "cooperative",
            "ncba",
            "absa",
            "stanbic",
            "dtb",
            "i&m",
        }
    )


DEFAULT_SIGNS = OwnAccountSigns()


def paybill_identifiers(payment: Transaction) -> dict[str, str] | None:
    """The paybill name and account number a payment was sent to, or None when it was not
    sent to a paybill account."""
    if payment.kind != TransactionKind.PAYMENT:
        return None
    return paybill(payment.direction, payment.counterparty, payment.reference)


def paybill(
    direction: Direction | None, counterparty: str | None, reference: str | None
) -> dict[str, str] | None:
    """The same, from what was read from a message."""
    if direction != Direction.OUT or not counterparty or not reference:
        return None
    account = "".join(reference.split()).upper()
    return {"paybill": counterparty_key(counterparty), "account": account}


def may_be_own_account(payment: Transaction, signs: OwnAccountSigns = DEFAULT_SIGNS) -> bool:
    if paybill_identifiers(payment) is None or not payment.counterparty:
        return False
    name = payment.counterparty.lower()
    return any(re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", name) for word in signs.words)


def own_account_for(payment: Transaction, accounts: list[MoneyAccount]) -> MoneyAccount | None:
    """The user's account this payment was sent to, when they said the paybill is theirs."""
    identifiers = paybill_identifiers(payment)
    if identifiers is None:
        return None
    return next((a for a in accounts if a.identifiers == identifiers), None)


def account_name(identifiers: dict[str, str], counterparty: str) -> str:
    """Such as "EQUITY PAYBILL ending 6789", short enough for the account name."""
    return f"{' '.join(counterparty.split())[:60]} ending {identifiers['account'][-4:]}"


def as_transfer(payment: Transaction, to_account: MoneyAccount) -> Transaction:
    line = TransactionLine(payment.amount_cents, OWN_TRANSFER_OUT, Purpose.PERSONAL)
    return replace(
        payment, kind=TransactionKind.TRANSFER, to_account_id=to_account.id, lines=(line,)
    )

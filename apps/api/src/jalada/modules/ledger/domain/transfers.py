"""Transfers between the user's own accounts, such as M-Pesa to a bank through its paybill,
or money sent back from the bank to M-Pesa.

The first payment to a paybill, or from a sender, that looks like a bank or a savings
account is asked about: is it the user's own account? Once they say yes, every payment
to that paybill and account number, or from that sender, is a transfer, which is neither
money in nor money out (design 03, "Moved M-Pesa to the bank")."""

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
OWN_TRANSFER_IN = "own_transfer"
TRANSFER_CATEGORIES = {Direction.OUT: OWN_TRANSFER_OUT, Direction.IN: OWN_TRANSFER_IN}
# A Kenyan mobile number, as it ends a person's name in a received message.
PHONE_AT_END = re.compile(r"(?:\+?254|0)\d{9}$")


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


def own_identifiers(payment: Transaction) -> dict[str, str] | None:
    """How the other side of a payment would name one of the user's accounts: the paybill
    and account number it was sent to, or the business it came from. None for anything
    else, such as money to or from a person."""
    if payment.kind != TransactionKind.PAYMENT:
        return None
    return identifiers(payment.direction, payment.counterparty, payment.reference)


def identifiers(
    direction: Direction | None, counterparty: str | None, reference: str | None
) -> dict[str, str] | None:
    """The same, from what was read from a message."""
    return paybill(direction, counterparty, reference) or sender(direction, counterparty)


def sender(direction: Direction | None, counterparty: str | None) -> dict[str, str] | None:
    """The business money came from. A bank sending to M-Pesa gives no account number, so
    its name is all there is."""
    if direction != Direction.IN or not counterparty:
        return None
    if PHONE_AT_END.search(counterparty.strip()):
        return None
    return {"sender": counterparty_key(counterparty)}


def paybill(
    direction: Direction | None, counterparty: str | None, reference: str | None
) -> dict[str, str] | None:
    """The paybill name and account number money was sent to."""
    if direction != Direction.OUT or not counterparty or not reference:
        return None
    account = "".join(reference.split()).upper()
    return {"paybill": counterparty_key(counterparty), "account": account}


def may_be_own_account(payment: Transaction, signs: OwnAccountSigns = DEFAULT_SIGNS) -> bool:
    if own_identifiers(payment) is None or not payment.counterparty:
        return False
    name = payment.counterparty.lower()
    return any(re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", name) for word in signs.words)


def own_account_for(payment: Transaction, accounts: list[MoneyAccount]) -> MoneyAccount | None:
    """The user's account on the other side of this payment, when they said it is theirs."""
    named = own_identifiers(payment)
    if named is None:
        return None
    return next((a for a in accounts if a.identifiers == named), None)


def account_name(identifiers: dict[str, str], counterparty: str) -> str:
    """Such as "EQUITY PAYBILL ending 6789", or the sender's name, short enough for the
    account name."""
    name = " ".join(counterparty.split())[:60]
    number = identifiers.get("account")
    return f"{name} ending {number[-4:]}" if number else name


def as_transfer(payment: Transaction, other_account: MoneyAccount) -> Transaction:
    category = TRANSFER_CATEGORIES[payment.direction or Direction.OUT]
    line = TransactionLine(payment.amount_cents, category, Purpose.PERSONAL)
    return replace(
        payment, kind=TransactionKind.TRANSFER, to_account_id=other_account.id, lines=(line,)
    )

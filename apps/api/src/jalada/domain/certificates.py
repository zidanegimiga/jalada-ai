"""Matching withholding certificates with the payments that settled them.

A client who withholds tax pays the rest: the deposit is the gross amount on the
certificate minus the tax withheld. Linked payments are counted through the certificate,
never again on their own.
"""

from datetime import date, timedelta

from jalada.domain.categories import Direction
from jalada.domain.entries import Entry, EntryKind, EntryStatus, counterparty_key

# The certificate's date is the transaction date. Clients often pay some weeks either side.
LOOK_BEFORE = timedelta(days=90)
LOOK_AFTER = timedelta(days=60)
MAX_SUGGESTIONS = 5


def expected_payment_cents(certificate: Entry) -> int:
    """What a client who withheld the tax would have paid in."""
    return (certificate.amount_cents or 0) - (certificate.tax_withheld_cents or 0)


def search_window(certificate: Entry) -> tuple[date, date]:
    if certificate.occurred_on is None:
        raise ValueError("A certificate without a date cannot be matched")
    return certificate.occurred_on - LOOK_BEFORE, certificate.occurred_on + LOOK_AFTER


def can_be_payment(entry: Entry) -> bool:
    return (
        entry.kind == EntryKind.TRANSACTION
        and entry.status == EntryStatus.CONFIRMED
        and entry.direction == Direction.IN
        and bool(entry.amount_cents)
    )


def suggest_payments(
    certificate: Entry, deposits: list[Entry], linked_cents: int = 0
) -> list[Entry]:
    """Likely payments first: the exact amount still expected, then the same payer, then the
    closest date. A deposit larger than what is left of the gross amount cannot be one."""
    day = certificate.occurred_on
    if day is None:
        return []
    expected = expected_payment_cents(certificate) - linked_cents
    room = (certificate.amount_cents or 0) - linked_cents
    payer = counterparty_key(certificate.counterparty or "")
    usable = [d for d in deposits if can_be_payment(d) and (d.amount_cents or 0) <= room]

    def rank(deposit: Entry) -> tuple[bool, bool, timedelta]:
        return (
            deposit.amount_cents != expected,
            counterparty_key(deposit.counterparty or "") != payer,
            abs((deposit.occurred_on or day) - day),
        )

    return sorted(usable, key=rank)[:MAX_SUGGESTIONS]


def link_problem(certificate: Entry, payment: Entry, already_linked_cents: int) -> str | None:
    """Why this payment cannot be linked to this certificate, or None if it can."""
    if not can_be_payment(payment):
        return "Only confirmed money coming in can be linked to a certificate."
    if already_linked_cents + (payment.amount_cents or 0) > (certificate.amount_cents or 0):
        return "Payments linked to a certificate cannot add up to more than its gross amount."
    return None

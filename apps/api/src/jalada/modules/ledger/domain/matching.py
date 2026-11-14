"""Whether two records describe the same money. Matching is separate from classification:
a category is never a reason to treat two payments as one (design 03, "Matching").

An exact match is made without asking. It needs a code issued by the payment system, read
in its right shape, on a payment with the same amount going the same way. Anything less is
at most a suggestion for the user."""

import re
from datetime import date

from jalada.modules.ledger.domain.categories import Direction
from jalada.modules.ledger.domain.transactions import Transaction, TransactionStatus

# M-Pesa transaction codes: ten capital letters and digits.
MPESA_CODE = re.compile(r"[A-Z0-9]{10}")


def is_exact_match(
    payment: Transaction,
    code: str | None,
    amount_cents: int | None,
    direction: Direction | None,
    occurred_on: date | None = None,
) -> bool:
    """True when the evidence read as (code, amount, direction, date) is the same payment.
    A date, when both have one, must agree too."""
    if not code or not MPESA_CODE.fullmatch(code) or payment.payment_code != code:
        return False
    if payment.status == TransactionStatus.REJECTED:
        # The user said it is not money moving. Another copy changes nothing about that.
        return False
    if amount_cents is None or payment.amount_cents != amount_cents:
        return False
    if direction is None or payment.direction != direction:
        return False
    dates = (payment.occurred_on, occurred_on)
    return None in dates or dates[0] == dates[1]

"""What the user can change on a payment before confirming it, and what a confirmed payment
must have. The messages are shown to the user as they are."""

from dataclasses import replace
from datetime import datetime

from jalada.modules.ledger.domain.categories import CATEGORIES
from jalada.modules.ledger.domain.entries import Correction
from jalada.modules.ledger.domain.transactions import (
    Transaction,
    TransactionStatus,
    line_problems,
)


class ReviewProblem(ValueError):
    """Why a change or a confirmation was refused, in words for the user."""


def corrected(transaction: Transaction, correction: Correction) -> Transaction:
    if correction.category is not None and correction.category not in CATEGORIES:
        raise ReviewProblem("That category does not exist.")
    if correction.amount_cents is not None and correction.amount_cents <= 0:
        raise ReviewProblem("The amount must be more than zero.")
    changes = {
        name: value
        for name, value in vars(correction).items()
        if value is not None and name != "category"
    }
    if "counterparty" in changes:
        changes["counterparty"] = " ".join(changes["counterparty"].split())[:200] or None
    changed = replace(transaction, **changes)
    if correction.amount_cents is None and correction.category is None:
        return changed
    if len(changed.lines) != 1:
        raise ReviewProblem("Change a split payment one line at a time.")
    [line] = changed.lines
    if correction.amount_cents is not None:
        line = replace(line, amount_cents=correction.amount_cents)
    if correction.category is not None:
        line = replace(line, category=correction.category)
    return replace(changed, lines=(line,))


def confirmed(transaction: Transaction, now: datetime) -> Transaction:
    """The payment confirmed, with each line's purpose taken from its category."""
    missing = [
        name
        for name, absent in (
            ("date", transaction.occurred_on is None),
            ("amount", transaction.amount_cents is None),
            ("direction", transaction.direction is None),
            ("category", any(line.category is None for line in transaction.lines)),
        )
        if absent
    ]
    if missing:
        raise ReviewProblem(f"Add the {', '.join(missing)} before confirming.")
    lines = []
    for line in transaction.lines:
        category = CATEGORIES[line.category or ""]
        if category.direction != transaction.direction:
            raise ReviewProblem("That category does not fit money going this way.")
        lines.append(replace(line, purpose=category.purpose))
    done = replace(
        transaction,
        status=TransactionStatus.CONFIRMED,
        confirmed_at=now,
        lines=tuple(lines),
    )
    if line_problems(done):
        raise ReviewProblem("The lines do not add up to the amount.")
    return done

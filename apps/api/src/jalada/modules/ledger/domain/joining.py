"""Joining a receipt waiting as a candidate into the payment the user said it belongs to,
and separating them again when the user takes that back."""

from dataclasses import replace
from datetime import datetime

from jalada.modules.ledger.domain.transactions import (
    LinkedBy,
    Transaction,
    TransactionLine,
    TransactionStatus,
)


def joined(
    payment: Transaction, candidate: Transaction, now: datetime
) -> tuple[Transaction, Transaction]:
    """The payment with the receipt's evidence, and the candidate, merged into it. The
    receipt supplies the category when the payment has none of its own yet. Nothing is
    confirmed: the user still confirms the payment."""
    if candidate.status != TransactionStatus.CANDIDATE:
        raise ValueError("Only a candidate can be joined into a payment")
    known = {link.evidence_id for link in payment.evidence}
    links = tuple(
        replace(link, linked_by=LinkedBy.SUGGESTED, linked_at=now)
        for link in candidate.evidence
        if link.evidence_id not in known
    )
    lines = _lines(payment.lines, candidate.lines)
    return (
        replace(payment, evidence=(*payment.evidence, *links), lines=lines),
        replace(candidate, status=TransactionStatus.MERGED),
    )


def _lines(
    paid: tuple[TransactionLine, ...], receipt: tuple[TransactionLine, ...]
) -> tuple[TransactionLine, ...]:
    """A category chosen by the user or a rule stays. One that is missing or only a model's
    guess gives way to the receipt's, which keeps its own suggested flag."""
    if len(paid) != 1 or len(receipt) != 1:
        return paid
    [line], [read] = paid, receipt
    if read.category is None or (line.category is not None and not line.suggested):
        return paid
    return (replace(line, category=read.category, purpose=read.purpose, suggested=read.suggested),)


def separated(
    payment: Transaction,
    candidate: Transaction,
    lines_before: tuple[TransactionLine, ...] | None,
) -> tuple[Transaction, Transaction]:
    """The payment without the receipt's evidence, and the receipt waiting again.
    `lines_before` are the payment's lines from before the join, given only when nobody has
    changed them since: a category the user chose afterwards stays."""
    if candidate.status != TransactionStatus.MERGED:
        raise ValueError("Only a merged candidate can be separated")
    receipt = {link.evidence_id for link in candidate.evidence}
    evidence = tuple(link for link in payment.evidence if link.evidence_id not in receipt)
    lines = payment.lines if lines_before is None else lines_before
    return (
        replace(payment, evidence=evidence, lines=lines),
        replace(candidate, status=TransactionStatus.CANDIDATE),
    )

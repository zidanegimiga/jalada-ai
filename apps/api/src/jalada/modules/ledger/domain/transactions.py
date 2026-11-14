from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from jalada.modules.evidence.domain.evidence import EvidenceKind
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.entries import Entry, EntryKind, EntryStatus


class TransactionKind(StrEnum):
    PAYMENT = "payment"
    TRANSFER = "transfer"
    REVERSAL = "reversal"
    REFUND = "refund"


class TransactionStatus(StrEnum):
    # A purchase a receipt says happened, with no payment found yet. Never counted.
    CANDIDATE = "candidate"
    PROPOSED = "proposed"
    NEEDS_REVIEW = "needs_review"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class EvidenceRole(StrEnum):
    """What a piece of evidence does for a transaction."""

    PAYMENT_PROOF = "payment_proof"
    RECEIPT = "receipt"
    INVOICE = "invoice"
    CERTIFICATE = "certificate"
    PAYSLIP = "payslip"
    STATEMENT = "statement"
    OTHER = "other"


class LinkedBy(StrEnum):
    """How evidence came to be linked: read from it, an exact code match, a suggestion the
    user accepted, or the user's own choice."""

    PIPELINE = "pipeline"
    EXACT = "exact"
    SUGGESTED = "suggested"
    USER = "user"


ROLES = {
    EvidenceKind.MPESA_MESSAGE: EvidenceRole.PAYMENT_PROOF,
    EvidenceKind.RECEIPT: EvidenceRole.RECEIPT,
    EvidenceKind.STATEMENT: EvidenceRole.STATEMENT,
    EvidenceKind.PAYSLIP: EvidenceRole.PAYSLIP,
    EvidenceKind.WITHHOLDING_CERTIFICATE: EvidenceRole.CERTIFICATE,
}


def role_for(kind: EvidenceKind) -> EvidenceRole:
    return ROLES.get(kind, EvidenceRole.OTHER)


@dataclass(frozen=True)
class TransactionLine:
    """What part of a transaction was for. One line until the user splits it."""

    amount_cents: int | None
    category: str | None
    purpose: Purpose


@dataclass(frozen=True)
class EvidenceLink:
    evidence_id: UUID
    role: EvidenceRole
    linked_by: LinkedBy
    linked_at: datetime


@dataclass(frozen=True)
class Transaction:
    """Money that moved. Amounts are in cents."""

    id: UUID
    user_id: UUID
    # None while it is not known which account paid, such as a receipt read on its own.
    account_id: UUID | None
    kind: TransactionKind
    status: TransactionStatus
    occurred_on: date | None
    direction: Direction | None
    amount_cents: int | None
    counterparty: str | None
    reference: str | None
    # A code issued by the payment system, such as an M-Pesa code. One per user.
    payment_code: str | None
    confidence: float
    # None for transactions typed in by hand, which no pipeline run produced.
    run_id: UUID | None
    created_at: datetime
    confirmed_at: datetime | None
    lines: tuple[TransactionLine, ...]
    evidence: tuple[EvidenceLink, ...]


def line_problems(transaction: Transaction) -> list[str]:
    """Why the lines cannot stand for a confirmed transaction. Empty when they can."""
    problems = []
    if not transaction.lines:
        problems.append("no lines")
    if any(line.category is None for line in transaction.lines):
        problems.append("a line has no category")
    amounts = [line.amount_cents for line in transaction.lines]
    if None in amounts or sum(a or 0 for a in amounts) != transaction.amount_cents:
        problems.append("the lines do not add up to the amount")
    return problems


def from_entry(entry: Entry, account_id: UUID | None, role: EvidenceRole) -> Transaction:
    """The transaction an entry stands for, while both models exist. It keeps the entry's
    id, so links made to the entry still point at the same money."""
    if entry.kind != EntryKind.TRANSACTION:
        raise ValueError("Only transaction entries become transactions")
    linked_by = LinkedBy.PIPELINE if entry.run_id else LinkedBy.USER
    return Transaction(
        id=entry.id,
        user_id=entry.user_id,
        account_id=account_id,
        kind=TransactionKind.PAYMENT,
        status=TransactionStatus(entry.status.value),
        occurred_on=entry.occurred_on,
        direction=entry.direction,
        amount_cents=entry.amount_cents,
        counterparty=entry.counterparty,
        reference=entry.reference,
        payment_code=entry.mpesa_code,
        confidence=entry.confidence,
        run_id=entry.run_id,
        created_at=entry.created_at,
        confirmed_at=entry.confirmed_at,
        lines=(TransactionLine(entry.amount_cents, entry.category, entry.purpose),),
        evidence=(EvidenceLink(entry.evidence_id, role, linked_by, entry.created_at),),
    )


def as_entry(transaction: Transaction) -> Entry:
    """The entry a transaction stands for, so screens built on entries can read transactions
    while both models exist. Goes with entries."""
    if transaction.status == TransactionStatus.CANDIDATE or not transaction.evidence:
        raise ValueError("Only transactions with evidence and an entry status have an entry")
    # One line until splitting exists. A split has no single category to show.
    line = transaction.lines[0] if len(transaction.lines) == 1 else None
    return Entry(
        id=transaction.id,
        user_id=transaction.user_id,
        evidence_id=transaction.evidence[0].evidence_id,
        run_id=transaction.run_id,
        kind=EntryKind.TRANSACTION,
        status=EntryStatus(transaction.status.value),
        occurred_on=transaction.occurred_on,
        direction=transaction.direction,
        amount_cents=transaction.amount_cents,
        counterparty=transaction.counterparty,
        reference=transaction.reference,
        mpesa_code=transaction.payment_code,
        certificate_serial=None,
        tax_withheld_cents=None,
        purpose=line.purpose if line else Purpose.UNSURE,
        category=line.category if line else None,
        confidence=transaction.confidence,
        created_at=transaction.created_at,
        confirmed_at=transaction.confirmed_at,
    )

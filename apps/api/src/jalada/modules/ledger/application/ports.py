from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, Protocol
from uuid import UUID

from jalada.modules.ledger.domain.audit import AuditEvent
from jalada.modules.ledger.domain.categories import Purpose

if TYPE_CHECKING:
    pass
from jalada.modules.ledger.domain.entries import Entry, EntryKind
from jalada.modules.ledger.domain.ledger import LedgerFilter, LedgerPosition, Total
from jalada.modules.ledger.domain.money_accounts import MoneyAccount
from jalada.modules.ledger.domain.transactions import Transaction
from jalada.modules.pipeline.domain.classifier import Preference


@dataclass(frozen=True)
class Revision:
    entry_id: UUID
    before: dict[str, Any]
    after: dict[str, Any]
    changed_at: datetime


class EntryRepository(Protocol):
    """Ledger entries for one user."""

    def add(self, entry: Entry) -> None: ...
    def get(self, entry_id: UUID) -> Entry | None: ...
    def for_evidence(self, evidence_id: UUID) -> Entry | None: ...
    def update(self, entry: Entry) -> None: ...
    def add_revision(self, before: Entry, after: Entry, changed_at: datetime) -> None: ...
    def pending(self, limit: int, kind: EntryKind | None = None) -> list[Entry]: ...
    def confirmed(
        self,
        filters: LedgerFilter,
        after: LedgerPosition | None,
        limit: int,
        kind: EntryKind | None = None,
    ) -> list[Entry]: ...
    def monthly_totals(self, year: int, kind: EntryKind | None = None) -> list[Total]: ...
    def all(self) -> list[Entry]: ...
    def revisions(self) -> list[Revision]: ...
    def has_certificate_serial(self, serial: str) -> bool: ...


class CertificatePaymentRepository(Protocol):
    """Payments linked to withholding certificates, for one user."""

    def links(self) -> dict[UUID, UUID]:
        """Payment id to the id of the certificate it settled."""
        ...

    def link(self, certificate_id: UUID, payment_id: UUID, at: datetime) -> None: ...
    def unlink(self, certificate_id: UUID, payment_id: UUID) -> None: ...


class PreferenceRepository(Protocol):
    def all(self) -> dict[str, Preference]: ...
    def remember(self, counterparty_key: str, category: str, purpose: Purpose) -> None: ...


class MoneyAccountRepository(Protocol):
    """Where one user's money sits."""

    def all(self) -> list[MoneyAccount]: ...
    def add(self, account: MoneyAccount) -> None: ...


class TransactionRepository(Protocol):
    """One user's transactions, with their lines and evidence."""

    def add(self, transaction: Transaction) -> None: ...
    def get(self, transaction_id: UUID) -> Transaction | None: ...
    def pending(self, limit: int) -> list[Transaction]:
        """Transactions waiting for the user: proposed or needing a look."""
        ...

    def confirmed(
        self, filters: LedgerFilter, after: LedgerPosition | None, limit: int
    ) -> list[Transaction]:
        """Newest first, by date and then id, starting after `after`."""
        ...

    def all(self) -> list[Transaction]:
        """Every transaction, oldest first, for the data download."""
        ...

    def incoming(self, start: date, end: date) -> list[Transaction]:
        """Confirmed payments in between two dates, oldest first."""
        ...

    def has_payment_code(self, code: str) -> bool:
        """Whether a transaction already carries this payment system code."""
        ...

    def monthly_totals(self, year: int) -> list[Total]:
        """Confirmed lines per month, direction and purpose. Payments linked to a
        certificate are left out: the certificate's gross amount counts them."""
        ...

    def update(self, transaction: Transaction) -> None:
        """Saves the fields and the lines, and adds any new evidence links. Links are never
        removed here: unlinking is its own action."""
        ...


class AuditTrail(Protocol):
    """One user's audit trail. Events are added, never changed or removed."""

    def add(self, event: AuditEvent) -> None: ...
    def for_subject(self, subject_id: UUID) -> list[AuditEvent]:
        """Oldest first, and in the order written when the time is the same."""
        ...

    def all(self) -> list[AuditEvent]: ...

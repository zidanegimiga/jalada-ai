"""Confirmed records while both models exist: payments from transactions, and withholding
certificates, which are still entries. Both are given in the shape of entries, so the
screens and the workbook read them as before."""

from uuid import UUID

from jalada.modules.ledger.domain.entries import Entry, EntryKind
from jalada.modules.ledger.domain.ledger import LedgerFilter, LedgerPosition
from jalada.modules.ledger.domain.transactions import as_entry
from jalada.unit_of_work import UnitOfWork

CERTIFICATE = EntryKind.WITHHOLDING_CERTIFICATE


def confirmed(
    work: UnitOfWork,
    user_id: UUID,
    filters: LedgerFilter,
    after: LedgerPosition | None,
    limit: int,
) -> list[Entry]:
    """Newest first, by date and then id, as the ledger pages through them."""
    payments = work.transactions_for(user_id).confirmed(filters, after, limit)
    certificates = work.entries_for(user_id).confirmed(filters, after, limit, CERTIFICATE)
    merged = [as_entry(t) for t in payments] + certificates
    merged.sort(key=lambda e: (e.occurred_on, e.id), reverse=True)
    return merged[:limit]

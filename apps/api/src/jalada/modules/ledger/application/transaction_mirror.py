"""Keeps a transaction beside every transaction entry while both models exist, as in
design 03, "Moving from entries". This goes once nothing reads entries."""

from dataclasses import replace
from uuid import UUID

from jalada.modules.evidence.domain.evidence import EvidenceKind
from jalada.modules.ledger.domain.entries import Entry, EntryKind
from jalada.modules.ledger.domain.money_accounts import MoneyAccountKind
from jalada.modules.ledger.domain.transactions import (
    EvidenceRole,
    Transaction,
    from_entry,
    role_for,
)
from jalada.unit_of_work import UnitOfWork

Mirrored = tuple[Transaction | None, Transaction | None]


def mirror_entry(work: UnitOfWork, entry: Entry) -> Mirrored:
    """Saves the transaction an entry stands for, in the same database transaction, and
    returns it before and after. Certificates are not transactions and are left alone."""
    if entry.kind != EntryKind.TRANSACTION:
        return None, None
    transactions = work.transactions_for(entry.user_id)
    existing = transactions.get(entry.id)
    if existing:
        # The account and the evidence links are the transaction's own: an entry knows
        # neither, so they are kept as they are.
        updated = from_entry(entry, existing.account_id, EvidenceRole.OTHER)
        updated = replace(updated, evidence=existing.evidence)
        transactions.update(updated)
        return existing, updated
    evidence = work.evidence_for(entry.user_id).get(entry.evidence_id)
    kind = evidence.kind if evidence else EvidenceKind.UNKNOWN
    account_id = _mpesa_account(work, entry.user_id) if kind == EvidenceKind.MPESA_MESSAGE else None
    created = from_entry(entry, account_id, role_for(kind))
    transactions.add(created)
    return None, created


def _mpesa_account(work: UnitOfWork, user_id: UUID) -> UUID | None:
    accounts = work.money_accounts_for(user_id).all()
    return next((a.id for a in accounts if a.kind == MoneyAccountKind.MPESA), None)

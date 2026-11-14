from uuid import UUID

from jalada.modules.evidence.domain.evidence import EvidenceKind
from jalada.modules.ledger.domain.money_accounts import MoneyAccountKind
from jalada.unit_of_work import UnitOfWork


def account_for(work: UnitOfWork, user_id: UUID, kind: EvidenceKind) -> UUID | None:
    """The account a piece of evidence shows money moving on, when its kind says so. An
    M-Pesa message is about the user's M-Pesa account; anything else is not known yet."""
    if kind != EvidenceKind.MPESA_MESSAGE:
        return None
    accounts = work.money_accounts_for(user_id).all()
    return next((a.id for a in accounts if a.kind == MoneyAccountKind.MPESA), None)

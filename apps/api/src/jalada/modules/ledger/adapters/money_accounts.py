from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from jalada.modules.ledger.adapters.tables import MoneyAccountRow
from jalada.modules.ledger.domain.money_accounts import MoneyAccount, MoneyAccountKind


class SqlMoneyAccounts:
    """One user's money accounts. Every query filters by user."""

    def __init__(self, db: DbSession, user_id: UUID) -> None:
        self._db = db
        self._user_id = user_id

    def all(self) -> list[MoneyAccount]:
        query = (
            select(MoneyAccountRow)
            .where(MoneyAccountRow.user_id == self._user_id)
            .order_by(MoneyAccountRow.created_at, MoneyAccountRow.name)
        )
        return [_to_account(row) for row in self._db.scalars(query)]

    def add(self, account: MoneyAccount) -> None:
        if account.user_id != self._user_id:
            raise PermissionError("Account belongs to another user")
        self._db.add(
            MoneyAccountRow(
                id=account.id,
                user_id=account.user_id,
                kind=account.kind,
                name=account.name,
                tracked=account.tracked,
                created_at=account.created_at,
            )
        )
        self._db.flush()


def _to_account(row: MoneyAccountRow) -> MoneyAccount:
    return MoneyAccount(
        row.id, row.user_id, MoneyAccountKind(row.kind), row.name, row.tracked, row.created_at
    )

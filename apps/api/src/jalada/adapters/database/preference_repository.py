from uuid import UUID

from sqlalchemy import case, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session as DbSession

from jalada.adapters.database.tables import CounterpartyPreferenceRow
from jalada.domain.categories import Purpose
from jalada.pipeline.classifier import Preference


class SqlPreferenceRepository:
    def __init__(self, db: DbSession, user_id: UUID) -> None:
        self._db = db
        self._user_id = user_id

    def all(self) -> dict[str, Preference]:
        rows = self._db.scalars(
            select(CounterpartyPreferenceRow).where(
                CounterpartyPreferenceRow.user_id == self._user_id
            )
        )
        return {
            row.counterparty_key: Preference(row.category, Purpose(row.purpose), row.times_used)
            for row in rows
        }

    def remember(self, counterparty_key: str, category: str, purpose: Purpose) -> None:
        """Save the user's choice. Choosing the same again makes it count for more."""
        row = CounterpartyPreferenceRow
        statement = insert(row).values(
            user_id=self._user_id,
            counterparty_key=counterparty_key,
            category=category,
            purpose=purpose,
            times_used=1,
        )
        # In ON CONFLICT, the table's columns are the row already saved.
        same_choice = (row.category == category) & (row.purpose == purpose)
        self._db.execute(
            statement.on_conflict_do_update(
                index_elements=["user_id", "counterparty_key"],
                set_={
                    "category": category,
                    "purpose": purpose,
                    # A different choice starts counting again from one.
                    "times_used": case((same_choice, row.times_used + 1), else_=1),
                },
            )
        )

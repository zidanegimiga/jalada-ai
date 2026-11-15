from uuid import UUID

from sqlalchemy import Select, or_, select, update
from sqlalchemy.orm import Session as DbSession

from jalada.modules.ledger.adapters.suggestion_tables import MatchSuggestionRow
from jalada.modules.ledger.domain.suggestions import (
    MatchSuggestion,
    SuggestionKind,
    SuggestionStatus,
)


class SqlMatchSuggestions:
    """One user's suggested matches. Every query filters by user."""

    def __init__(self, db: DbSession, user_id: UUID) -> None:
        self._db = db
        self._user_id = user_id

    def add(self, suggestion: MatchSuggestion) -> None:
        self._check_owner(suggestion)
        self._db.add(
            MatchSuggestionRow(
                id=suggestion.id,
                user_id=suggestion.user_id,
                kind=suggestion.kind,
                payment_id=suggestion.payment_id,
                candidate_id=suggestion.candidate_id,
                score=suggestion.score,
                reasons=list(suggestion.reasons),
                status=suggestion.status,
                created_at=suggestion.created_at,
                decided_at=suggestion.decided_at,
            )
        )
        self._db.flush()

    def get(self, suggestion_id: UUID) -> MatchSuggestion | None:
        found = self._list(self._mine().where(MatchSuggestionRow.id == suggestion_id))
        return found[0] if found else None

    def involving(self, transaction_id: UUID) -> list[MatchSuggestion]:
        either_side = or_(
            MatchSuggestionRow.payment_id == transaction_id,
            MatchSuggestionRow.candidate_id == transaction_id,
        )
        return self._list(self._mine().where(either_side))

    def open(self) -> list[MatchSuggestion]:
        return self._list(self._mine().where(MatchSuggestionRow.status == SuggestionStatus.OPEN))

    def all(self) -> list[MatchSuggestion]:
        return self._list(self._mine())

    def decide(self, suggestion: MatchSuggestion) -> None:
        self._check_owner(suggestion)
        self._db.execute(
            update(MatchSuggestionRow)
            .where(
                MatchSuggestionRow.user_id == self._user_id,
                MatchSuggestionRow.id == suggestion.id,
            )
            .values(status=suggestion.status, decided_at=suggestion.decided_at)
        )

    def _mine(self) -> Select[MatchSuggestionRow]:
        return select(MatchSuggestionRow).where(MatchSuggestionRow.user_id == self._user_id)

    def _list(self, query: Select[MatchSuggestionRow]) -> list[MatchSuggestion]:
        order = (MatchSuggestionRow.created_at, MatchSuggestionRow.id)
        return [_to_suggestion(row) for row in self._db.scalars(query.order_by(*order))]

    def _check_owner(self, suggestion: MatchSuggestion) -> None:
        if suggestion.user_id != self._user_id:
            raise PermissionError("Suggestion belongs to another user")


def _to_suggestion(row: MatchSuggestionRow) -> MatchSuggestion:
    return MatchSuggestion(
        id=row.id,
        user_id=row.user_id,
        kind=SuggestionKind(row.kind),
        payment_id=row.payment_id,
        candidate_id=row.candidate_id,
        score=row.score,
        reasons=tuple(row.reasons),
        status=SuggestionStatus(row.status),
        created_at=row.created_at,
        decided_at=row.decided_at,
    )

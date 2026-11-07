from collections.abc import Callable
from uuid import UUID

from jalada.modules.accounts.domain.users import normalize_email
from jalada.modules.evidence.application.ports import EvidenceStore
from jalada.shared.errors import ConfirmationMismatch, NotSignedIn
from jalada.unit_of_work import UnitOfWork


class AccountDeletion:
    """Deletes a user and everything held about them. It cannot be undone."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork], store: EvidenceStore) -> None:
        self._unit_of_work = unit_of_work
        self._store = store

    def delete(self, user_id: UUID, typed_email: str) -> None:
        """`typed_email` must match the account's email, so a stray tap cannot delete it."""
        with self._unit_of_work() as work:
            user = work.users.get(user_id)
            evidence = work.evidence_for(user_id).all()
        if user is None:
            raise NotSignedIn
        if normalize_email(typed_email) != user.email:
            raise ConfirmationMismatch
        # Files first: if this stops halfway, the account still exists and can be deleted again.
        for item in evidence:
            self._store.delete(item.id, user_id)
        with self._unit_of_work() as work:
            work.jobs.discard_for(user_id)
            work.users.delete(user_id)
            work.commit()

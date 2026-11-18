from collections.abc import Callable
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.accounts.domain.consent import ConsentStatus, ModelConsent, holds
from jalada.unit_of_work import UnitOfWork


class ConsentToModels:
    """Asking, recording and withdrawing a person's agreement to have a model read their records.

    `notice` names the provider, where it is and its terms; None when no model is set up, and
    then there is nothing to agree to.
    """

    def __init__(
        self, unit_of_work: Callable[[], UnitOfWork], clock: Clock, notice: str | None
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._notice = notice

    def status(self, user_id: UUID) -> ConsentStatus:
        if self._notice is None:
            return ConsentStatus(required=False, given=False, notice="")
        with self._unit_of_work() as work:
            consent = work.model_consents.get(user_id)
        return ConsentStatus(True, holds(consent, self._notice), self._notice)

    def give(self, user_id: UUID) -> ConsentStatus:
        if self._notice is not None:
            with self._unit_of_work() as work:
                work.model_consents.give(ModelConsent(user_id, self._notice, self._clock.now()))
                work.commit()
        return self.status(user_id)

    def withdraw(self, user_id: UUID) -> ConsentStatus:
        with self._unit_of_work() as work:
            work.model_consents.withdraw(user_id)
            work.commit()
        return self.status(user_id)

    def allows(self, user_id: UUID) -> bool:
        """Whether this person's records may go to the model now."""
        status = self.status(user_id)
        return status.required and status.given

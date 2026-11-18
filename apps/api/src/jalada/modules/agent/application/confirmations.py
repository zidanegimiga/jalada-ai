from collections.abc import Callable, Mapping
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.agent.domain.proposals import ActionKind, ActionStatus, ProposedAction
from jalada.shared.errors import ActionClosed, ActionNotFound
from jalada.unit_of_work import UnitOfWork

# Makes one kind of change through the ledger's own use case, for the person who tapped.
Executor = Callable[[UUID, Mapping[str, str]], None]


class ActionConfirmations:
    """The person's answer to a suggested change. Confirming runs it; no model is asked again."""

    def __init__(
        self,
        unit_of_work: Callable[[], UnitOfWork],
        clock: Clock,
        executors: Mapping[ActionKind, Executor],
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._executors = executors

    def confirm(self, user_id: UUID, action_id: UUID) -> ProposedAction:
        """Raises ActionNotFound, ActionClosed, or whatever the ledger raises, such as
        InvalidEntry when the payment changed since the suggestion."""
        action = self._open(user_id, action_id)
        self._executors[action.kind](user_id, action.payload)
        return self._decide(user_id, action, ActionStatus.CONFIRMED)

    def decline(self, user_id: UUID, action_id: UUID) -> ProposedAction:
        return self._decide(user_id, self._open(user_id, action_id), ActionStatus.DECLINED)

    def _open(self, user_id: UUID, action_id: UUID) -> ProposedAction:
        with self._unit_of_work() as work:
            action = work.agent_actions_for(user_id).get(action_id)
        if action is None:
            raise ActionNotFound
        if action.status_at(self._clock.now()) != ActionStatus.PROPOSED:
            raise ActionClosed
        return action

    def _decide(
        self, user_id: UUID, action: ProposedAction, status: ActionStatus
    ) -> ProposedAction:
        decided = action.decided(status, self._clock.now())
        with self._unit_of_work() as work:
            work.agent_actions_for(user_id).save(decided)
            work.commit()
        return decided

from collections.abc import Callable
from uuid import UUID, uuid4

from jalada.core.ports import Clock
from jalada.modules.agent.application.tools import ToolContext
from jalada.modules.agent.domain.proposals import ActionKind, ActionStatus, ProposedAction
from jalada.unit_of_work import UnitOfWork


class ActionProposals:
    """Keeps a change the assistant suggests, to wait for the person. Changes nothing else."""

    def __init__(
        self,
        unit_of_work: Callable[[], UnitOfWork],
        clock: Clock,
        new_id: Callable[[], UUID] = uuid4,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._new_id = new_id

    def propose(
        self, context: ToolContext, kind: ActionKind, payload: dict[str, str], summary: str
    ) -> ProposedAction:
        if context.run_id is None or context.thread_id is None:
            raise ValueError("A change can only be suggested during a turn in a conversation")
        action = ProposedAction(
            self._new_id(),
            context.user_id,
            context.thread_id,
            context.run_id,
            kind,
            payload,
            summary,
            ActionStatus.PROPOSED,
            self._clock.now(),
        )
        with self._unit_of_work() as work:
            work.agent_actions_for(context.user_id).add(action)
            work.commit()
        return action

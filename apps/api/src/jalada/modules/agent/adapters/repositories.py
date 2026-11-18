from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Select, select, update
from sqlalchemy.orm import Session as DbSession

from jalada.modules.agent.adapters.tables import (
    AgentActionRow,
    AgentMessageRow,
    AgentRunRow,
    AgentStepRow,
    AgentThreadRow,
)
from jalada.modules.agent.application.ports import AgentRun
from jalada.modules.agent.domain.conversation import Message, Role, Thread
from jalada.modules.agent.domain.proposals import ActionKind, ActionStatus, ProposedAction
from jalada.modules.agent.domain.run import AgentStep, Outcome, StepKind
from jalada.modules.pipeline.domain.model import ModelUsage


class SqlThreads:
    """Every query is limited to one user's threads."""

    def __init__(self, db: DbSession, user_id: UUID) -> None:
        self._db = db
        self._user_id = user_id

    def add(self, thread: Thread) -> None:
        if thread.user_id != self._user_id:
            raise ValueError("A thread can only be added for its own user")
        self._db.add(
            AgentThreadRow(
                id=thread.id,
                user_id=thread.user_id,
                title=thread.title,
                created_at=thread.created_at,
                updated_at=thread.updated_at,
            )
        )
        self._db.flush()

    def get(self, thread_id: UUID) -> Thread | None:
        row = self._db.scalar(
            select(AgentThreadRow).where(
                AgentThreadRow.id == thread_id, AgentThreadRow.user_id == self._user_id
            )
        )
        return _thread(row) if row is not None else None

    def recent(self, limit: int) -> list[Thread]:
        rows = self._db.scalars(
            select(AgentThreadRow)
            .where(AgentThreadRow.user_id == self._user_id)
            .order_by(AgentThreadRow.updated_at.desc(), AgentThreadRow.id)
            .limit(limit)
        ).all()
        return [_thread(row) for row in rows]

    def touch(self, thread_id: UUID, at: datetime) -> None:
        self._db.execute(
            update(AgentThreadRow)
            .where(AgentThreadRow.id == thread_id, AgentThreadRow.user_id == self._user_id)
            .values(updated_at=at)
        )

    def add_message(self, thread_id: UUID, message: Message) -> None:
        if self.get(thread_id) is None:
            raise ValueError("No such thread for this user")
        self._db.add(
            AgentMessageRow(
                thread_id=thread_id,
                role=message.role,
                text=message.text,
                created_at=message.at,
                run_id=message.run_id,
            )
        )
        self._db.flush()

    def recent_messages(self, thread_id: UUID, limit: int) -> list[Message]:
        rows = self._db.scalars(
            select(AgentMessageRow)
            .join(AgentThreadRow, AgentThreadRow.id == AgentMessageRow.thread_id)
            .where(AgentThreadRow.id == thread_id, AgentThreadRow.user_id == self._user_id)
            .order_by(AgentMessageRow.id.desc())
            .limit(limit)
        ).all()
        return [
            Message(Role(row.role), row.text, row.created_at, row.run_id) for row in reversed(rows)
        ]


def _thread(row: AgentThreadRow) -> Thread:
    return Thread(row.id, row.user_id, row.title, row.created_at, row.updated_at)


class SqlAgentRuns:
    def __init__(self, db: DbSession) -> None:
        self._db = db

    def add(self, run: AgentRun) -> None:
        usage = sum((step.usage for step in run.steps), ModelUsage())
        self._db.add(
            AgentRunRow(
                id=run.id,
                user_id=run.user_id,
                thread_id=run.thread_id,
                outcome=run.outcome,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cost_usd=usage.cost_usd,
                started_at=run.started_at,
                finished_at=run.finished_at,
            )
        )
        self._db.flush()
        for position, step in enumerate(run.steps):
            self._db.add(
                AgentStepRow(
                    run_id=run.id,
                    position=position,
                    kind=step.kind,
                    name=step.name,
                    outcome=step.outcome,
                    input_tokens=step.usage.input_tokens,
                    output_tokens=step.usage.output_tokens,
                    cost_usd=step.usage.cost_usd,
                    duration_ms=step.duration_ms,
                )
            )

    def for_user(self, user_id: UUID) -> list[AgentRun]:
        runs = self._db.scalars(
            select(AgentRunRow)
            .where(AgentRunRow.user_id == user_id)
            .order_by(AgentRunRow.started_at)
        ).all()
        return [self._run(row) for row in runs]

    def _run(self, row: AgentRunRow) -> AgentRun:
        steps = self._db.scalars(
            select(AgentStepRow)
            .where(AgentStepRow.run_id == row.id)
            .order_by(AgentStepRow.position)
        ).all()
        return AgentRun(
            id=row.id,
            user_id=row.user_id,
            thread_id=row.thread_id,
            outcome=Outcome(row.outcome),
            steps=tuple(
                AgentStep(
                    StepKind(step.kind),
                    step.name,
                    step.outcome,
                    step.duration_ms,
                    ModelUsage(step.input_tokens, step.output_tokens, Decimal(step.cost_usd)),
                )
                for step in steps
            ),
            started_at=row.started_at,
            finished_at=row.finished_at,
        )


class SqlActions:
    """Every query is limited to one user's actions."""

    def __init__(self, db: DbSession, user_id: UUID) -> None:
        self._db = db
        self._user_id = user_id

    def add(self, action: ProposedAction) -> None:
        if action.user_id != self._user_id:
            raise ValueError("An action can only be added for its own user")
        self._db.add(
            AgentActionRow(
                id=action.id,
                user_id=action.user_id,
                thread_id=action.thread_id,
                run_id=action.run_id,
                kind=action.kind,
                payload=action.payload,
                summary=action.summary,
                status=action.status,
                created_at=action.created_at,
                decided_at=action.decided_at,
            )
        )
        self._db.flush()

    def get(self, action_id: UUID) -> ProposedAction | None:
        row = self._db.scalar(self._mine().where(AgentActionRow.id == action_id))
        return _action(row) if row is not None else None

    def save(self, action: ProposedAction) -> None:
        self._db.execute(
            update(AgentActionRow)
            .where(AgentActionRow.id == action.id, AgentActionRow.user_id == self._user_id)
            .values(status=action.status, decided_at=action.decided_at)
        )

    def for_run(self, run_id: UUID) -> list[ProposedAction]:
        query = self._mine().where(AgentActionRow.run_id == run_id)
        return [_action(row) for row in self._db.scalars(query.order_by(AgentActionRow.created_at))]

    def for_thread(self, thread_id: UUID) -> list[ProposedAction]:
        query = self._mine().where(AgentActionRow.thread_id == thread_id)
        return [_action(row) for row in self._db.scalars(query.order_by(AgentActionRow.created_at))]

    def _mine(self) -> Select[AgentActionRow]:
        return select(AgentActionRow).where(AgentActionRow.user_id == self._user_id)


def _action(row: AgentActionRow) -> ProposedAction:
    return ProposedAction(
        id=row.id,
        user_id=row.user_id,
        thread_id=row.thread_id,
        run_id=row.run_id,
        kind=ActionKind(row.kind),
        payload=dict(row.payload),
        summary=row.summary,
        status=ActionStatus(row.status),
        created_at=row.created_at,
        decided_at=row.decided_at,
    )

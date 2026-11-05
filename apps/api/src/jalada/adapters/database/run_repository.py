from dataclasses import asdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from jalada.adapters.database.tables import PipelineRunRow, PipelineStepRow
from jalada.application.ports import PipelineRun
from jalada.pipeline.run_types import StepRecord


class SqlRunRepository:
    """The trace of each pipeline run, so any entry can be explained later."""

    def __init__(self, db: DbSession) -> None:
        self._db = db

    def add(self, run: PipelineRun, steps: list[StepRecord]) -> None:
        self._db.add(PipelineRunRow(**asdict(run)))
        self._db.flush()
        self._db.add_all(PipelineStepRow(run_id=run.id, **asdict(step)) for step in steps)

    def for_user(self, user_id: UUID) -> list[tuple[PipelineRun, list[StepRecord]]]:
        runs = self._db.scalars(
            select(PipelineRunRow)
            .where(PipelineRunRow.user_id == user_id)
            .order_by(PipelineRunRow.started_at)
        ).all()
        steps = self._db.scalars(
            select(PipelineStepRow)
            .where(PipelineStepRow.run_id.in_([run.id for run in runs]))
            .order_by(PipelineStepRow.id)
        ).all()
        return [
            (
                _to_run(run),
                [_to_step(step) for step in steps if step.run_id == run.id],
            )
            for run in runs
        ]


def _to_run(row: PipelineRunRow) -> PipelineRun:
    return PipelineRun(
        row.id,
        row.user_id,
        row.evidence_id,
        row.outcome,
        row.attempts,
        row.input_tokens,
        row.output_tokens,
        row.cost_usd,
        row.started_at,
        row.finished_at,
    )


def _to_step(row: PipelineStepRow) -> StepRecord:
    return StepRecord(row.step, row.attempt, row.input, row.output, row.verdict, row.duration_ms)

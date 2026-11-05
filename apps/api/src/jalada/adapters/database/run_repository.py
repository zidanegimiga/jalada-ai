from dataclasses import asdict

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

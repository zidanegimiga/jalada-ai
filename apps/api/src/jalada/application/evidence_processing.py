import uuid
from collections.abc import Callable
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from jalada.application.ports import Clock, EvidenceStore, PipelineRun, TextReader, UnitOfWork
from jalada.domain.entries import Entry, EntryKind, EntryStatus
from jalada.domain.evidence import Evidence, EvidenceKind, EvidenceStatus
from jalada.domain.extraction import Classification, Extraction
from jalada.pipeline.process import Budget, PipelineResult, run_pipeline

STATUS_FOR_OUTCOME = {
    "proposed": EvidenceStatus.PROPOSED,
    "needs_review": EvidenceStatus.NEEDS_REVIEW,
    "duplicate": EvidenceStatus.DUPLICATE,
}


class EvidenceProcessor:
    """Runs one piece of evidence through the pipeline and saves what it found."""

    def __init__(
        self,
        unit_of_work: Callable[[], UnitOfWork],
        store: EvidenceStore,
        reader: TextReader,
        clock: Clock,
        budget: Budget,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._store = store
        self._reader = reader
        self._clock = clock
        self._budget = budget

    def handle(self, payload: dict[str, Any]) -> None:
        self.process(UUID(payload["user_id"]), UUID(payload["evidence_id"]))

    def give_up(self, payload: dict[str, Any]) -> None:
        user_id, evidence_id = UUID(payload["user_id"]), UUID(payload["evidence_id"])
        with self._unit_of_work() as work:
            work.evidence_for(user_id).set_outcome(
                evidence_id, EvidenceKind.UNKNOWN, EvidenceStatus.FAILED
            )
            work.commit()

    def process(self, user_id: UUID, evidence_id: UUID) -> str:
        started = self._clock.now()
        with self._unit_of_work() as work:
            evidence = work.evidence_for(user_id).get(evidence_id)
            preferences = work.preferences_for(user_id).all()
        if evidence is None:
            return "missing"
        data = self._store.get(evidence.id, user_id, evidence.encryption_key_id)
        text = self._reader.read(evidence.content_type, data)
        result = run_pipeline(
            text,
            evidence.content_type,
            preferences,
            is_duplicate=lambda extraction: self._is_duplicate(user_id, extraction),
            today=started.date(),
            budget=self._budget,
        )
        self._save(evidence, result, started)
        return result.outcome

    def _is_duplicate(self, user_id: UUID, extraction: Extraction) -> bool:
        with self._unit_of_work() as work:
            entries = work.entries_for(user_id)
            if extraction.mpesa_code and entries.has_mpesa_code(extraction.mpesa_code):
                return True
            serial = extraction.certificate_serial
            return bool(serial and entries.has_certificate_serial(serial))

    def _save(self, evidence: Evidence, result: PipelineResult, started: datetime) -> None:
        run = PipelineRun(
            id=uuid.uuid4(),
            user_id=evidence.user_id,
            evidence_id=evidence.id,
            outcome=result.outcome,
            attempts=result.attempts,
            input_tokens=0,
            output_tokens=0,
            cost_usd=Decimal(0),
            started_at=started,
            finished_at=self._clock.now(),
        )
        with self._unit_of_work() as work:
            work.runs.add(run, result.steps)
            if result.extraction and result.classification and result.outcome != "duplicate":
                entry = self._entry(evidence, run, result, result.extraction, result.classification)
                work.entries_for(evidence.user_id).add(entry)
            status = STATUS_FOR_OUTCOME[result.outcome]
            work.evidence_for(evidence.user_id).set_outcome(evidence.id, result.kind, status)
            work.commit()

    def _entry(
        self,
        evidence: Evidence,
        run: PipelineRun,
        result: PipelineResult,
        extraction: Extraction,
        classification: Classification,
    ) -> Entry:
        is_certificate = extraction.kind == EvidenceKind.WITHHOLDING_CERTIFICATE
        return Entry(
            id=uuid.uuid4(),
            user_id=evidence.user_id,
            evidence_id=evidence.id,
            run_id=run.id,
            kind=EntryKind.WITHHOLDING_CERTIFICATE if is_certificate else EntryKind.TRANSACTION,
            status=EntryStatus.PROPOSED
            if result.outcome == "proposed"
            else EntryStatus.NEEDS_REVIEW,
            occurred_on=extraction.occurred_on,
            direction=extraction.direction,
            amount_cents=extraction.amount_cents,
            counterparty=extraction.counterparty,
            reference=extraction.reference,
            mpesa_code=extraction.mpesa_code,
            certificate_serial=extraction.certificate_serial,
            tax_withheld_cents=extraction.tax_withheld_cents,
            purpose=classification.purpose,
            category=classification.category,
            confidence=classification.confidence,
            created_at=self._clock.now(),
        )

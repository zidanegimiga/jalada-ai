import logging
import uuid
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from typing import Any
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.evidence.application.ports import EvidenceStore
from jalada.modules.evidence.domain.evidence import Evidence, EvidenceKind, EvidenceStatus
from jalada.modules.ledger.application import history
from jalada.modules.ledger.application.evidence_accounts import account_for
from jalada.modules.ledger.application.matching import link_exact_match
from jalada.modules.ledger.domain.audit import Actor, AuditAction
from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.ledger.domain.transactions import as_entry
from jalada.modules.pipeline.application.ports import PipelineRun, ProcessingNotifier, TextReader
from jalada.modules.pipeline.application.proposals import proposed_certificate, proposed_payment
from jalada.modules.pipeline.domain.extraction import Classification, Extraction
from jalada.modules.pipeline.domain.model import ImageInput, LanguageModel
from jalada.modules.pipeline.domain.process import run_pipeline
from jalada.modules.pipeline.domain.run_types import Budget, EvidenceInput, PipelineResult
from jalada.shared.dates import kenyan_date
from jalada.unit_of_work import UnitOfWork

logger = logging.getLogger("jalada.processing")

STATUS_FOR_OUTCOME = {
    "proposed": EvidenceStatus.PROPOSED,
    "needs_review": EvidenceStatus.NEEDS_REVIEW,
    "duplicate": EvidenceStatus.DUPLICATE,
    "linked": EvidenceStatus.LINKED,
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
        model: LanguageModel | None = None,
        notifier: ProcessingNotifier | None = None,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._store = store
        self._reader = reader
        self._clock = clock
        self._budget = budget
        self._model = model
        self._notifier = notifier

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
        is_photo = evidence.content_type.startswith("image/")
        given = EvidenceInput(
            text=self._reader.read(evidence.content_type, data),
            content_type=evidence.content_type,
            image=ImageInput(data, evidence.content_type) if is_photo else None,
        )
        result = run_pipeline(
            given,
            preferences,
            is_duplicate=lambda extraction: self._is_duplicate(user_id, extraction),
            today=kenyan_date(started),
            budget=self._budget,
            model=self._model,
        )
        outcome, entry = self._save(evidence, result, started)
        self._notify(evidence, outcome, entry, _reasons(result))
        return outcome

    def _notify(
        self, evidence: Evidence, outcome: str, entry: Entry | None, reasons: list[str]
    ) -> None:
        """Telling the user is a courtesy. If it fails, the saved result still stands."""
        if self._notifier is None:
            return
        try:
            self._notifier.notify(evidence, outcome, entry, reasons)
        except Exception as error:
            logger.warning("notifying about evidence failed with %s", type(error).__name__)

    def _is_duplicate(self, user_id: UUID, extraction: Extraction) -> bool:
        with self._unit_of_work() as work:
            code = extraction.mpesa_code
            if code and work.transactions_for(user_id).with_payment_code(code):
                return True
            serial = extraction.certificate_serial
            return bool(serial and work.entries_for(user_id).has_certificate_serial(serial))

    def _save(
        self, evidence: Evidence, result: PipelineResult, started: datetime
    ) -> tuple[str, Entry | None]:
        """Saves the run and what it found. Returns the outcome, which is "linked" when a
        duplicate turned out to be another copy of a payment already recorded."""
        run = PipelineRun(
            id=uuid.uuid4(),
            user_id=evidence.user_id,
            evidence_id=evidence.id,
            outcome=result.outcome,
            attempts=result.attempts,
            input_tokens=result.usage.input_tokens,
            output_tokens=result.usage.output_tokens,
            cost_usd=result.usage.cost_usd,
            started_at=started,
            finished_at=self._clock.now(),
        )
        extraction, classification = result.extraction, result.classification
        with self._unit_of_work() as work:
            linked = None
            if extraction and result.outcome == "duplicate":
                linked = link_exact_match(
                    work,
                    evidence,
                    extraction.kind,
                    extraction.mpesa_code,
                    extraction.amount_cents,
                    extraction.direction,
                    extraction.occurred_on,
                    run.finished_at,
                )
            if linked:
                run = replace(run, outcome="linked")
            # Saved before what it found, which points back at it.
            work.runs.add(run, result.steps)
            found = as_entry(linked) if linked else None
            if extraction and classification and result.outcome != "duplicate":
                ready = result.outcome == "proposed"
                found = self._propose(work, evidence, run, ready, extraction, classification)
            status = STATUS_FOR_OUTCOME[run.outcome]
            work.evidence_for(evidence.user_id).set_outcome(evidence.id, result.kind, status)
            work.commit()
        return run.outcome, found

    @staticmethod
    def _propose(
        work: UnitOfWork,
        evidence: Evidence,
        run: PipelineRun,
        ready: bool,
        extraction: Extraction,
        classification: Classification,
    ) -> Entry:
        """Saves the payment or certificate the pipeline read, with its audit event. Returns
        it in the shape of an entry, for the message back to the user."""
        now = run.finished_at
        if extraction.kind == EvidenceKind.WITHHOLDING_CERTIFICATE:
            certificate = proposed_certificate(
                evidence, run, ready, extraction, classification, now
            )
            work.entries_for(evidence.user_id).add(certificate)
            history.record_entry(work, None, certificate, Actor.PIPELINE, AuditAction.PROPOSED, now)
            return certificate
        account_id = account_for(work, evidence.user_id, extraction.kind)
        payment = proposed_payment(
            evidence, run, ready, extraction, classification, account_id, now
        )
        work.transactions_for(evidence.user_id).add(payment)
        history.record_transaction(work, None, payment, Actor.PIPELINE, AuditAction.PROPOSED, now)
        return as_entry(payment)


def _reasons(result: PipelineResult) -> list[str]:
    verdict = result.verdict
    return verdict.problems + verdict.review_reasons if verdict else []

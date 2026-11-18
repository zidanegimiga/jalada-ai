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
from jalada.modules.ledger.application.matching import link_exact_match
from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.ledger.domain.transactions import Transaction, as_entry
from jalada.modules.pipeline.application.ports import PipelineRun, ProcessingNotifier, TextReader
from jalada.modules.pipeline.application.proposals import waits_as_candidate
from jalada.modules.pipeline.application.proposing import MAY_MATCH, save_proposal
from jalada.modules.pipeline.domain.extraction import Extraction
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
    "candidate": EvidenceStatus.CANDIDATE,
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
        may_use_model: Callable[[UUID], bool] = lambda _: True,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._store = store
        self._reader = reader
        self._clock = clock
        self._budget = budget
        self._model = model
        self._notifier = notifier
        # Whether this person agreed to have a model read their records (decision 0026).
        # Without it, rules and OCR alone read the evidence, as with no model at all.
        self._may_use_model = may_use_model

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
            accounts = work.money_accounts_for(user_id).all()
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
            model=self._model if self._may_use_model(user_id) else None,
            own_accounts=[a.identifiers for a in accounts if a.identifiers],
        )
        outcome, entry, may_match = self._save(evidence, result, started)
        reasons = _reasons(result) + ([MAY_MATCH] if may_match else [])
        self._notify(evidence, outcome, entry, reasons)
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
    ) -> tuple[str, Entry | None, bool]:
        """Saves the run and what it found. Returns the outcome, which is "linked" when a
        duplicate turned out to be another copy of a payment already recorded, and
        "candidate" for a receipt waiting for its payment. Then what was found, and whether
        it may be the same purchase as something already recorded."""
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
            linked = self._link_copy(work, evidence, result, run.finished_at)
            run = replace(run, outcome=_outcome(result, linked is not None))
            # Saved before what it found, which points back at it.
            work.runs.add(run, result.steps)
            found, may_match = (as_entry(linked) if linked else None), False
            if extraction and classification and result.outcome != "duplicate":
                ready = result.outcome == "proposed"
                proposal = save_proposal(work, evidence, run, ready, extraction, classification)
                found, may_match = proposal.entry, proposal.may_match
            status = STATUS_FOR_OUTCOME[run.outcome]
            work.evidence_for(evidence.user_id).set_outcome(evidence.id, result.kind, status)
            work.commit()
        return run.outcome, found, may_match

    @staticmethod
    def _link_copy(
        work: UnitOfWork, evidence: Evidence, result: PipelineResult, now: datetime
    ) -> Transaction | None:
        """For a duplicate: the payment it is another copy of, once linked to it."""
        extraction = result.extraction
        if extraction is None or result.outcome != "duplicate":
            return None
        return link_exact_match(
            work,
            evidence,
            extraction.kind,
            extraction.mpesa_code,
            extraction.amount_cents,
            extraction.direction,
            extraction.occurred_on,
            now,
        )


def _outcome(result: PipelineResult, linked: bool) -> str:
    if linked:
        return "linked"
    extraction = result.extraction
    if result.outcome != "duplicate" and extraction and waits_as_candidate(extraction):
        return "candidate"
    return result.outcome


def _reasons(result: PipelineResult) -> list[str]:
    verdict = result.verdict
    return verdict.problems + verdict.review_reasons if verdict else []

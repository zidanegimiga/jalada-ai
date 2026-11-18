"""Builds the pipeline module's use cases from the pieces the composition root shares."""

from collections.abc import Callable
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.evidence.application.ports import EvidenceStore
from jalada.modules.pipeline.adapters.text.ocr import TesseractOcr
from jalada.modules.pipeline.adapters.text.reader import EvidenceTextReader
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.application.ports import ProcessingNotifier
from jalada.modules.pipeline.domain.model import LanguageModel
from jalada.modules.pipeline.domain.run_types import Budget
from jalada.unit_of_work import UnitOfWork


def build_evidence_processor(
    unit_of_work: Callable[[], UnitOfWork],
    store: EvidenceStore,
    clock: Clock,
    budget: Budget,
    model: LanguageModel | None,
    notifier: ProcessingNotifier | None,
    may_use_model: Callable[[UUID], bool] = lambda _: True,
) -> EvidenceProcessor:
    return EvidenceProcessor(
        unit_of_work=unit_of_work,
        store=store,
        reader=EvidenceTextReader(TesseractOcr()),
        clock=clock,
        budget=budget,
        model=model,
        notifier=notifier,
        may_use_model=may_use_model,
    )

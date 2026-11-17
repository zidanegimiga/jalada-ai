"""Builds the evidence module's use cases from the pieces the composition root shares."""

from collections.abc import Callable

from jalada.core.ports import Clock
from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.application.ports import EvidenceStore
from jalada.unit_of_work import UnitOfWork


def build_evidence(
    unit_of_work: Callable[[], UnitOfWork], store: EvidenceStore, clock: Clock
) -> EvidenceCapture:
    return EvidenceCapture(unit_of_work=unit_of_work, store=store, clock=clock)

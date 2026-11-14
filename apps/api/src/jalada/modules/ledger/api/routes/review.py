from uuid import UUID

from fastapi import APIRouter, status

from jalada.dependencies import CurrentUser, ServicesDependency
from jalada.modules.ledger.api.schemas.entries import (
    CorrectionRequest,
    EntryResponse,
    ReviewItemResponse,
    ReviewQueue,
)

router = APIRouter(tags=["review"])


@router.get("/v1/review")
def read_review_queue(user: CurrentUser, services: ServicesDependency) -> ReviewQueue:
    items = services.review.queue(user.id)
    return ReviewQueue(items=[ReviewItemResponse.from_item(item) for item in items])


@router.post("/v1/entries/{entry_id}/confirm")
def confirm_entry(entry_id: UUID, user: CurrentUser, services: ServicesDependency) -> EntryResponse:
    return EntryResponse.from_entry(services.review.confirm(user.id, entry_id))


@router.patch("/v1/entries/{entry_id}")
def correct_entry(
    entry_id: UUID, body: CorrectionRequest, user: CurrentUser, services: ServicesDependency
) -> EntryResponse:
    """Change what the pipeline got wrong, and confirm the entry in the same step."""
    entry = services.review.confirm(user.id, entry_id, body.to_correction())
    return EntryResponse.from_entry(entry)


@router.post("/v1/evidence/{evidence_id}/entry", status_code=status.HTTP_201_CREATED)
def enter_by_hand(
    evidence_id: UUID, body: CorrectionRequest, user: CurrentUser, services: ServicesDependency
) -> EntryResponse:
    entry = services.review.enter_by_hand(user.id, evidence_id, body.to_correction())
    return EntryResponse.from_entry(entry)


@router.post("/v1/evidence/{evidence_id}/not-a-transaction", status_code=status.HTTP_204_NO_CONTENT)
def mark_not_a_transaction(
    evidence_id: UUID, user: CurrentUser, services: ServicesDependency
) -> None:
    """For evidence that does not record money moving, such as a balance message."""
    services.review.mark_not_a_transaction(user.id, evidence_id)

from typing import Any
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from jalada.dependencies import CurrentUser, ServicesDependency
from jalada.modules.ledger.api.schemas.entries import (
    ChangedElsewhereResponse,
    ConfirmAllRequest,
    ConfirmAllResponse,
    ConfirmRequest,
    CorrectionRequest,
    EntryResponse,
    ErrorDetail,
    ReviewItemResponse,
    ReviewQueue,
)
from jalada.modules.ledger.domain.versions import ChangedElsewhere

router = APIRouter(tags=["review"])

CHANGED_ELSEWHERE: dict[int | str, dict[str, Any]] = {409: {"model": ChangedElsewhereResponse}}


def changed_elsewhere(conflict: ChangedElsewhere) -> JSONResponse:
    body = ChangedElsewhereResponse(
        error=ErrorDetail(
            code="changed_elsewhere",
            message="This entry changed since you edited it. Check it and choose what to keep.",
        ),
        current=EntryResponse.from_entry(conflict.current),
    )
    return JSONResponse(body.model_dump(mode="json"), status_code=409)


@router.get("/v1/review")
def read_review_queue(user: CurrentUser, services: ServicesDependency) -> ReviewQueue:
    items = services.review.queue(user.id)
    return ReviewQueue(items=[ReviewItemResponse.from_item(item) for item in items])


@router.post(
    "/v1/entries/{entry_id}/confirm", response_model=EntryResponse, responses=CHANGED_ELSEWHERE
)
def confirm_entry(
    entry_id: UUID,
    user: CurrentUser,
    services: ServicesDependency,
    body: ConfirmRequest | None = None,
) -> EntryResponse | JSONResponse:
    try:
        entry = services.review.confirm(user.id, entry_id, based_on=body.version if body else None)
    except ChangedElsewhere as conflict:
        return changed_elsewhere(conflict)
    return EntryResponse.from_entry(entry)


@router.post("/v1/review/confirm-all")
def confirm_all(
    body: ConfirmAllRequest, user: CurrentUser, services: ServicesDependency
) -> ConfirmAllResponse:
    """Confirms the listed payments that are ready to confirm. The rest are skipped."""
    entries = services.review.confirm_all(user.id, body.entry_ids)
    return ConfirmAllResponse(confirmed=[EntryResponse.from_entry(entry) for entry in entries])


@router.patch("/v1/entries/{entry_id}", response_model=EntryResponse, responses=CHANGED_ELSEWHERE)
def correct_entry(
    entry_id: UUID, body: CorrectionRequest, user: CurrentUser, services: ServicesDependency
) -> EntryResponse | JSONResponse:
    """Change what the pipeline got wrong, and confirm the entry in the same step."""
    try:
        entry = services.review.confirm(user.id, entry_id, body.to_correction(), body.version)
    except ChangedElsewhere as conflict:
        return changed_elsewhere(conflict)
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


@router.delete(
    "/v1/evidence/{evidence_id}/not-a-transaction", status_code=status.HTTP_204_NO_CONTENT
)
def put_back(evidence_id: UUID, user: CurrentUser, services: ServicesDependency) -> None:
    """Takes back "Not a transaction". The evidence goes back to where it was."""
    services.review.put_back(user.id, evidence_id)

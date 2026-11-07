from uuid import UUID

from fastapi import APIRouter, Request, Response, UploadFile, status

from jalada.dependencies import CurrentUser, ServicesDependency
from jalada.modules.evidence.api.schemas.evidence import (
    EvidenceList,
    EvidenceResponse,
    PasteRequest,
)
from jalada.modules.evidence.application.evidence_capture import Captured
from jalada.modules.evidence.domain.evidence import MAX_FILE_BYTES, EvidenceSource
from jalada.shared.errors import FileTooLarge
from jalada.shared.http.errors import TooManyAttempts

router = APIRouter(tags=["evidence"])

# Room for multipart headers around the file itself.
MAX_REQUEST_BYTES = MAX_FILE_BYTES + 64 * 1024


def _respond(captured: Captured, response: Response) -> EvidenceResponse:
    # 201 for new evidence, 200 when the same thing was already captured.
    response.status_code = status.HTTP_200_OK if captured.duplicate else status.HTTP_201_CREATED
    return EvidenceResponse.from_evidence(captured.evidence, captured.duplicate)


def _check_rate(services: ServicesDependency, user: CurrentUser) -> None:
    if not services.upload_limiter.allow(f"user:{user.id}"):
        raise TooManyAttempts


@router.post("/v1/evidence", status_code=status.HTTP_201_CREATED)
def upload_evidence(
    file: UploadFile,
    request: Request,
    response: Response,
    user: CurrentUser,
    services: ServicesDependency,
) -> EvidenceResponse:
    if int(request.headers.get("content-length", 0)) > MAX_REQUEST_BYTES:
        raise FileTooLarge
    _check_rate(services, user)
    data = file.file.read(MAX_FILE_BYTES + 1)
    captured = services.evidence.capture_file(user.id, data, EvidenceSource.WEB_UPLOAD)
    return _respond(captured, response)


@router.post("/v1/evidence/text", status_code=status.HTTP_201_CREATED)
def paste_evidence(
    body: PasteRequest, response: Response, user: CurrentUser, services: ServicesDependency
) -> EvidenceResponse:
    _check_rate(services, user)
    captured = services.evidence.capture_text(user.id, body.text, EvidenceSource.WEB_PASTE)
    return _respond(captured, response)


@router.get("/v1/evidence")
def list_evidence(user: CurrentUser, services: ServicesDependency) -> EvidenceList:
    items = services.evidence.list_recent(user.id)
    return EvidenceList(items=[EvidenceResponse.from_evidence(item) for item in items])


@router.get("/v1/evidence/{evidence_id}")
def read_evidence(
    evidence_id: UUID, user: CurrentUser, services: ServicesDependency
) -> EvidenceResponse:
    return EvidenceResponse.from_evidence(services.evidence.get(user.id, evidence_id))


@router.get("/v1/evidence/{evidence_id}/file")
def read_evidence_file(
    evidence_id: UUID, user: CurrentUser, services: ServicesDependency
) -> Response:
    evidence, data = services.evidence.read_original(user.id, evidence_id)
    return Response(
        content=data,
        media_type=evidence.content_type,
        headers={
            "Content-Disposition": "inline",
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )

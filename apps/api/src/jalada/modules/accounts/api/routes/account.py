import tempfile
from collections.abc import Iterator
from typing import IO

from fastapi import APIRouter, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from jalada.dependencies import CurrentUser, ServicesDependency
from jalada.modules.accounts.api.session_cookie import SESSION_COOKIE
from jalada.shared.http.errors import TooManyAttempts

router = APIRouter(tags=["account"])

# Small exports stay in memory; bigger ones spill to a temporary file that is removed after.
IN_MEMORY_BYTES = 20 * 1024 * 1024
CHUNK_BYTES = 64 * 1024


def _chunks(file: IO[bytes]) -> Iterator[bytes]:
    try:
        while chunk := file.read(CHUNK_BYTES):
            yield chunk
    finally:
        file.close()


@router.get("/v1/account/export")
def export_account(user: CurrentUser, services: ServicesDependency) -> StreamingResponse:
    """Everything held about the signed-in user, with the original files, as one download."""
    if not services.upload_limiter.allow(f"export:{user.id}"):
        raise TooManyAttempts
    export = services.account_export
    file = tempfile.SpooledTemporaryFile(max_size=IN_MEMORY_BYTES)  # noqa: SIM115 (closed by _chunks)
    export.write(user.id, file)
    file.seek(0)
    return StreamingResponse(
        _chunks(file),
        media_type=export.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="jalada-data.{export.extension}"',
            "Cache-Control": "private, no-store",
        },
    )


class DeleteAccountRequest(BaseModel):
    # The account's email, typed again to confirm.
    email: str = Field(max_length=320)


@router.delete("/v1/account", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    body: DeleteAccountRequest, response: Response, user: CurrentUser, services: ServicesDependency
) -> None:
    """Deletes the signed-in user and everything held about them, then signs them out."""
    if not services.sign_in_limiter.allow(f"delete:{user.id}"):
        raise TooManyAttempts
    services.account_deletion.delete(user.id, body.email)
    response.delete_cookie(SESSION_COOKIE)

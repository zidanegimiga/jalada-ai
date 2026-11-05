import tempfile
from collections.abc import Iterator
from typing import IO

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from jalada.api.dependencies import CurrentUser, ServicesDependency
from jalada.api.errors import TooManyAttempts

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

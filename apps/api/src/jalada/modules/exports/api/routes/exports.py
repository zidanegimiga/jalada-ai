from typing import Annotated

from fastapi import APIRouter, Path, Response

from jalada.dependencies import CurrentUser, ServicesDependency

router = APIRouter(tags=["export"])


@router.get("/v1/exports/{year}.xlsx")
def download_tax_year(
    year: Annotated[int, Path(ge=2000, le=2100)],
    user: CurrentUser,
    services: ServicesDependency,
) -> Response:
    """The tax-year workbook, built from confirmed entries on request and never stored."""
    export = services.tax_year_export
    return Response(
        content=export.workbook(user.id, year),
        media_type=export.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="jalada-{year}.xlsx"',
            "Cache-Control": "private, no-store",
        },
    )

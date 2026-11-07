from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from jalada.dependencies import CurrentUser, ServicesDependency
from jalada.modules.ledger.api.schemas.ledger import (
    CategoryResponse,
    LedgerResponse,
    MonthResponse,
    YearResponse,
    all_categories,
    decode_position,
)
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.ledger import LedgerFilter

router = APIRouter(tags=["ledger"])


@router.get("/v1/entries")
def read_ledger(
    user: CurrentUser,
    services: ServicesDependency,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
    direction: Direction | None = None,
    purpose: Purpose | None = None,
    category: str | None = None,
    cursor: str | None = None,
) -> LedgerResponse:
    """Confirmed entries, newest first. Pass `next_cursor` back as `cursor` for the next page."""
    filters = LedgerFilter(start, end, direction, purpose, category)
    after = decode_position(cursor) if cursor else None
    return LedgerResponse.from_page(services.ledger.page(user.id, filters, after))


@router.get("/v1/summary/monthly")
def read_monthly_summary(
    user: CurrentUser,
    services: ServicesDependency,
    year: Annotated[int, Query(ge=2000, le=2100)],
) -> YearResponse:
    months = services.ledger.year(user.id, year)
    return YearResponse(year=year, months=[MonthResponse.from_summary(m) for m in months])


@router.get("/v1/categories")
def read_categories() -> list[CategoryResponse]:
    return all_categories()

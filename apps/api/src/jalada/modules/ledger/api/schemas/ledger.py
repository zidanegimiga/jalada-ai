import base64
import binascii
from datetime import date
from uuid import UUID

from pydantic import BaseModel

from jalada.modules.ledger.api.schemas.entries import EntryResponse
from jalada.modules.ledger.application.ledger import LedgerPage
from jalada.modules.ledger.domain.categories import CATEGORIES, Direction, Purpose
from jalada.modules.ledger.domain.ledger import LedgerPosition, MonthSummary


def encode_position(position: LedgerPosition) -> str:
    raw = f"{position.occurred_on.isoformat()}|{position.entry_id}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_position(cursor: str) -> LedgerPosition | None:
    """None for a cursor that was not made by `encode_position`."""
    try:
        day, entry_id = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
        return LedgerPosition(date.fromisoformat(day), UUID(entry_id))
    except (ValueError, binascii.Error):
        return None


class LedgerResponse(BaseModel):
    items: list[EntryResponse]
    next_cursor: str | None

    @classmethod
    def from_page(cls, page: LedgerPage) -> "LedgerResponse":
        cursor = encode_position(page.next_position) if page.next_position else None
        links = page.certificate_payments
        items = [
            EntryResponse.from_entry(e).model_copy(
                update={
                    "linked_certificate_id": links.get(e.id),
                    "linked_payment_ids": [p for p, c in links.items() if c == e.id],
                }
            )
            for e in page.entries
        ]
        return cls(items=items, next_cursor=cursor)


class MonthResponse(BaseModel):
    month: int
    in_business_cents: int
    in_personal_cents: int
    out_business_cents: int
    out_personal_cents: int

    @classmethod
    def from_summary(cls, summary: MonthSummary) -> "MonthResponse":
        def total(side: dict[Purpose, int], purpose: Purpose) -> int:
            return side.get(purpose, 0)

        return cls(
            month=summary.month,
            in_business_cents=total(summary.money_in, Purpose.BUSINESS),
            in_personal_cents=total(summary.money_in, Purpose.PERSONAL),
            out_business_cents=total(summary.money_out, Purpose.BUSINESS),
            out_personal_cents=total(summary.money_out, Purpose.PERSONAL),
        )


class YearResponse(BaseModel):
    year: int
    months: list[MonthResponse]


class CategoryResponse(BaseModel):
    slug: str
    name: str
    direction: Direction
    purpose: Purpose


def all_categories() -> list[CategoryResponse]:
    return [
        CategoryResponse(slug=c.slug, name=c.name, direction=c.direction, purpose=c.purpose)
        for c in CATEGORIES.values()
    ]

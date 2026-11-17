from pydantic import BaseModel

from jalada.modules.ledger.domain.categories import CATEGORIES, Direction
from jalada.modules.ledger.domain.ledger import CategoryTotal


class CategoryTotalResponse(BaseModel):
    direction: Direction
    # None for money confirmed without a category.
    category: str | None
    name: str
    cents: int

    @classmethod
    def from_total(cls, total: CategoryTotal) -> "CategoryTotalResponse":
        known = CATEGORIES.get(total.category) if total.category else None
        return cls(
            direction=total.direction,
            category=total.category,
            name=known.name if known else "Not categorised",
            cents=total.cents,
        )


class CategoryTotalsResponse(BaseModel):
    """Totals per category between two dates, largest first."""

    totals: list[CategoryTotalResponse]

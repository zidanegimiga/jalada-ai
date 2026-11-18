"""How records are shown to the model: amounts in shillings as text, names not slugs."""

from datetime import date
from decimal import Decimal
from typing import Any

from jalada.modules.ledger.domain.categories import CATEGORIES
from jalada.modules.ledger.domain.entries import Entry


def kes(cents: int | None) -> str | None:
    """Shillings with two decimals, as text so no rounding creeps in."""
    if cents is None:
        return None
    return str((Decimal(cents) / 100).quantize(Decimal("0.01")))


def category_name(slug: str | None) -> str | None:
    if slug is None:
        return None
    category = CATEGORIES.get(slug)
    return category.name if category else slug


def payment(entry: Entry) -> dict[str, Any]:
    return {
        "id": str(entry.id),
        "date": _day(entry.occurred_on),
        "direction": entry.direction,
        "amount": kes(entry.amount_cents),
        "with": entry.counterparty,
        "category": entry.category,
        "category_name": category_name(entry.category),
        "purpose": entry.purpose,
    }


def unknown_category(slug: str) -> dict[str, Any]:
    """Told to the model so it can try again with a category that exists."""
    return {
        "error": f"There is no category {slug!r}.",
        "categories": {c.slug: c.name for c in CATEGORIES.values()},
    }


def _day(day: date | None) -> str | None:
    return day.isoformat() if day else None

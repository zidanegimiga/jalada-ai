from dataclasses import dataclass
from enum import StrEnum


class Direction(StrEnum):
    IN = "in"
    OUT = "out"


class Purpose(StrEnum):
    BUSINESS = "business"
    PERSONAL = "personal"
    UNSURE = "unsure"


@dataclass(frozen=True)
class Category:
    slug: str
    name: str
    direction: Direction
    purpose: Purpose | None  # None for money in, where purpose does not apply


def _money_in(slug: str, name: str) -> Category:
    return Category(slug, name, Direction.IN, None)


def _cost(slug: str, name: str, purpose: Purpose) -> Category:
    return Category(slug, name, Direction.OUT, purpose)


B, P = Purpose.BUSINESS, Purpose.PERSONAL

CATEGORIES: dict[str, Category] = {
    c.slug: c
    for c in [
        _money_in("salary", "Salary"),
        _money_in("consultancy_fees", "Consultancy or freelance fees"),
        _money_in("business_sales", "Business sales"),
        _money_in("family_support", "Support from family or friends"),
        _money_in("own_transfer", "Transfer between own accounts"),
        _money_in("refund", "Refund"),
        _money_in("other_income", "Other money in"),
        _cost("business_airtime_data", "Data and airtime", B),
        _cost("business_transport", "Transport", B),
        _cost("business_equipment", "Equipment that lasts years", B),
        _cost("business_software", "Software and subscriptions", B),
        _cost("business_rent", "Workspace rent", B),
        _cost("business_stock", "Stock and supplies", B),
        _cost("business_professional_fees", "Professional fees", B),
        _cost("business_other", "Other business cost", B),
        _cost("personal_food", "Food", P),
        _cost("personal_rent", "Rent", P),
        _cost("personal_transport", "Transport", P),
        _cost("personal_airtime_data", "Airtime and data", P),
        _cost("personal_family_support", "Family support given", P),
        _cost("personal_school_fees", "School fees", P),
        _cost("personal_health", "Health", P),
        _cost("personal_other", "Other personal cost", P),
    ]
}

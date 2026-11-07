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
    """A kind of money in or out. Purpose groups it as business or personal in monthly views."""

    slug: str
    name: str
    direction: Direction
    purpose: Purpose


def _money_in(slug: str, name: str, purpose: Purpose) -> Category:
    return Category(slug, name, Direction.IN, purpose)


def _cost(slug: str, name: str, purpose: Purpose) -> Category:
    return Category(slug, name, Direction.OUT, purpose)


B, P = Purpose.BUSINESS, Purpose.PERSONAL

CATEGORIES: dict[str, Category] = {
    c.slug: c
    for c in [
        _money_in("salary", "Salary", P),
        _money_in("consultancy_fees", "Consultancy or freelance fees", B),
        _money_in("business_sales", "Business sales", B),
        _money_in("family_support", "Support from family or friends", P),
        _money_in("own_transfer", "Transfer between own accounts", P),
        _money_in("refund", "Refund", P),
        _money_in("other_income", "Other money in", P),
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

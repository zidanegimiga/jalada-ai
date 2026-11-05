"""Confirmed entries grouped the way the iTax return asks for them. No tax is calculated."""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from jalada.domain.categories import CATEGORIES, Direction
from jalada.domain.entries import Entry, EntryKind
from jalada.domain.ledger import MonthSummary


@dataclass(frozen=True)
class SectionRule:
    title: str
    # The iTax return sheet this section relates to, or None when it does not go on the return.
    itax_sheet: str | None
    categories: frozenset[str]


INCOME_SECTIONS = [
    SectionRule("Employment income", "F_Employment_Income", frozenset({"salary"})),
    SectionRule(
        "Business and consultancy income",
        "B_Profit_Loss_Account_Self",
        frozenset({"consultancy_fees", "business_sales"}),
    ),
    SectionRule("Other money in, to check", None, frozenset({"other_income"})),
    SectionRule(
        "Not income: support, own transfers and refunds",
        None,
        frozenset({"family_support", "own_transfer", "refund"}),
    ),
]
EXPENSE_SECTIONS = [
    SectionRule(
        "Business costs",
        "B_Profit_Loss_Account_Self",
        frozenset(
            slug
            for slug, category in CATEGORIES.items()
            if category.direction == Direction.OUT
            and slug.startswith("business_")
            and slug != "business_equipment"
        ),
    ),
    SectionRule(
        "Equipment that lasts years",
        "E2 capital allowance sheets",
        frozenset({"business_equipment"}),
    ),
]


@dataclass(frozen=True)
class Section:
    rule: SectionRule
    entries: list[Entry]

    @property
    def total_cents(self) -> int:
        return sum(entry.amount_cents or 0 for entry in self.entries)


@dataclass(frozen=True)
class TaxYearReport:
    year: int
    generated_on: date
    income: list[Section]
    expenses: list[Section]
    certificates: list[Entry]
    months: list[MonthSummary]
    # Where each entry's original evidence can be opened, by evidence id.
    evidence_links: dict[UUID, str]


def build_report(
    year: int,
    entries: list[Entry],
    months: list[MonthSummary],
    generated_on: date,
    evidence_link: str,
) -> TaxYearReport:
    """`evidence_link` has an `{id}` placeholder, filled in for each piece of evidence."""
    in_year = sorted(
        (e for e in entries if e.occurred_on and e.occurred_on.year == year),
        key=lambda e: (e.occurred_on, e.counterparty or ""),
    )
    return TaxYearReport(
        year=year,
        generated_on=generated_on,
        income=_sections(INCOME_SECTIONS, in_year),
        expenses=_sections(EXPENSE_SECTIONS, in_year),
        certificates=[e for e in in_year if e.kind == EntryKind.WITHHOLDING_CERTIFICATE],
        months=months,
        evidence_links={e.evidence_id: evidence_link.format(id=e.evidence_id) for e in in_year},
    )


def _sections(rules: list[SectionRule], entries: list[Entry]) -> list[Section]:
    return [Section(rule, [e for e in entries if e.category in rule.categories]) for rule in rules]

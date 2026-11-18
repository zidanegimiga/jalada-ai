import uuid
from collections.abc import Callable
from dataclasses import replace
from datetime import date
from typing import Any

import pytest
from fakes import FakeUnitOfWork, Store
from samples import confirmed_entry

from jalada.modules.agent.application.lookups.payments import AddUpPayments, SearchPayments
from jalada.modules.agent.application.lookups.summaries import MonthlySummary, SpendingByCategory
from jalada.modules.agent.application.tools import Tool, ToolContext
from jalada.modules.ledger.application.ledger import Ledger

ME, SOMEONE_ELSE = uuid.uuid4(), uuid.uuid4()
TODAY = date(2026, 11, 18)


@pytest.fixture
def ledger(store: Store) -> Ledger:
    def paid(
        user: uuid.UUID, day: date, cents: int, to: str, category: str = "business_other"
    ) -> Any:
        return replace(confirmed_entry(user, day, cents, "out", category), counterparty=to)

    store.save_entries(
        paid(ME, date(2026, 7, 4), 250_000, "KPLC PREPAID"),
        paid(ME, date(2026, 8, 6), 200_000, "KPLC PREPAID"),
        paid(ME, date(2026, 8, 9), 80_050, "Java House", "personal_food"),
        paid(ME, date(2025, 12, 30), 99_000, "KPLC PREPAID"),
        replace(
            confirmed_entry(ME, date(2026, 8, 1), 4_000_000, "in", "consultancy_fees"),
            counterparty="ACME LTD",
        ),
        paid(SOMEONE_ELSE, date(2026, 8, 6), 9_900_000, "KPLC PREPAID"),
    )
    return Ledger(lambda: FakeUnitOfWork(store))


def call(tool: Tool[Any], user: uuid.UUID = ME, **arguments: Any) -> dict[str, Any]:
    return tool.call(ToolContext(user, TODAY), arguments)


def test_search_finds_payments_by_counterparty_and_period(ledger: Ledger) -> None:
    found = call(SearchPayments(ledger), counterparty="kplc", start="2026-01-01")

    assert [(p["date"], p["amount"], p["with"]) for p in found["payments"]] == [
        ("2026-08-06", "2000.00", "KPLC PREPAID"),
        ("2026-07-04", "2500.00", "KPLC PREPAID"),
    ]
    assert found["payments"][0]["category_name"] == "Other business cost"
    assert found["more_not_shown"] is False


def test_search_says_when_there_are_more(ledger: Ledger) -> None:
    found = call(SearchPayments(ledger), limit=2)

    assert len(found["payments"]) == 2
    assert found["more_not_shown"] is True


def test_adding_up_gives_totals_both_ways(ledger: Ledger) -> None:
    totals = call(AddUpPayments(ledger), start="2026-07-01", end="2026-09-30")

    assert totals == {
        "payments": 4,
        "money_in": "40000.00",
        "money_out": "5300.50",
        "from": "2026-07-01",
        "to": "2026-09-30",
        "complete": True,
    }


def test_an_unknown_category_lists_the_real_ones(ledger: Ledger) -> None:
    found = call(SearchPayments(ledger), category="electricity")

    assert "no category 'electricity'" in found["error"]
    assert found["categories"]["personal_food"] == "Food"


def test_totals_by_category_default_to_this_year(ledger: Ledger) -> None:
    totals = call(SpendingByCategory(ledger))

    assert (totals["from"], totals["to"]) == ("2026-01-01", "2026-11-18")
    assert totals["money_out"] == [
        {"category": "business_other", "category_name": "Other business cost", "amount": "4500.00"},
        {"category": "personal_food", "category_name": "Food", "amount": "800.50"},
    ]
    assert totals["money_in"][0]["amount"] == "40000.00"


def test_the_monthly_summary_shows_only_months_with_money(ledger: Ledger) -> None:
    summary = call(MonthlySummary(ledger))

    assert [m["month"] for m in summary["months"]] == ["2026-07", "2026-08"]
    assert summary["months"][1]["money_out"] == {"business": "2000.00", "personal": "800.50"}
    assert (summary["year_money_in"], summary["year_money_out"]) == ("40000.00", "5300.50")


LOOKUPS: list[Callable[[Ledger], Tool[Any]]] = [
    SearchPayments,
    AddUpPayments,
    SpendingByCategory,
    MonthlySummary,
]


@pytest.mark.parametrize("lookup", LOOKUPS)
def test_no_lookup_reaches_another_persons_records(
    ledger: Ledger, lookup: Callable[[Ledger], Tool[Any]]
) -> None:
    assert "99000.00" not in str(call(lookup(ledger)))


def test_another_person_sees_only_their_own(ledger: Ledger) -> None:
    totals = call(AddUpPayments(ledger), SOMEONE_ELSE)

    assert (totals["payments"], totals["money_out"]) == (1, "99000.00")

import uuid
from dataclasses import replace
from datetime import date

import pytest
from fakes import FakeUnitOfWork, Store
from samples import certificate, confirmed_entry, deposit

from jalada.modules.ledger.application.ledger import Ledger
from jalada.modules.ledger.domain.categories import Direction, Purpose
from jalada.modules.ledger.domain.entries import Entry, EntryStatus
from jalada.modules.ledger.domain.ledger import LedgerFilter
from jalada.modules.ledger.domain.transactions import EvidenceRole, from_entry

USER = uuid.uuid4()


@pytest.fixture
def ledger(store: Store) -> Ledger:
    entries = [
        confirmed_entry(USER, date(2026, 1, 5), 4_000_000, "in", "consultancy_fees"),
        confirmed_entry(USER, date(2026, 1, 9), 500_000, "in", "family_support"),
        confirmed_entry(USER, date(2026, 1, 20), 25_000, "out", "business_airtime_data"),
        confirmed_entry(USER, date(2026, 2, 3), 80_000, "out", "personal_food"),
        confirmed_entry(USER, date(2025, 12, 30), 99_000, "out", "personal_food"),
        confirmed_entry(uuid.uuid4(), date(2026, 1, 5), 1_000, "out", "personal_food"),
    ]
    store.save_entries(*entries)
    return Ledger(lambda: FakeUnitOfWork(store))


def test_pages_run_newest_first_with_no_gaps_or_repeats(ledger: Ledger) -> None:
    seen: list[Entry] = []
    page = ledger.page(USER, LedgerFilter(), size=2)
    seen += page.entries
    while page.next_position:
        page = ledger.page(USER, LedgerFilter(), page.next_position, size=2)
        seen += page.entries

    days = [e.occurred_on for e in seen if e.occurred_on]
    assert len(seen) == 5
    assert days == sorted(days, reverse=True)


def test_filters_narrow_the_ledger(ledger: Ledger) -> None:
    january = LedgerFilter(start=date(2026, 1, 1), end=date(2026, 1, 31))

    assert len(ledger.page(USER, january).entries) == 3
    business = ledger.page(USER, LedgerFilter(purpose=Purpose.BUSINESS)).entries
    assert {e.category for e in business} == {"consultancy_fees", "business_airtime_data"}
    money_in = ledger.page(USER, LedgerFilter(direction=Direction.IN)).entries
    assert all(e.direction == Direction.IN for e in money_in) and len(money_in) == 2


def test_entries_waiting_for_review_stay_out_of_the_ledger(ledger: Ledger, store: Store) -> None:
    waiting = confirmed_entry(USER, date(2026, 1, 6), 1_000, "out", "personal_food")
    store.save_entries(replace(waiting, status=EntryStatus.PROPOSED))

    assert waiting.id not in {e.id for e in ledger.page(USER, LedgerFilter()).entries}


def test_a_payment_linked_to_a_certificate_is_left_out_of_the_month(
    ledger: Ledger, store: Store
) -> None:
    cert = certificate(USER, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT")
    paid = deposit(USER, date(2026, 3, 5), 3_800_000, "CLIENT")
    store.save_entries(cert, paid)
    store.certificate_payments[paid.id] = (USER, cert.id)

    march = ledger.year(USER, 2026)[2]

    assert march.money_in == {Purpose.BUSINESS: 4_000_000}


def test_the_year_splits_each_month_into_business_and_personal(ledger: Ledger) -> None:
    months = ledger.year(USER, 2026)

    assert len(months) == 12
    january, february = months[0], months[1]
    assert january.money_in == {Purpose.BUSINESS: 4_000_000, Purpose.PERSONAL: 500_000}
    assert january.money_out == {Purpose.BUSINESS: 25_000}
    assert february.money_out == {Purpose.PERSONAL: 80_000}
    assert months[11].money_out == {}, "December 2025 belongs to last year"


def test_payments_are_read_from_transactions(ledger: Ledger, store: Store) -> None:
    entry = confirmed_entry(USER, date(2026, 4, 1), 7_000, "out", "personal_food")
    store.transactions[entry.id] = from_entry(entry, None, EvidenceRole.OTHER)

    listed = ledger.page(USER, LedgerFilter(start=date(2026, 4, 1))).entries

    assert listed == [entry], "a payment with no entry beside it is still listed"

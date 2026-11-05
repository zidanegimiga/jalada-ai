import uuid
from dataclasses import replace
from datetime import date

from samples import confirmed_entry

from jalada.domain.entries import Entry, EntryKind
from jalada.domain.tax_year import build_report

USER = uuid.uuid4()
LINK = "https://app.example.com/v1/evidence/{id}/file"


def entries() -> list[Entry]:
    certificate = replace(
        confirmed_entry(USER, date(2026, 3, 3), 4_000_000, "in", "consultancy_fees"),
        kind=EntryKind.WITHHOLDING_CERTIFICATE,
        certificate_serial="KRAWHTEON0000000001",
        tax_withheld_cents=200_000,
        payer_tax_number="P000000000A",
    )
    return [
        certificate,
        confirmed_entry(USER, date(2026, 1, 31), 6_000_000, "in", "salary"),
        confirmed_entry(USER, date(2026, 2, 10), 500_000, "in", "family_support"),
        confirmed_entry(USER, date(2026, 2, 11), 25_000, "out", "business_airtime_data"),
        confirmed_entry(USER, date(2026, 5, 2), 9_000_000, "out", "business_equipment"),
        confirmed_entry(USER, date(2026, 5, 3), 80_000, "out", "personal_food"),
        confirmed_entry(USER, date(2025, 12, 31), 99_000, "in", "salary"),
    ]


def test_income_is_grouped_by_the_itax_sheet_it_relates_to() -> None:
    report = build_report(2026, entries(), [], date(2026, 11, 5), LINK)

    sections = {s.rule.title: s for s in report.income}
    assert sections["Employment income"].rule.itax_sheet == "F_Employment_Income"
    assert sections["Employment income"].total_cents == 6_000_000
    business = sections["Business and consultancy income"]
    assert business.rule.itax_sheet == "B_Profit_Loss_Account_Self"
    assert business.total_cents == 4_000_000
    not_income = sections["Not income: support, own transfers and refunds"]
    assert not_income.rule.itax_sheet is None
    assert not_income.total_cents == 500_000


def test_business_costs_are_kept_apart_from_equipment_and_personal_costs_are_left_out() -> None:
    report = build_report(2026, entries(), [], date(2026, 11, 5), LINK)

    costs, equipment = report.expenses
    assert costs.total_cents == 25_000
    assert equipment.rule.itax_sheet == "E2 capital allowance sheets"
    assert equipment.total_cents == 9_000_000
    every_entry = [e for s in report.expenses + report.income for e in s.entries]
    assert all(e.category != "personal_food" for e in every_entry)


def test_certificates_are_listed_and_other_years_are_left_out() -> None:
    report = build_report(2026, entries(), [], date(2026, 11, 5), LINK)

    [certificate] = report.certificates
    assert certificate.certificate_serial == "KRAWHTEON0000000001"
    assert all(
        e.occurred_on and e.occurred_on.year == 2026 for s in report.income for e in s.entries
    )
    assert report.income[0].entries[0].occurred_on == date(2026, 1, 31)


def test_each_entry_links_to_its_original_evidence() -> None:
    report = build_report(2026, entries(), [], date(2026, 11, 5), LINK)

    entry = report.income[0].entries[0]
    assert report.evidence_links[entry.evidence_id] == (
        f"https://app.example.com/v1/evidence/{entry.evidence_id}/file"
    )

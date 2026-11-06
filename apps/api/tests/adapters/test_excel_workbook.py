import io
import uuid
from dataclasses import replace
from datetime import date, datetime

import pytest
from openpyxl import Workbook, load_workbook
from samples import confirmed_entry

from jalada.adapters.export.workbook import ExcelWorkbookWriter
from jalada.domain.categories import Purpose
from jalada.domain.entries import EntryKind
from jalada.domain.ledger import MonthSummary
from jalada.domain.tax_year import build_report

USER = uuid.uuid4()
INJECTION = '=HYPERLINK("https://evil.example.com","Click")'


@pytest.fixture(scope="module")
def workbook() -> Workbook:
    certificate = replace(
        confirmed_entry(USER, date(2026, 3, 3), 4_000_000, "in", "consultancy_fees"),
        kind=EntryKind.WITHHOLDING_CERTIFICATE,
        counterparty="EXAMPLE CONSULTING LTD",
        certificate_serial="KRAWHTEON0000000001",
        tax_withheld_cents=200_000,
        payer_tax_number="P000000000A",
    )
    shop = replace(
        confirmed_entry(USER, date(2026, 2, 11), 25_050, "out", "business_stock"),
        counterparty=INJECTION,
        mpesa_code="UK5AB1CD23",
    )
    payment = replace(
        confirmed_entry(USER, date(2026, 3, 5), 3_800_000, "in", "consultancy_fees"),
        counterparty="EXAMPLE CONSULTING LTD",
    )
    months = [MonthSummary(m) for m in range(1, 13)]
    months[2].money_in[Purpose.BUSINESS] = 4_000_000
    report = build_report(
        2026,
        [certificate, shop, payment],
        months,
        date(2026, 11, 5),
        "https://app.example.com/v1/evidence/{id}/file",
        {certificate.id: [payment]},
    )
    return load_workbook(io.BytesIO(ExcelWorkbookWriter().write(report)))


def test_the_five_sheets_are_in_order(workbook: Workbook) -> None:
    assert workbook.sheetnames == [
        "Instructions",
        "Income",
        "Expenses",
        "Withholding Tax",
        "Summary",
    ]


def test_instructions_name_the_year_and_say_this_is_not_tax_advice(workbook: Workbook) -> None:
    cells = " ".join(
        str(c.value) for row in workbook["Instructions"].iter_rows() for c in row if c.value
    )

    assert "Jalada AI records for 2026" in cells
    assert "Tax year 1 January to 31 December 2026. Made on 05/11/2026." in cells
    assert "not tax advice" in cells
    assert "link that payment to its certificate" in cells


def test_income_rows_carry_dates_amounts_sources_and_links(workbook: Workbook) -> None:
    sheet = workbook["Income"]
    rows = {row[1].value: row for row in sheet.iter_rows(min_row=1) if row[1].value}
    row = rows["EXAMPLE CONSULTING LTD"]

    assert row[0].value == datetime(2026, 3, 3)
    assert row[0].number_format == "dd/mm/yyyy"
    assert row[2].value == "Consultancy or freelance fees"
    assert row[3].value == 40000
    assert row[3].number_format == "#,##0.00"
    assert row[4].value == "Withholding certificate"
    assert row[5].hyperlink is not None
    assert str(row[5].hyperlink.target).startswith("https://app.example.com/v1/evidence/")
    assert sheet["A2"].value == "Relates to iTax sheet F_Employment_Income"


def test_text_from_evidence_never_becomes_a_formula(workbook: Workbook) -> None:
    sheet = workbook["Expenses"]
    [cell] = [c for row in sheet.iter_rows() for c in row if c.value == INJECTION]

    assert cell.data_type == "s"


def test_amounts_keep_their_cents(workbook: Workbook) -> None:
    rows = [r for r in workbook["Expenses"].iter_rows() if r[1].value == INJECTION]

    assert rows[0][3].value == 250.5


def test_withholding_tax_lists_each_certificate_with_its_payer(workbook: Workbook) -> None:
    sheet = workbook["Withholding Tax"]

    assert [c.value for c in sheet[2]][1:7] == [
        "EXAMPLE CONSULTING LTD",
        "P000000000A",
        "KRAWHTEON0000000001",
        40000,
        2000,
        38000,
    ]
    assert sheet["D3"].value == "Total" and sheet["F3"].value == 2000
    assert sheet["G3"].value == 38000


def test_a_linked_payment_is_not_listed_as_income_again(workbook: Workbook) -> None:
    amounts = [row[3].value for row in workbook["Income"].iter_rows() if row[3].value]

    assert 38000 not in amounts
    assert 40000 in amounts


def test_the_summary_totals_groups_and_months_without_calculating_tax(workbook: Workbook) -> None:
    sheet = workbook["Summary"]
    groups = {r[0].value: r[2].value for r in sheet.iter_rows(min_row=2, max_row=8) if r[0].value}

    assert groups["Business and consultancy income"] == 40000
    assert groups["Business costs"] == 250.5
    assert groups["Tax withheld on certificates"] == 2000
    months = [r for r in sheet.iter_rows() if r[0].value == "March"]
    assert months[0][1].value == 40000


def test_every_sheet_prints_one_page_wide(workbook: Workbook) -> None:
    for sheet in workbook.worksheets:
        assert sheet.page_setup.orientation == "landscape"
        assert sheet.page_setup.fitToWidth == 1
        assert sheet.sheet_properties.pageSetUpPr is not None
        assert sheet.sheet_properties.pageSetUpPr.fitToPage


def test_the_notes_wrap_across_the_sheet(workbook: Workbook) -> None:
    sheet = workbook["Instructions"]
    [note] = [c for row in sheet.iter_rows() for c in row if str(c.value).startswith("3. ")]

    assert note.alignment.wrap_text
    assert f"{note.coordinate}:C{note.row}" in {str(r) for r in sheet.merged_cells.ranges}

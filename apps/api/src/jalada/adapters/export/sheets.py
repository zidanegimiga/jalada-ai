"""One function per sheet. Each writes from the report and never calculates tax."""

from openpyxl.worksheet.worksheet import Worksheet

from jalada.adapters.export.cells import TITLE, day, header, link, money, text, widths
from jalada.domain.categories import CATEGORIES, Purpose
from jalada.domain.entries import Entry, EntryKind
from jalada.domain.ledger import MonthSummary
from jalada.domain.tax_year import Section, TaxYearReport

MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def source(entry: Entry) -> str:
    if entry.kind == EntryKind.WITHHOLDING_CERTIFICATE:
        return "Withholding certificate"
    return f"M-Pesa {entry.mpesa_code}" if entry.mpesa_code else "Receipt or document"


def sections(sheet: Worksheet, report: TaxYearReport, groups: list[Section], last: str) -> None:
    """Each section: a title, the iTax sheet it relates to, its entries and a total."""
    row = 1
    for group in groups:
        text(sheet, row, 1, group.rule.title, bold=True)
        sheet.cell(row, 1).font = TITLE
        sheet_name = group.rule.itax_sheet
        text(
            sheet,
            row + 1,
            1,
            f"Relates to iTax sheet {sheet_name}"
            if sheet_name
            else "Not entered on the return. Kept to explain deposits.",
        )
        header(
            sheet, row + 2, ["Date", "Paid to / from", "Category", "Amount (KSh)", last, "Evidence"]
        )
        row += 3
        for entry in group.entries:
            day(sheet, row, 1, entry.occurred_on)
            text(sheet, row, 2, entry.counterparty)
            text(sheet, row, 3, CATEGORIES[entry.category or ""].name if entry.category else "")
            money(sheet, row, 4, entry.amount_cents)
            text(sheet, row, 5, source(entry) if last == "Source" else "")
            link(sheet, row, 6, report.evidence_links.get(entry.evidence_id))
            row += 1
        text(sheet, row, 3, "Total", bold=True)
        money(sheet, row, 4, group.total_cents, bold=True)
        row += 3
    widths(sheet, [12, 32, 30, 16, 26, 10])


def withholding(sheet: Worksheet, report: TaxYearReport) -> None:
    header(
        sheet,
        1,
        [
            "Date",
            "Payer",
            "Payer PIN",
            "Certificate serial",
            "Gross (KSh)",
            "Tax withheld (KSh)",
            "Linked payments (KSh)",
            "Evidence",
        ],
    )
    for row, entry in enumerate(report.certificates, start=2):
        day(sheet, row, 1, entry.occurred_on)
        text(sheet, row, 2, entry.counterparty)
        text(sheet, row, 3, entry.payer_tax_number)
        text(sheet, row, 4, entry.certificate_serial)
        money(sheet, row, 5, entry.amount_cents)
        money(sheet, row, 6, entry.tax_withheld_cents)
        money(sheet, row, 7, report.paid_in_cents(entry))
        link(sheet, row, 8, report.evidence_links.get(entry.evidence_id))
    total_row = len(report.certificates) + 2
    text(sheet, total_row, 4, "Total", bold=True)
    money(sheet, total_row, 5, sum(e.amount_cents or 0 for e in report.certificates), bold=True)
    money(
        sheet, total_row, 6, sum(e.tax_withheld_cents or 0 for e in report.certificates), bold=True
    )
    money(sheet, total_row, 7, sum(report.paid_in_cents(e) for e in report.certificates), bold=True)
    widths(sheet, [12, 32, 14, 24, 16, 22, 22, 10])


def summary(sheet: Worksheet, report: TaxYearReport) -> None:
    header(sheet, 1, ["Group", "Relates to iTax sheet", "Total (KSh)"])
    row = 2
    for group in report.income + report.expenses:
        text(sheet, row, 1, group.rule.title)
        text(sheet, row, 2, group.rule.itax_sheet or "Not on the return")
        money(sheet, row, 3, group.total_cents)
        row += 1
    text(sheet, row, 1, "Tax withheld on certificates")
    text(sheet, row, 2, "O_WHT_Credits")
    money(sheet, row, 3, sum(e.tax_withheld_cents or 0 for e in report.certificates))
    row += 3
    header(sheet, row, ["Month", "In: business", "In: personal", "Out: business", "Out: personal"])
    for month in report.months:
        row += 1
        text(sheet, row, 1, MONTHS[month.month - 1])
        for column, cents in enumerate(_month_values(month), start=2):
            money(sheet, row, column, cents)
    widths(sheet, [44, 28, 16, 16, 16])


def _month_values(month: MonthSummary) -> list[int]:
    business, personal = Purpose.BUSINESS, Purpose.PERSONAL
    return [
        month.money_in.get(business, 0),
        month.money_in.get(personal, 0),
        month.money_out.get(business, 0),
        month.money_out.get(personal, 0),
    ]

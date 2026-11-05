from openpyxl.worksheet.worksheet import Worksheet

from jalada.adapters.export.cells import TITLE, header, text, widths
from jalada.domain.tax_year import TaxYearReport

GUIDE = [
    (
        "Income",
        "Money in, grouped as employment, business and consultancy, other, and money "
        "that is not income.",
        "F_Employment_Income, B_Profit_Loss_Account_Self",
    ),
    (
        "Expenses",
        "Business costs, with equipment that lasts years listed apart. Personal costs "
        "are left out.",
        "B_Profit_Loss_Account_Self, E2 capital allowance sheets",
    ),
    ("Withholding Tax", "One row per withholding certificate.", "O_WHT_Credits"),
    ("Summary", "Totals per group and per month.", ""),
]

NOTES = [
    "These are your own records, grouped to help you fill in your iTax return. They are not "
    "tax advice, and nothing here has been checked by the Kenya Revenue Authority.",
    "Only entries you confirmed are included. Anything still waiting in Jalada AI is not.",
    "A client who withheld tax may have paid you by M-Pesa or bank as well. That income can "
    "then appear twice: as the certificate (the gross amount) and as the deposit (the amount "
    "after tax). Count it once.",
    "Costs generally need an electronic tax invoice (eTIMS) from the seller to be allowed. The "
    "Expenses sheet has a column for you to note which ones have one.",
    "Equipment that lasts years, such as a laptop, is claimed over time as a capital allowance, "
    "not all at once.",
    "Each row has a link to the original receipt, message or certificate. The link needs you to "
    "be signed in to Jalada AI.",
]


def instructions(sheet: Worksheet, report: TaxYearReport) -> None:
    text(sheet, 1, 1, f"Jalada AI records for {report.year}")
    sheet.cell(1, 1).font = TITLE
    text(
        sheet,
        2,
        1,
        f"Tax year 1 January to 31 December {report.year}. Made on "
        f"{report.generated_on.strftime('%d/%m/%Y')}.",
    )
    header(sheet, 4, ["Sheet", "What is in it", "Relates to iTax sheet"])
    for row, (name, what, itax) in enumerate(GUIDE, start=5):
        text(sheet, row, 1, name, bold=True)
        text(sheet, row, 2, what)
        text(sheet, row, 3, itax)
    row = 5 + len(GUIDE) + 1
    text(sheet, row, 1, "Before you file", bold=True)
    for offset, note in enumerate(NOTES, start=1):
        text(sheet, row + offset, 1, f"{offset}. {note}")
    widths(sheet, [18, 70, 48])

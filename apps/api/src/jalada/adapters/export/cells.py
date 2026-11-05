"""Small helpers for writing safe, readable cells."""

from datetime import date
from decimal import Decimal

from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import PageSetupProperties
from openpyxl.worksheet.worksheet import Worksheet

MONEY_FORMAT = "#,##0.00"
DATE_FORMAT = "dd/mm/yyyy"
BOLD = Font(bold=True)
TITLE = Font(bold=True, size=14)
HEADER_FILL = PatternFill("solid", fgColor="FDF2A0")


def text(sheet: Worksheet, row: int, column: int, value: str | None, bold: bool = False) -> None:
    """Text is always stored as text. Without this, a counterparty such as "=HYPERLINK(...)"
    taken from a receipt would become a live formula in the user's spreadsheet."""
    cell = sheet.cell(row, column)
    cell.value = value or ""
    cell.data_type = "s"
    if bold:
        cell.font = BOLD


def money(sheet: Worksheet, row: int, column: int, cents: int | None, bold: bool = False) -> None:
    cell = sheet.cell(row, column, Decimal(cents or 0) / 100)
    cell.number_format = MONEY_FORMAT
    if bold:
        cell.font = BOLD


def day(sheet: Worksheet, row: int, column: int, value: date | None) -> None:
    cell = sheet.cell(row, column, value)
    cell.number_format = DATE_FORMAT


def link(sheet: Worksheet, row: int, column: int, url: str | None) -> None:
    if url:
        cell = sheet.cell(row, column, "Open")
        cell.hyperlink = url
        cell.font = Font(underline="single", color="0000EE")


def header(sheet: Worksheet, row: int, names: list[str]) -> None:
    for column, name in enumerate(names, start=1):
        text(sheet, row, column, name, bold=True)
        sheet.cell(row, column).fill = HEADER_FILL


def widths(sheet: Worksheet, sizes: list[int]) -> None:
    for column, size in enumerate(sizes, start=1):
        sheet.column_dimensions[get_column_letter(column)].width = size


def printable(sheet: Worksheet) -> None:
    """Landscape, one page wide, so a printed sheet is not cut into columns."""
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    sheet.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)


def paragraph(sheet: Worksheet, row: int, value: str, last_column: int) -> None:
    """Long text across several columns, wrapped, with a row tall enough to show it."""
    text(sheet, row, 1, value)
    sheet.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_column)
    sheet.cell(row, 1).alignment = Alignment(wrap_text=True, vertical="top")
    sheet.row_dimensions[row].height = 15 * (1 + len(value) // 110)

"""Small helpers for writing safe, readable cells."""

from datetime import date
from decimal import Decimal

from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
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

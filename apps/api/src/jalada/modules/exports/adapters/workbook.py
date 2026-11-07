import io

from openpyxl import Workbook

from jalada.modules.exports.adapters.cells import printable
from jalada.modules.exports.adapters.instructions import instructions
from jalada.modules.exports.adapters.sheets import sections, summary, withholding
from jalada.modules.exports.domain.tax_year import TaxYearReport


class ExcelWorkbookWriter:
    """The tax-year workbook: Instructions, Income, Expenses, Withholding Tax and Summary."""

    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def write(self, report: TaxYearReport) -> bytes:
        workbook = Workbook()
        first = workbook.active
        if first is None:
            raise RuntimeError("A new workbook has no sheet")
        first.title = "Instructions"
        instructions(first, report)
        sections(workbook.create_sheet("Income"), report, report.income, last="Source")
        sections(workbook.create_sheet("Expenses"), report, report.expenses, last="eTIMS invoice")
        withholding(workbook.create_sheet("Withholding Tax"), report)
        summary(workbook.create_sheet("Summary"), report)
        for sheet in workbook.worksheets:
            printable(sheet)
        out = io.BytesIO()
        workbook.save(out)
        return out.getvalue()

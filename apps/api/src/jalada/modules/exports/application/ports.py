from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    pass
from jalada.modules.exports.domain.tax_year import TaxYearReport


class WorkbookWriter(Protocol):
    """Turns a tax-year report into a spreadsheet file."""

    content_type: str

    def write(self, report: TaxYearReport) -> bytes: ...

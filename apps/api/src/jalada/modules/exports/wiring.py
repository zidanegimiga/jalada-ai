"""Builds the exports module's use cases from the pieces the composition root shares."""

from collections.abc import Callable

from jalada.core.ports import Clock
from jalada.modules.exports.adapters.workbook import ExcelWorkbookWriter
from jalada.modules.exports.application.tax_year_export import TaxYearExport
from jalada.unit_of_work import UnitOfWork


def build_tax_year_export(
    unit_of_work: Callable[[], UnitOfWork], clock: Clock, evidence_link: str
) -> TaxYearExport:
    """`evidence_link` is a URL with `{id}` where each row's evidence id goes."""
    return TaxYearExport(unit_of_work, ExcelWorkbookWriter(), clock, evidence_link=evidence_link)

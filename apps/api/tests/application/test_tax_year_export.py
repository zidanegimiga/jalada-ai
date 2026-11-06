import uuid
from datetime import date, timedelta

from fakes import FakeUnitOfWork, FixedClock, Store
from samples import confirmed_entry

from jalada.application.tax_year_export import TaxYearExport
from jalada.domain.categories import Purpose
from jalada.domain.dates import kenyan_date
from jalada.domain.tax_year import TaxYearReport

USER = uuid.uuid4()


class RecordingWriter:
    content_type = "application/test"

    def __init__(self) -> None:
        self.reports: list[TaxYearReport] = []

    def write(self, report: TaxYearReport) -> bytes:
        self.reports.append(report)
        return b"workbook"


def test_the_workbook_covers_every_confirmed_entry_of_the_year(
    store: Store, clock: FixedClock
) -> None:
    first = date(2026, 1, 1)
    for n in range(1200):
        entry = confirmed_entry(
            USER, first + timedelta(days=n % 365), 1_000, "out", "business_stock"
        )
        store.entries[entry.id] = entry
    other = confirmed_entry(uuid.uuid4(), first, 1_000, "out", "business_stock")
    store.entries[other.id] = other
    writer = RecordingWriter()
    export = TaxYearExport(lambda: FakeUnitOfWork(store), writer, clock, "/v1/evidence/{id}/file")

    assert export.workbook(USER, 2026) == b"workbook"

    [report] = writer.reports
    assert len(report.expenses[0].entries) == 1200, "all three pages were read"
    assert report.expenses[0].total_cents == 1_200_000
    # Three full years of 31 January days, plus 31 more from the last partial cycle.
    assert report.months[0].money_out[Purpose.BUSINESS] == 1_000 * 124
    assert report.generated_on == kenyan_date(clock.now())
    assert export.content_type == "application/test"

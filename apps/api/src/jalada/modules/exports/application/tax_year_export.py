from collections.abc import Callable
from datetime import date
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.exports.application.ports import WorkbookWriter
from jalada.modules.exports.domain.tax_year import TaxYearReport, build_report
from jalada.modules.ledger.application.ports import EntryRepository
from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.ledger.domain.ledger import LedgerFilter, LedgerPosition, summarise
from jalada.shared.dates import kenyan_date
from jalada.unit_of_work import UnitOfWork

PAGE_SIZE = 500


class TaxYearExport:
    """One workbook for a tax year (1 January to 31 December), built from confirmed entries.

    Built on request and never stored.
    """

    def __init__(
        self,
        unit_of_work: Callable[[], UnitOfWork],
        writer: WorkbookWriter,
        clock: Clock,
        evidence_link: str,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._writer = writer
        self._clock = clock
        self._evidence_link = evidence_link

    @property
    def content_type(self) -> str:
        return self._writer.content_type

    def report(self, user_id: UUID, year: int) -> TaxYearReport:
        year_filter = LedgerFilter(start=date(year, 1, 1), end=date(year, 12, 31))
        with self._unit_of_work() as work:
            entries = work.entries_for(user_id)
            confirmed = _all_pages(lambda after: entries.confirmed(year_filter, after, PAGE_SIZE))
            months = summarise(entries.monthly_totals(year))
            links = work.certificate_payments_for(user_id).links()
            payments = _payments_by_certificate(entries, links)
        today = kenyan_date(self._clock.now())
        return build_report(year, confirmed, months, today, self._evidence_link, payments)

    def workbook(self, user_id: UUID, year: int) -> bytes:
        return self._writer.write(self.report(user_id, year))


def _payments_by_certificate(
    entries: EntryRepository, links: dict[UUID, UUID]
) -> dict[UUID, list[Entry]]:
    """Linked payments grouped by certificate, wherever in time each payment falls."""
    grouped: dict[UUID, list[Entry]] = {}
    for payment_id, certificate_id in links.items():
        payment = entries.get(payment_id)
        if payment:
            grouped.setdefault(certificate_id, []).append(payment)
    return grouped


def _all_pages(fetch: Callable[[LedgerPosition | None], list[Entry]]) -> list[Entry]:
    found: list[Entry] = []
    after: LedgerPosition | None = None
    while True:
        page = fetch(after)
        found += page
        if len(page) < PAGE_SIZE or page[-1].occurred_on is None:
            return found
        after = LedgerPosition(page[-1].occurred_on, page[-1].id)

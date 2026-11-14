from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from jalada.core.ports import Clock
from jalada.modules.ledger.application import records
from jalada.modules.ledger.domain.certificates import link_problem, search_window, suggest_payments
from jalada.modules.ledger.domain.entries import Entry, EntryKind
from jalada.shared.errors import EntryNotFound, InvalidEntry
from jalada.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class CertificateView:
    certificate: Entry
    # Payments already linked, which the certificate's gross amount counts for.
    payments: list[Entry]
    # Unlinked money in that could be the payment, most likely first.
    suggestions: list[Entry]


class CertificatePayments:
    """Linking withholding certificates to the deposits that paid them, so income counts once."""

    def __init__(self, unit_of_work: Callable[[], UnitOfWork], clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    def view(self, user_id: UUID, certificate_id: UUID) -> CertificateView:
        with self._unit_of_work() as work:
            return self._view(work, user_id, certificate_id)

    def link(self, user_id: UUID, certificate_id: UUID, payment_id: UUID) -> CertificateView:
        with self._unit_of_work() as work:
            view = self._view(work, user_id, certificate_id)
            links = work.certificate_payments_for(user_id)
            already = links.links().get(payment_id)
            if already == certificate_id:
                return view
            if already is not None:
                raise InvalidEntry("That payment is already linked to another certificate.")
            payment = records.payment(work, user_id, payment_id)
            if payment is None:
                raise EntryNotFound
            linked_cents = sum(p.amount_cents or 0 for p in view.payments)
            problem = link_problem(view.certificate, payment, linked_cents)
            if problem:
                raise InvalidEntry(problem)
            links.link(certificate_id, payment_id, self._clock.now())
            work.commit()
            return self._view(work, user_id, certificate_id)

    def unlink(self, user_id: UUID, certificate_id: UUID, payment_id: UUID) -> CertificateView:
        with self._unit_of_work() as work:
            self._certificate(work, user_id, certificate_id)
            work.certificate_payments_for(user_id).unlink(certificate_id, payment_id)
            work.commit()
            return self._view(work, user_id, certificate_id)

    def _view(self, work: UnitOfWork, user_id: UUID, certificate_id: UUID) -> CertificateView:
        certificate = self._certificate(work, user_id, certificate_id)
        links = work.certificate_payments_for(user_id).links()
        paid = [records.payment(work, user_id, p) for p, c in links.items() if c == certificate_id]
        payments = sorted((p for p in paid if p), key=lambda p: p.occurred_on or date.min)
        window = search_window(certificate)
        deposits = [d for d in records.incoming(work, user_id, *window) if d.id not in links]
        linked_cents = sum(p.amount_cents or 0 for p in payments)
        suggestions = suggest_payments(certificate, deposits, linked_cents)
        return CertificateView(certificate, payments, suggestions)

    @staticmethod
    def _certificate(work: UnitOfWork, user_id: UUID, certificate_id: UUID) -> Entry:
        found = work.entries_for(user_id).get(certificate_id)
        if found is None or found.kind != EntryKind.WITHHOLDING_CERTIFICATE:
            raise EntryNotFound
        if found.occurred_on is None or not found.amount_cents:
            raise InvalidEntry("Add the certificate's date and gross amount first.")
        return found

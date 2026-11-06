import uuid
from datetime import date

import pytest
from fakes import FakeUnitOfWork, FixedClock, Store
from samples import certificate, deposit

from jalada.application.certificate_payments import CertificatePayments
from jalada.application.errors import EntryNotFound, InvalidEntry
from jalada.domain.entries import Entry

USER = uuid.uuid4()
OTHER_USER = uuid.uuid4()


@pytest.fixture
def payments(store: Store) -> CertificatePayments:
    return CertificatePayments(lambda: FakeUnitOfWork(store), FixedClock())


def add(store: Store, *entries: Entry) -> tuple[Entry, ...]:
    for entry in entries:
        store.entries[entry.id] = entry
    return entries


def test_suggestions_leave_out_payments_already_linked_anywhere(
    store: Store, payments: CertificatePayments
) -> None:
    march, april = add(
        store,
        certificate(USER, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT"),
        certificate(USER, date(2026, 4, 3), 4_000_000, 200_000, "CLIENT"),
    )
    paid_march, paid_april = add(
        store,
        deposit(USER, date(2026, 3, 5), 3_800_000, "CLIENT"),
        deposit(USER, date(2026, 4, 5), 3_800_000, "CLIENT"),
    )

    payments.link(USER, march.id, paid_march.id)
    view = payments.view(USER, april.id)

    assert view.payments == []
    assert view.suggestions == [paid_april]


def test_linking_and_unlinking_a_payment(store: Store, payments: CertificatePayments) -> None:
    (cert,) = add(store, certificate(USER, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT"))
    (paid,) = add(store, deposit(USER, date(2026, 3, 5), 3_800_000, "CLIENT"))

    linked = payments.link(USER, cert.id, paid.id)
    again = payments.link(USER, cert.id, paid.id)

    assert linked.payments == again.payments == [paid]
    assert linked.suggestions == []
    assert store.certificate_payments == {paid.id: (USER, cert.id)}

    unlinked = payments.unlink(USER, cert.id, paid.id)

    assert unlinked.payments == []
    assert unlinked.suggestions == [paid]


def test_a_payment_settles_one_certificate_only(
    store: Store, payments: CertificatePayments
) -> None:
    first, second = add(
        store,
        certificate(USER, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT"),
        certificate(USER, date(2026, 3, 4), 4_000_000, 200_000, "CLIENT"),
    )
    (paid,) = add(store, deposit(USER, date(2026, 3, 5), 3_800_000, "CLIENT"))
    payments.link(USER, first.id, paid.id)

    with pytest.raises(InvalidEntry, match="another certificate"):
        payments.link(USER, second.id, paid.id)


def test_payments_cannot_exceed_the_gross_amount(
    store: Store, payments: CertificatePayments
) -> None:
    (cert,) = add(store, certificate(USER, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT"))
    first, second = add(
        store,
        deposit(USER, date(2026, 3, 5), 3_800_000, "CLIENT"),
        deposit(USER, date(2026, 3, 6), 300_000, "CLIENT"),
    )
    payments.link(USER, cert.id, first.id)

    with pytest.raises(InvalidEntry, match="more than its gross"):
        payments.link(USER, cert.id, second.id)


def test_other_users_entries_and_non_certificates_are_not_found(
    store: Store, payments: CertificatePayments
) -> None:
    (cert,) = add(store, certificate(USER, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT"))
    (theirs,) = add(store, deposit(OTHER_USER, date(2026, 3, 5), 3_800_000, "CLIENT"))
    (mine,) = add(store, deposit(USER, date(2026, 3, 5), 3_800_000, "CLIENT"))

    with pytest.raises(EntryNotFound):
        payments.view(OTHER_USER, cert.id)
    with pytest.raises(EntryNotFound):
        payments.view(USER, mine.id)
    with pytest.raises(EntryNotFound):
        payments.link(USER, cert.id, theirs.id)
    assert store.certificate_payments == {}

import uuid
from dataclasses import replace
from datetime import date

import pytest
from samples import certificate, confirmed_entry

from jalada.modules.evidence.domain.evidence import EvidenceKind
from jalada.modules.ledger.domain.categories import Purpose
from jalada.modules.ledger.domain.entries import EntryStatus
from jalada.modules.ledger.domain.transactions import (
    EvidenceRole,
    LinkedBy,
    TransactionKind,
    TransactionLine,
    TransactionStatus,
    as_entry,
    from_entry,
    line_problems,
    role_for,
)

USER = uuid.uuid4()
MPESA = uuid.uuid4()


def test_an_entry_becomes_a_payment_with_one_line_and_its_evidence() -> None:
    entry = replace(
        confirmed_entry(USER, date(2026, 11, 4), 15000, "out", "personal_food"),
        mpesa_code="UK5AB1CD23",
        run_id=uuid.uuid4(),
    )

    transaction = from_entry(entry, MPESA, EvidenceRole.PAYMENT_PROOF)

    assert transaction.id == entry.id, "links made to the entry keep working"
    assert transaction.account_id == MPESA
    assert transaction.kind == TransactionKind.PAYMENT
    assert transaction.status == TransactionStatus.CONFIRMED
    assert transaction.payment_code == "UK5AB1CD23"
    assert transaction.lines == (TransactionLine(15000, "personal_food", entry.purpose),)
    [link] = transaction.evidence
    assert (link.evidence_id, link.role, link.linked_by) == (
        entry.evidence_id,
        EvidenceRole.PAYMENT_PROOF,
        LinkedBy.PIPELINE,
    )
    assert line_problems(transaction) == []


def test_an_entry_typed_in_by_hand_was_linked_by_the_user() -> None:
    entry = confirmed_entry(USER, date(2026, 11, 4), 15000, "out", "personal_food")

    [link] = from_entry(entry, None, EvidenceRole.RECEIPT).evidence

    assert link.linked_by == LinkedBy.USER


def test_every_entry_status_has_a_transaction_status() -> None:
    entry = confirmed_entry(USER, date(2026, 11, 4), 15000, "out", "personal_food")

    for status in EntryStatus:
        changed = from_entry(replace(entry, status=status), None, EvidenceRole.OTHER)
        assert changed.status.value == status.value


def test_certificates_are_not_transactions() -> None:
    with pytest.raises(ValueError):
        from_entry(
            certificate(USER, date(2026, 3, 3), 4_000_000, 200_000, "CLIENT"),
            None,
            EvidenceRole.CERTIFICATE,
        )


def test_each_kind_of_evidence_has_a_role() -> None:
    assert role_for(EvidenceKind.MPESA_MESSAGE) == EvidenceRole.PAYMENT_PROOF
    assert role_for(EvidenceKind.RECEIPT) == EvidenceRole.RECEIPT
    assert role_for(EvidenceKind.FREE_TEXT) == EvidenceRole.OTHER
    assert role_for(EvidenceKind.UNKNOWN) == EvidenceRole.OTHER


def test_lines_must_add_up_and_have_a_category() -> None:
    entry = confirmed_entry(USER, date(2026, 11, 4), 15000, "out", "personal_food")
    transaction = from_entry(entry, None, EvidenceRole.OTHER)
    split = (
        TransactionLine(10000, "personal_food", Purpose.PERSONAL),
        TransactionLine(5000, "business_stock", Purpose.BUSINESS),
    )

    assert line_problems(replace(transaction, lines=split)) == []
    assert line_problems(replace(transaction, lines=split[:1])) == [
        "the lines do not add up to the amount"
    ]
    assert line_problems(replace(transaction, lines=())) == [
        "no lines",
        "the lines do not add up to the amount",
    ]
    uncategorised = (TransactionLine(15000, None, Purpose.UNSURE),)
    assert line_problems(replace(transaction, lines=uncategorised)) == ["a line has no category"]


def test_a_transaction_reads_back_as_the_entry_it_came_from() -> None:
    entry = replace(
        confirmed_entry(USER, date(2026, 11, 4), 15000, "out", "personal_food"),
        mpesa_code="UK5AB1CD23",
        run_id=uuid.uuid4(),
    )
    for status in EntryStatus:
        changed = replace(entry, status=status)
        assert as_entry(from_entry(changed, MPESA, EvidenceRole.PAYMENT_PROOF)) == changed


def test_a_split_transaction_has_no_single_category() -> None:
    entry = confirmed_entry(USER, date(2026, 11, 4), 15000, "out", "personal_food")
    split = (
        TransactionLine(10000, "personal_food", Purpose.PERSONAL),
        TransactionLine(5000, "business_stock", Purpose.BUSINESS),
    )
    transaction = replace(from_entry(entry, None, EvidenceRole.OTHER), lines=split)

    shown = as_entry(transaction)

    assert (shown.category, shown.purpose) == (None, Purpose.UNSURE)


def test_a_candidate_has_no_entry() -> None:
    entry = confirmed_entry(USER, date(2026, 11, 4), 15000, "out", "personal_food")
    candidate = replace(
        from_entry(entry, None, EvidenceRole.RECEIPT), status=TransactionStatus.CANDIDATE
    )

    with pytest.raises(ValueError):
        as_entry(candidate)

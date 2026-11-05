from datetime import date

import pytest
from samples import CERTIFICATE, MPESA, MPESA_PAYBILL, MPESA_SENT

from jalada.domain.categories import Direction
from jalada.domain.evidence import EvidenceKind
from jalada.domain.money import to_cents
from jalada.pipeline.certificates import parse_certificate
from jalada.pipeline.detector import detect
from jalada.pipeline.mpesa import parse_mpesa


@pytest.mark.parametrize(
    ("text", "cents"),
    [("Ksh1,000.00", 100000), ("40,000.00", 4000000), ("Ksh7.00", 700), ("0.5", 50), ("abc", None)],
)
def test_amounts_become_whole_cents(text: str, cents: int | None) -> None:
    assert to_cents(text) == cents


@pytest.mark.parametrize(
    ("text", "content_type", "kind"),
    [
        (MPESA_SENT, "text/plain", EvidenceKind.MPESA_MESSAGE),
        (MPESA, "text/plain", EvidenceKind.MPESA_MESSAGE),
        (CERTIFICATE, "application/pdf", EvidenceKind.WITHHOLDING_CERTIFICATE),
        ("Lunch with a client, 800 bob", "text/plain", EvidenceKind.FREE_TEXT),
        ("Net pay 45,000", "application/pdf", EvidenceKind.PAYSLIP),
        (None, "image/jpeg", EvidenceKind.UNKNOWN),
        ("some receipt text", "image/jpeg", EvidenceKind.UNKNOWN),
    ],
)
def test_detector(text: str | None, content_type: str, kind: EvidenceKind) -> None:
    assert detect(text, content_type) == kind


def test_money_sent_to_a_person() -> None:
    extraction = parse_mpesa(MPESA_SENT)

    assert extraction is not None
    assert extraction.mpesa_code == "UK5AB1CD23"
    assert extraction.direction == Direction.OUT
    assert extraction.amount_cents == 15000
    assert extraction.fee_cents == 700
    assert extraction.counterparty == "JANE WANJIKU"
    assert extraction.occurred_on == date(2026, 11, 5)


def test_money_sent_to_a_paybill_keeps_the_account_reference() -> None:
    extraction = parse_mpesa(MPESA_PAYBILL)

    assert extraction is not None
    assert extraction.counterparty == "M-PESA CARD"
    assert extraction.reference == "Paystack-Shop-Music +254700000000KE"
    assert extraction.amount_cents == 41900
    assert extraction.fee_cents == 0


def test_money_received() -> None:
    extraction = parse_mpesa(MPESA)

    assert extraction is not None
    assert extraction.direction == Direction.IN
    assert extraction.amount_cents == 100000
    assert extraction.counterparty == "EXAMPLE BANK 1 500000"
    assert extraction.fee_cents is None
    assert extraction.occurred_on == date(2026, 11, 4)


def test_unknown_mpesa_wording_is_left_for_the_model() -> None:
    assert parse_mpesa("UK5AB1CD26 Confirmed. Ksh50.00 paid to SOME SHOP. on 5/11/26") is None


def test_an_impossible_date_is_left_empty() -> None:
    extraction = parse_mpesa(MPESA_SENT.replace("5/11/26", "31/02/26"))

    assert extraction is not None and extraction.occurred_on is None


def test_withholding_certificate() -> None:
    extraction = parse_certificate(CERTIFICATE)

    assert extraction is not None
    assert extraction.certificate_serial == "KRAWHTEON0000000001"
    assert extraction.counterparty == "EXAMPLE CONSULTING LTD"
    assert extraction.payer_tax_number == "P000000000A"
    assert extraction.amount_cents == 4000000
    assert extraction.tax_withheld_cents == 200000
    assert extraction.tax_rate_percent == "5.00"
    assert extraction.occurred_on == date(2026, 3, 3)
    assert extraction.direction == Direction.IN
    assert extraction.nature == (
        "Management, Professional Training or Consultancy Fees Which Is Over 24,000 In A Month"
    )

"""Rules for M-Pesa confirmation messages, as worded in docs/domain/mpesa-messages.md."""

import re
from datetime import date, datetime

from jalada.modules.evidence.domain.evidence import EvidenceKind
from jalada.modules.ledger.domain.categories import Direction
from jalada.modules.pipeline.domain.extraction import Extraction
from jalada.shared.money import to_cents

AMOUNT = r"Ksh[0-9,]+\.[0-9]{2}"
WHEN = r"on (?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{2}) at (?P<time>\d{1,2}:\d{2} [AP]M)"

SENT_TO_ACCOUNT = re.compile(
    rf"^(?P<code>[A-Z0-9]{{10}}) Confirmed\. ?(?P<amount>{AMOUNT}) sent to (?P<name>.+?) "
    rf"for account (?P<account>.+?)\s+{WHEN}"
)
SENT_TO_PERSON = re.compile(
    rf"^(?P<code>[A-Z0-9]{{10}}) Confirmed\. ?(?P<amount>{AMOUNT}) sent to (?P<name>.+?) "
    rf"(?P<phone>(?:\+?254|0)\d{{9}}) {WHEN}"
)
RECEIVED = re.compile(
    rf"^(?P<code>[A-Z0-9]{{10}}) Confirmed\. ?You have received (?P<amount>{AMOUNT}) "
    rf"from (?P<name>.+?) {WHEN}"
)
FEE = re.compile(rf"Transaction cost, (?P<fee>{AMOUNT})")


def parse_mpesa(text: str) -> Extraction | None:
    """Fields from a sent or received confirmation. None for wording the rules do not know."""
    text = " ".join(text.split())
    for pattern, direction in (
        (SENT_TO_ACCOUNT, Direction.OUT),
        (SENT_TO_PERSON, Direction.OUT),
        (RECEIVED, Direction.IN),
    ):
        match = pattern.match(text)
        if match:
            return _to_extraction(match, direction, text)
    return None


def _to_extraction(match: re.Match[str], direction: Direction, text: str) -> Extraction:
    fields = match.groupdict()
    fee = FEE.search(text)
    return Extraction(
        kind=EvidenceKind.MPESA_MESSAGE,
        occurred_on=_date(fields),
        direction=direction,
        amount_cents=to_cents(fields["amount"]),
        counterparty=fields["name"].strip(),
        reference=fields.get("account"),
        mpesa_code=fields["code"],
        fee_cents=to_cents(fee.group("fee")) if fee else None,
    )


def _date(fields: dict[str, str]) -> date | None:
    try:
        return datetime(2000 + int(fields["year"]), int(fields["month"]), int(fields["day"])).date()
    except ValueError:
        return None

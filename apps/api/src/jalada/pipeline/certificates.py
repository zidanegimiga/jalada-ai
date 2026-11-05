"""Rules for iTax withholding certificates, as laid out in docs/domain."""

import re
from datetime import date, datetime

from jalada.domain.categories import Direction
from jalada.domain.evidence import EvidenceKind
from jalada.domain.extraction import Extraction
from jalada.domain.money import to_cents

FIELDS = {
    "serial": r"Certificate Serial Number:?\s*(KRAWHT[A-Z0-9]+)",
    "payer_pin": r"PIN of Withholder\s+([A-Z]\d{9}[A-Z])",
    "payer": r"Name of Withholder\s+(.+)",
    # The label sits in the middle of its own value, so read the whole section around it.
    "nature": r"(?s)Details of Tax Withheld\s+(.+?)\s+Transaction Date",
    "date": r"Transaction Date\s+(\d{2}/\d{2}/\d{4})",
    "gross": r"Gross Amount of Transaction \(Ksh\)\s+([0-9,]+\.\d{2})",
    "rate": r"Withholding Tax Rate\s+([0-9.]+)",
    "withheld": r"Amount of Tax Withheld \(Ksh\)\s+([0-9,]+\.\d{2})",
}


def parse_certificate(text: str) -> Extraction | None:
    found = {name: re.search(pattern, text) for name, pattern in FIELDS.items()}
    if not (found["serial"] and found["gross"]):
        return None
    value = {name: " ".join(m.group(1).split()) if m else None for name, m in found.items()}
    return Extraction(
        kind=EvidenceKind.WITHHOLDING_CERTIFICATE,
        occurred_on=_date(value["date"]),
        direction=Direction.IN,
        amount_cents=to_cents(value["gross"] or ""),
        counterparty=value["payer"],
        certificate_serial=value["serial"],
        tax_withheld_cents=to_cents(value["withheld"] or ""),
        tax_rate_percent=value["rate"],
        payer_tax_number=value["payer_pin"],
        nature=(value["nature"] or "").replace("Nature of Transaction ", "") or None,
    )


def _date(text: str | None) -> date | None:
    try:
        return datetime.strptime(text or "", "%d/%m/%Y").date()
    except ValueError:
        return None

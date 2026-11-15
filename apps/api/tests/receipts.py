"""A made-up receipt and the paybill payment it belongs to, for the matching tests."""

import uuid
from collections.abc import Callable

USER = uuid.uuid4()
# The receipt for the paybill payment in samples.MPESA_PAYBILL: the same amount on the
# same day.
RECEIPT = {
    "kind": "receipt",
    "occurred_on": "2026-11-05",
    "direction": "out",
    "amount_ksh": "419.00",
    "counterparty": "SAMPLE MUSIC SHOP",
    "confidence": 0.95,
}
LEISURE = {"purpose": "personal", "category": "personal_other", "confidence": 0.95}
# Sends a receipt photo ("receipt") or the paybill message ("message"), reads it, and
# returns the evidence id and the outcome.
Send = Callable[..., tuple[uuid.UUID, str]]

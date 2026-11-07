import re
from decimal import Decimal, InvalidOperation

AMOUNT = re.compile(r"(?:Ksh|KES|Kshs)?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", re.IGNORECASE)


def to_cents(text: str) -> int | None:
    """'Ksh1,000.00' or '40,000.00' to 100000 or 4000000. Money is never held as a float."""
    match = AMOUNT.fullmatch(text.strip())
    if not match:
        return None
    try:
        return int(Decimal(match.group(1).replace(",", "")) * 100)
    except InvalidOperation:
        return None


def format_ksh(cents: int) -> str:
    return f"KSh {cents / 100:,.2f}"

"""Every amount in an answer must come from the person's records.

Amounts are numbers with a decimal point or thousands separator, numbers of 100 or more,
and numbers after a currency. Small whole numbers such as counts and days are not checked:
"3 payments" or "on the 15th" cannot be matched reliably and are rarely the risk.
"""

import re
from collections.abc import Iterable
from decimal import Decimal, InvalidOperation

# Ids hold digits that could match an amount by chance, so they are removed first.
ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)
NUMBER = re.compile(r"(?<![\w.])(?:(ksh|kes)\s*\.?\s*)?(\d{1,3}(?:,\d{3})+|\d+)(\.\d+)?", re.I)


def amounts(text: str) -> set[Decimal]:
    """The amounts in some text, as numbers, so 1,500 and 1500.00 are the same."""
    found: set[Decimal] = set()
    for currency, whole, fraction in NUMBER.findall(text):
        value = _number(whole.replace(",", "") + fraction)
        if value is None:
            continue
        if currency or fraction or "," in whole or value >= 100:
            found.add(value)
    return found


def numbers(text: str) -> set[Decimal]:
    """Every number in some text, small ones included, to check amounts against."""
    found: set[Decimal] = set()
    for _, whole, fraction in NUMBER.findall(ID.sub(" ", text)):
        value = _number(whole.replace(",", "") + fraction)
        if value is not None:
            found.add(value)
    return found


def ungrounded(answer: str, sources: Iterable[str]) -> list[Decimal]:
    """Amounts in the answer that appear in none of the sources, smallest first."""
    known: set[Decimal] = set()
    for source in sources:
        known |= numbers(source)
    return sorted(amounts(answer) - known)


def _number(text: str) -> Decimal | None:
    try:
        return Decimal(text).normalize()
    except InvalidOperation:
        return None


# How an answer tells the person a change is waiting for them. "Confirm" only with a capital,
# as the button is named: "I cannot confirm what you owe" promises nothing.
WAITING_CHANGE = re.compile(r"\b(?i:tap|tapping|suggested)\b|\bConfirm\b")


def promises_a_change(answer: str) -> bool:
    """Whether the answer says a change waits for the person's tap, which must then be true."""
    return bool(WAITING_CHANGE.search(answer))

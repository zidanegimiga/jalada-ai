from collections.abc import Callable, Sequence

from jalada.modules.evidence.domain.evidence import Evidence, EvidenceSource
from jalada.modules.ledger.domain.categories import CATEGORIES, Direction
from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.telegram.application.ports import ChatChannel
from jalada.shared.money import format_ksh
from jalada.unit_of_work import UnitOfWork

# The verifier's reasons for holding an entry back, in words for the user.
REASONS = {
    "purpose not certain": "I was not sure what it was for.",
    "amount or date not certain": "I was not sure I read the amount and date right.",
    "no amount": "I could not find the amount.",
    "no date": "I could not find the date.",
    "date is in the future": "The date is after today, which looks wrong.",
    "date is more than seven years ago": (
        "The date is more than seven years ago, which looks wrong."
    ),
    "no direction": "I could not tell if the money came in or went out.",
    "no certificate serial": "I could not find the certificate number.",
    "no tax amounts": "I could not find the tax amounts.",
    "tax withheld does not match gross amount times rate": (
        "The tax withheld does not match the amount and rate."
    ),
}
SOMETHING_ELSE = "Some details need a look."


class TelegramNotifier:
    """Replies in the Telegram chat that sent the evidence, once it has been read."""

    def __init__(
        self, unit_of_work: Callable[[], UnitOfWork], bot: ChatChannel, review_url: str
    ) -> None:
        self._unit_of_work = unit_of_work
        self._bot = bot
        self._review_url = review_url

    def notify(
        self, evidence: Evidence, outcome: str, entry: Entry | None, reasons: list[str]
    ) -> None:
        if evidence.source != EvidenceSource.TELEGRAM:
            return
        with self._unit_of_work() as work:
            chat_id = work.telegram.chat_for(evidence.user_id)
        if chat_id is not None:
            self._bot.send(chat_id, self.message(outcome, entry, reasons))

    def message(self, outcome: str, entry: Entry | None, reasons: Sequence[str] = ()) -> str:
        if outcome == "duplicate":
            return "That transaction is already in your records."
        if outcome == "linked" and entry is not None:
            return f"That is the same payment as {_summary(entry)}, so I added it there as proof."
        if entry is None or entry.amount_cents is None:
            return f"I could not read that one. You can type it in here: {self._review_url}"
        summary = _summary(entry)
        category = CATEGORIES.get(entry.category or "")
        if category:
            summary = f"{summary}: {category.name}"
        if outcome == "proposed":
            return f"{summary}. Confirm it here: {self._review_url}"
        return f"{summary}. {_explain(reasons)} Check it here: {self._review_url}"


def _summary(entry: Entry) -> str:
    """For example "KSh 150.00 to JANE WANJIKU on 5 Nov 2026"."""
    words = [format_ksh(entry.amount_cents or 0)]
    if entry.counterparty:
        words.append(("from " if entry.direction == Direction.IN else "to ") + entry.counterparty)
    if entry.occurred_on:
        words.append(f"on {entry.occurred_on.day} {entry.occurred_on:%b %Y}")
    return " ".join(words)


def _explain(reasons: Sequence[str]) -> str:
    """One sentence per reason, each said once, in the order the verifier found them."""
    sentences = dict.fromkeys(REASONS.get(reason, SOMETHING_ELSE) for reason in reasons)
    return " ".join(sentences) or SOMETHING_ELSE

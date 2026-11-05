from collections.abc import Callable

from jalada.application.ports import ChatChannel, UnitOfWork
from jalada.domain.categories import CATEGORIES, Direction
from jalada.domain.entries import Entry
from jalada.domain.evidence import Evidence, EvidenceSource
from jalada.domain.money import format_ksh


class TelegramNotifier:
    """Replies in the Telegram chat that sent the evidence, once it has been read."""

    def __init__(
        self, unit_of_work: Callable[[], UnitOfWork], bot: ChatChannel, review_url: str
    ) -> None:
        self._unit_of_work = unit_of_work
        self._bot = bot
        self._review_url = review_url

    def notify(self, evidence: Evidence, outcome: str, entry: Entry | None) -> None:
        if evidence.source != EvidenceSource.TELEGRAM:
            return
        with self._unit_of_work() as work:
            chat_id = work.telegram.chat_for(evidence.user_id)
        if chat_id is not None:
            self._bot.send(chat_id, self.message(outcome, entry))

    def message(self, outcome: str, entry: Entry | None) -> str:
        if outcome == "duplicate":
            return "That transaction is already in your records."
        if entry is None or entry.amount_cents is None:
            return f"I could not read that one. You can type it in here: {self._review_url}"
        summary = _summary(entry)
        category = CATEGORIES.get(entry.category or "")
        if outcome == "proposed" and category:
            return f"{summary}: {category.name}. Confirm it here: {self._review_url}"
        return f"{summary}. I was not sure what it was for. Check it here: {self._review_url}"


def _summary(entry: Entry) -> str:
    """For example "KSh 150.00 to JANE WANJIKU on 5 Nov 2026"."""
    words = [format_ksh(entry.amount_cents or 0)]
    if entry.counterparty:
        words.append(("from " if entry.direction == Direction.IN else "to ") + entry.counterparty)
    if entry.occurred_on:
        words.append(f"on {entry.occurred_on.day} {entry.occurred_on:%b %Y}")
    return " ".join(words)

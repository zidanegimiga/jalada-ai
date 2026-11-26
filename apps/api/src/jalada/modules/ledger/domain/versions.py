from collections.abc import Callable

from jalada.modules.ledger.domain.entries import Entry


class ChangedElsewhere(Exception):
    """An edit was made from a copy older than the entry now is: on another device, or
    queued offline while it changed. Nothing is merged; the person sees both and picks
    (decision 0029)."""

    def __init__(self, current: Entry) -> None:
        super().__init__("The entry changed since this edit was made.")
        self.current = current


def still_current(version: int, based_on: int | None, current: Callable[[], Entry]) -> None:
    """Passes when the edit was made from this version, or did not say which."""
    if based_on is not None and based_on != version:
        raise ChangedElsewhere(current())

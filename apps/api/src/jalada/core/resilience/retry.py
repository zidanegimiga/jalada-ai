import random
from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RetryPolicy:
    """How often to try one provider, and how long to wait between tries.

    Waits double from `base_delay`, never beyond `max_delay`, with jitter so many callers
    do not retry in step. A wait the provider asked for is used instead, within the cap.
    """

    tries: int = 2
    base_delay: float = 0.5
    max_delay: float = 8.0
    jitter: Callable[[], float] = field(default=lambda: random.uniform(0.5, 1.0))  # noqa: S311

    def wait_before(self, retry_number: int, asked_for: float | None = None) -> float:
        """Seconds to wait before retry number `retry_number` (1 for the first retry)."""
        if asked_for is not None:
            return float(min(asked_for, self.max_delay))
        backoff = self.base_delay * 2 ** (retry_number - 1)
        return float(min(backoff, self.max_delay) * self.jitter())


NO_RETRIES = RetryPolicy(tries=1)

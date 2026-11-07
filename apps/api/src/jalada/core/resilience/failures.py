from enum import StrEnum


class FailureKind(StrEnum):
    """Why a provider call failed, which decides what happens next."""

    # Worth trying the same provider again after a wait.
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    UNAVAILABLE = "unavailable"
    # Not worth repeating on the same provider; the next one may manage.
    BAD_OUTPUT = "bad_output"
    TOO_LARGE = "too_large"
    REFUSED = "refused"
    MISCONFIGURED = "misconfigured"


RETRYABLE = frozenset({FailureKind.TIMEOUT, FailureKind.RATE_LIMITED, FailureKind.UNAVAILABLE})


class ProviderFailure(Exception):
    """A provider call failed. Carries only the kind: provider messages can repeat the input,
    which may be someone's financial records."""

    def __init__(self, kind: FailureKind, retry_after: float | None = None) -> None:
        super().__init__(kind.value)
        self.kind = kind
        # Seconds the provider asked us to wait, when it said.
        self.retry_after = retry_after

    @property
    def retryable(self) -> bool:
        return self.kind in RETRYABLE

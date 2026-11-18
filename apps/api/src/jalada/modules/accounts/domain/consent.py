"""A person's agreement to have their records read by a language model provider.

Sending receipts, messages and questions to a provider's servers is a transfer out of Kenya,
and M-Pesa records may count as sensitive "property details" under the Data Protection Act,
so the app asks first (decision 0026). The agreement names the provider: when the provider
changes, so does the notice, and everyone is asked again.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

# Shown when no provider is named in settings, which production does not allow.
UNNAMED_PROVIDER = "the language model provider set up for this app"


@dataclass(frozen=True)
class ModelConsent:
    user_id: UUID
    # The provider notice the person agreed to, word for word.
    notice: str
    given_at: datetime


@dataclass(frozen=True)
class ConsentStatus:
    # False when no model is set up, so there is nothing to agree to.
    required: bool
    given: bool
    # Who reads the records, where, and on what terms, in the person's words.
    notice: str


def holds(consent: ModelConsent | None, notice: str) -> bool:
    """Whether a consent covers the provider named now."""
    return consent is not None and consent.notice == notice

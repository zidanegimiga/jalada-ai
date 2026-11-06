from dataclasses import dataclass, field

from jalada.api.rate_limit import RateLimiter
from jalada.application.account_deletion import AccountDeletion
from jalada.application.account_export import AccountExport
from jalada.application.authentication import Authenticator
from jalada.application.certificate_payments import CertificatePayments
from jalada.application.entry_review import EntryReview
from jalada.application.evidence_capture import EvidenceCapture
from jalada.application.google_sign_in import GoogleSignIn
from jalada.application.ledger import Ledger
from jalada.application.ports import HealthCheck
from jalada.application.tax_year_export import TaxYearExport
from jalada.application.telegram_capture import TelegramCapture
from jalada.application.telegram_linking import TelegramLinking


@dataclass(frozen=True)
class Services:
    """Everything the routes need, built once in the composition root."""

    authenticator: Authenticator
    sign_in_limiter: RateLimiter
    evidence: EvidenceCapture
    upload_limiter: RateLimiter
    review: EntryReview
    ledger: Ledger
    certificate_payments: CertificatePayments
    tax_year_export: TaxYearExport
    telegram_linking: TelegramLinking
    account_export: AccountExport
    account_deletion: AccountDeletion
    # None when Google sign-in is not configured.
    google_sign_in: GoogleSignIn | None = None
    # None when the Telegram bot is not configured.
    telegram_capture: TelegramCapture | None = None
    # What /health/ready checks: the database and evidence storage.
    health_checks: list[HealthCheck] = field(default_factory=list)

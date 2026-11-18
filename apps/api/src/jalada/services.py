from dataclasses import dataclass, field

from jalada.core.ports import HealthCheck
from jalada.modules.accounts.application.account_deletion import AccountDeletion
from jalada.modules.accounts.application.account_export import AccountExport
from jalada.modules.accounts.application.authentication import Authenticator
from jalada.modules.accounts.application.google_sign_in import GoogleSignIn
from jalada.modules.agent.application.conversations import Conversations
from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.exports.application.tax_year_export import TaxYearExport
from jalada.modules.ledger.application.certificate_payments import CertificatePayments
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.how_paid import HowPaid
from jalada.modules.ledger.application.ledger import Ledger
from jalada.modules.ledger.application.match_review import MatchReview
from jalada.modules.ledger.application.own_accounts import OwnAccounts
from jalada.modules.telegram.application.telegram_capture import TelegramCapture
from jalada.modules.telegram.application.telegram_linking import TelegramLinking
from jalada.shared.http.rate_limit import RateLimiter


@dataclass(frozen=True)
class Services:
    """Everything the routes need, built once in the composition root."""

    authenticator: Authenticator
    sign_in_limiter: RateLimiter
    evidence: EvidenceCapture
    upload_limiter: RateLimiter
    review: EntryReview
    matches: MatchReview
    how_paid: HowPaid
    own_accounts: OwnAccounts
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
    # None unless the assistant is switched on (decision 0025).
    conversations: Conversations | None = None
    # What /health/ready checks: the database and evidence storage.
    health_checks: list[HealthCheck] = field(default_factory=list)

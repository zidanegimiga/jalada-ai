"""Builds the ledger module's use cases from the pieces the composition root shares."""

from collections.abc import Callable
from dataclasses import dataclass

from jalada.core.ports import Clock
from jalada.modules.ledger.application.certificate_payments import CertificatePayments
from jalada.modules.ledger.application.entry_review import EntryReview
from jalada.modules.ledger.application.how_paid import HowPaid
from jalada.modules.ledger.application.ledger import Ledger
from jalada.modules.ledger.application.match_review import MatchReview
from jalada.modules.ledger.application.own_accounts import OwnAccounts
from jalada.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class LedgerServices:
    review: EntryReview
    matches: MatchReview
    how_paid: HowPaid
    own_accounts: OwnAccounts
    ledger: Ledger
    certificate_payments: CertificatePayments


def build_ledger(unit_of_work: Callable[[], UnitOfWork], clock: Clock) -> LedgerServices:
    return LedgerServices(
        review=EntryReview(unit_of_work, clock),
        matches=MatchReview(unit_of_work, clock),
        how_paid=HowPaid(unit_of_work, clock),
        own_accounts=OwnAccounts(unit_of_work, clock),
        ledger=Ledger(unit_of_work),
        certificate_payments=CertificatePayments(unit_of_work, clock),
    )

from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import IO
from uuid import UUID

from jalada.modules.accounts.application.ports import ArchiveWriter
from jalada.modules.accounts.domain.users import User
from jalada.modules.evidence.application.ports import EvidenceStore
from jalada.modules.evidence.domain.evidence import Evidence
from jalada.modules.ledger.application.ports import Revision
from jalada.modules.ledger.domain.entries import Entry
from jalada.modules.ledger.domain.money_accounts import MoneyAccount
from jalada.modules.pipeline.application.ports import PipelineRun
from jalada.modules.pipeline.domain.classifier import Preference
from jalada.modules.pipeline.domain.run_types import StepRecord
from jalada.shared.errors import NotSignedIn
from jalada.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class AccountData:
    """Everything held about one user, apart from secrets such as the password hash."""

    user: User
    telegram_linked: bool
    evidence: list[Evidence]
    entries: list[Entry]
    revisions: list[Revision]
    runs: list[tuple[PipelineRun, list[StepRecord]]]
    preferences: dict[str, Preference]
    # Payment entry id to the certificate entry id it was linked to.
    certificate_payments: dict[UUID, UUID] = field(default_factory=dict)
    money_accounts: list[MoneyAccount] = field(default_factory=list)


class AccountExport:
    """A copy of all of a user's data, including the original files, in one download."""

    def __init__(
        self,
        unit_of_work: Callable[[], UnitOfWork],
        store: EvidenceStore,
        writer: ArchiveWriter,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._store = store
        self._writer = writer

    @property
    def content_type(self) -> str:
        return self._writer.content_type

    @property
    def extension(self) -> str:
        return self._writer.extension

    def collect(self, user_id: UUID) -> AccountData:
        with self._unit_of_work() as work:
            user = work.users.get(user_id)
            if user is None:
                raise NotSignedIn
            return AccountData(
                user=user,
                telegram_linked=work.telegram.chat_for(user_id) is not None,
                evidence=work.evidence_for(user_id).all(),
                entries=work.entries_for(user_id).all(),
                revisions=work.entries_for(user_id).revisions(),
                runs=work.runs.for_user(user_id),
                preferences=work.preferences_for(user_id).all(),
                certificate_payments=work.certificate_payments_for(user_id).links(),
                money_accounts=work.money_accounts_for(user_id).all(),
            )

    def write(self, user_id: UUID, out: IO[bytes]) -> None:
        data = self.collect(user_id)
        self._writer.write(data, self._originals(user_id, data.evidence), out)

    def _originals(
        self, user_id: UUID, evidence: list[Evidence]
    ) -> Iterator[tuple[Evidence, bytes]]:
        """One original at a time, so a year of photos is never all in memory at once."""
        for item in evidence:
            yield item, self._store.get(item.id, user_id, item.encryption_key_id)

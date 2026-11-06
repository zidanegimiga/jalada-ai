from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import IO
from uuid import UUID

from jalada.application.errors import NotSignedIn
from jalada.application.ports import (
    ArchiveWriter,
    EvidenceStore,
    PipelineRun,
    Revision,
    UnitOfWork,
)
from jalada.domain.entries import Entry
from jalada.domain.evidence import Evidence
from jalada.domain.users import User
from jalada.pipeline.classifier import Preference
from jalada.pipeline.run_types import StepRecord


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

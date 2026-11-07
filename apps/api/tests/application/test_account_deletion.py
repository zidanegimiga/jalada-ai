import uuid

import pytest
from fakes import FakeEvidenceStore, FakeUnitOfWork, Store
from samples import JPEG, MPESA

from jalada.modules.accounts.application.account_deletion import AccountDeletion
from jalada.modules.accounts.application.authentication import Authenticator
from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceSource
from jalada.modules.telegram.application.telegram_linking import TelegramLinking
from jalada.shared.errors import ConfirmationMismatch


@pytest.fixture
def deletion(store: Store, evidence_store: FakeEvidenceStore) -> AccountDeletion:
    return AccountDeletion(lambda: FakeUnitOfWork(store), evidence_store)


@pytest.fixture
def jane(
    authenticator: Authenticator, capture: EvidenceCapture, linking: TelegramLinking
) -> uuid.UUID:
    user = authenticator.sign_up("jane@example.com", "correct horse battery", "Jane").user
    capture.capture_file(user.id, JPEG, EvidenceSource.WEB_UPLOAD)
    capture.capture_text(user.id, MPESA, EvidenceSource.WEB_PASTE)
    linking.link(linking.new_code(user.id).code, 111, 222)
    return user.id


def test_a_mistyped_email_deletes_nothing(
    deletion: AccountDeletion, jane: uuid.UUID, store: Store, evidence_store: FakeEvidenceStore
) -> None:
    with pytest.raises(ConfirmationMismatch):
        deletion.delete(jane, "jane@exmaple.com")

    assert jane in store.users
    assert len(evidence_store.objects) == 2


def test_everything_about_the_user_is_deleted(
    deletion: AccountDeletion,
    jane: uuid.UUID,
    store: Store,
    evidence_store: FakeEvidenceStore,
    authenticator: Authenticator,
    capture: EvidenceCapture,
) -> None:
    other = authenticator.sign_up("other@example.com", "another long password", "O").user
    capture.capture_text(other.id, "someone else's note", EvidenceSource.WEB_PASTE)

    deletion.delete(jane, "  Jane@Example.com ")

    assert jane not in store.users
    assert [owner for owner, _ in evidence_store.objects] == [other.id]
    assert all(e.user_id == other.id for e in store.evidence.values())
    assert all(s.user_id == other.id for s in store.sessions.values())
    assert all(p.get("user_id") == str(other.id) for _, p in store.jobs)
    assert jane not in store.telegram_links

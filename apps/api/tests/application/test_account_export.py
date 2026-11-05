import io
import json
import uuid
import zipfile

import pytest
from fakes import FakeEvidenceStore, FakeTextReader, FakeUnitOfWork, FixedClock, Store
from samples import JPEG, MPESA_SENT

from jalada.adapters.export.account_archive import ZipAccountArchive
from jalada.application.account_export import AccountExport
from jalada.application.authentication import Authenticator
from jalada.application.entry_review import EntryReview
from jalada.application.errors import NotSignedIn
from jalada.application.evidence_capture import EvidenceCapture
from jalada.application.evidence_processing import EvidenceProcessor
from jalada.domain.entries import Correction
from jalada.domain.evidence import EvidenceSource
from jalada.pipeline.run_types import Budget


@pytest.fixture
def user_id(
    authenticator: Authenticator,
    capture: EvidenceCapture,
    review: EntryReview,
    store: Store,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
) -> uuid.UUID:
    """A user with a photo and a processed, corrected M-Pesa message."""
    user = authenticator.sign_up("jane@example.com", "correct horse battery", "Jane").user
    capture.capture_file(user.id, JPEG, EvidenceSource.WEB_UPLOAD)
    message = capture.capture_text(user.id, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence
    EvidenceProcessor(
        lambda: FakeUnitOfWork(store), evidence_store, FakeTextReader(), clock, Budget()
    ).process(user.id, message.id)
    [entry] = store.entries.values()
    review.confirm(user.id, entry.id, Correction(category="personal_family_support"))
    return user.id


def export_zip(
    store: Store, evidence_store: FakeEvidenceStore, user_id: uuid.UUID
) -> zipfile.ZipFile:
    out = io.BytesIO()
    AccountExport(lambda: FakeUnitOfWork(store), evidence_store, ZipAccountArchive()).write(
        user_id, out
    )
    return zipfile.ZipFile(io.BytesIO(out.getvalue()))


def test_the_archive_holds_every_kind_of_data(
    store: Store, evidence_store: FakeEvidenceStore, user_id: uuid.UUID
) -> None:
    archive = export_zip(store, evidence_store, user_id)
    names = set(archive.namelist())

    assert {
        "README.txt",
        "account.json",
        "evidence.json",
        "entries.json",
        "entry_revisions.json",
        "pipeline_runs.json",
        "preferences.json",
    } <= names
    account = json.loads(archive.read("account.json"))
    assert account["email"] == "jane@example.com" and account["telegram_linked"] is False
    [entry] = json.loads(archive.read("entries.json"))
    assert entry["amount_cents"] == 15000 and entry["status"] == "confirmed"
    assert len(json.loads(archive.read("entry_revisions.json"))) == 1
    [run] = json.loads(archive.read("pipeline_runs.json"))
    assert len(run["steps"]) == 4
    assert "jane wanjiku" in json.loads(archive.read("preferences.json"))


def test_the_originals_come_back_exactly_with_sensible_names(
    store: Store, evidence_store: FakeEvidenceStore, user_id: uuid.UUID
) -> None:
    archive = export_zip(store, evidence_store, user_id)
    listed = {
        item["content_type"]: item["file"] for item in json.loads(archive.read("evidence.json"))
    }

    assert listed["image/jpeg"].endswith(".jpg")
    assert archive.read(listed["image/jpeg"]) == JPEG
    assert archive.read(listed["text/plain; charset=utf-8"]).decode() == MPESA_SENT


def test_secrets_and_other_users_never_appear(
    authenticator: Authenticator,
    capture: EvidenceCapture,
    store: Store,
    evidence_store: FakeEvidenceStore,
    user_id: uuid.UUID,
) -> None:
    other = authenticator.sign_up("other@example.com", "another long password", "O").user
    capture.capture_text(other.id, "someone else's note", EvidenceSource.WEB_PASTE)

    archive = export_zip(store, evidence_store, user_id)
    everything = b"".join(archive.read(name) for name in archive.namelist())

    assert b"hashed:" not in everything, "no password hash"
    assert b"other@example.com" not in everything
    assert b"someone else's note" not in everything


def test_a_user_who_no_longer_exists_cannot_export(
    store: Store, evidence_store: FakeEvidenceStore
) -> None:
    with pytest.raises(NotSignedIn):
        export_zip(store, evidence_store, uuid.uuid4())

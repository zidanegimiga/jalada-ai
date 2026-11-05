import uuid
from datetime import timedelta

import pytest
from fakes import FakeEvidenceStore, FakeUnitOfWork, FixedClock, Store
from samples import JPEG, MPESA

from jalada.application.errors import EmptyEvidence, EvidenceNotFound, FileTooLarge, UnsupportedFile
from jalada.application.evidence_capture import PROCESS_EVIDENCE_JOB, EvidenceCapture
from jalada.domain.evidence import MAX_FILE_BYTES, EvidenceSource, EvidenceStatus

USER = uuid.uuid4()
OTHER_USER = uuid.uuid4()


def test_a_photo_is_stored_recorded_and_queued(
    capture: EvidenceCapture, store: Store, evidence_store: FakeEvidenceStore
) -> None:
    captured = capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD)

    evidence = captured.evidence
    assert captured.duplicate is False
    assert evidence.content_type == "image/jpeg"
    assert evidence.status == EvidenceStatus.RECEIVED
    assert evidence.size_bytes == len(JPEG)
    assert evidence.encryption_key_id == "test-key"
    assert evidence_store.objects[(USER, evidence.id)] == JPEG
    assert store.jobs == [
        (PROCESS_EVIDENCE_JOB, {"evidence_id": str(evidence.id), "user_id": str(USER)})
    ]


def test_pasted_text_is_trimmed_and_stored_as_text(
    capture: EvidenceCapture, evidence_store: FakeEvidenceStore
) -> None:
    captured = capture.capture_text(USER, f"  {MPESA}\n", EvidenceSource.WEB_PASTE)

    assert captured.evidence.content_type == "text/plain; charset=utf-8"
    assert evidence_store.objects[(USER, captured.evidence.id)] == MPESA.encode()


def test_the_same_file_twice_is_only_kept_once(
    capture: EvidenceCapture, store: Store, evidence_store: FakeEvidenceStore
) -> None:
    first = capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD)

    second = capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD)

    assert second.duplicate is True
    assert second.evidence == first.evidence
    assert len(evidence_store.objects) == 1
    assert len(store.jobs) == 1


def test_two_users_can_send_the_same_file(capture: EvidenceCapture) -> None:
    capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD)

    assert not capture.capture_file(OTHER_USER, JPEG, EvidenceSource.WEB_UPLOAD).duplicate


@pytest.mark.parametrize(
    ("data", "error"),
    [(b"not a picture", UnsupportedFile), (JPEG + b"0" * MAX_FILE_BYTES, FileTooLarge)],
)
def test_bad_files_are_refused_before_anything_is_stored(
    capture: EvidenceCapture,
    evidence_store: FakeEvidenceStore,
    data: bytes,
    error: type[Exception],
) -> None:
    with pytest.raises(error):
        capture.capture_file(USER, data, EvidenceSource.WEB_UPLOAD)

    assert evidence_store.objects == {}


@pytest.mark.parametrize(("text", "error"), [("   ", EmptyEvidence), ("x" * 5001, FileTooLarge)])
def test_empty_or_huge_text_is_refused(
    capture: EvidenceCapture, text: str, error: type[Exception]
) -> None:
    with pytest.raises(error):
        capture.capture_text(USER, text, EvidenceSource.WEB_PASTE)


def test_the_stored_file_is_removed_if_saving_the_record_fails(
    store: Store, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> None:
    class BrokenCommit(FakeUnitOfWork):
        def commit(self) -> None:
            raise RuntimeError("database down")

    capture = EvidenceCapture(lambda: BrokenCommit(store), evidence_store, clock)

    with pytest.raises(RuntimeError):
        capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD)

    assert evidence_store.objects == {}


def test_users_only_see_their_own_evidence(capture: EvidenceCapture) -> None:
    mine = capture.capture_file(USER, JPEG, EvidenceSource.WEB_UPLOAD).evidence

    assert capture.list_recent(OTHER_USER) == []
    with pytest.raises(EvidenceNotFound):
        capture.get(OTHER_USER, mine.id)
    with pytest.raises(EvidenceNotFound):
        capture.read_original(OTHER_USER, mine.id)


def test_recent_evidence_is_newest_first(capture: EvidenceCapture, clock: FixedClock) -> None:
    older = capture.capture_text(USER, "first", EvidenceSource.WEB_PASTE).evidence
    clock.current += timedelta(minutes=1)
    newer = capture.capture_text(USER, "second", EvidenceSource.WEB_PASTE).evidence

    assert capture.list_recent(USER) == [newer, older]

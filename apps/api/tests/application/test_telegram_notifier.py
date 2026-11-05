import uuid
from dataclasses import replace
from datetime import date

import pytest
from fakes import FakeChat, FakeEvidenceStore, FakeTextReader, FakeUnitOfWork, FixedClock, Store
from samples import JPEG, MPESA_SENT, confirmed_entry

from jalada.application.evidence_capture import EvidenceCapture
from jalada.application.evidence_processing import EvidenceProcessor
from jalada.application.telegram_linking import TelegramLinking
from jalada.application.telegram_notifier import TelegramNotifier
from jalada.domain.entries import EntryStatus
from jalada.domain.evidence import EvidenceSource
from jalada.pipeline.run_types import Budget

USER = uuid.uuid4()
REVIEW = "https://app.example.com/review"


@pytest.fixture
def notifier(store: Store, chat: FakeChat, linking: TelegramLinking) -> TelegramNotifier:
    linking.link(linking.new_code(USER).code, 111, 222)
    return TelegramNotifier(lambda: FakeUnitOfWork(store), chat, REVIEW)


def test_messages_say_what_was_found_and_where_to_check() -> None:
    notifier = TelegramNotifier(lambda: FakeUnitOfWork(Store()), FakeChat(), REVIEW)
    entry = replace(
        confirmed_entry(USER, date(2026, 11, 5), 15_000, "out", "personal_food"),
        counterparty="JANE WANJIKU",
        status=EntryStatus.PROPOSED,
    )

    assert notifier.message("proposed", entry) == (
        f"KSh 150.00 to JANE WANJIKU on 5 Nov 2026: Food. Confirm it here: {REVIEW}"
    )
    assert notifier.message("needs_review", replace(entry, category=None)) == (
        f"KSh 150.00 to JANE WANJIKU on 5 Nov 2026. I was not sure what it was for. "
        f"Check it here: {REVIEW}"
    )
    assert notifier.message("needs_review", None).startswith("I could not read that one.")
    assert notifier.message("duplicate", None) == "That transaction is already in your records."


def test_only_evidence_sent_through_telegram_gets_a_reply(
    capture: EvidenceCapture,
    store: Store,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
    chat: FakeChat,
    notifier: TelegramNotifier,
) -> None:
    processor = EvidenceProcessor(
        lambda: FakeUnitOfWork(store),
        evidence_store,
        FakeTextReader(),
        clock,
        Budget(),
        notifier=notifier,
    )
    from_web = capture.capture_text(USER, MPESA_SENT, EvidenceSource.WEB_PASTE).evidence
    from_chat = capture.capture_file(USER, JPEG, EvidenceSource.TELEGRAM).evidence

    processor.process(USER, from_web.id)
    processor.process(USER, from_chat.id)

    assert chat.sent == [(222, f"I could not read that one. You can type it in here: {REVIEW}")]


def test_a_failing_reply_does_not_undo_the_processing(
    capture: EvidenceCapture, store: Store, evidence_store: FakeEvidenceStore, clock: FixedClock
) -> None:
    class BrokenNotifier:
        def notify(self, *args: object) -> None:
            raise ConnectionError("Telegram is down")

    processor = EvidenceProcessor(
        lambda: FakeUnitOfWork(store),
        evidence_store,
        FakeTextReader(),
        clock,
        Budget(),
        notifier=BrokenNotifier(),
    )
    evidence = capture.capture_text(USER, MPESA_SENT, EvidenceSource.TELEGRAM).evidence

    assert processor.process(USER, evidence.id) == "needs_review"
    assert len(store.entries) == 1

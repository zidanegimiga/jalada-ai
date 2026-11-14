import uuid
from dataclasses import replace
from datetime import UTC, date, datetime

import pytest
from fakes import FakeChat, FakeEvidenceStore, FakeTextReader, FakeUnitOfWork, FixedClock, Store
from samples import JPEG, MPESA_SENT, confirmed_entry

from jalada.modules.evidence.application.evidence_capture import EvidenceCapture
from jalada.modules.evidence.domain.evidence import EvidenceKind, EvidenceSource
from jalada.modules.ledger.domain.categories import Purpose
from jalada.modules.ledger.domain.entries import EntryStatus
from jalada.modules.pipeline.application.evidence_processing import EvidenceProcessor
from jalada.modules.pipeline.domain.extraction import Classification, Extraction
from jalada.modules.pipeline.domain.run_types import Budget
from jalada.modules.pipeline.domain.verifier import verify
from jalada.modules.telegram.application.telegram_linking import TelegramLinking
from jalada.modules.telegram.application.telegram_notifier import REASONS, TelegramNotifier

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
    unsure = replace(entry, category=None)
    assert notifier.message("needs_review", unsure, ["purpose not certain"]) == (
        f"KSh 150.00 to JANE WANJIKU on 5 Nov 2026. I was not sure what it was for. "
        f"Check it here: {REVIEW}"
    )
    assert notifier.message("needs_review", None).startswith("I could not read that one.")
    assert notifier.message("duplicate", None) == "That transaction is already in your records."


def test_a_held_entry_says_why_it_was_held() -> None:
    notifier = TelegramNotifier(lambda: FakeUnitOfWork(Store()), FakeChat(), REVIEW)
    entry = replace(
        confirmed_entry(USER, date(2026, 11, 6), 30_000, "out", "personal_family_support"),
        counterparty="JANE WANJIKU",
        status=EntryStatus.NEEDS_REVIEW,
    )

    assert notifier.message("needs_review", entry, ["date is in the future"]) == (
        "KSh 300.00 to JANE WANJIKU on 6 Nov 2026: Family support given. "
        f"The date is after today, which looks wrong. Check it here: {REVIEW}"
    )
    both = ["date is in the future", "purpose not certain", "purpose not certain"]
    assert "wrong. I was not sure what it was for. Check" in notifier.message(
        "needs_review", replace(entry, category=None), both
    )
    assert "Some details need a look." in notifier.message("needs_review", entry, ["new"])
    assert "Some details need a look." in notifier.message("needs_review", entry, [])


def test_every_reason_the_verifier_gives_has_words_for_the_user() -> None:
    later = date(2026, 11, 6)
    blank = Extraction(EvidenceKind.WITHHOLDING_CERTIFICATE, later, None, None)
    unsure = Classification(Purpose.UNSURE, None, 0.0, "none")

    verdict = verify(blank, unsure, date(2026, 11, 5), False, extraction_confidence=0.1)
    too_old = verify(replace(blank, occurred_on=date(2010, 1, 1)), unsure, date(2026, 11, 5), False)
    no_date = verify(replace(blank, occurred_on=None), unsure, date(2026, 11, 5), False)
    certificate = replace(
        blank, occurred_on=date(2026, 11, 5), certificate_serial="KRAWHTEON0000000001"
    )
    no_tax = verify(certificate, unsure, date(2026, 11, 5), False)
    mismatch = verify(
        replace(certificate, amount_cents=100_000, tax_withheld_cents=1, tax_rate_percent="5"),
        unsure,
        date(2026, 11, 5),
        False,
    )

    reasons = {
        reason
        for found in (verdict, too_old, no_date, no_tax, mismatch)
        for reason in found.problems + found.review_reasons
    }
    assert reasons <= REASONS.keys()
    assert len(reasons) == len(REASONS)


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


def test_the_reply_carries_the_reasons_the_pipeline_found(
    capture: EvidenceCapture,
    store: Store,
    evidence_store: FakeEvidenceStore,
    clock: FixedClock,
    chat: FakeChat,
    notifier: TelegramNotifier,
) -> None:
    # The message is dated 5 November; in Nairobi it is still 4 November.
    clock.current = datetime(2026, 11, 4, 10, 0, tzinfo=UTC)
    processor = EvidenceProcessor(
        lambda: FakeUnitOfWork(store),
        evidence_store,
        FakeTextReader(),
        clock,
        Budget(),
        notifier=notifier,
    )
    evidence = capture.capture_text(USER, MPESA_SENT, EvidenceSource.TELEGRAM).evidence

    processor.process(USER, evidence.id)

    [(_, text)] = chat.sent
    assert "The date is after today, which looks wrong. I was not sure what it was for." in text


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
    assert len(store.payments()) == 1

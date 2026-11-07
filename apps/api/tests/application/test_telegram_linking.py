import uuid
from datetime import timedelta

from fakes import FakeUnitOfWork, FixedClock, Store

from jalada.modules.telegram.application.telegram_linking import TelegramLinking
from jalada.modules.telegram.domain.telegram import CODE_ALPHABET, CODE_LENGTH

USER = uuid.uuid4()


def linking(store: Store, clock: FixedClock) -> TelegramLinking:
    return TelegramLinking(lambda: FakeUnitOfWork(store), clock)


def test_codes_are_short_unambiguous_and_stored_hashed(store: Store, clock: FixedClock) -> None:
    issued = linking(store, clock).new_code(USER)

    assert len(issued.code) == CODE_LENGTH
    assert set(issued.code) <= set(CODE_ALPHABET)
    assert issued.expires_at == clock.now() + timedelta(minutes=10)
    assert issued.code not in store.telegram_codes


def test_a_code_links_the_telegram_account_once(store: Store, clock: FixedClock) -> None:
    links = linking(store, clock)
    code = links.new_code(USER).code

    assert links.link(code.lower(), telegram_user_id=111, chat_id=222) == USER
    assert links.is_linked(USER)
    assert links.user_for(111) == USER
    assert links.link(code, telegram_user_id=333, chat_id=444) is None, "used up"


def test_an_expired_or_replaced_code_does_not_link(store: Store, clock: FixedClock) -> None:
    links = linking(store, clock)
    old = links.new_code(USER).code
    new = links.new_code(USER).code

    assert links.link(old, 111, 222) is None, "a newer code replaced it"
    clock.current += timedelta(minutes=11)
    assert links.link(new, 111, 222) is None, "expired"
    assert not links.is_linked(USER)


def test_linking_a_telegram_account_again_moves_it(store: Store, clock: FixedClock) -> None:
    links = linking(store, clock)
    other = uuid.uuid4()
    links.link(links.new_code(USER).code, 111, 222)

    links.link(links.new_code(other).code, 111, 222)

    assert links.user_for(111) == other
    assert not links.is_linked(USER)

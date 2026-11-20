import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session, sessionmaker

from jalada.core.idempotency.ports import Answer, Seen
from jalada.core.idempotency.requests import owner_of
from jalada.core.idempotency.sql import SqlIdempotencyStore
from jalada.modules.accounts.adapters.tables import SessionRow, UserRow

NOW = datetime(2026, 11, 20, 9, 0, tzinfo=UTC)
LONG_AGO = NOW - timedelta(days=1)


def a_session(session_factory: sessionmaker[Session], token: str) -> str:
    user_id = uuid.uuid4()
    with session_factory.begin() as db:
        db.add(
            UserRow(id=user_id, email=f"{user_id}@example.com", display_name="J", created_at=NOW)
        )
        db.flush()
        db.add(SessionRow(token_hash=owner_of(token), user_id=user_id, expires_at=NOW))
    return owner_of(token)


def begin(store: SqlIdempotencyStore, owner: str, fingerprint: str = "f1") -> Seen:
    return store.begin(owner, "change-1", fingerprint, NOW, LONG_AGO, LONG_AGO).seen


def test_the_first_answer_is_kept_and_compared(session_factory: sessionmaker[Session]) -> None:
    store = SqlIdempotencyStore(session_factory)
    owner = a_session(session_factory, "token-a")

    assert begin(store, owner) is Seen.NEW
    assert begin(store, owner) is Seen.RUNNING
    store.keep(owner, "change-1", Answer(201, "application/json", b'{"id": 1}'))

    replay = store.begin(owner, "change-1", "f1", NOW, LONG_AGO, LONG_AGO)
    assert replay.seen is Seen.ANSWERED
    assert replay.answer == Answer(201, "application/json", b'{"id": 1}')
    assert begin(store, owner, "f2") is Seen.DIFFERENT


def test_a_dropped_attempt_can_start_again(session_factory: sessionmaker[Session]) -> None:
    store = SqlIdempotencyStore(session_factory)
    owner = a_session(session_factory, "token-a")
    begin(store, owner)

    store.drop(owner, "change-1")

    assert begin(store, owner) is Seen.NEW


def test_old_answers_are_cleared(session_factory: sessionmaker[Session]) -> None:
    store = SqlIdempotencyStore(session_factory)
    owner = a_session(session_factory, "token-a")
    begin(store, owner)
    store.keep(owner, "change-1", Answer(200, None, b""))

    later = NOW + timedelta(days=2)
    seen = store.begin(owner, "change-1", "f1", later, later - timedelta(days=1), later).seen

    assert seen is Seen.NEW


def test_a_token_that_is_not_a_session_keeps_nothing(
    session_factory: sessionmaker[Session],
) -> None:
    store = SqlIdempotencyStore(session_factory)

    assert begin(store, owner_of("made-up")) is Seen.NO_SESSION


def test_signing_out_removes_the_session_answers(session_factory: sessionmaker[Session]) -> None:
    store = SqlIdempotencyStore(session_factory)
    owner = a_session(session_factory, "token-a")
    begin(store, owner)

    with session_factory.begin() as db:
        db.query(SessionRow).filter_by(token_hash=owner).delete()

    assert begin(store, owner) is Seen.NO_SESSION

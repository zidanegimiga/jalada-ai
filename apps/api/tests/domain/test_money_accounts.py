import uuid
from datetime import UTC, datetime

from jalada.modules.ledger.domain.money_accounts import MoneyAccountKind, default_accounts

NOW = datetime(2026, 11, 14, 9, 0, tzinfo=UTC)


def test_every_user_starts_with_mpesa_and_cash() -> None:
    user_id = uuid.uuid4()

    accounts = default_accounts(user_id, NOW)

    assert [(a.kind, a.name) for a in accounts] == [
        (MoneyAccountKind.MPESA, "M-Pesa"),
        (MoneyAccountKind.CASH, "Cash"),
    ]
    assert all(a.user_id == user_id and a.tracked and a.created_at == NOW for a in accounts)
    assert len({a.id for a in accounts}) == 2

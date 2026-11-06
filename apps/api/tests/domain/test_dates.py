from datetime import UTC, date, datetime

from jalada.shared.dates import kenyan_date


def test_kenya_is_three_hours_ahead_of_utc() -> None:
    assert kenyan_date(datetime(2026, 11, 5, 20, 59, tzinfo=UTC)) == date(2026, 11, 5)
    assert kenyan_date(datetime(2026, 11, 5, 21, 0, tzinfo=UTC)) == date(2026, 11, 6)
    assert kenyan_date(datetime(2026, 12, 31, 22, 0, tzinfo=UTC)) == date(2027, 1, 1)

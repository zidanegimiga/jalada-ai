from datetime import date, datetime, timedelta, timezone

# Kenya keeps East Africa Time all year, with no daylight saving.
KENYA_TIME = timezone(timedelta(hours=3), "EAT")


def kenyan_date(moment: datetime) -> date:
    """The date in Kenya at a moment. M-Pesa messages and receipts carry Kenyan dates."""
    return moment.astimezone(KENYA_TIME).date()

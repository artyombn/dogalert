from datetime import date, datetime


def calculate_days_delta(next_date: datetime | date | None) -> int | None:
    if next_date is None:
        return None

    today = date.today()

    if isinstance(next_date, datetime):
        next_date = next_date.date()

    delta = next_date - today
    return delta.days

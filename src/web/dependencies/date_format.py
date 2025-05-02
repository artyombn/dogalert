from datetime import datetime

from babel.dates import format_date


def format_russian_date(date: datetime | None) -> str | None:
    if date is None:
        return None
    return format_date(date, format="d MMMM y", locale="ru")

from datetime import datetime, timezone


def parse_date(date: str | None, current_db_time: datetime | None = None) -> datetime | None:
    if not date:
        return None

    if isinstance(date, datetime):
        if date.tzinfo is not None:
            return date
        return date.replace(tzinfo=timezone.utc)

    if isinstance(date, str):
        if date.strip() == "":
            return None
        try:
            new_date = datetime.strptime(date.strip(), "%Y-%m-%d")
            if (current_db_time and
                    current_db_time.date() == new_date.date()):
                return current_db_time
            return new_date.replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    return None

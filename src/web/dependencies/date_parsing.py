from datetime import UTC, datetime


def parse_date(date: str | None, current_db_time: datetime | None = None) -> datetime | None:
    if not date or date.strip() == "":
        return None

    try:
        new_date = datetime.strptime(date.strip(), "%Y-%m-%d")
        if current_db_time and current_db_time.date() == new_date.date():
            return current_db_time
        return new_date.replace(tzinfo=UTC)
    except ValueError:
        return None

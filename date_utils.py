from datetime import date, datetime

IMDB_DATE_FORMAT = "%b %d, %Y"


def parse_imdb_release_date(date_text: str) -> date:
    return datetime.strptime(date_text, IMDB_DATE_FORMAT).date()

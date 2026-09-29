from __future__ import annotations

from datetime import date, datetime
from functools import cache

IMDB_DATE_FORMAT = "%b %d, %Y"


# ⚡ Bolt: Cache parsed date to avoid redundant datetime.strptime calculation
@cache
def parse_imdb_release_date(date_text: str) -> date:
    return datetime.strptime(date_text, IMDB_DATE_FORMAT).date()

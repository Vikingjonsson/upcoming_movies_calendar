from __future__ import annotations

from datetime import date, datetime
from functools import lru_cache

IMDB_DATE_FORMAT = "%b %d, %Y"


# ⚡ Bolt: Cache parsed dates to prevent redundant datetime.strptime calls
# for movies sharing the exact same release date.
@lru_cache(maxsize=None)
def parse_imdb_release_date(date_text: str) -> date:
    return datetime.strptime(date_text, IMDB_DATE_FORMAT).date()

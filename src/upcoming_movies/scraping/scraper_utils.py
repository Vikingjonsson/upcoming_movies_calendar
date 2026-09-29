from __future__ import annotations

import functools
from datetime import date, datetime

IMDB_DATE_FORMAT = "%b %d, %Y"


# ⚡ Bolt: Used lru_cache to memoize datetime.strptime, avoiding redundant
# string parsing for movies that share the same release date.
@functools.lru_cache(maxsize=128)
def parse_imdb_release_date(date_text: str) -> date:
    return datetime.strptime(date_text, IMDB_DATE_FORMAT).date()

from __future__ import annotations

import functools
from datetime import date, datetime
from email.utils import parsedate_to_datetime

IMDB_DATE_FORMAT = "%b %d, %Y"


@functools.cache
def parse_imdb_release_date(date_text: str) -> date:
    """Parse traditional IMDB release date string (e.g. 'Oct 2, 2026')."""
    return datetime.strptime(date_text, IMDB_DATE_FORMAT).date()


@functools.cache
def parse_flexible_release_date(date_text: str) -> date:
    """Parse release dates from various formats (RFC 2822, ISO, or IMDB textual)."""
    cleaned = date_text.strip()
    # 1. Try RFC 2822 (e.g. "Fri, 02 Oct 2026 00:00:00 GMT")
    try:
        dt = parsedate_to_datetime(cleaned)
        if dt is not None:
            return dt.date()
    except Exception:
        pass

    # 2. Try ISO format (e.g. "2026-10-02")
    try:
        return date.fromisoformat(cleaned)
    except Exception:
        pass

    # 3. Fall back to standard IMDB date format
    return parse_imdb_release_date(cleaned)

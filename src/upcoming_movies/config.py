from __future__ import annotations

from typing import TypedDict

# Common IMDB region codes
REGIONS: dict[str, str] = {
    "US": "United States",
    "SE": "Sweden",
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "JP": "Japan",
    "AU": "Australia",
    "CA": "Canada",
    "IT": "Italy",
    "ES": "Spain",
    "NL": "Netherlands",
    "BR": "Brazil",
    "IN": "India",
    "KR": "South Korea",
    "CN": "China",
}


class AppConfig(TypedDict):
    region: str
    output_filename: str
    calendar_name: str
    headless: bool
    window_size: str
    timeout: float


DEFAULT_CONFIG: AppConfig = {
    "region": "SE",
    "output_filename": "upcoming_movies.ics",
    "calendar_name": "Upcoming Movies",
    "headless": True,
    "window_size": "1440,900",
    "timeout": 10.0,
}

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class ScheduledMovie:
    title: str
    release_date_text: str
    imdb_url: str


@dataclass
class MovieCalendarEvent:
    title: str
    release_date: date
    imdb_url: str
    plot_description: str
    poster_image_url: str | None = None

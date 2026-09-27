from dataclasses import dataclass
from datetime import date
from typing import Optional


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
    poster_image_url: Optional[str] = None

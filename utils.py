"""Pure logic utility functions for upcoming movies calendar."""

from __future__ import annotations

from calendar_builder import (
    DEFAULT_CALENDAR_NAME,
    DEFAULT_OUTPUT_FILENAME,
    build_icalendar_from_movie_events,
    create_calendar_event_from_movie,
    generate_calendar_event_uid,
    save_calendar_to_file,
)
from date_utils import parse_imdb_release_date
from models import MovieCalendarEvent, ScheduledMovie
from scraper import (
    RawDetailPayload,
    RawMoviePayload,
    parse_scheduled_movie_records,
)

__all__ = [
    "DEFAULT_CALENDAR_NAME",
    "DEFAULT_OUTPUT_FILENAME",
    "MovieCalendarEvent",
    "RawDetailPayload",
    "RawMoviePayload",
    "ScheduledMovie",
    "build_icalendar_from_movie_events",
    "create_calendar_event_from_movie",
    "generate_calendar_event_uid",
    "parse_imdb_release_date",
    "parse_scheduled_movie_records",
    "save_calendar_to_file",
]

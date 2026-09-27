"""Pure logic utility functions for upcoming movies calendar."""

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

__all__ = [
    "DEFAULT_CALENDAR_NAME",
    "DEFAULT_OUTPUT_FILENAME",
    "MovieCalendarEvent",
    "ScheduledMovie",
    "build_icalendar_from_movie_events",
    "create_calendar_event_from_movie",
    "generate_calendar_event_uid",
    "parse_imdb_release_date",
    "save_calendar_to_file",
]

from __future__ import annotations

import argparse
import logging

from calendar_builder import (
    DEFAULT_CALENDAR_NAME,
    DEFAULT_OUTPUT_FILENAME,
    build_icalendar_from_movie_events,
    create_calendar_event_from_movie as _create_calendar_event_from_movie,
    generate_calendar_event_uid,
    save_calendar_to_file,
)
from config import DEFAULT_CONFIG
from date_utils import parse_imdb_release_date
from models import MovieCalendarEvent, ScheduledMovie
from scraper import scrape_upcoming_movies_from_imdb

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Re-exports for backwards compatibility
__all__ = [
    "DEFAULT_CALENDAR_NAME",
    "DEFAULT_OUTPUT_FILENAME",
    "DEFAULT_REGION",
    "MovieCalendarEvent",
    "ScheduledMovie",
    "_create_calendar_event_from_movie",
    "build_icalendar_from_movie_events",
    "generate_calendar_event_uid",
    "main",
    "parse_command_line_arguments",
    "parse_imdb_release_date",
    "save_calendar_to_file",
    "scrape_upcoming_movies_from_imdb",
]

DEFAULT_REGION: str = DEFAULT_CONFIG["region"]


def parse_command_line_arguments() -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser(
        description="Scrape upcoming movies from IMDB and create an iCalendar file"
    )
    argument_parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help="IMDB region code (default: SE for Sweden)",
    )
    argument_parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_FILENAME,
        help="Output filename for the iCalendar file (default: upcoming_movies.ics)",
    )
    argument_parser.add_argument(
        "--calendar-name",
        default=DEFAULT_CALENDAR_NAME,
        help="Name for the calendar (default: Upcoming Movies)",
    )
    argument_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )
    return argument_parser.parse_args()


def main() -> None:
    arguments = parse_command_line_arguments()

    if arguments.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info("Starting movie scraping process")
    movie_events = scrape_upcoming_movies_from_imdb(arguments.region)

    if not movie_events:
        logging.warning("No movies found. Skipping calendar file creation.")
        return

    calendar = build_icalendar_from_movie_events(
        movie_events, calendar_name=arguments.calendar_name
    )
    save_calendar_to_file(calendar, arguments.output)

    logging.info(
        "Process completed. Created calendar with %d movies.", len(movie_events)
    )


if __name__ == "__main__":
    main()

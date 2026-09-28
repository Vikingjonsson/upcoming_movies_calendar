from __future__ import annotations

import argparse
import logging

from upcoming_movies.config import DEFAULT_CONFIG
from upcoming_movies.exporters import (
    DEFAULT_FORMAT,
    SUPPORTED_FORMATS,
    export_movie_events,
    prompt_output_format,
    resolve_output_filename,
)
from upcoming_movies.exporters.ics_exporter import DEFAULT_CALENDAR_NAME
from upcoming_movies.scraping.scraper import scrape_upcoming_movies_from_imdb

DEFAULT_REGION: str = DEFAULT_CONFIG["region"]

logger = logging.getLogger(__name__)


def parse_command_line_arguments() -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser(
        description=(
            "Scrape upcoming movies from IMDB and export to multiple formats "
            "(ICS, JSON)"
        )
    )
    argument_parser.add_argument(
        "-f",
        "--format",
        choices=list(SUPPORTED_FORMATS.keys()),
        default=None,
        help=(
            "Output format ('ics' for iCalendar, 'json' for JSON). "
            "If omitted, prompts interactively."
        ),
    )
    argument_parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help="IMDB region code (default: SE for Sweden)",
    )
    argument_parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output filename (default: upcoming_movies.<format>)",
    )
    argument_parser.add_argument(
        "--calendar-name",
        default=DEFAULT_CALENDAR_NAME,
        help="Name for the calendar when exporting to ICS (default: Upcoming Movies)",
    )
    argument_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )
    return argument_parser.parse_args()


def main() -> None:
    arguments = parse_command_line_arguments()

    log_level = logging.DEBUG if arguments.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    if arguments.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    selected_format = arguments.format or prompt_output_format(default=DEFAULT_FORMAT)
    output_filepath = resolve_output_filename(selected_format, arguments.output)

    logger.info("Starting movie scraping process for region: %s", arguments.region)
    movie_events = scrape_upcoming_movies_from_imdb(arguments.region)

    if not movie_events:
        logger.warning("No movies found. Skipping file creation.")
        return

    export_movie_events(
        movie_events,
        format_name=selected_format,
        output_filepath=output_filepath,
        calendar_name=arguments.calendar_name,
    )

    logger.info(
        "Process completed. Exported %d movies to %s (%s format).",
        len(movie_events),
        output_filepath,
        selected_format,
    )


if __name__ == "__main__":
    main()

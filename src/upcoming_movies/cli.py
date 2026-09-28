"""Command-line interface for upcoming_movies using Python's argparse."""

from __future__ import annotations

import argparse
import logging
import sys
import warnings
from collections.abc import Sequence

from upcoming_movies.config import DEFAULT_CONFIG, REGIONS
from upcoming_movies.exporters import (
    DEFAULT_FORMAT,
    SUPPORTED_FORMATS,
    export_movie_events,
    prompt_output_format,
    resolve_output_filename,
)
from upcoming_movies.exporters.ics_exporter import DEFAULT_CALENDAR_NAME
from upcoming_movies.scraping.scraper import scrape_upcoming_movies_from_imdb

logger = logging.getLogger(__name__)


def display_regions() -> None:
    """Print common IMDB region codes in a clean readable list."""
    default_region = DEFAULT_CONFIG["region"]
    print("Common IMDB Region Codes:")
    for code, name in REGIONS.items():
        suffix = " (default)" if code == default_region else ""
        print(f"  {code:<4} - {name}{suffix}")
    print("\nUse with: upcoming-movies -r <CODE> (e.g. upcoming-movies -r US)")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="upcoming-movies",
        description="Scrape upcoming movies from IMDB and export to ICS or JSON.",
        epilog=(
            "examples:\n"
            "  upcoming-movies                     # Prompt for format (interactive)\n"
            "  upcoming-movies -f json             # Export to JSON (Sweden)\n"
            "  upcoming-movies -f ics -r US        # Export to ICS (United States)\n"
            "  upcoming-movies -f json -o out.json # Export to custom filename\n"
            "  upcoming-movies -l                  # List common region codes\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=list(SUPPORTED_FORMATS.keys()),
        default=None,
        help="Output format ('ics' or 'json'). Prompts if omitted.",
    )
    parser.add_argument(
        "-r",
        "--region",
        default=DEFAULT_CONFIG["region"],
        help=f"IMDB region code (default: {DEFAULT_CONFIG['region']} for Sweden).",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output filename (default: upcoming_movies.<format>).",
    )
    parser.add_argument(
        "-c",
        "--calendar-name",
        default=DEFAULT_CALENDAR_NAME,
        help=f"Calendar name for ICS export (default: '{DEFAULT_CALENDAR_NAME}').",
    )
    parser.add_argument(
        "-l",
        "--list-regions",
        action="store_true",
        help="List common IMDB region codes and exit.",
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not prompt interactively; use default format (ics) if -f is omitted.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Quiet mode: only output the resulting file path.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging.",
    )
    return parser


def parse_command_line_arguments(
    args: Sequence[str] | None = None,
) -> argparse.Namespace:
    """Parse command line arguments."""
    return build_parser().parse_args(args)


def cli_main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface and return exit code."""
    # Suppress urllib3 warning on LibreSSL platforms
    warnings.filterwarnings("ignore", module="urllib3")

    parser = build_parser()
    arguments = parser.parse_args(argv)

    if arguments.list_regions:
        display_regions()
        return 0

    log_level = logging.DEBUG if arguments.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    if arguments.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    # Determine format: CLI flag -> prompt (if interactive) -> default
    if arguments.format:
        selected_format = arguments.format
    elif arguments.no_prompt or not sys.stdin.isatty():
        selected_format = DEFAULT_FORMAT
    else:
        selected_format = prompt_output_format(default=DEFAULT_FORMAT)

    output_filepath = resolve_output_filename(selected_format, arguments.output)
    region = arguments.region.upper()
    region_name = REGIONS.get(region, region)

    if not arguments.quiet:
        print(f"Scraping upcoming movies from IMDB for {region_name} ({region})...")

    logger.info("Starting movie scraping process for region: %s", region)
    try:
        movie_events = scrape_upcoming_movies_from_imdb(region)
    except Exception as exc:
        print(f"Error scraping movies: {exc}", file=sys.stderr)
        return 1

    if not movie_events:
        logger.warning("No movies found. Skipping file creation.")
        if not arguments.quiet:
            print(f"No upcoming movies found for region '{region}'.")
        return 0

    try:
        export_movie_events(
            movie_events,
            format_name=selected_format,
            output_filepath=output_filepath,
            calendar_name=arguments.calendar_name,
        )
    except Exception as exc:
        print(f"Error exporting movies: {exc}", file=sys.stderr)
        return 1

    logger.info(
        "Process completed. Exported %d movies to %s (%s format).",
        len(movie_events),
        output_filepath,
        selected_format,
    )

    if arguments.quiet:
        print(output_filepath)
    else:
        print(
            f"Successfully exported {len(movie_events)} movies to "
            f"{output_filepath} ({selected_format} format)."
        )

    return 0


def main() -> None:
    """CLI entrypoint."""
    try:
        exit_code = cli_main()
        if exit_code != 0:
            sys.exit(exit_code)
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        sys.exit(130)


if __name__ == "__main__":
    main()

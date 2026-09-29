"""Command-line interface for upcoming_movies using Python's argparse."""

from __future__ import annotations

import argparse
import logging
import sys
import warnings
from collections.abc import Sequence
from datetime import date
from typing import Any

from upcoming_movies.cache import (
    get_cached_movies,
    get_stale_cached_movies,
    save_cached_movies,
)
from upcoming_movies.config import DEFAULT_CONFIG, REGIONS
from upcoming_movies.exporters import (
    DEFAULT_FORMAT,
    SUPPORTED_FORMATS,
    build_terminal_cards_from_movie_events,
    export_movie_events,
    filter_movies_by_date,
    get_weekend_movies,
    load_json_from_file,
    normalize_format,
    prompt_output_format,
    resolve_output_filename,
)
from upcoming_movies.exporters.ics_exporter import DEFAULT_CALENDAR_NAME
from upcoming_movies.models import MovieCalendarEvent
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


def prompt_region(default: str = DEFAULT_CONFIG["region"]) -> str:
    """Prompt user to interactively select an IMDB region code."""
    print("\nSelect IMDB region:")
    region_keys = list(REGIONS.keys())
    for index, (code, name) in enumerate(REGIONS.items(), 1):
        suffix = " (default)" if code == default else ""
        print(f"  {index:>2}) {code} - {name}{suffix}")
    print("      Or enter any country code (e.g. US, JP, IT, NO)")

    if not sys.stdin.isatty():
        return default

    try:
        prompt_msg = (
            f"Select region [1-{len(region_keys)} or code] (default: {default}): "
        )
        user_input = input(prompt_msg).strip().upper()
    except (EOFError, KeyboardInterrupt):
        print()
        return default

    if not user_input:
        return default

    if user_input.isdigit():
        idx = int(user_input) - 1
        if 0 <= idx < len(region_keys):
            return region_keys[idx]

    return user_input


def prompt_date_filter() -> tuple[date | None, date | None, bool]:
    """Prompt user to interactively choose a date filter.

    Returns:
        tuple of (from_date, to_date, is_weekend)
    """
    print("\nSelect date filter:")
    print("  1) All upcoming releases (default)")
    print("  2) This weekend (Friday - Sunday)")
    print("  3) Today's releases")
    print("  4) Custom date range")

    if not sys.stdin.isatty():
        return (None, None, False)

    try:
        user_input = input("Select filter [1-4] (default: 1): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return (None, None, False)

    if user_input in ("", "1"):
        return (None, None, False)

    if user_input == "2":
        return (None, None, True)

    if user_input == "3":
        today = date.today()
        return (today, today, False)

    if user_input == "4":
        from_d: date | None = None
        to_d: date | None = None
        try:
            from_str = input("  From date (YYYY-MM-DD) [empty for any]: ").strip()
            if from_str:
                from_d = date.fromisoformat(from_str)
        except ValueError:
            print("  Invalid date format, skipping start date limit.")

        try:
            to_str = input("  To date (YYYY-MM-DD) [empty for any]: ").strip()
            if to_str:
                to_d = date.fromisoformat(to_str)
        except ValueError:
            print("  Invalid date format, skipping end date limit.")

        return (from_d, to_d, False)

    return (None, None, False)


def prompt_card_carousel() -> bool:
    """Prompt whether to format cards as an Antigravity carousel."""
    print("\nSelect card presentation style:")
    print("  1) Standard markdown cards (default)")
    print("  2) Antigravity carousel")

    if not sys.stdin.isatty():
        return False

    try:
        user_input = input("Select style [1-2] (default: 1): ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return False

    return user_input == "2"


def prompt_output_filepath(
    default_filename: str, *, is_terminal: bool = False
) -> str | None:
    """Prompt user for custom output file path or accept default."""
    if not sys.stdin.isatty():
        return None if is_terminal else default_filename

    prompt_label = (
        "\nOutput file path [press Enter to print to terminal]: "
        if is_terminal
        else f"\nOutput file path (default: {default_filename}): "
    )
    try:
        user_input = input(prompt_label).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None if is_terminal else default_filename

    if user_input:
        return user_input
    return None if is_terminal else default_filename


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="upcoming-movies",
        description="Scrape upcoming movies from IMDB and export to ICS/JSON/Cards.",
        epilog=(
            "examples:\n"
            "  upcoming-movies                     # Interactive mode (prompts)\n"
            "  upcoming-movies --card-view         # View movies as cards in terminal\n"
            "  upcoming-movies -f terminal         # View movies as terminal cards\n"
            "  upcoming-movies -i data.json --card-view # Card view from cached JSON\n"
            "  upcoming-movies -f json             # Export to JSON (Sweden)\n"
            "  upcoming-movies -f cards --weekend  # Export weekend movies as cards\n"
            "  upcoming-movies -f ics -r US        # Export to ICS (United States)\n"
            "  upcoming-movies -l                  # List common region codes\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=list(SUPPORTED_FORMATS.keys()) + ["card", "term"],
        default=None,
        help="Output format ('ics', 'json', 'cards', 'terminal'). Prompts if omitted.",
    )
    parser.add_argument(
        "--card-view",
        action="store_true",
        help="Display movies as visual cards directly in the terminal.",
    )
    parser.add_argument(
        "-r",
        "--region",
        default=None,
        help="IMDB region code (e.g. SE, US, GB). Prompts if omitted.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output filename (default: upcoming_movies.<format>).",
    )
    parser.add_argument(
        "-i",
        "--from-json",
        metavar="PATH",
        default=None,
        help="Load movies from an existing JSON file instead of scraping IMDB.",
    )
    parser.add_argument(
        "-c",
        "--calendar-name",
        default=DEFAULT_CALENDAR_NAME,
        help=f"Calendar name for ICS export (default: '{DEFAULT_CALENDAR_NAME}').",
    )
    parser.add_argument(
        "--today",
        action="store_true",
        help="Filter movies releasing today.",
    )
    parser.add_argument(
        "--weekend",
        action="store_true",
        help="Filter movies releasing on or around the upcoming weekend (Fri-Sun).",
    )
    parser.add_argument(
        "--from-date",
        metavar="YYYY-MM-DD",
        default=None,
        help="Filter movies releasing on or after this date (inclusive).",
    )
    parser.add_argument(
        "--to-date",
        metavar="YYYY-MM-DD",
        default=None,
        help="Filter movies releasing on or before this date (inclusive).",
    )
    parser.add_argument(
        "--carousel",
        action="store_true",
        help="Format markdown cards as an Antigravity carousel (cards format only).",
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
        help="Do not prompt interactively; use default values if flags are omitted.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Quiet mode: only output the resulting file path.",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force refresh: bypass cached movie data and fetch fresh from IMDB.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Bypass cache reading and writing completely.",
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

    is_interactive = sys.stdin.isatty() and not arguments.no_prompt

    # 1. Determine region
    if arguments.region:
        region = arguments.region.upper()
    elif is_interactive:
        region = prompt_region(default=DEFAULT_CONFIG["region"]).upper()
    else:
        region = DEFAULT_CONFIG["region"]

    # 2. Determine format
    if arguments.card_view:
        selected_format = "terminal"
    elif arguments.format:
        selected_format = normalize_format(arguments.format)
    elif is_interactive:
        selected_format = prompt_output_format(default=DEFAULT_FORMAT)
    else:
        selected_format = DEFAULT_FORMAT

    # 3. Determine carousel option for cards
    is_carousel = arguments.carousel
    if selected_format == "cards" and not arguments.carousel and is_interactive:
        is_carousel = prompt_card_carousel()

    # 4. Determine output filepath
    default_filename = resolve_output_filename(selected_format)
    output_filepath: str | None = None
    if arguments.output:
        output_filepath = arguments.output
    elif selected_format == "terminal":
        output_filepath = None
    elif is_interactive:
        output_filepath = prompt_output_filepath(default_filename, is_terminal=False)
    else:
        output_filepath = default_filename

    # 5. Determine date filters
    parsed_from: date | None = None
    parsed_to: date | None = None
    is_weekend: bool = False

    has_cli_date_filter = (
        arguments.today
        or arguments.weekend
        or arguments.from_date is not None
        or arguments.to_date is not None
    )

    if has_cli_date_filter:
        if arguments.today:
            today = date.today()
            parsed_from = today
            parsed_to = today
        else:
            if arguments.from_date:
                try:
                    parsed_from = date.fromisoformat(arguments.from_date)
                except ValueError:
                    print(
                        f"Error: Invalid date for --from-date '{arguments.from_date}'. "
                        "Use YYYY-MM-DD.",
                        file=sys.stderr,
                    )
                    return 1
            if arguments.to_date:
                try:
                    parsed_to = date.fromisoformat(arguments.to_date)
                except ValueError:
                    print(
                        f"Error: Invalid date for --to-date '{arguments.to_date}'. "
                        "Use YYYY-MM-DD.",
                        file=sys.stderr,
                    )
                    return 1
        is_weekend = arguments.weekend
    elif is_interactive:
        parsed_from, parsed_to, is_weekend = prompt_date_filter()

    region_name = REGIONS.get(region, region)

    movie_events: list[MovieCalendarEvent] = []

    if arguments.from_json:
        if not arguments.quiet:
            print(f"Loading movies from '{arguments.from_json}'...")
        try:
            movie_events = load_json_from_file(arguments.from_json)
        except Exception as exc:
            logger.debug("Loading from JSON failed with exception", exc_info=True)
            print(
                f"Error reading JSON file '{arguments.from_json}': {exc}",
                file=sys.stderr,
            )
            return 1
    else:
        # Check automatic cache unless --refresh or --no-cache is requested
        cached_events: list[MovieCalendarEvent] | None = None
        if not arguments.no_cache and not arguments.refresh:
            cached_events = get_cached_movies(region)

        if cached_events is not None:
            if not arguments.quiet:
                print(
                    f"Using cached releases for {region_name} ({region}) "
                    f"({len(cached_events)} movies). Use --refresh to update."
                )
            movie_events = cached_events
        else:
            action_label = "Refreshing" if arguments.refresh else "Fetching"
            if not arguments.quiet:
                print(
                    f"{action_label} upcoming movies from IMDB for "
                    f"{region_name} ({region})..."
                )

            logger.info("Starting movie scraping process for region: %s", region)
            scrape_failed = False
            try:
                movie_events = scrape_upcoming_movies_from_imdb(region)
            except Exception as exc:
                logger.debug("Scraping failed with exception", exc_info=True)
                print(f"Error scraping movies: {exc}", file=sys.stderr)
                scrape_failed = True

            if scrape_failed and not arguments.no_cache:
                # Try stale cache as fallback
                stale_events = get_stale_cached_movies(region)
                if stale_events:
                    if not arguments.quiet:
                        print(
                            "Warning: Live fetch failed. "
                            f"Falling back to cache ({len(stale_events)} movies).",
                            file=sys.stderr,
                        )
                    movie_events = stale_events
                else:
                    return 1
            elif not scrape_failed and not arguments.no_cache:
                save_cached_movies(region, movie_events)

    if is_weekend:
        movie_events = get_weekend_movies(movie_events)
    elif parsed_from is not None or parsed_to is not None:
        movie_events = filter_movies_by_date(
            movie_events, start_date=parsed_from, end_date=parsed_to
        )

    if not movie_events:
        logger.warning("No movies found. Skipping file creation.")
        if not arguments.quiet:
            print("No matching movies found.")
        return 0

    if selected_format == "terminal" or arguments.card_view:
        cards_output = build_terminal_cards_from_movie_events(movie_events)
        if not arguments.quiet:
            print()
            print(cards_output, end="")

        if output_filepath:
            try:
                export_movie_events(
                    movie_events,
                    format_name="terminal",
                    output_filepath=output_filepath,
                )
                if not arguments.quiet:
                    print(
                        f"Saved {len(movie_events)} terminal cards to "
                        f"{output_filepath}."
                    )
            except Exception as exc:
                logger.debug("Export failed with exception", exc_info=True)
                print(f"Error saving terminal cards: {exc}", file=sys.stderr)
                return 1

        if arguments.quiet:
            if output_filepath:
                print(output_filepath)
            else:
                print(cards_output, end="")
        return 0

    export_filepath = output_filepath or default_filename
    export_kwargs: dict[str, Any] = {
        "calendar_name": arguments.calendar_name,
    }
    if selected_format == "cards":
        export_kwargs["as_carousel"] = is_carousel

    try:
        export_movie_events(
            movie_events,
            format_name=selected_format,
            output_filepath=export_filepath,
            **export_kwargs,
        )
    except Exception as exc:
        logger.debug("Export failed with exception", exc_info=True)
        print(f"Error exporting movies: {exc}", file=sys.stderr)
        return 1

    logger.info(
        "Process completed. Exported %d movies to %s (%s format).",
        len(movie_events),
        export_filepath,
        selected_format,
    )

    if arguments.quiet:
        print(export_filepath)
    else:
        print(
            f"Successfully exported {len(movie_events)} movies to "
            f"{export_filepath} ({selected_format} format)."
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
    except BrokenPipeError:
        sys.exit(0)


if __name__ == "__main__":
    main()

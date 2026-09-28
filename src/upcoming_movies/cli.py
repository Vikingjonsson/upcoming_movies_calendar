"""Command-line interface for upcoming_movies."""

from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import sys
import warnings

# Suppress urllib3 NotOpenSSLWarning before selenium/webdriver packages are imported
warnings.filterwarnings("ignore", module="urllib3")

from upcoming_movies.config import DEFAULT_CONFIG, REGIONS  # noqa: E402
from upcoming_movies.exporters import (  # noqa: E402
    DEFAULT_FORMAT,
    SUPPORTED_FORMATS,
    export_movie_events,
    load_json_from_file,
    prompt_output_format,
    resolve_output_filename,
)
from upcoming_movies.exporters.ics_exporter import DEFAULT_CALENDAR_NAME  # noqa: E402
from upcoming_movies.models import MovieCalendarEvent  # noqa: E402
from upcoming_movies.scraping.scraper import (  # noqa: E402
    scrape_upcoming_movies_from_imdb,
)

logger = logging.getLogger(__name__)

# ANSI styling codes
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"
COLOR_GREEN = "\033[32m"
COLOR_CYAN = "\033[36m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_MAGENTA = "\033[35m"

_ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def supports_color() -> bool:
    """Check if the current terminal supports ANSI color codes."""
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return True


def style(text: str, *codes: str) -> str:
    """Wrap text in ANSI formatting codes if color is supported."""
    if not supports_color() or not codes:
        return text
    return "".join(codes) + text + COLOR_RESET


def visible_length(text: str) -> int:
    """Calculate the visible character length of a string ignoring ANSI codes."""
    return len(_ANSI_ESCAPE_RE.sub("", text))


def print_banner() -> None:
    """Print a clean CLI header banner."""
    header = "🎬 Upcoming Movies Calendar & Exporter"
    line = "─" * len(header)
    print(style(header, COLOR_BOLD, COLOR_CYAN))
    print(style(line, COLOR_DIM))


def format_regions_table() -> str:
    """Format the list of known IMDB region codes into a readable table."""
    lines: list[str] = [
        style("Available IMDB Region Codes:", COLOR_BOLD),
        f"  {style('Code', COLOR_BOLD):<10} {style('Country / Market', COLOR_BOLD)}",
        f"  {'────':<4}      {'────────────────'}",
    ]
    for code, name in REGIONS.items():
        is_default = code == DEFAULT_CONFIG["region"]
        suffix = style(" (default)", COLOR_GREEN) if is_default else ""
        lines.append(f"  {style(code, COLOR_CYAN):<14} {name}{suffix}")

    lines.append("")
    lines.append(
        style(
            "Tip: You can use any 2-letter country code with '--region <CODE>'.",
            COLOR_DIM,
        )
    )
    return "\n".join(lines)


def format_movies_table(
    movie_events: list[MovieCalendarEvent], max_width: int | None = None
) -> str:
    """Format a list of MovieCalendarEvents into a clean Unicode table."""
    if not movie_events:
        return ""

    if max_width is None:
        term_width = shutil.get_terminal_size((80, 24)).columns
    else:
        term_width = max_width

    date_w = 12
    usable_width = max(50, term_width - 8)
    title_w = max(24, int((usable_width - date_w) * 0.45))
    url_w = max(28, usable_width - date_w - title_w)

    bar_d = "─" * (date_w + 2)
    bar_t = "─" * (title_w + 2)
    bar_u = "─" * (url_w + 2)

    top_border = f"┌{bar_d}┬{bar_t}┬{bar_u}┐"
    d_hdr = style("Date", COLOR_BOLD)
    t_hdr = style("Title", COLOR_BOLD)
    u_hdr = style("IMDB URL", COLOR_BOLD)
    header = (
        f"│ {d_hdr:<{date_w + len(d_hdr) - 4}} │ "
        f"{t_hdr:<{title_w + len(t_hdr) - 5}} │ "
        f"{u_hdr:<{url_w + len(u_hdr) - 8}} │"
    )
    mid_border = f"├{bar_d}┼{bar_t}┼{bar_u}┤"
    bot_border = f"└{bar_d}┴{bar_t}┴{bar_u}┘"

    lines: list[str] = [top_border, header, mid_border]

    for event in movie_events:
        date_str = event.release_date.isoformat()
        title_str = event.title
        if len(title_str) > title_w:
            title_str = title_str[: title_w - 1] + "…"
        url_str = event.imdb_url
        if len(url_str) > url_w:
            url_str = url_str[: url_w - 1] + "…"

        d_styled = style(date_str, COLOR_CYAN)
        u_styled = style(url_str, COLOR_DIM)
        d_pad = date_w + len(d_styled) - len(date_str)
        u_pad = url_w + len(u_styled) - len(url_str)

        lines.append(
            f"│ {d_styled:<{d_pad}} │ {title_str:<{title_w}} │ {u_styled:<{u_pad}} │"
        )

    lines.append(bot_border)
    return "\n".join(lines)


def prompt_text(message: str, default: str = "") -> str:
    """Prompt the user for a text value with an optional default."""
    prompt_str = f"{message} [{default}]: " if default else f"{message}: "
    try:
        user_input = input(prompt_str).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return user_input if user_input else default


def prompt_region_choice(default_region: str = "SE") -> str:
    """Interactively prompt user to select an IMDB region."""
    popular_regions = [
        ("SE", "Sweden"),
        ("US", "United States"),
        ("GB", "United Kingdom"),
        ("DE", "Germany"),
        ("FR", "France"),
        ("JP", "Japan"),
        ("AU", "Australia"),
    ]

    print("\nSelect IMDB region:")
    default_index = 1
    for index, (code, name) in enumerate(popular_regions, 1):
        if code == default_region:
            default_index = index
            print(f"  {index}) {name} ({code}) {style('[default]', COLOR_GREEN)}")
        else:
            print(f"  {index}) {name} ({code})")
    custom_index = len(popular_regions) + 1
    print(f"  {custom_index}) Other custom 2-letter code")

    if not sys.stdin.isatty():
        return default_region

    prompt_msg = f"Select region [1-{custom_index}] (default: {default_index}): "
    try:
        user_input = input(prompt_msg).strip().upper()
    except (EOFError, KeyboardInterrupt):
        print()
        return default_region

    if not user_input:
        return default_region

    if user_input.isdigit():
        idx = int(user_input)
        if 1 <= idx <= len(popular_regions):
            return popular_regions[idx - 1][0]
        if idx == custom_index:
            custom = prompt_text("Enter 2-letter region code", default=default_region)
            return custom.upper()

    if len(user_input) == 2 and user_input.isalpha():
        return user_input

    return default_region


def run_interactive_wizard() -> dict[str, str]:
    """Run an interactive wizard to configure all scraping options."""
    print_banner()
    print(style("\nWelcome! Let's configure your movie export settings:\n", COLOR_BOLD))

    # Step 1: Region
    region = prompt_region_choice(default_region=DEFAULT_CONFIG["region"])

    # Step 2: Format
    format_choice = prompt_output_format(default=DEFAULT_FORMAT)

    # Step 3: Output path
    default_output = resolve_output_filename(format_choice)
    output_filepath = prompt_text("Output file path", default=default_output)

    # Step 4: Calendar name (if ICS)
    calendar_name = DEFAULT_CALENDAR_NAME
    if format_choice == "ics":
        calendar_name = prompt_text("Calendar name", default=DEFAULT_CALENDAR_NAME)

    return {
        "region": region,
        "format": format_choice,
        "output": output_filepath,
        "calendar_name": calendar_name,
    }


def add_common_scrape_arguments(parser: argparse.ArgumentParser) -> None:
    """Add scrape flags to an argument parser."""
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
        default=None,
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
        help=f"Calendar name for ICS (default: {DEFAULT_CALENDAR_NAME}).",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Run interactive setup wizard for region, format, and export.",
    )
    parser.add_argument(
        "--no-prompt",
        action="store_true",
        help="Do not prompt interactively; fall back to defaults.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of movies to export.",
    )
    parser.add_argument(
        "--no-table",
        action="store_true",
        help="Do not print the terminal summary table of scraped movies.",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser with subcommands and root flags."""
    parser = argparse.ArgumentParser(
        prog="upcoming-movies",
        description="Scrape upcoming movies from IMDB and export to ICS or JSON.",
        epilog=(
            "examples:\n"
            "  upcoming-movies                     # Interactive mode / prompt\n"
            "  upcoming-movies wizard              # Step-by-step setup wizard\n"
            "  upcoming-movies -f json             # Export to JSON (Sweden)\n"
            "  upcoming-movies -f ics -r US        # Export to ICS (United States)\n"
            "  upcoming-movies regions             # List available IMDB regions\n"
            "  upcoming-movies export -i data.json # Convert existing JSON to ICS\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global options
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug logging."
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Quiet mode: only output generated file path or error message.",
    )
    parser.add_argument(
        "--list-regions",
        action="store_true",
        help="List available IMDB region codes and exit.",
    )

    # Allow scrape arguments directly on root parser for backward compatibility
    add_common_scrape_arguments(parser)

    # Subparsers
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # 'scrape' subcommand
    scrape_parser = subparsers.add_parser(
        "scrape",
        help="Scrape upcoming movies from IMDB and export (default command)",
    )
    add_common_scrape_arguments(scrape_parser)

    # 'regions' subcommand
    subparsers.add_parser(
        "regions",
        help="List popular and supported IMDB region codes",
    )

    # 'wizard' subcommand
    subparsers.add_parser(
        "wizard",
        help="Launch the interactive configuration wizard",
    )

    # 'export' subcommand (re-export from JSON without re-scraping)
    export_parser = subparsers.add_parser(
        "export",
        help="Export/convert an existing JSON file to another format",
    )
    export_parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input JSON file path containing movie data.",
    )
    export_parser.add_argument(
        "-f",
        "--format",
        choices=list(SUPPORTED_FORMATS.keys()),
        default=DEFAULT_FORMAT,
        help=f"Target output format (default: {DEFAULT_FORMAT}).",
    )
    export_parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output filepath (default: upcoming_movies.<format>).",
    )
    export_parser.add_argument(
        "-c",
        "--calendar-name",
        default=DEFAULT_CALENDAR_NAME,
        help=f"Calendar name when exporting to ICS (default: {DEFAULT_CALENDAR_NAME}).",
    )
    export_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of movies to export.",
    )
    export_parser.add_argument(
        "--no-table",
        action="store_true",
        help="Do not print the summary table.",
    )

    return parser


def handle_regions(args: argparse.Namespace) -> int:
    """Handler for displaying available regions."""
    print(format_regions_table())
    return 0


def handle_export(args: argparse.Namespace) -> int:
    """Handler for converting an existing JSON file to another format."""
    input_file = args.input
    target_format = args.format or DEFAULT_FORMAT
    output_filepath = resolve_output_filename(target_format, args.output)
    calendar_name = getattr(args, "calendar_name", DEFAULT_CALENDAR_NAME)

    if not getattr(args, "quiet", False):
        print(
            f"🔄 Converting {style(input_file, COLOR_CYAN)} to "
            f"{style(target_format.upper(), COLOR_GREEN)} ({output_filepath})..."
        )

    try:
        movie_events = load_json_from_file(input_file)
    except Exception as exc:
        print(style(f"✖ Error reading {input_file}: {exc}", COLOR_RED), file=sys.stderr)
        return 1

    if not movie_events:
        print(style("Warning: No movies found in input file.", COLOR_YELLOW))
        return 0

    if args.limit and args.limit > 0:
        movie_events = movie_events[: args.limit]

    try:
        export_movie_events(
            movie_events,
            format_name=target_format,
            output_filepath=output_filepath,
            calendar_name=calendar_name,
        )
    except Exception as exc:
        print(style(f"✖ Export failed: {exc}", COLOR_RED), file=sys.stderr)
        return 1

    if getattr(args, "quiet", False):
        print(output_filepath)
        return 0

    if not getattr(args, "no_table", False) and sys.stdout.isatty():
        print(f"\n{format_movies_table(movie_events)}\n")

    summary_msg = (
        f"✔ Successfully exported {len(movie_events)} movies to "
        f"{output_filepath} ({target_format.upper()} format)."
    )
    print(style(summary_msg, COLOR_GREEN, COLOR_BOLD))
    return 0


def handle_scrape(args: argparse.Namespace, is_bare_invocation: bool = False) -> int:
    """Handler for scraping IMDB and exporting."""
    is_bare_interactive = (
        is_bare_invocation
        and sys.stdin.isatty()
        and not getattr(args, "no_prompt", False)
    )
    should_run_wizard = (
        getattr(args, "subcommand", None) == "wizard"
        or getattr(args, "interactive", False)
        or is_bare_interactive
    )

    if should_run_wizard:
        config = run_interactive_wizard()
        region = config["region"]
        selected_format = config["format"]
        output_filepath = config["output"]
        calendar_name = config["calendar_name"]
    else:
        region = args.region or DEFAULT_CONFIG["region"]
        calendar_name = getattr(args, "calendar_name", DEFAULT_CALENDAR_NAME)

        if args.format:
            selected_format = args.format
        elif getattr(args, "no_prompt", False) or not sys.stdin.isatty():
            selected_format = DEFAULT_FORMAT
        else:
            selected_format = prompt_output_format(default=DEFAULT_FORMAT)

        output_filepath = resolve_output_filename(selected_format, args.output)

    quiet = getattr(args, "quiet", False)
    region_name = REGIONS.get(region, region)

    if not quiet:
        print(
            f"🍿 Fetching upcoming movies from IMDB for "
            f"{style(f'{region_name} ({region})', COLOR_CYAN, COLOR_BOLD)}..."
        )

    logger.info("Starting movie scraping process for region: %s", region)
    try:
        movie_events = scrape_upcoming_movies_from_imdb(region)
    except Exception as exc:
        print(style(f"✖ Failed to scrape IMDB: {exc}", COLOR_RED), file=sys.stderr)
        return 1

    if not movie_events:
        logger.warning("No movies found. Skipping file creation.")
        if not quiet:
            print(
                style(
                    f"Warning: No upcoming movies found for region '{region}'.",
                    COLOR_YELLOW,
                )
            )
        return 0

    if getattr(args, "limit", None) and args.limit > 0:
        movie_events = movie_events[: args.limit]

    try:
        export_movie_events(
            movie_events,
            format_name=selected_format,
            output_filepath=output_filepath,
            calendar_name=calendar_name,
        )
    except Exception as exc:
        print(style(f"✖ Failed to export movies: {exc}", COLOR_RED), file=sys.stderr)
        return 1

    logger.info(
        "Process completed. Exported %d movies to %s (%s format).",
        len(movie_events),
        output_filepath,
        selected_format,
    )

    if quiet:
        print(output_filepath)
        return 0

    if not getattr(args, "no_table", False) and sys.stdout.isatty():
        print(f"\n{format_movies_table(movie_events)}\n")

    print(
        style(
            f"✔ Successfully exported {len(movie_events)} movies to "
            f"{style(output_filepath, COLOR_BOLD)} ({selected_format.upper()} format).",
            COLOR_GREEN,
        )
    )
    return 0


def cli_main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint. Parses arguments and routes to command handlers."""
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()
    args = parser.parse_args(argv)

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        # Hide root logger info messages from standard CLI output unless verbose
        logging.getLogger().setLevel(logging.WARNING)

    # Check for --list-regions flag or 'regions' subcommand
    if getattr(args, "list_regions", False) or args.subcommand == "regions":
        return handle_regions(args)

    # Subcommand 'export'
    if args.subcommand == "export":
        return handle_export(args)

    # Subcommand 'wizard'
    if args.subcommand == "wizard":
        args.interactive = True
        return handle_scrape(args, is_bare_invocation=False)

    # Default / scrape command
    is_bare_invocation = len(argv) == 0
    try:
        return handle_scrape(args, is_bare_invocation=is_bare_invocation)
    except (KeyboardInterrupt, EOFError):
        print(f"\n{style('Aborted by user.', COLOR_YELLOW)}")
        return 130


if __name__ == "__main__":
    sys.exit(cli_main())

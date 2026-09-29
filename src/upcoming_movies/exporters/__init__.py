"""Output formats and exporters registry for upcoming movies."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from typing import Any, TypedDict

from upcoming_movies.exporters.card_exporter import (
    build_cards_from_movie_events as build_cards_from_movie_events,
)
from upcoming_movies.exporters.card_exporter import (
    build_terminal_cards_from_movie_events as build_terminal_cards_from_movie_events,
)
from upcoming_movies.exporters.card_exporter import (
    format_movie_card as format_movie_card,
)
from upcoming_movies.exporters.card_exporter import (
    format_terminal_card as format_terminal_card,
)
from upcoming_movies.exporters.card_exporter import (
    save_cards_to_file as save_cards_to_file,
)
from upcoming_movies.exporters.card_exporter import (
    save_terminal_cards_to_file as save_terminal_cards_to_file,
)
from upcoming_movies.exporters.ics_exporter import (
    DEFAULT_CALENDAR_NAME,
    build_icalendar_from_movie_events,
    save_calendar_to_file,
)
from upcoming_movies.exporters.json_exporter import (
    filter_movies_by_date as filter_movies_by_date,
)
from upcoming_movies.exporters.json_exporter import (
    get_weekend_movies as get_weekend_movies,
)
from upcoming_movies.exporters.json_exporter import (
    load_json_from_file as load_json_from_file,
)
from upcoming_movies.exporters.json_exporter import (
    save_json_to_file as save_json_to_file,
)
from upcoming_movies.models import MovieCalendarEvent

logger = logging.getLogger(__name__)


class FormatDefinition(TypedDict):
    name: str
    extension: str
    default_filename: str
    shorthand: str
    exporter: Callable[..., None]


def _export_ics(
    movie_events: list[MovieCalendarEvent],
    output_filepath: str,
    *,
    calendar_name: str = DEFAULT_CALENDAR_NAME,
    **_kwargs: Any,
) -> None:
    calendar = build_icalendar_from_movie_events(
        movie_events, calendar_name=calendar_name
    )
    save_calendar_to_file(calendar, output_filepath)


def _export_json(
    movie_events: list[MovieCalendarEvent],
    output_filepath: str,
    **_kwargs: Any,
) -> None:
    save_json_to_file(movie_events, output_filepath)


def _export_cards(
    movie_events: list[MovieCalendarEvent],
    output_filepath: str,
    *,
    as_carousel: bool = False,
    title: str = "Upcoming Movies",
    **_kwargs: Any,
) -> None:
    save_cards_to_file(
        movie_events, output_filepath, title=title, as_carousel=as_carousel
    )


def _export_terminal(
    movie_events: list[MovieCalendarEvent],
    output_filepath: str,
    *,
    width: int = 70,
    **_kwargs: Any,
) -> None:
    save_terminal_cards_to_file(movie_events, output_filepath, width=width)


SUPPORTED_FORMATS: dict[str, FormatDefinition] = {
    "ics": {
        "name": "iCalendar (.ics)",
        "extension": ".ics",
        "default_filename": "upcoming_movies.ics",
        "shorthand": "ics",
        "exporter": _export_ics,
    },
    "json": {
        "name": "JSON (.json)",
        "extension": ".json",
        "default_filename": "upcoming_movies.json",
        "shorthand": "json",
        "exporter": _export_json,
    },
    "cards": {
        "name": "Markdown Cards (.md)",
        "extension": ".md",
        "default_filename": "upcoming_movies.md",
        "shorthand": "cards",
        "exporter": _export_cards,
    },
    "terminal": {
        "name": "Terminal Card View",
        "extension": ".txt",
        "default_filename": "upcoming_movies_cards.txt",
        "shorthand": "terminal",
        "exporter": _export_terminal,
    },
}

DEFAULT_FORMAT = "ics"


def normalize_format(format_name: str) -> str:
    """Normalize format name and aliases (e.g. 'term' -> 'terminal')."""
    lower = format_name.lower().strip()
    if lower in ("card", "markdown-cards", "md-cards"):
        return "cards"
    if lower in ("terminal-cards", "terminal-card", "card-view", "term"):
        return "terminal"
    return lower


def prompt_output_format(default: str = DEFAULT_FORMAT) -> str:
    """Prompt user to interactively select an output format when none was provided."""
    print("\nAvailable output formats:")
    for index, (key, definition) in enumerate(SUPPORTED_FORMATS.items(), 1):
        print(f"  {index}) {definition['name']:<20} [shorthand: -f {key}]")

    if not sys.stdin.isatty():
        return default

    try:
        prompt_msg = f"Select format [1-{len(SUPPORTED_FORMATS)}] (default: 1): "
        user_input = input(prompt_msg).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return default

    if not user_input:
        return default

    # Match by numeric index (e.g. "1", "2")
    format_keys = list(SUPPORTED_FORMATS.keys())
    if user_input.isdigit():
        idx = int(user_input) - 1
        if 0 <= idx < len(format_keys):
            return format_keys[idx]

    norm = normalize_format(user_input)
    if norm in SUPPORTED_FORMATS:
        return norm

    print(f"Unknown format '{user_input}', defaulting to '{default}'.")
    return default


def resolve_output_filename(format_name: str, custom_output: str | None = None) -> str:
    """Resolve output filename based on selected format and user argument."""
    if custom_output:
        return custom_output
    norm_format = normalize_format(format_name)
    format_def = SUPPORTED_FORMATS.get(norm_format)
    if format_def:
        return format_def["default_filename"]
    return f"upcoming_movies.{norm_format}"


def export_movie_events(
    movie_events: list[MovieCalendarEvent],
    format_name: str,
    output_filepath: str,
    **kwargs: Any,
) -> None:
    """Export movie events using the handler for the specified format."""
    norm_format = normalize_format(format_name)
    format_def = SUPPORTED_FORMATS.get(norm_format)
    if not format_def:
        supported = list(SUPPORTED_FORMATS.keys())
        raise ValueError(
            f"Unsupported format '{format_name}'. Supported formats: {supported}"
        )
    format_def["exporter"](movie_events, output_filepath, **kwargs)

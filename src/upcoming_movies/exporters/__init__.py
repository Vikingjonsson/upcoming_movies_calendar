"""Output formats and exporters registry for upcoming movies."""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from typing import Any, TypedDict

from upcoming_movies.exporters.ics_exporter import (
    DEFAULT_CALENDAR_NAME,
    build_icalendar_from_movie_events,
    save_calendar_to_file,
)
from upcoming_movies.exporters.json_exporter import save_json_to_file
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
}

DEFAULT_FORMAT = "ics"


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

    # Match by key name or shorthand (e.g. "ics", "json")
    if user_input in SUPPORTED_FORMATS:
        return user_input

    print(f"Unknown format '{user_input}', defaulting to '{default}'.")
    return default


def resolve_output_filename(format_name: str, custom_output: str | None = None) -> str:
    """Resolve output filename based on selected format and user argument."""
    if custom_output:
        return custom_output
    format_def = SUPPORTED_FORMATS.get(format_name)
    if format_def:
        return format_def["default_filename"]
    return f"upcoming_movies.{format_name}"


def export_movie_events(
    movie_events: list[MovieCalendarEvent],
    format_name: str,
    output_filepath: str,
    **kwargs: Any,
) -> None:
    """Export movie events using the handler for the specified format."""
    format_def = SUPPORTED_FORMATS.get(format_name)
    if not format_def:
        supported = list(SUPPORTED_FORMATS.keys())
        raise ValueError(
            f"Unsupported format '{format_name}'. Supported formats: {supported}"
        )
    format_def["exporter"](movie_events, output_filepath, **kwargs)

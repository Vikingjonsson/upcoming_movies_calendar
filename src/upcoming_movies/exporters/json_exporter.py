"""JSON exporter for upcoming movie events."""

from __future__ import annotations

import json
import logging
from typing import TypedDict

from upcoming_movies.models import MovieCalendarEvent

logger = logging.getLogger(__name__)


class SerializedMovie(TypedDict):
    title: str
    release_date: str
    imdb_url: str
    plot_description: str
    poster_image_url: str | None


def serialize_movie_event(movie_event: MovieCalendarEvent) -> SerializedMovie:
    """Convert a MovieCalendarEvent to a JSON-serializable dictionary."""
    return {
        "title": movie_event.title,
        "release_date": movie_event.release_date.isoformat(),
        "imdb_url": movie_event.imdb_url,
        "plot_description": movie_event.plot_description,
        "poster_image_url": movie_event.poster_image_url,
    }


def build_json_from_movie_events(
    movie_events: list[MovieCalendarEvent],
) -> list[SerializedMovie]:
    """Serialize a list of movie events into a list of dictionaries."""
    return [serialize_movie_event(event) for event in movie_events]


def save_json_to_file(
    movie_events: list[MovieCalendarEvent], output_filepath: str
) -> None:
    """Serialize movie events and save to a JSON file."""
    data = build_json_from_movie_events(movie_events)
    try:
        with open(output_filepath, "w", encoding="utf-8") as output_file:
            json.dump(data, output_file, indent=2, ensure_ascii=False)
        logger.info(
            "JSON data saved to %s (%d movies)", output_filepath, len(movie_events)
        )
    except OSError as error:
        logger.error("Error saving JSON to %s: %s", output_filepath, error)
        raise

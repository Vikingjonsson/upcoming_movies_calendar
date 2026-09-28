"""JSON exporter for upcoming movie events."""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any, TypedDict

from upcoming_movies.models import MovieCalendarEvent

logger = logging.getLogger(__name__)


class SerializedMovie(TypedDict, total=False):
    title: str
    release_date: str
    imdb_url: str
    plot_description: str
    poster_image_url: str | None
    genres: list[str]


def serialize_movie_event(movie_event: MovieCalendarEvent) -> SerializedMovie:
    """Convert a MovieCalendarEvent to a JSON-serializable dictionary."""
    data: SerializedMovie = {
        "title": movie_event.title,
        "release_date": movie_event.release_date.isoformat(),
        "imdb_url": movie_event.imdb_url,
        "plot_description": movie_event.plot_description,
        "poster_image_url": movie_event.poster_image_url,
    }
    if movie_event.genres:
        data["genres"] = movie_event.genres
    return data


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


def deserialize_movie_event(data: dict[str, Any]) -> MovieCalendarEvent:
    """Convert a dictionary to a MovieCalendarEvent."""
    return MovieCalendarEvent(
        title=data["title"],
        release_date=date.fromisoformat(data["release_date"]),
        imdb_url=data["imdb_url"],
        plot_description=data.get("plot_description", ""),
        poster_image_url=data.get("poster_image_url"),
        genres=data.get("genres", []),
    )


def load_json_from_file(input_filepath: str) -> list[MovieCalendarEvent]:
    """Load and deserialize movie events from a JSON file."""
    try:
        with open(input_filepath, encoding="utf-8") as input_file:
            data = json.load(input_file)
        if not isinstance(data, list):
            raise ValueError(
                f"Expected a JSON array of movies in {input_filepath}, "
                f"got {type(data).__name__}"
            )
        movie_events = [deserialize_movie_event(item) for item in data]
        logger.info(
            "Loaded %d movies from JSON file %s", len(movie_events), input_filepath
        )
        return movie_events
    except OSError as error:
        logger.error("Error reading JSON from %s: %s", input_filepath, error)
        raise


def filter_movies_by_date(
    movie_events: list[MovieCalendarEvent],
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[MovieCalendarEvent]:
    """Filter movie events within an inclusive date range."""
    filtered: list[MovieCalendarEvent] = []
    for event in movie_events:
        if start_date and event.release_date < start_date:
            continue
        if end_date and event.release_date > end_date:
            continue
        filtered.append(event)
    return filtered


def get_weekend_movies(
    movie_events: list[MovieCalendarEvent],
    reference_date: date | None = None,
) -> list[MovieCalendarEvent]:
    """Get movies releasing on or around the upcoming weekend (Friday through Sunday).

    If reference_date is a Monday-Thursday, returns the coming Friday-Sunday.
    If reference_date is Friday, Saturday, or Sunday, returns this Friday-Sunday.
    """
    ref = reference_date or date.today()
    weekday = ref.weekday()  # Monday=0, Sunday=6

    if weekday < 4:
        days_to_friday = 4 - weekday
    elif weekday == 4:
        days_to_friday = 0
    else:
        days_to_friday = 4 - weekday

    friday = ref + timedelta(days=days_to_friday)
    sunday = friday + timedelta(days=2)

    return filter_movies_by_date(movie_events, start_date=friday, end_date=sunday)

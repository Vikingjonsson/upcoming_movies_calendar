from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from upcoming_movies.exporters.json_exporter import (
    build_json_from_movie_events,
    save_json_to_file,
    serialize_movie_event,
)
from upcoming_movies.models import MovieCalendarEvent


def _make_movie_event(
    title: str = "Test Movie",
    release_date: date = date(2026, 4, 1),
    imdb_url: str = "https://imdb.com/title/tt123",
    plot_description: str = "A test movie plot",
    poster_image_url: str | None = "https://img.com/poster.jpg",
) -> MovieCalendarEvent:
    return MovieCalendarEvent(
        title=title,
        release_date=release_date,
        imdb_url=imdb_url,
        plot_description=plot_description,
        poster_image_url=poster_image_url,
    )


class TestSerializeMovieEvent:
    def test_serialize_with_all_fields(self) -> None:
        event = _make_movie_event()
        data = serialize_movie_event(event)

        assert data == {
            "title": "Test Movie",
            "release_date": "2026-04-01",
            "imdb_url": "https://imdb.com/title/tt123",
            "plot_description": "A test movie plot",
            "poster_image_url": "https://img.com/poster.jpg",
        }

    def test_serialize_without_poster(self) -> None:
        event = _make_movie_event(poster_image_url=None)
        data = serialize_movie_event(event)

        assert data["poster_image_url"] is None
        assert data["title"] == "Test Movie"


class TestBuildJsonFromMovieEvents:
    def test_empty_list_returns_empty_list(self) -> None:
        assert build_json_from_movie_events([]) == []

    def test_multiple_events_serialized(self) -> None:
        events = [
            _make_movie_event(title="Movie 1", release_date=date(2026, 5, 1)),
            _make_movie_event(title="Movie 2", release_date=date(2026, 6, 1)),
        ]
        result = build_json_from_movie_events(events)

        assert len(result) == 2
        assert result[0]["title"] == "Movie 1"
        assert result[0]["release_date"] == "2026-05-01"
        assert result[1]["title"] == "Movie 2"
        assert result[1]["release_date"] == "2026-06-01"


class TestSaveJsonToFile:
    def test_save_json_file(self, tmp_path: Path) -> None:
        events = [
            _make_movie_event(title="Sample Movie", release_date=date(2026, 7, 4))
        ]
        output_file = tmp_path / "movies.json"
        save_json_to_file(events, str(output_file))

        assert output_file.exists()
        loaded = json.loads(output_file.read_text(encoding="utf-8"))
        assert len(loaded) == 1
        assert loaded[0]["title"] == "Sample Movie"
        assert loaded[0]["release_date"] == "2026-07-04"

    def test_save_json_raises_on_invalid_path(self) -> None:
        events = [_make_movie_event()]
        with pytest.raises(OSError):
            save_json_to_file(events, "/nonexistent_dir/output.json")

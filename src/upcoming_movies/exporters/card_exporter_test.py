from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from upcoming_movies.exporters.card_exporter import (
    build_cards_from_movie_events,
    format_movie_card,
    save_cards_to_file,
)
from upcoming_movies.models import MovieCalendarEvent


def _make_movie_event(
    title: str = "Dune: Part Two",
    release_date: date = date(2026, 3, 1),
    imdb_url: str = "https://imdb.com/title/tt15239678/",
    plot_description: str = "Paul Atreides unites with Chani and the Fremen.",
    poster_image_url: str | None = "https://img.com/dune.jpg",
    genres: list[str] | None = None,
) -> MovieCalendarEvent:
    if genres is None:
        genres = ["Action", "Adventure", "Sci-Fi"]
    return MovieCalendarEvent(
        title=title,
        release_date=release_date,
        imdb_url=imdb_url,
        plot_description=plot_description,
        poster_image_url=poster_image_url,
        genres=genres,
    )


class TestFormatMovieCard:
    def test_format_card_with_all_fields(self) -> None:
        event = _make_movie_event()
        card = format_movie_card(event)

        assert "### 🎬 [Dune: Part Two](https://imdb.com/title/tt15239678/)" in card
        assert "**Release Date**: March 01, 2026 (Sunday)" in card
        assert "`Action` `Adventure` `Sci-Fi`" in card
        assert "Paul Atreides unites with Chani" in card
        assert "[![Poster](https://img.com/dune.jpg)]" in card

    def test_format_card_without_poster_and_genres(self) -> None:
        event = _make_movie_event(poster_image_url=None, genres=[])
        card = format_movie_card(event)

        assert "### 🎬 [Dune: Part Two]" in card
        assert "**Genres**" not in card
        assert "![Poster]" not in card


class TestBuildCardsFromMovieEvents:
    def test_empty_movie_events(self) -> None:
        result = build_cards_from_movie_events([])
        assert "*No upcoming movies found.*" in result

    def test_standard_cards_formatting(self) -> None:
        events = [
            _make_movie_event(title="Movie One"),
            _make_movie_event(title="Movie Two"),
        ]
        result = build_cards_from_movie_events(events, title="Weekend Movies")

        assert "# Weekend Movies" in result
        assert "### 🎬 [Movie One]" in result
        assert "### 🎬 [Movie Two]" in result
        assert "\n---\n\n" in result

    def test_carousel_formatting(self) -> None:
        events = [
            _make_movie_event(title="Movie One"),
            _make_movie_event(title="Movie Two"),
        ]
        result = build_cards_from_movie_events(
            events, title="Weekend Movies", as_carousel=True
        )

        assert "# Weekend Movies" in result
        assert "````carousel" in result
        assert "<!-- slide -->" in result
        assert "````" in result


class TestSaveCardsToFile:
    def test_save_cards(self, tmp_path: Path) -> None:
        events = [_make_movie_event()]
        output_file = tmp_path / "cards.md"
        save_cards_to_file(events, str(output_file))

        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "### 🎬 [Dune: Part Two]" in content

    def test_save_cards_raises_on_invalid_path(self) -> None:
        events = [_make_movie_event()]
        with pytest.raises(OSError):
            save_cards_to_file(events, "/nonexistent_dir/output.md")

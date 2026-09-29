from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from upcoming_movies.exporters import (
    DEFAULT_FORMAT,
    export_movie_events,
    normalize_format,
    prompt_output_format,
    resolve_output_filename,
)
from upcoming_movies.models import MovieCalendarEvent


def _make_movie() -> MovieCalendarEvent:
    return MovieCalendarEvent(
        title="Test Movie",
        release_date=date(2026, 4, 1),
        imdb_url="https://imdb.com/title/tt123",
        plot_description="A test movie plot",
    )


class TestNormalizeFormat:
    def test_normalize_cards(self) -> None:
        assert normalize_format("cards") == "cards"
        assert normalize_format("card") == "cards"
        assert normalize_format("CARD") == "cards"

    def test_normalize_terminal(self) -> None:
        assert normalize_format("terminal") == "terminal"
        assert normalize_format("terminal-cards") == "terminal"
        assert normalize_format("card-view") == "terminal"
        assert normalize_format("term") == "terminal"

    def test_normalize_standard_formats(self) -> None:
        assert normalize_format("json") == "json"
        assert normalize_format("ics") == "ics"
        assert normalize_format("JSON") == "json"


class TestResolveOutputFilename:
    def test_custom_output_preserved(self) -> None:
        assert resolve_output_filename("json", "custom.json") == "custom.json"
        assert resolve_output_filename("ics", "custom.ics") == "custom.ics"
        assert resolve_output_filename("cards", "custom.md") == "custom.md"
        assert resolve_output_filename("terminal", "custom.txt") == "custom.txt"

    def test_default_filename_for_ics(self) -> None:
        assert resolve_output_filename("ics") == "upcoming_movies.ics"

    def test_default_filename_for_json(self) -> None:
        assert resolve_output_filename("json") == "upcoming_movies.json"

    def test_default_filename_for_cards(self) -> None:
        assert resolve_output_filename("cards") == "upcoming_movies.md"
        assert resolve_output_filename("card") == "upcoming_movies.md"

    def test_default_filename_for_terminal(self) -> None:
        assert resolve_output_filename("terminal") == "upcoming_movies_cards.txt"
        assert resolve_output_filename("term") == "upcoming_movies_cards.txt"

    def test_unknown_format_fallback(self) -> None:
        assert resolve_output_filename("xml") == "upcoming_movies.xml"


class TestPromptOutputFormat:
    def test_non_tty_returns_default(self) -> None:
        with patch("sys.stdin.isatty", return_value=False):
            assert prompt_output_format() == DEFAULT_FORMAT

    def test_empty_input_returns_default(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value=""),
        ):
            assert prompt_output_format() == DEFAULT_FORMAT

    def test_numeric_selection_one(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="1"),
        ):
            assert prompt_output_format() == "ics"

    def test_numeric_selection_two(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="2"),
        ):
            assert prompt_output_format() == "json"

    def test_numeric_selection_four(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="4"),
        ):
            assert prompt_output_format() == "terminal"

    def test_name_selection(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="json"),
        ):
            assert prompt_output_format() == "json"

    def test_invalid_selection_falls_back_to_default(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="99"),
        ):
            assert prompt_output_format() == DEFAULT_FORMAT

    def test_eof_falls_back_to_default(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", side_effect=EOFError),
        ):
            assert prompt_output_format() == DEFAULT_FORMAT


class TestExportMovieEvents:
    def test_export_json(self, tmp_path: Path) -> None:
        output_file = tmp_path / "test.json"
        export_movie_events([_make_movie()], "json", str(output_file))
        assert output_file.exists()
        assert "Test Movie" in output_file.read_text(encoding="utf-8")

    def test_export_ics(self, tmp_path: Path) -> None:
        output_file = tmp_path / "test.ics"
        export_movie_events([_make_movie()], "ics", str(output_file))
        assert output_file.exists()
        assert b"BEGIN:VCALENDAR" in output_file.read_bytes()

    def test_export_cards(self, tmp_path: Path) -> None:
        output_file = tmp_path / "test.md"
        export_movie_events([_make_movie()], "cards", str(output_file))
        assert output_file.exists()
        assert "### 🎬 [Test Movie]" in output_file.read_text(encoding="utf-8")

    def test_export_card_alias(self, tmp_path: Path) -> None:
        output_file = tmp_path / "test_alias.md"
        export_movie_events([_make_movie()], "card", str(output_file))
        assert output_file.exists()
        assert "### 🎬 [Test Movie]" in output_file.read_text(encoding="utf-8")

    def test_export_terminal(self, tmp_path: Path) -> None:
        output_file = tmp_path / "terminal.txt"
        export_movie_events([_make_movie()], "terminal", str(output_file))
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "[1] 🎬 Test Movie  [MOVIE]" in content

    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Unsupported format"):
            export_movie_events([], "yaml", str(tmp_path / "test.yaml"))

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from upcoming_movies.exporters import (
    DEFAULT_FORMAT,
    export_movie_events,
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


class TestResolveOutputFilename:
    def test_custom_output_preserved(self) -> None:
        assert resolve_output_filename("json", "custom.json") == "custom.json"
        assert resolve_output_filename("ics", "custom.ics") == "custom.ics"

    def test_default_filename_for_ics(self) -> None:
        assert resolve_output_filename("ics") == "upcoming_movies.ics"

    def test_default_filename_for_json(self) -> None:
        assert resolve_output_filename("json") == "upcoming_movies.json"

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

    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="Unsupported format"):
            export_movie_events([], "yaml", str(tmp_path / "test.yaml"))

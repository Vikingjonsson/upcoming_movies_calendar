from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from upcoming_movies.cli import (
    build_parser,
    cli_main,
    format_movies_table,
    format_regions_table,
    handle_export,
    handle_regions,
    handle_scrape,
    prompt_region_choice,
    prompt_text,
    style,
    supports_color,
)
from upcoming_movies.models import MovieCalendarEvent


def _make_test_movie(
    title: str = "Test Film",
    release_date: date = date(2026, 5, 10),
    imdb_url: str = "https://www.imdb.com/title/tt1111111/",
) -> MovieCalendarEvent:
    return MovieCalendarEvent(
        title=title,
        release_date=release_date,
        imdb_url=imdb_url,
        plot_description="A test movie plot description.",
    )


class TestCliArgParsing:
    def test_default_empty_args(self) -> None:
        parser = build_parser()
        args = parser.parse_args([])
        assert args.subcommand is None
        assert args.format is None
        assert args.region is None
        assert args.output is None
        assert not args.verbose
        assert not args.quiet

    def test_root_flags_parsed(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["-f", "json", "-r", "US", "-o", "movies.json", "--no-prompt", "-v"]
        )
        assert args.format == "json"
        assert args.region == "US"
        assert args.output == "movies.json"
        assert args.no_prompt is True
        assert args.verbose is True

    def test_subcommand_scrape(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["scrape", "-f", "ics", "-r", "GB", "--limit", "5", "--no-table"]
        )
        assert args.subcommand == "scrape"
        assert args.format == "ics"
        assert args.region == "GB"
        assert args.limit == 5
        assert args.no_table is True

    def test_subcommand_regions(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["regions"])
        assert args.subcommand == "regions"

    def test_subcommand_wizard(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["wizard"])
        assert args.subcommand == "wizard"

    def test_subcommand_export(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["export", "-i", "data.json", "-f", "ics", "-o", "out.ics"]
        )
        assert args.subcommand == "export"
        assert args.input == "data.json"
        assert args.format == "ics"
        assert args.output == "out.ics"


class TestStylingAndTables:
    def test_supports_color_disabled_by_no_color(self) -> None:
        with patch.dict("os.environ", {"NO_COLOR": "1"}):
            assert supports_color() is False

    def test_supports_color_disabled_non_tty(self) -> None:
        with (
            patch.dict("os.environ", {}, clear=True),
            patch("sys.stdout.isatty", return_value=False),
        ):
            assert supports_color() is False

    def test_style_returns_plain_when_color_unsupported(self) -> None:
        with patch("upcoming_movies.cli.supports_color", return_value=False):
            assert style("test", "\033[32m") == "test"

    def test_style_wraps_code_when_supported(self) -> None:
        with patch("upcoming_movies.cli.supports_color", return_value=True):
            result = style("hello", "\033[32m")
            assert result == "\033[32mhello\033[0m"

    def test_format_regions_table_contains_regions(self) -> None:
        output = format_regions_table()
        assert "Available IMDB Region Codes:" in output
        assert "SE" in output
        assert "Sweden" in output
        assert "US" in output

    def test_format_movies_table_empty(self) -> None:
        assert format_movies_table([]) == ""

    def test_format_movies_table_renders_events(self) -> None:
        events = [_make_test_movie()]
        output = format_movies_table(events, max_width=80)
        assert "Date" in output
        assert "Title" in output
        assert "IMDB URL" in output
        assert "2026-05-10" in output
        assert "Test Film" in output


class TestInteractivePrompts:
    def test_prompt_text_with_default(self) -> None:
        with patch("builtins.input", return_value=""):
            assert prompt_text("Filename", default="movies.ics") == "movies.ics"

    def test_prompt_text_with_custom_input(self) -> None:
        with patch("builtins.input", return_value="custom.ics"):
            assert prompt_text("Filename", default="movies.ics") == "custom.ics"

    def test_prompt_region_non_tty_returns_default(self) -> None:
        with patch("sys.stdin.isatty", return_value=False):
            assert prompt_region_choice(default_region="SE") == "SE"

    def test_prompt_region_select_by_index(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="2"),
        ):
            # 2 is United States (US)
            assert prompt_region_choice(default_region="SE") == "US"

    def test_prompt_region_select_by_code(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="de"),
        ):
            assert prompt_region_choice(default_region="SE") == "DE"

    def test_prompt_region_custom_code_option(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", side_effect=["8", "no"]),
        ):
            assert prompt_region_choice(default_region="SE") == "NO"


class TestCommandHandlers:
    def test_handle_regions_returns_zero(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        parser = build_parser()
        args = parser.parse_args(["regions"])
        assert handle_regions(args) == 0
        captured = capsys.readouterr()
        assert "Available IMDB Region Codes" in captured.out

    def test_handle_export_success(self, tmp_path: Path) -> None:
        json_file = tmp_path / "movies.json"
        out_ics = tmp_path / "exported.ics"
        movie_data = [
            {
                "title": "Exported Movie",
                "release_date": "2026-06-15",
                "imdb_url": "https://www.imdb.com/title/tt999/",
            }
        ]
        json_file.write_text(json.dumps(movie_data), encoding="utf-8")

        parser = build_parser()
        args = parser.parse_args(
            [
                "export",
                "-i",
                str(json_file),
                "-f",
                "ics",
                "-o",
                str(out_ics),
                "--no-table",
            ]
        )

        exit_code = handle_export(args)
        assert exit_code == 0
        assert out_ics.exists()

    def test_handle_export_file_not_found(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["export", "-i", "/missing.json", "-f", "ics"])
        assert handle_export(args) == 1

    def test_handle_scrape_success(self, tmp_path: Path) -> None:
        out_json = tmp_path / "scraped.json"
        mock_movies = [_make_test_movie()]

        parser = build_parser()
        args = parser.parse_args(
            ["-f", "json", "-r", "SE", "-o", str(out_json), "--no-table"]
        )

        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
            return_value=mock_movies,
        ):
            assert handle_scrape(args) == 0

        assert out_json.exists()

    def test_handle_scrape_no_movies_found(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["-f", "ics", "-r", "SE", "--no-prompt"])

        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
            return_value=[],
        ):
            assert handle_scrape(args) == 0

    def test_handle_scrape_scraper_failure(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["-f", "ics", "-r", "SE", "--no-prompt"])

        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
            side_effect=RuntimeError("Scraper crashed"),
        ):
            assert handle_scrape(args) == 1


class TestCliMain:
    def test_cli_main_regions(self, capsys: pytest.CaptureFixture[str]) -> None:
        assert cli_main(["regions"]) == 0
        captured = capsys.readouterr()
        assert "Available IMDB Region Codes" in captured.out

    def test_cli_main_list_regions_flag(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert cli_main(["--list-regions"]) == 0
        captured = capsys.readouterr()
        assert "Available IMDB Region Codes" in captured.out

    def test_cli_main_keyboard_interrupt(self) -> None:
        with patch("upcoming_movies.cli.handle_scrape", side_effect=KeyboardInterrupt):
            assert cli_main(["-f", "ics", "--no-prompt"]) == 130

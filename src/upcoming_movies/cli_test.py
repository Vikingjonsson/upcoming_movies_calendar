"""Tests for the argparse CLI interface."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from upcoming_movies.cli import (
    build_parser,
    cli_main,
    display_regions,
    main,
    parse_command_line_arguments,
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
    def test_default_arguments(self) -> None:
        args = parse_command_line_arguments([])
        assert args.format is None
        assert args.region == "SE"
        assert args.output is None
        assert args.calendar_name == "Upcoming Movies"
        assert not args.list_regions
        assert not args.no_prompt
        assert not args.quiet
        assert not args.verbose

    def test_short_flags_parsed(self) -> None:
        args = parse_command_line_arguments(
            [
                "-f",
                "json",
                "-r",
                "US",
                "-o",
                "movies.json",
                "-c",
                "US Movies",
                "-v",
                "-q",
            ]
        )
        assert args.format == "json"
        assert args.region == "US"
        assert args.output == "movies.json"
        assert args.calendar_name == "US Movies"
        assert args.verbose is True
        assert args.quiet is True

    def test_long_flags_parsed(self) -> None:
        args = parse_command_line_arguments(
            [
                "--format",
                "ics",
                "--region",
                "GB",
                "--output",
                "custom.ics",
                "--calendar-name",
                "UK Cinema",
                "--no-prompt",
            ]
        )
        assert args.format == "ics"
        assert args.region == "GB"
        assert args.output == "custom.ics"
        assert args.calendar_name == "UK Cinema"
        assert args.no_prompt is True

    def test_list_regions_flag(self) -> None:
        args = parse_command_line_arguments(["-l"])
        assert args.list_regions is True

    def test_invalid_format_fails(self) -> None:
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["-f", "invalid_format"])


class TestDisplayRegions:
    def test_display_regions_prints_common_regions(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        display_regions()
        captured = capsys.readouterr()
        assert "Common IMDB Region Codes:" in captured.out
        assert "SE" in captured.out
        assert "Sweden (default)" in captured.out
        assert "US" in captured.out
        assert "United States" in captured.out


class TestCliMain:
    def test_list_regions_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = cli_main(["-l"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Common IMDB Region Codes:" in captured.out

    def test_scrape_successful(self, tmp_path: Path) -> None:
        out_file = tmp_path / "movies.json"
        mock_movies = [_make_test_movie()]

        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
            return_value=mock_movies,
        ):
            exit_code = cli_main(
                ["-f", "json", "-r", "SE", "-o", str(out_file), "--no-prompt"]
            )

        assert exit_code == 0
        assert out_file.exists()

    def test_scrape_quiet_mode(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out_file = tmp_path / "movies.json"
        mock_movies = [_make_test_movie()]

        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
            return_value=mock_movies,
        ):
            exit_code = cli_main(
                ["-f", "json", "-o", str(out_file), "-q", "--no-prompt"]
            )

        assert exit_code == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == str(out_file)

    def test_scrape_no_movies_found(self) -> None:
        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
            return_value=[],
        ):
            exit_code = cli_main(["-f", "ics", "--no-prompt"])
            assert exit_code == 0

    def test_scrape_scraper_exception(self) -> None:
        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
            side_effect=RuntimeError("Scraping failed"),
        ):
            exit_code = cli_main(["-f", "ics", "--no-prompt"])
            assert exit_code == 1

    def test_prompt_fallback_when_format_omitted(self, tmp_path: Path) -> None:
        out_file = tmp_path / "fallback.ics"
        mock_movies = [_make_test_movie()]

        with (
            patch(
                "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
                return_value=mock_movies,
            ),
            patch("sys.stdin.isatty", return_value=False),
        ):
            exit_code = cli_main(["-o", str(out_file)])

        assert exit_code == 0
        assert out_file.exists()

    def test_main_keyboard_interrupt(self) -> None:
        with (
            patch("upcoming_movies.cli.cli_main", side_effect=KeyboardInterrupt),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()
        assert exc_info.value.code == 130

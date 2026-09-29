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
    prompt_card_carousel,
    prompt_date_filter,
    prompt_output_filepath,
    prompt_region,
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


@pytest.fixture(autouse=True)
def isolate_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests run with an isolated, empty cache directory."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))


class TestCliArgParsing:
    def test_default_arguments(self) -> None:
        args = parse_command_line_arguments([])
        assert args.format is None
        assert args.region is None
        assert args.output is None
        assert args.from_json is None
        assert args.calendar_name == "Upcoming Movies"
        assert not args.today
        assert not args.weekend
        assert args.from_date is None
        assert args.to_date is None
        assert not args.carousel
        assert not args.card_view
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

    def test_card_view_flag(self) -> None:
        args = parse_command_line_arguments(["--card-view"])
        assert args.card_view is True

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

    def test_uses_cached_movies_if_fresh(self, tmp_path: Path) -> None:
        from upcoming_movies.cache import save_cached_movies

        mock_cached = [_make_test_movie("Cached Cinema")]
        save_cached_movies("SE", mock_cached)

        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb"
        ) as mock_scrape:
            exit_code = cli_main(["-f", "terminal", "--no-prompt"])
            assert exit_code == 0
            mock_scrape.assert_not_called()

    def test_refresh_flag_bypasses_cache(self, tmp_path: Path) -> None:
        from upcoming_movies.cache import save_cached_movies

        mock_cached = [_make_test_movie("Old Film")]
        save_cached_movies("SE", mock_cached)

        fresh_movies = [_make_test_movie("Fresh Live Film")]
        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
            return_value=fresh_movies,
        ) as mock_scrape:
            exit_code = cli_main(["--refresh", "-f", "terminal", "--no-prompt"])
            assert exit_code == 0
            mock_scrape.assert_called_once()

    def test_no_cache_flag_bypasses_cache(self, tmp_path: Path) -> None:
        from upcoming_movies.cache import save_cached_movies

        mock_cached = [_make_test_movie("Old Film")]
        save_cached_movies("SE", mock_cached)

        fresh_movies = [_make_test_movie("Fresh Film")]
        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
            return_value=fresh_movies,
        ) as mock_scrape:
            exit_code = cli_main(["--no-cache", "-f", "terminal", "--no-prompt"])
            assert exit_code == 0
            mock_scrape.assert_called_once()

    def test_fallback_to_stale_cache_on_exception(self, tmp_path: Path) -> None:
        import os
        import time

        from upcoming_movies.cache import save_cached_movies

        mock_cached = [_make_test_movie("Stale Resilient Film")]
        path = save_cached_movies("SE", mock_cached)
        # make it stale (>24h)
        old_time = time.time() - (48 * 3600)
        os.utime(path, (old_time, old_time))

        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
            side_effect=RuntimeError("Network down"),
        ):
            exit_code = cli_main(["-f", "terminal", "--no-prompt"])
            assert exit_code == 0

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

    def test_main_broken_pipe(self) -> None:
        with (
            patch("upcoming_movies.cli.cli_main", side_effect=BrokenPipeError),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()
        assert exc_info.value.code == 0

    def test_from_json_offline_mode(self, tmp_path: Path) -> None:
        json_file = tmp_path / "cache.json"
        out_file = tmp_path / "cards.md"
        json_file.write_text(
            '[{"title": "Offline Movie", "release_date": "2026-05-10", '
            '"imdb_url": "https://imdb.com/title/tt999", "plot_description": "P"}]',
            encoding="utf-8",
        )
        exit_code = cli_main(
            ["-i", str(json_file), "-f", "cards", "-o", str(out_file), "--no-prompt"]
        )
        assert exit_code == 0
        assert out_file.exists()
        assert "Offline Movie" in out_file.read_text(encoding="utf-8")

    def test_invalid_from_date_format(self) -> None:
        exit_code = cli_main(["--from-date", "invalid-date", "--no-prompt"])
        assert exit_code == 1

    def test_invalid_to_date_format(self) -> None:
        exit_code = cli_main(["--to-date", "invalid-date", "--no-prompt"])
        assert exit_code == 1

    def test_weekend_flag_filtering(self, tmp_path: Path) -> None:
        out_file = tmp_path / "weekend.json"
        mock_movies = [
            _make_test_movie("Weekday Movie", release_date=date(2026, 4, 15)),
        ]
        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
            return_value=mock_movies,
        ):
            exit_code = cli_main(
                ["-f", "json", "--weekend", "-o", str(out_file), "--no-prompt"]
            )
        assert exit_code == 0
        assert not out_file.exists()

    def test_card_view_stdout(self, capsys: pytest.CaptureFixture[str]) -> None:
        mock_movies = [_make_test_movie("Terminal Movie")]
        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
            return_value=mock_movies,
        ):
            exit_code = cli_main(["--card-view", "--no-prompt"])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "[1] 🎬 Terminal Movie  [MOVIE]" in captured.out
        assert "─" * 70 in captured.out

    def test_format_terminal_with_file_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        out_file = tmp_path / "terminal.txt"
        mock_movies = [_make_test_movie("File Terminal Movie")]
        with patch(
            "upcoming_movies.cli.scrape_upcoming_movies_from_imdb",
            return_value=mock_movies,
        ):
            exit_code = cli_main(["-f", "terminal", "-o", str(out_file), "--no-prompt"])
        assert exit_code == 0
        assert out_file.exists()
        assert "[1] 🎬 File Terminal Movie  [MOVIE]" in out_file.read_text(
            encoding="utf-8"
        )
        captured = capsys.readouterr()
        assert "[1] 🎬 File Terminal Movie  [MOVIE]" in captured.out


class TestPromptHelpers:
    def test_prompt_region_non_tty(self) -> None:
        with patch("sys.stdin.isatty", return_value=False):
            assert prompt_region() == "SE"

    def test_prompt_region_numeric_choice(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="1"),
        ):
            assert prompt_region() == "US"

    def test_prompt_region_custom_code(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="gb"),
        ):
            assert prompt_region() == "GB"

    def test_prompt_region_empty_input_default(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value=""),
        ):
            assert prompt_region() == "SE"

    def test_prompt_date_filter_all(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="1"),
        ):
            assert prompt_date_filter() == (None, None, False)

    def test_prompt_date_filter_weekend(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="2"),
        ):
            assert prompt_date_filter() == (None, None, True)

    def test_prompt_date_filter_today(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="3"),
        ):
            start, end, weekend = prompt_date_filter()
            assert start == date.today()
            assert end == date.today()
            assert weekend is False

    def test_prompt_card_carousel(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="2"),
        ):
            assert prompt_card_carousel() is True

        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="1"),
        ):
            assert prompt_card_carousel() is False

    def test_prompt_output_filepath(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value="custom.json"),
        ):
            assert prompt_output_filepath("default.json") == "custom.json"

        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value=""),
        ):
            assert prompt_output_filepath("default.json") == "default.json"

    def test_prompt_output_filepath_terminal_default_none(self) -> None:
        with (
            patch("sys.stdin.isatty", return_value=True),
            patch("builtins.input", return_value=""),
        ):
            assert (
                prompt_output_filepath("upcoming_movies_cards.txt", is_terminal=True)
                is None
            )

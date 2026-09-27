from __future__ import annotations

from datetime import date

import pytest

from upcoming_movies.scraping.scraper_utils import parse_imdb_release_date


class TestParseImdbReleaseDate:
    def test_standard_date(self) -> None:
        assert parse_imdb_release_date("Mar 29, 2026") == date(2026, 3, 29)

    def test_january_first(self) -> None:
        assert parse_imdb_release_date("Jan 1, 2025") == date(2025, 1, 1)

    def test_december_end(self) -> None:
        assert parse_imdb_release_date("Dec 31, 2024") == date(2024, 12, 31)

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_imdb_release_date("2026-03-29")

    def test_nonsense_raises(self) -> None:
        with pytest.raises(ValueError):
            parse_imdb_release_date("not a date")

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from upcoming_movies.models import MovieCalendarEvent, ScheduledMovie
from upcoming_movies.scraping.scraper import (
    RawMoviePayload,
    _scrape_all_movie_details,
    parse_scheduled_movie_records,
)


class TestParseScheduledMovieRecords:
    def test_parse_valid_records(self) -> None:
        raw: list[RawMoviePayload] = [
            {
                "title": "Movie 1",
                "release_date_text": "Oct 1, 2026",
                "imdb_url": "https://imdb.com/title/tt111",
            },
            {
                "title": "Movie 2",
                "release_date_text": "Nov 5, 2026",
                "imdb_url": "https://imdb.com/title/tt222",
            },
        ]
        movies = parse_scheduled_movie_records(raw)
        assert len(movies) == 2
        assert movies[0].title == "Movie 1"
        assert movies[0].release_date_text == "Oct 1, 2026"
        assert movies[0].imdb_url == "https://imdb.com/title/tt111"
        assert movies[1].title == "Movie 2"

    def test_parse_empty_records(self) -> None:
        assert parse_scheduled_movie_records([]) == []


class TestScrapeAllMovieDetailsCaching:
    def test_deduplicates_page_loads_for_same_base_url(self) -> None:
        mock_driver = MagicMock()
        movies = [
            ScheduledMovie(
                "Movie A", "Oct 1, 2026", "https://imdb.com/title/tt123?ref_=a"
            ),
            ScheduledMovie(
                "Movie A (Wide)", "Oct 8, 2026", "https://imdb.com/title/tt123?ref_=b"
            ),
        ]

        with patch(
            "upcoming_movies.scraping.scraper.scrape_movie_detail_page"
        ) as mock_scrape:
            mock_scrape.return_value = MovieCalendarEvent(
                title="Movie A",
                release_date=date(2026, 10, 1),
                imdb_url="https://imdb.com/title/tt123?ref_=a",
                plot_description="A cool movie",
                poster_image_url="https://img.com/poster.jpg",
            )
            events = _scrape_all_movie_details(mock_driver, movies)

            assert len(events) == 2
            assert mock_scrape.call_count == 1
            assert events[0].plot_description == "A cool movie"
            assert events[1].plot_description == "A cool movie"
            assert events[0].release_date == date(2026, 10, 1)
            assert events[1].release_date == date(2026, 10, 8)


class TestScrapeViaNextData:
    def test_parses_valid_next_data_payload(self) -> None:
        mock_driver = MagicMock()
        mock_driver.execute_async_script.return_value = {
            "movies": [
                {
                    "id": "tt123",
                    "title": "Fast Movie",
                    "release_date_str": "Fri, 02 Oct 2026 00:00:00 GMT",
                    "genres": ["Action", "Thriller"],
                    "poster": "https://img.com/p.jpg",
                    "imdb_url": "https://imdb.com/title/tt123/",
                    "plot": "Fast plot",
                }
            ]
        }
        from upcoming_movies.scraping.scraper import _scrape_via_next_data

        events = _scrape_via_next_data(mock_driver)
        assert events is not None
        assert len(events) == 1
        assert events[0].title == "Fast Movie"
        assert events[0].release_date == date(2026, 10, 2)
        assert events[0].genres == ["Action", "Thriller"]
        assert events[0].poster_image_url == "https://img.com/p.jpg"
        assert events[0].plot_description == "Fast plot"

    def test_returns_none_on_error(self) -> None:
        mock_driver = MagicMock()
        mock_driver.execute_async_script.return_value = {"error": "Failed"}
        from upcoming_movies.scraping.scraper import _scrape_via_next_data

        assert _scrape_via_next_data(mock_driver) is None

    def test_returns_none_on_webdriver_exception(self) -> None:
        from selenium.common.exceptions import WebDriverException

        from upcoming_movies.scraping.scraper import _scrape_via_next_data

        mock_driver = MagicMock()
        mock_driver.execute_async_script.side_effect = WebDriverException("Timeout")
        assert _scrape_via_next_data(mock_driver) is None

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from upcoming_movies.models import MovieCalendarEvent, ScheduledMovie
from upcoming_movies.scraper import (
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

        with patch("upcoming_movies.scraper.scrape_movie_detail_page") as mock_scrape:
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

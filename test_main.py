from datetime import date

import pytest

from main import (
    MovieCalendarEvent,
    build_icalendar_from_movie_events,
    generate_calendar_event_uid,
    parse_imdb_release_date,
)


class TestParseImdbReleaseDate:
    def test_standard_date(self):
        assert parse_imdb_release_date("Mar 29, 2026") == date(2026, 3, 29)

    def test_january_first(self):
        assert parse_imdb_release_date("Jan 1, 2025") == date(2025, 1, 1)

    def test_december_end(self):
        assert parse_imdb_release_date("Dec 31, 2024") == date(2024, 12, 31)

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError):
            parse_imdb_release_date("2026-03-29")

    def test_nonsense_raises(self):
        with pytest.raises(ValueError):
            parse_imdb_release_date("not a date")


class TestGenerateCalendarEventUid:
    def test_same_input_produces_same_uid(self):
        first_uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt123", date(2026, 3, 29)
        )
        second_uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt123", date(2026, 3, 29)
        )
        assert first_uid == second_uid

    def test_different_url_produces_different_uid(self):
        first_uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt123", date(2026, 3, 29)
        )
        second_uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt456", date(2026, 3, 29)
        )
        assert first_uid != second_uid

    def test_different_date_produces_different_uid(self):
        first_uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt123", date(2026, 3, 29)
        )
        second_uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt123", date(2026, 4, 1)
        )
        assert first_uid != second_uid

    def test_uid_ends_with_domain_suffix(self):
        uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt123", date(2026, 3, 29)
        )
        assert uid.endswith("@upcoming-movies")


class TestBuildIcalendarFromMovieEvents:
    def _make_movie_event(self, **overrides) -> MovieCalendarEvent:
        defaults = {
            "title": "Test Movie",
            "release_date": date(2026, 4, 1),
            "imdb_url": "https://imdb.com/title/tt123",
            "plot_description": "A test movie",
        }
        defaults.update(overrides)
        return MovieCalendarEvent(**defaults)

    def test_calendar_contains_movie_titles(self):
        movie_events = [
            self._make_movie_event(title="Movie A"),
            self._make_movie_event(
                title="Movie B", imdb_url="https://imdb.com/title/tt456"
            ),
        ]
        calendar = build_icalendar_from_movie_events(
            movie_events, calendar_name="Test Calendar"
        )
        calendar_text = calendar.to_ical().decode()

        assert "Movie A" in calendar_text
        assert "Movie B" in calendar_text
        assert "Test Calendar" in calendar_text

    def test_events_have_uid(self):
        movie_events = [self._make_movie_event()]
        calendar = build_icalendar_from_movie_events(movie_events)
        calendar_text = calendar.to_ical().decode()

        assert "UID" in calendar_text
        assert "@upcoming-movies" in calendar_text

    def test_empty_events_produces_no_vevent(self):
        calendar = build_icalendar_from_movie_events([], calendar_name="Empty")
        calendar_text = calendar.to_ical().decode()

        assert "Empty" in calendar_text
        assert "VEVENT" not in calendar_text

    def test_event_dates_span_one_day(self):
        movie_events = [self._make_movie_event(release_date=date(2026, 6, 15))]
        calendar = build_icalendar_from_movie_events(movie_events)
        calendar_text = calendar.to_ical().decode()

        assert "20260615" in calendar_text
        assert "20260616" in calendar_text

    def test_event_contains_imdb_url(self):
        movie_events = [
            self._make_movie_event(imdb_url="https://imdb.com/title/tt999")
        ]
        calendar = build_icalendar_from_movie_events(movie_events)
        calendar_text = calendar.to_ical().decode()

        assert "https://imdb.com/title/tt999" in calendar_text

    def test_event_contains_plot_description(self):
        movie_events = [self._make_movie_event(plot_description="A great plot")]
        calendar = build_icalendar_from_movie_events(movie_events)
        calendar_text = calendar.to_ical().decode()

        assert "A great plot" in calendar_text

    def test_event_contains_poster_attachment(self):
        poster_url = "https://m.media-amazon.com/images/poster.jpg"
        movie_events = [self._make_movie_event(poster_image_url=poster_url)]
        calendar = build_icalendar_from_movie_events(movie_events)
        calendar_text = calendar.to_ical().decode()

        assert "ATTACH" in calendar_text
        assert poster_url in calendar_text

    def test_event_without_poster_has_no_attachment(self):
        movie_events = [self._make_movie_event(poster_image_url=None)]
        calendar = build_icalendar_from_movie_events(movie_events)
        calendar_text = calendar.to_ical().decode()

        assert "ATTACH" not in calendar_text

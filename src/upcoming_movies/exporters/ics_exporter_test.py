from __future__ import annotations

from datetime import date
from pathlib import Path

from upcoming_movies.exporters.ics_exporter import (
    build_icalendar_from_movie_events,
    generate_calendar_event_uid,
    save_calendar_to_file,
)
from upcoming_movies.models import MovieCalendarEvent


class TestGenerateCalendarEventUid:
    def test_same_input_produces_same_uid(self) -> None:
        first_uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt123", date(2026, 3, 29)
        )
        second_uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt123", date(2026, 3, 29)
        )
        assert first_uid == second_uid

    def test_different_url_produces_different_uid(self) -> None:
        first_uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt123", date(2026, 3, 29)
        )
        second_uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt456", date(2026, 3, 29)
        )
        assert first_uid != second_uid

    def test_different_date_produces_different_uid(self) -> None:
        first_uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt123", date(2026, 3, 29)
        )
        second_uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt123", date(2026, 4, 1)
        )
        assert first_uid != second_uid

    def test_uid_ends_with_domain_suffix(self) -> None:
        uid = generate_calendar_event_uid(
            "https://imdb.com/title/tt123", date(2026, 3, 29)
        )
        assert uid.endswith("@upcoming-movies")


class TestBuildIcalendarFromMovieEvents:
    def _make_movie_event(
        self,
        title: str = "Test Movie",
        release_date: date = date(2026, 4, 1),
        imdb_url: str = "https://imdb.com/title/tt123",
        plot_description: str = "A test movie",
        poster_image_url: str | None = None,
    ) -> MovieCalendarEvent:
        return MovieCalendarEvent(
            title=title,
            release_date=release_date,
            imdb_url=imdb_url,
            plot_description=plot_description,
            poster_image_url=poster_image_url,
        )

    def test_calendar_contains_movie_titles(self) -> None:
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

    def test_events_have_uid(self) -> None:
        movie_events = [self._make_movie_event()]
        calendar = build_icalendar_from_movie_events(movie_events)
        calendar_text = calendar.to_ical().decode()

        assert "UID" in calendar_text
        assert "@upcoming-movies" in calendar_text

    def test_empty_events_produces_no_vevent(self) -> None:
        calendar = build_icalendar_from_movie_events([], calendar_name="Empty")
        calendar_text = calendar.to_ical().decode()

        assert "Empty" in calendar_text
        assert "VEVENT" not in calendar_text

    def test_event_dates_span_one_day(self) -> None:
        movie_events = [self._make_movie_event(release_date=date(2026, 6, 15))]
        calendar = build_icalendar_from_movie_events(movie_events)
        calendar_text = calendar.to_ical().decode()

        assert "20260615" in calendar_text
        assert "20260616" in calendar_text

    def test_event_contains_imdb_url(self) -> None:
        movie_events = [self._make_movie_event(imdb_url="https://imdb.com/title/tt999")]
        calendar = build_icalendar_from_movie_events(movie_events)
        calendar_text = calendar.to_ical().decode()

        assert "https://imdb.com/title/tt999" in calendar_text

    def test_event_contains_plot_description(self) -> None:
        movie_events = [self._make_movie_event(plot_description="A great plot")]
        calendar = build_icalendar_from_movie_events(movie_events)
        calendar_text = calendar.to_ical().decode()

        assert "A great plot" in calendar_text

    def test_event_contains_poster_attachment(self) -> None:
        poster_url = "https://m.media-amazon.com/images/poster.jpg"
        movie_events = [self._make_movie_event(poster_image_url=poster_url)]
        calendar = build_icalendar_from_movie_events(movie_events)
        calendar_text = calendar.to_ical().decode()

        assert "ATTACH" in calendar_text
        assert poster_url in calendar_text

    def test_event_without_poster_has_no_attachment(self) -> None:
        movie_events = [self._make_movie_event(poster_image_url=None)]
        calendar = build_icalendar_from_movie_events(movie_events)
        calendar_text = calendar.to_ical().decode()

        assert "ATTACH" not in calendar_text


class TestSaveCalendarToFile:
    def test_save_calendar_to_file(self, tmp_path: Path) -> None:
        calendar = build_icalendar_from_movie_events([], calendar_name="Test")
        output_file = tmp_path / "test_calendar.ics"
        save_calendar_to_file(calendar, str(output_file))

        assert output_file.exists()
        content = output_file.read_bytes()
        assert b"BEGIN:VCALENDAR" in content
        assert b"Test" in content

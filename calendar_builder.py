import hashlib
import logging
from datetime import date, timedelta

from icalendar import Calendar, Event, vUri

from config import DEFAULT_CONFIG
from models import MovieCalendarEvent

EVENT_UID_DOMAIN = "@upcoming-movies"
EVENT_UID_HASH_LENGTH = 16


def generate_calendar_event_uid(imdb_url: str, release_date: date) -> str:
    raw_identifier = f"{imdb_url}:{release_date.isoformat()}"
    hash_prefix = hashlib.sha256(raw_identifier.encode()).hexdigest()[
        :EVENT_UID_HASH_LENGTH
    ]
    return f"{hash_prefix}{EVENT_UID_DOMAIN}"


def create_calendar_event_from_movie(movie_event: MovieCalendarEvent) -> Event:
    day_after_release = movie_event.release_date + timedelta(days=1)

    calendar_event = Event()
    calendar_event.add(
        "uid",
        generate_calendar_event_uid(movie_event.imdb_url, movie_event.release_date),
    )
    calendar_event.add("dtstart", movie_event.release_date)
    calendar_event.add("dtend", day_after_release)
    calendar_event.add("summary", movie_event.title)
    calendar_event.add("description", movie_event.plot_description)
    calendar_event.add("url", movie_event.imdb_url)

    if movie_event.poster_image_url:
        calendar_event.add(
            "attach",
            vUri(movie_event.poster_image_url),
            parameters={"FMTTYPE": "image/jpeg"},
        )

    return calendar_event


DEFAULT_CALENDAR_NAME = str(DEFAULT_CONFIG["calendar_name"])


def build_icalendar_from_movie_events(
    movie_events: list[MovieCalendarEvent],
    calendar_name: str = DEFAULT_CALENDAR_NAME,
) -> Calendar:
    logging.info(
        "Creating calendar '%s' with %d events",
        calendar_name,
        len(movie_events),
    )

    calendar = Calendar()
    calendar.add("prodid", value="Upcoming Movies Calendar")
    calendar.add("version", "2.0")
    calendar.add("x-wr-calname", calendar_name)

    for movie_event in movie_events:
        calendar.add_component(create_calendar_event_from_movie(movie_event))

    return calendar


DEFAULT_OUTPUT_FILENAME = str(DEFAULT_CONFIG["output_filename"])


def save_calendar_to_file(
    calendar: Calendar, output_filepath: str = DEFAULT_OUTPUT_FILENAME
) -> None:
    try:
        with open(output_filepath, "wb") as output_file:
            output_file.write(calendar.to_ical())
        logging.info("Calendar saved to %s", output_filepath)
    except IOError as error:
        logging.error("Error saving calendar to %s: %s", output_filepath, error)
        raise

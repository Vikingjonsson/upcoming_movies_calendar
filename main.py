from dataclasses import dataclass
from datetime import datetime, timedelta

from icalendar import Calendar, Event
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager


@dataclass
class ScheduledMovie:
    release_date: str
    uri: str


@dataclass
class CalendarEvent:
    summary: str
    date: str
    uri: str
    description: str


def scrape_imdb_upcoming_movies_by_region(region: str) -> list[CalendarEvent]:
    url = f"https://www.imdb.com/calendar/?ref_=rlm&region={region}&type=MOVIE"

    options = Options()
    options.add_argument("-headless")
    options.add_argument("--window-size=1440,1035")

    driver = webdriver.Firefox(
        service=FirefoxService(GeckoDriverManager().install()), options=options
    )
    driver.get(url=url)

    scheduled_movie_links: list[ScheduledMovie] = []

    calendar_sections = driver.find_elements(
        By.CSS_SELECTOR, '[data-testid="calendar-section"]'
    )

    for section in calendar_sections:
        release_date_elem = section.find_element(By.CLASS_NAME, "ipc-title__text")
        release_date = release_date_elem.text.strip()
        upcoming_movies = section.find_elements(
            By.CSS_SELECTOR, '[data-testid="coming-soon-entry"]'
        )

        for movie in upcoming_movies:
            title_elem = movie.find_element(
                By.CLASS_NAME, "ipc-metadata-list-summary-item__t"
            )
            href = title_elem.get_attribute("href")
            if href and release_date:
                scheduled_movie_links.append(
                    ScheduledMovie(
                        release_date=release_date,
                        uri=href.strip(),
                    )
                )

    scraped_movies: list[CalendarEvent] = []

    for movie_link in scheduled_movie_links:
        driver.get(movie_link.uri)
        hero_elem = driver.find_element(
            By.CSS_SELECTOR, '[data-testid="hero__primary-text"]'
        )
        plot_elem = driver.find_element(By.CSS_SELECTOR, '[data-testid="plot-xl"]')

        summary = hero_elem.text.strip()
        description = plot_elem.text.strip()

        scraped_movies.append(
            CalendarEvent(
                summary=summary,
                date=movie_link.release_date,
                uri=movie_link.uri,
                description=description,
            )
        )

    driver.quit()
    return scraped_movies


def create_ical_object(
    scheduled_events: list[CalendarEvent], calendar_name="Upcoming Movies"
):
    """Create an iOS iCalendar"""
    calendar = Calendar()
    calendar.add("prodid", value="Upcoming Movies Calendar")
    calendar.add("version", "2.0")
    calendar.add("x-wr-calname", calendar_name)

    for event_data in scheduled_events:
        start_date = datetime.strptime(event_data.date, "%b %d, %Y").date()
        end_date = start_date + timedelta(days=1)

        event = Event()
        event.add("dtstart", start_date)
        event.add("dtend", end_date)
        event.add("summary", event_data.summary)
        event.add("description", event_data.description)
        event.add("url", event_data.uri)

        calendar.add_component(event)

    return calendar


if __name__ == "__main__":
    movies = scrape_imdb_upcoming_movies_by_region("SE")
    calendar = create_ical_object(movies, calendar_name="Upcoming Movies in Sweden")

    with open("upcoming_movies.ics", "wb") as f:
        f.write(calendar.to_ical())

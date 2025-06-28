import argparse
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Generator

from icalendar import Calendar, Event
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


@contextmanager
def get_webdriver() -> Generator[webdriver.Firefox, None, None]:
    """Context manager for WebDriver to ensure proper cleanup."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1440,1035")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        driver = webdriver.Firefox(
            service=FirefoxService(GeckoDriverManager().install()), options=options
        )
        yield driver
    finally:
        if driver:
            driver.quit()


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
    """Scrape upcoming movies from IMDB for a specific region."""
    url = f"https://www.imdb.com/calendar/?ref_=rlm&region={region}&type=MOVIE"
    logging.info(f"Scraping upcoming movies for region: {region}")

    with get_webdriver() as driver:
        try:
            driver.get(url)
            logging.info(f"Loaded IMDB calendar page for region {region}")

            scheduled_movie_links: list[ScheduledMovie] = []

            calendar_sections = driver.find_elements(
                By.CSS_SELECTOR, '[data-testid="calendar-section"]'
            )

            if not calendar_sections:
                logging.warning("No calendar sections found on the page")
                return []

            logging.info(f"Found {len(calendar_sections)} calendar sections")

            for section in calendar_sections:
                try:
                    release_date_elem = section.find_element(
                        By.CLASS_NAME, "ipc-title__text"
                    )
                    release_date = release_date_elem.text.strip()

                    upcoming_movies = section.find_elements(
                        By.CSS_SELECTOR, '[data-testid="coming-soon-entry"]'
                    )

                    for movie in upcoming_movies:
                        try:
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
                        except NoSuchElementException:
                            logging.warning("Could not find movie title element")
                            continue

                except NoSuchElementException:
                    logging.warning("Could not find release date element")
                    continue

            logging.info(f"Found {len(scheduled_movie_links)} movies")

            scraped_movies: list[CalendarEvent] = []

            for i, movie_link in enumerate(scheduled_movie_links, 1):
                try:
                    logging.info(
                        f"Scraping movie {i}/{len(scheduled_movie_links)}: {movie_link.uri}"
                    )
                    driver.get(movie_link.uri)

                    try:
                        hero_elem = driver.find_element(
                            By.CSS_SELECTOR, '[data-testid="hero__primary-text"]'
                        )
                        summary = hero_elem.text.strip()
                    except NoSuchElementException:
                        logging.warning(
                            f"Could not find title for movie: {movie_link.uri}"
                        )
                        summary = "Unknown Title"

                    try:
                        plot_elem = driver.find_element(
                            By.CSS_SELECTOR, '[data-testid="plot-xl"]'
                        )
                        description = plot_elem.text.strip()
                    except NoSuchElementException:
                        logging.warning(
                            f"Could not find plot for movie: {movie_link.uri}"
                        )
                        description = "No description available"

                    scraped_movies.append(
                        CalendarEvent(
                            summary=summary,
                            date=movie_link.release_date,
                            uri=movie_link.uri,
                            description=description,
                        )
                    )

                except WebDriverException as e:
                    logging.error(f"Error scraping movie {movie_link.uri}: {e}")
                    continue

            logging.info(f"Successfully scraped {len(scraped_movies)} movies")
            return scraped_movies

        except WebDriverException as e:
            logging.error(f"WebDriver error: {e}")
            return []


def create_ical_object(
    scheduled_events: list[CalendarEvent], calendar_name: str = "Upcoming Movies"
) -> Calendar:
    """Create an iCalendar object from scheduled events."""
    if not scheduled_events:
        logging.warning("No events provided for calendar creation")

    logging.info(
        f"Creating calendar '{calendar_name}' with {len(scheduled_events)} events"
    )

    calendar = Calendar()
    calendar.add("prodid", value="Upcoming Movies Calendar")
    calendar.add("version", "2.0")
    calendar.add("x-wr-calname", calendar_name)

    for event_data in scheduled_events:
        try:
            start_date = datetime.strptime(event_data.date, "%b %d, %Y").date()
            end_date = start_date + timedelta(days=1)

            event = Event()
            event.add("dtstart", start_date)
            event.add("dtend", end_date)
            event.add("summary", event_data.summary)
            event.add("description", event_data.description)
            event.add("url", event_data.uri)

            calendar.add_component(event)
        except ValueError as e:
            logging.error(
                f"Error parsing date '{event_data.date}' for event '{event_data.summary}': {e}"
            )
            continue

    return calendar


def save_calendar_to_file(
    calendar: Calendar, filename: str = "upcoming_movies.ics"
) -> None:
    """Save calendar to file with error handling."""
    try:
        with open(filename, "wb") as f:
            f.write(calendar.to_ical())
        logging.info(f"Calendar saved to {filename}")
    except IOError as e:
        logging.error(f"Error saving calendar to {filename}: {e}")
        raise


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape upcoming movies from IMDB and create an iCalendar file"
    )
    parser.add_argument(
        "--region", default="SE", help="IMDB region code (default: SE for Sweden)"
    )
    parser.add_argument(
        "--output",
        default="upcoming_movies.ics",
        help="Output filename for the iCalendar file (default: upcoming_movies.ics)",
    )
    parser.add_argument(
        "--calendar-name",
        default="Upcoming Movies",
        help="Name for the calendar (default: Upcoming Movies)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    return parser.parse_args()


def main() -> None:
    """Main function to scrape movies and create calendar."""
    args = parse_arguments()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        logging.info("Starting movie scraping process")
        movies = scrape_imdb_upcoming_movies_by_region(args.region)

        if not movies:
            logging.warning("No movies found, calendar will be empty")

        calendar = create_ical_object(movies, calendar_name=args.calendar_name)
        save_calendar_to_file(calendar, args.output)

        logging.info(
            f"Process completed successfully. Created calendar with {len(movies)} movies."
        )

    except Exception as e:
        logging.error(f"An error occurred during execution: {e}")
        raise


if __name__ == "__main__":
    main()

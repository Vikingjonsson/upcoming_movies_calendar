import argparse
import hashlib
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Generator, Optional

from icalendar import Calendar, Event, vUri
from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        WebDriverException)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from config import DEFAULT_CONFIG

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

IMDB_CALENDAR_URL_TEMPLATE = (
    "https://www.imdb.com/calendar/?ref_=rlm&region={region}&type=MOVIE"
)
IMDB_DATE_FORMAT = "%b %d, %Y"

PAGE_LOAD_TIMEOUT_SECONDS = 30
ELEMENT_WAIT_TIMEOUT_SECONDS = float(str(DEFAULT_CONFIG["timeout"]))

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
BROWSER_WINDOW_SIZE = str(DEFAULT_CONFIG["window_size"])

CALENDAR_SECTION_SELECTOR = '[data-testid="calendar-section"]'
MOVIE_ENTRY_SELECTOR = '[data-testid="coming-soon-entry"]'
MOVIE_TITLE_CLASS_NAME = "ipc-metadata-list-summary-item__t"
RELEASE_DATE_CLASS_NAME = "ipc-title__text"
PLOT_SELECTOR = '[data-testid="plot-xl"]'
POSTER_IMAGE_SELECTOR = '[data-testid="hero-media__poster"] img'

EVENT_UID_DOMAIN = "@upcoming-movies"
EVENT_UID_HASH_LENGTH = 16

DEFAULT_REGION = str(DEFAULT_CONFIG["region"])
DEFAULT_OUTPUT_FILENAME = str(DEFAULT_CONFIG["output_filename"])
DEFAULT_CALENDAR_NAME = str(DEFAULT_CONFIG["calendar_name"])
DEFAULT_DESCRIPTION = "No description available"


@dataclass
class ScheduledMovie:
    title: str
    release_date_text: str
    imdb_url: str


@dataclass
class MovieCalendarEvent:
    title: str
    release_date: date
    imdb_url: str
    plot_description: str
    poster_image_url: Optional[str] = None


def parse_imdb_release_date(date_text: str) -> date:
    return datetime.strptime(date_text, IMDB_DATE_FORMAT).date()


def generate_calendar_event_uid(imdb_url: str, release_date: date) -> str:
    raw_identifier = f"{imdb_url}:{release_date.isoformat()}"
    hash_prefix = hashlib.sha256(raw_identifier.encode()).hexdigest()[
        :EVENT_UID_HASH_LENGTH
    ]
    return f"{hash_prefix}{EVENT_UID_DOMAIN}"


def _build_chrome_options() -> Options:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size={BROWSER_WINDOW_SIZE}")
    chrome_options.add_argument(f"--user-agent={BROWSER_USER_AGENT}")

    # ⚡ Bolt: Optimize page load times by using eager strategy (don't wait for all resources)
    chrome_options.page_load_strategy = "eager"
    # ⚡ Bolt: Disable image loading to significantly reduce bandwidth and load time
    chrome_options.add_experimental_option(
        "prefs", {"profile.managed_default_content_settings.images": 2}
    )

    return chrome_options


@contextmanager
def create_headless_chrome_driver() -> Generator[webdriver.Chrome, None, None]:
    chrome_driver = None
    try:
        chrome_service = ChromeService(ChromeDriverManager().install())
        chrome_driver = webdriver.Chrome(
            service=chrome_service, options=_build_chrome_options()
        )
        chrome_driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
        yield chrome_driver
    finally:
        if chrome_driver:
            chrome_driver.quit()


def collect_movie_links_from_calendar_page(
    driver: webdriver.Chrome,
) -> list[ScheduledMovie]:
    element_wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT_SECONDS)
    # Wait until calendar sections are present
    element_wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, CALENDAR_SECTION_SELECTOR)
        )
    )

    # ⚡ Bolt: Use execute_script for bulk data extraction to avoid multiple slow IPC round-trips
    # when calling find_element, get_attribute, and text from Python.
    script = """
    const sections = document.querySelectorAll(arguments[0]);
    const results = [];

    for (const section of sections) {
        const dateEl = section.querySelector('.' + arguments[1]);
        if (!dateEl) continue;
        const releaseDateText = dateEl.textContent.trim();

        const entries = section.querySelectorAll(arguments[2]);
        for (const entry of entries) {
            const titleEl = entry.querySelector('.' + arguments[3]);
            if (!titleEl) {
                console.warn("Could not find movie title element");
                continue;
            }

            const movieUrl = titleEl.href;
            const movieTitle = titleEl.textContent.trim();

            if (movieUrl && releaseDateText && movieTitle) {
                results.push({
                    title: movieTitle,
                    release_date_text: releaseDateText,
                    imdb_url: movieUrl.trim()
                });
            }
        }
    }
    return results;
    """

    raw_movies = driver.execute_script(
        script,
        CALENDAR_SECTION_SELECTOR,
        RELEASE_DATE_CLASS_NAME,
        MOVIE_ENTRY_SELECTOR,
        MOVIE_TITLE_CLASS_NAME,
    )

    movie_links = [
        ScheduledMovie(
            title=movie["title"],
            release_date_text=movie["release_date_text"],
            imdb_url=movie["imdb_url"],
        )
        for movie in raw_movies
    ]

    logging.info("Found %d movies on calendar page", len(movie_links))
    return movie_links


def _scrape_plot_description(driver: webdriver.Chrome, movie_title: str) -> str:
    try:
        element_wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT_SECONDS)
        plot_element = element_wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, PLOT_SELECTOR))
        )
        return plot_element.text.strip()
    except WebDriverException:
        logging.warning("Could not fetch description for '%s'", movie_title)
        return DEFAULT_DESCRIPTION


def _scrape_poster_image_url(
    driver: webdriver.Chrome, movie_title: str
) -> Optional[str]:
    try:
        poster_element = driver.find_element(By.CSS_SELECTOR, POSTER_IMAGE_SELECTOR)
        return poster_element.get_attribute("src")
    except NoSuchElementException:
        logging.warning("Could not find poster for '%s'", movie_title)
        return None


def scrape_movie_detail_page(
    driver: webdriver.Chrome, movie: ScheduledMovie, parsed_release_date: date
) -> MovieCalendarEvent:
    plot_description = DEFAULT_DESCRIPTION
    poster_image_url = None

    try:
        driver.get(movie.imdb_url)
        plot_description = _scrape_plot_description(driver, movie.title)
        poster_image_url = _scrape_poster_image_url(driver, movie.title)
    except WebDriverException:
        logging.warning("Could not load detail page for '%s'", movie.title)

    return MovieCalendarEvent(
        title=movie.title,
        release_date=parsed_release_date,
        imdb_url=movie.imdb_url,
        plot_description=plot_description,
        poster_image_url=poster_image_url,
    )


def _scrape_all_movie_details(
    chrome_driver: webdriver.Chrome, movie_links: list[ScheduledMovie]
) -> list[MovieCalendarEvent]:
    scraped_movie_events: list[MovieCalendarEvent] = []

    for movie_index, scheduled_movie in enumerate(movie_links, 1):
        try:
            # ⚡ Bolt: Cache parsed date to avoid redundant calculation in scrape_movie_detail_page
            parsed_date = parse_imdb_release_date(scheduled_movie.release_date_text)
        except ValueError:
            logging.error(
                "Could not parse date '%s' for movie '%s', skipping",
                scheduled_movie.release_date_text,
                scheduled_movie.title,
            )
            continue

        logging.debug(
            "Scraping details for movie %d/%d: %s",
            movie_index,
            len(movie_links),
            scheduled_movie.title,
        )
        scraped_movie_events.append(
            scrape_movie_detail_page(chrome_driver, scheduled_movie, parsed_date)
        )

    return scraped_movie_events


def scrape_upcoming_movies_from_imdb(region: str) -> list[MovieCalendarEvent]:
    calendar_url = IMDB_CALENDAR_URL_TEMPLATE.format(region=region)
    logging.info("Scraping upcoming movies for region: %s", region)

    with create_headless_chrome_driver() as chrome_driver:
        try:
            chrome_driver.get(calendar_url)
            logging.debug("Loaded IMDB calendar page for region %s", region)

            movie_links = collect_movie_links_from_calendar_page(chrome_driver)
            scraped_movie_events = _scrape_all_movie_details(chrome_driver, movie_links)

            logging.info("Successfully scraped %d movies", len(scraped_movie_events))
            return scraped_movie_events

        except WebDriverException as error:
            logging.error("WebDriver error: %s", error)
            return []


def _create_calendar_event_from_movie(movie_event: MovieCalendarEvent) -> Event:
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
        calendar.add_component(_create_calendar_event_from_movie(movie_event))

    return calendar


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


def parse_command_line_arguments() -> argparse.Namespace:
    argument_parser = argparse.ArgumentParser(
        description="Scrape upcoming movies from IMDB and create an iCalendar file"
    )
    argument_parser.add_argument(
        "--region",
        default=DEFAULT_REGION,
        help="IMDB region code (default: SE for Sweden)",
    )
    argument_parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT_FILENAME,
        help="Output filename for the iCalendar file (default: upcoming_movies.ics)",
    )
    argument_parser.add_argument(
        "--calendar-name",
        default=DEFAULT_CALENDAR_NAME,
        help="Name for the calendar (default: Upcoming Movies)",
    )
    argument_parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )
    return argument_parser.parse_args()


def main() -> None:
    arguments = parse_command_line_arguments()

    if arguments.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logging.info("Starting movie scraping process")
    movie_events = scrape_upcoming_movies_from_imdb(arguments.region)

    if not movie_events:
        logging.warning("No movies found. Skipping calendar file creation.")
        return

    calendar = build_icalendar_from_movie_events(
        movie_events, calendar_name=arguments.calendar_name
    )
    save_calendar_to_file(calendar, arguments.output)

    logging.info(
        "Process completed. Created calendar with %d movies.", len(movie_events)
    )


if __name__ == "__main__":
    main()

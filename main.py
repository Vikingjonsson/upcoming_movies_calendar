import argparse
import hashlib
import logging
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Generator, Optional

from icalendar import Calendar, Event, vUri
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

IMDB_CALENDAR_URL_TEMPLATE = (
    "https://www.imdb.com/calendar/?ref_=rlm&region={region}&type=MOVIE"
)
IMDB_DATE_FORMAT = "%b %d, %Y"

PAGE_LOAD_TIMEOUT_SECONDS = 30
ELEMENT_WAIT_TIMEOUT_SECONDS = 10

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
BROWSER_WINDOW_SIZE = "1440,900"

CALENDAR_SECTION_SELECTOR = '[data-testid="calendar-section"]'
MOVIE_ENTRY_SELECTOR = '[data-testid="coming-soon-entry"]'
MOVIE_TITLE_CLASS_NAME = "ipc-metadata-list-summary-item__t"
RELEASE_DATE_CLASS_NAME = "ipc-title__text"
PLOT_SELECTOR = '[data-testid="plot-xl"]'
POSTER_IMAGE_SELECTOR = '[data-testid="hero-media__poster"] img'

EVENT_UID_DOMAIN = "@upcoming-movies"
EVENT_UID_HASH_LENGTH = 16

DEFAULT_REGION = "SE"
DEFAULT_OUTPUT_FILENAME = "upcoming_movies.ics"
DEFAULT_CALENDAR_NAME = "Upcoming Movies"
DEFAULT_DESCRIPTION = "No description available"


@contextmanager
def create_headless_chrome_driver() -> Generator[webdriver.Chrome, None, None]:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size={BROWSER_WINDOW_SIZE}")
    chrome_options.add_argument(f"--user-agent={BROWSER_USER_AGENT}")

    chrome_driver = None
    try:
        chrome_service = ChromeService(ChromeDriverManager().install())
        chrome_driver = webdriver.Chrome(
            service=chrome_service, options=chrome_options
        )
        chrome_driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
        yield chrome_driver
    finally:
        if chrome_driver:
            chrome_driver.quit()


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


def collect_movie_links_from_calendar_page(
    driver: webdriver.Chrome,
) -> list[ScheduledMovie]:
    element_wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT_SECONDS)
    calendar_sections = element_wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, CALENDAR_SECTION_SELECTOR)
        )
    )

    logging.info("Found %d calendar sections", len(calendar_sections))

    movie_links: list[ScheduledMovie] = []

    for section in calendar_sections:
        try:
            release_date_element = section.find_element(
                By.CLASS_NAME, RELEASE_DATE_CLASS_NAME
            )
            release_date_text = release_date_element.text.strip()

            movie_entries = section.find_elements(
                By.CSS_SELECTOR, MOVIE_ENTRY_SELECTOR
            )

            for movie_entry in movie_entries:
                try:
                    title_element = movie_entry.find_element(
                        By.CLASS_NAME, MOVIE_TITLE_CLASS_NAME
                    )
                    movie_url = title_element.get_attribute("href")
                    movie_title = title_element.text.strip()
                    if movie_url and release_date_text and movie_title:
                        movie_links.append(
                            ScheduledMovie(
                                title=movie_title,
                                release_date_text=release_date_text,
                                imdb_url=movie_url.strip(),
                            )
                        )
                except NoSuchElementException:
                    logging.warning("Could not find movie title element")

        except NoSuchElementException:
            logging.warning("Could not find release date element in section")

    logging.info("Found %d movies on calendar page", len(movie_links))
    return movie_links


def scrape_movie_detail_page(
    driver: webdriver.Chrome, movie: ScheduledMovie
) -> MovieCalendarEvent:
    parsed_release_date = parse_imdb_release_date(movie.release_date_text)
    plot_description = DEFAULT_DESCRIPTION
    poster_image_url = None

    try:
        driver.get(movie.imdb_url)

        try:
            element_wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT_SECONDS)
            plot_element = element_wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, PLOT_SELECTOR)
                )
            )
            plot_description = plot_element.text.strip()
        except WebDriverException:
            logging.warning("Could not fetch description for '%s'", movie.title)

        try:
            poster_element = driver.find_element(
                By.CSS_SELECTOR, POSTER_IMAGE_SELECTOR
            )
            poster_image_url = poster_element.get_attribute("src")
        except NoSuchElementException:
            logging.warning("Could not find poster for '%s'", movie.title)

    except WebDriverException:
        logging.warning("Could not load detail page for '%s'", movie.title)

    return MovieCalendarEvent(
        title=movie.title,
        release_date=parsed_release_date,
        imdb_url=movie.imdb_url,
        plot_description=plot_description,
        poster_image_url=poster_image_url,
    )


def scrape_upcoming_movies_from_imdb(region: str) -> list[MovieCalendarEvent]:
    calendar_url = IMDB_CALENDAR_URL_TEMPLATE.format(region=region)
    logging.info("Scraping upcoming movies for region: %s", region)

    with create_headless_chrome_driver() as chrome_driver:
        try:
            chrome_driver.get(calendar_url)
            logging.debug("Loaded IMDB calendar page for region %s", region)

            movie_links = collect_movie_links_from_calendar_page(chrome_driver)

            scraped_movie_events: list[MovieCalendarEvent] = []

            for movie_index, scheduled_movie in enumerate(movie_links, 1):
                try:
                    parsed_release_date = parse_imdb_release_date(
                        scheduled_movie.release_date_text
                    )
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

                movie_event = scrape_movie_detail_page(
                    chrome_driver, scheduled_movie
                )
                scraped_movie_events.append(movie_event)

            logging.info(
                "Successfully scraped %d movies", len(scraped_movie_events)
            )
            return scraped_movie_events

        except WebDriverException as error:
            logging.error("WebDriver error: %s", error)
            return []


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
        day_after_release = movie_event.release_date + timedelta(days=1)

        calendar_event = Event()
        calendar_event.add(
            "uid",
            generate_calendar_event_uid(
                movie_event.imdb_url, movie_event.release_date
            ),
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

        calendar.add_component(calendar_event)

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

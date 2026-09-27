import argparse
import logging
from contextlib import contextmanager
from datetime import date
from typing import Generator

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from calendar_builder import (
    DEFAULT_CALENDAR_NAME,
    DEFAULT_OUTPUT_FILENAME,
    build_icalendar_from_movie_events,
    create_calendar_event_from_movie as _create_calendar_event_from_movie,
    generate_calendar_event_uid,
    save_calendar_to_file,
)
from config import DEFAULT_CONFIG
from date_utils import parse_imdb_release_date
from models import MovieCalendarEvent, ScheduledMovie

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Re-exports for backward compatibility
__all__ = [
    "DEFAULT_CALENDAR_NAME",
    "DEFAULT_OUTPUT_FILENAME",
    "DEFAULT_REGION",
    "MovieCalendarEvent",
    "ScheduledMovie",
    "_create_calendar_event_from_movie",
    "build_icalendar_from_movie_events",
    "generate_calendar_event_uid",
    "parse_imdb_release_date",
    "save_calendar_to_file",
]

# --- Chrome Driver Setup ---

PAGE_LOAD_TIMEOUT_SECONDS = 30
BROWSER_WINDOW_SIZE = str(DEFAULT_CONFIG["window_size"])
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def _build_chrome_options() -> Options:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(f"--window-size={BROWSER_WINDOW_SIZE}")
    chrome_options.add_argument(f"--user-agent={BROWSER_USER_AGENT}")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation"]
    )
    chrome_options.add_experimental_option("useAutomationExtension", False)

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


# --- Scraping Logic ---

ELEMENT_WAIT_TIMEOUT_SECONDS = float(str(DEFAULT_CONFIG["timeout"]))

CALENDAR_SECTION_SELECTOR = '[data-testid="calendar-section"]'
MOVIE_ENTRY_SELECTOR = '[data-testid="coming-soon-entry"]'
MOVIE_TITLE_CLASS_NAME = "ipc-metadata-list-summary-item__t"
RELEASE_DATE_CLASS_NAME = "ipc-title__text"


def collect_movie_links_from_calendar_page(
    driver: webdriver.Chrome,
) -> list[ScheduledMovie]:
    element_wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT_SECONDS)
    element_wait.until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, CALENDAR_SECTION_SELECTOR)
        )
    )

    # ⚡ Bolt: Bulk fetch movie links via JavaScript to eliminate massive IPC overhead
    # from multiple synchronous find_element and .text calls.
    js_script = """
    const sections = document.querySelectorAll(arguments[0]);
    const results = [];
    for (const section of sections) {
        const dateEl = section.querySelector('.' + arguments[1]);
        if (!dateEl) continue;
        const dateText = dateEl.innerText.trim();

        const entries = section.querySelectorAll(arguments[2]);
        for (const entry of entries) {
            const titleEl = entry.querySelector('.' + arguments[3]);
            if (titleEl && titleEl.href) {
                const titleText = titleEl.innerText.trim();
                if (titleText && dateText) {
                    results.push({
                        title: titleText,
                        release_date_text: dateText,
                        imdb_url: titleEl.href.trim()
                    });
                }
            }
        }
    }
    return results;
    """

    movie_data = driver.execute_script(
        js_script,
        CALENDAR_SECTION_SELECTOR,
        RELEASE_DATE_CLASS_NAME,
        MOVIE_ENTRY_SELECTOR,
        MOVIE_TITLE_CLASS_NAME,
    )

    movie_links = [
        ScheduledMovie(
            title=data["title"],
            release_date_text=data["release_date_text"],
            imdb_url=data["imdb_url"],
        )
        for data in movie_data
    ]

    logging.info("Found %d movies on calendar page", len(movie_links))
    return movie_links


DEFAULT_DESCRIPTION = "No description available"
PLOT_SELECTOR = '[data-testid="plot-xl"]'
POSTER_IMAGE_SELECTOR = '[data-testid="hero-media__poster"] img'


def scrape_movie_detail_page(
    driver: webdriver.Chrome, movie: ScheduledMovie, parsed_release_date: date
) -> MovieCalendarEvent:
    plot_description = DEFAULT_DESCRIPTION
    poster_image_url = None

    try:
        driver.get(movie.imdb_url)

        try:
            element_wait = WebDriverWait(driver, ELEMENT_WAIT_TIMEOUT_SECONDS)
            element_wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, PLOT_SELECTOR))
            )
        except WebDriverException:
            # We still execute the JS block to preserve independent fallback mechanisms
            # (e.g., extracting the poster even if the plot times out)
            pass

        # ⚡ Bolt: Fetch detail page data in bulk via JavaScript to minimize IPC roundtrips
        js_script = """
        const plotEl = document.querySelector(arguments[0]);
        const posterEl = document.querySelector(arguments[1]);
        return {
            plot: plotEl ? plotEl.innerText.trim() : null,
            poster: posterEl ? posterEl.src : null
        };
        """
        details = driver.execute_script(js_script, PLOT_SELECTOR, POSTER_IMAGE_SELECTOR)

        plot_description = details.get("plot") or DEFAULT_DESCRIPTION
        poster_image_url = details.get("poster") or None

        if plot_description == DEFAULT_DESCRIPTION:
            logging.warning("Could not fetch description for '%s'", movie.title)
        if not poster_image_url:
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


IMDB_CALENDAR_URL_TEMPLATE = (
    "https://www.imdb.com/calendar/?ref_=rlm&region={region}&type=MOVIE"
)


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


# --- CLI and Execution ---

DEFAULT_REGION = str(DEFAULT_CONFIG["region"])


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

from __future__ import annotations

import logging
from datetime import date
from typing import TypedDict, cast

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from upcoming_movies.config import DEFAULT_CONFIG
from upcoming_movies.models import MovieCalendarEvent, ScheduledMovie
from upcoming_movies.scraping.browser import create_headless_chrome_driver
from upcoming_movies.utils.date_utils import parse_imdb_release_date

ELEMENT_WAIT_TIMEOUT_SECONDS: float = DEFAULT_CONFIG["timeout"]

CALENDAR_SECTION_SELECTOR = '[data-testid="calendar-section"]'
MOVIE_ENTRY_SELECTOR = '[data-testid="coming-soon-entry"]'
MOVIE_TITLE_CLASS_NAME = "ipc-metadata-list-summary-item__t"
RELEASE_DATE_CLASS_NAME = "ipc-title__text"


class RawMoviePayload(TypedDict):
    title: str
    release_date_text: str
    imdb_url: str


class RawDetailPayload(TypedDict):
    plot: str | None
    poster: str | None


def parse_scheduled_movie_records(
    raw_records: list[RawMoviePayload],
) -> list[ScheduledMovie]:
    """Pure logic parsing raw DOM dicts into ScheduledMovie instances."""
    return [
        ScheduledMovie(
            title=data["title"],
            release_date_text=data["release_date_text"],
            imdb_url=data["imdb_url"],
        )
        for data in raw_records
    ]


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

    raw_data = cast(
        list[RawMoviePayload],
        driver.execute_script(
            js_script,
            CALENDAR_SECTION_SELECTOR,
            RELEASE_DATE_CLASS_NAME,
            MOVIE_ENTRY_SELECTOR,
            MOVIE_TITLE_CLASS_NAME,
        ),
    )

    movie_links = parse_scheduled_movie_records(raw_data)
    logging.info("Found %d movies on calendar page", len(movie_links))
    return movie_links


DEFAULT_DESCRIPTION = "No description available"
PLOT_SELECTOR = '[data-testid="plot-xl"]'
POSTER_IMAGE_SELECTOR = '[data-testid="hero-media__poster"] img'


def scrape_movie_detail_page(
    driver: webdriver.Chrome, movie: ScheduledMovie, parsed_release_date: date
) -> MovieCalendarEvent:
    plot_description = DEFAULT_DESCRIPTION
    poster_image_url: str | None = None

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
        details = cast(
            RawDetailPayload,
            driver.execute_script(
                js_script, PLOT_SELECTOR, POSTER_IMAGE_SELECTOR
            ),
        )

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
    movie_cache: dict[str, tuple[str, str | None]] = {}

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

        base_url = scheduled_movie.imdb_url.split("?")[0]
        if base_url in movie_cache:
            logging.debug(
                "Using cached details for movie %d/%d: %s",
                movie_index,
                len(movie_links),
                scheduled_movie.title,
            )
            plot_description, poster_image_url = movie_cache[base_url]
            scraped_movie_events.append(
                MovieCalendarEvent(
                    title=scheduled_movie.title,
                    release_date=parsed_date,
                    imdb_url=scheduled_movie.imdb_url,
                    plot_description=plot_description,
                    poster_image_url=poster_image_url,
                )
            )
        else:
            logging.debug(
                "Scraping details for movie %d/%d: %s",
                movie_index,
                len(movie_links),
                scheduled_movie.title,
            )
            event = scrape_movie_detail_page(
                chrome_driver, scheduled_movie, parsed_date
            )
            scraped_movie_events.append(event)
            movie_cache[base_url] = (event.plot_description, event.poster_image_url)

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

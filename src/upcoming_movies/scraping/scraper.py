from __future__ import annotations

import logging
from datetime import date
from typing import Any, TypedDict, cast

from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from upcoming_movies.config import DEFAULT_CONFIG
from upcoming_movies.models import MovieCalendarEvent, ScheduledMovie
from upcoming_movies.scraping.browser import create_headless_chrome_driver
from upcoming_movies.scraping.scraper_utils import (
    parse_flexible_release_date,
    parse_imdb_release_date,
)

logger = logging.getLogger(__name__)

ELEMENT_WAIT_TIMEOUT_SECONDS: float = DEFAULT_CONFIG["timeout"]

CALENDAR_SECTION_SELECTOR = '[data-testid="calendar-section"]'
MOVIE_ENTRY_SELECTOR = '[data-testid="coming-soon-entry"]'
MOVIE_TITLE_CLASS_NAME = "ipc-metadata-list-summary-item__t"
RELEASE_DATE_CLASS_NAME = "ipc-title__text"


class RawMoviePayload(TypedDict):
    title: str
    release_date_text: str
    imdb_url: str


class RawDetailPayload(TypedDict, total=False):
    plot: str | None
    poster: str | None
    genres: list[str]


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
    logger.info("Found %d movies on calendar page", len(movie_links))
    return movie_links


DEFAULT_DESCRIPTION = "No description available"
PLOT_SELECTOR = '[data-testid="plot-xl"]'
POSTER_IMAGE_SELECTOR = '[data-testid="hero-media__poster"] img'
GENRES_SELECTOR = '[data-testid="genres"] a, a.ipc-chip--on-base'


def scrape_movie_detail_page(
    driver: webdriver.Chrome, movie: ScheduledMovie, parsed_release_date: date
) -> MovieCalendarEvent:
    plot_description = DEFAULT_DESCRIPTION
    poster_image_url: str | None = None
    genres: list[str] = []

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

        # ⚡ Bolt: Fetch detail page data in bulk via JavaScript to minimize
        # IPC roundtrips
        js_script = """
        const plotEl = document.querySelector(arguments[0]);
        const posterEl = document.querySelector(arguments[1]);
        const genreEls = document.querySelectorAll(arguments[2]);
        const genres = Array.from(genreEls)
            .map(el => el.innerText.trim()).filter(Boolean);
        return {
            plot: plotEl ? plotEl.innerText.trim() : null,
            poster: posterEl ? posterEl.src : null,
            genres: genres
        };
        """
        details = cast(
            RawDetailPayload,
            driver.execute_script(
                js_script, PLOT_SELECTOR, POSTER_IMAGE_SELECTOR, GENRES_SELECTOR
            ),
        )

        plot_description = details.get("plot") or DEFAULT_DESCRIPTION
        poster_image_url = details.get("poster") or None
        genres = details.get("genres") or []

        if plot_description == DEFAULT_DESCRIPTION:
            logger.warning("Could not fetch description for '%s'", movie.title)
        if not poster_image_url:
            logger.warning("Could not find poster for '%s'", movie.title)

    except WebDriverException:
        logger.warning("Could not load detail page for '%s'", movie.title)

    return MovieCalendarEvent(
        title=movie.title,
        release_date=parsed_release_date,
        imdb_url=movie.imdb_url,
        plot_description=plot_description,
        poster_image_url=poster_image_url,
        genres=genres,
    )


def _scrape_all_movie_details(
    chrome_driver: webdriver.Chrome, movie_links: list[ScheduledMovie]
) -> list[MovieCalendarEvent]:
    scraped_movie_events: list[MovieCalendarEvent] = []
    movie_cache: dict[str, tuple[str, str | None, list[str]]] = {}

    for movie_index, scheduled_movie in enumerate(movie_links, 1):
        try:
            # ⚡ Bolt: Cache parsed date to avoid redundant calculation
            # in scrape_movie_detail_page
            parsed_date = parse_imdb_release_date(scheduled_movie.release_date_text)
        except ValueError:
            logger.error(
                "Could not parse date '%s' for movie '%s', skipping",
                scheduled_movie.release_date_text,
                scheduled_movie.title,
            )
            continue

        base_url = scheduled_movie.imdb_url.split("?")[0]
        if base_url in movie_cache:
            logger.debug(
                "Using cached details for movie %d/%d: %s",
                movie_index,
                len(movie_links),
                scheduled_movie.title,
            )
            plot_description, poster_image_url, genres = movie_cache[base_url]
            scraped_movie_events.append(
                MovieCalendarEvent(
                    title=scheduled_movie.title,
                    release_date=parsed_date,
                    imdb_url=scheduled_movie.imdb_url,
                    plot_description=plot_description,
                    poster_image_url=poster_image_url,
                    genres=genres,
                )
            )
        else:
            logger.debug(
                "Scraping details for movie %d/%d: %s",
                movie_index,
                len(movie_links),
                scheduled_movie.title,
            )
            event = scrape_movie_detail_page(
                chrome_driver, scheduled_movie, parsed_date
            )
            scraped_movie_events.append(event)
            movie_cache[base_url] = (
                event.plot_description,
                event.poster_image_url,
                event.genres,
            )

    return scraped_movie_events


class NextDataMoviePayload(TypedDict, total=False):
    id: str
    title: str
    release_date_str: str
    genres: list[str]
    poster: str | None
    imdb_url: str
    plot: str | None


def _scrape_via_next_data(
    driver: webdriver.Chrome,
) -> list[MovieCalendarEvent] | None:
    """Fast-path scraper using IMDB's __NEXT_DATA__ and parallel plot fetching.

    Extracts upcoming movies with posters, genres, and exact dates in 1 page load,
    and batches plot queries in parallel inside the browser.
    Returns None if __NEXT_DATA__ is unavailable.
    """
    js_script = """
    const callback = arguments[arguments.length - 1];
    let nextData = null;
    try {
        const el = document.getElementById("__NEXT_DATA__");
        if (el && el.textContent) {
            nextData = JSON.parse(el.textContent);
        }
    } catch (e) {
        callback({ error: "Failed to parse __NEXT_DATA__" });
        return;
    }

    const pageProps = nextData && nextData.props && nextData.props.pageProps;
    if (!pageProps || !pageProps.groups) {
        callback({ error: "No groups found in __NEXT_DATA__" });
        return;
    }

    const groups = pageProps.groups;
    const movies = [];
    for (const g of groups) {
        for (const e of g.entries || []) {
            if (!e.id || !e.titleText) continue;
            movies.push({
                id: e.id,
                title: e.titleText,
                release_date_str: e.releaseDate || "",
                genres: e.genres || [],
                poster: e.imageModel ? e.imageModel.url : null,
                imdb_url: "https://www.imdb.com/title/" + e.id + "/"
            });
        }
    }

    if (movies.length === 0) {
        callback({ error: "No movies found in groups" });
        return;
    }

    // Parallel fetch plots for upcoming releases (up to first 50)
    const toFetch = movies.slice(0, 50);
    async function fetchPlots() {
        const results = {};
        const chunkSize = 25;
        for (let i = 0; i < toFetch.length; i += chunkSize) {
            const chunk = toFetch.slice(i, i + chunkSize);
            const chunkRes = await Promise.all(chunk.map(async m => {
                const controller = new AbortController();
                const timer = setTimeout(() => controller.abort(), 3500);
                try {
                    const r = await fetch(
                        "/title/" + m.id + "/", { signal: controller.signal }
                    );
                    clearTimeout(timer);
                    const html = await r.text();
                    const doc = new DOMParser().parseFromString(html, "text/html");
                    const el = doc.querySelector("[data-testid='plot-xl']");
                    return { id: m.id, plot: el ? el.innerText.trim() : null };
                } catch (e) {
                    clearTimeout(timer);
                    return { id: m.id, plot: null };
                }
            }));
            for (const item of chunkRes) {
                results[item.id] = item.plot;
            }
        }
        return results;
    }

    fetchPlots().then(plotMap => {
        for (const m of movies) {
            m.plot = plotMap[m.id] || "No description available";
        }
        callback({ movies: movies });
    }).catch(err => {
        callback({ movies: movies, warning: String(err) });
    });
    """

    try:
        raw_result = cast(
            "dict[str, Any] | None",
            driver.execute_async_script(js_script),
        )
    except WebDriverException as exc:
        logger.debug("execute_async_script failed for NEXT_DATA: %s", exc)
        return None

    if not raw_result or "error" in raw_result:
        logger.debug("NEXT_DATA extraction returned: %s", raw_result)
        return None

    raw_movies = cast("list[NextDataMoviePayload]", raw_result.get("movies", []))
    events: list[MovieCalendarEvent] = []

    for item in raw_movies:
        date_str = item.get("release_date_str")
        if not date_str:
            continue
        try:
            rel_date = parse_flexible_release_date(date_str)
        except Exception:
            logger.debug(
                "Could not parse date '%s' for '%s'",
                date_str,
                item.get("title"),
            )
            continue

        plot_text = item.get("plot") or DEFAULT_DESCRIPTION
        events.append(
            MovieCalendarEvent(
                title=item["title"],
                release_date=rel_date,
                imdb_url=item["imdb_url"],
                plot_description=plot_text,
                poster_image_url=item.get("poster"),
                genres=item.get("genres", []),
            )
        )

    logger.info("Extracted %d movies via NEXT_DATA fast path", len(events))
    return events if events else None


IMDB_CALENDAR_URL_TEMPLATE = (
    "https://www.imdb.com/calendar/?ref_=rlm&region={region}&type=MOVIE"
)


def scrape_upcoming_movies_from_imdb(region: str) -> list[MovieCalendarEvent]:
    calendar_url = IMDB_CALENDAR_URL_TEMPLATE.format(region=region)
    logger.info("Scraping upcoming movies for region: %s", region)

    with create_headless_chrome_driver() as chrome_driver:
        try:
            chrome_driver.set_script_timeout(30.0)
            chrome_driver.get(calendar_url)
            logger.debug("Loaded IMDB calendar page for region %s", region)

            # Wait until either __NEXT_DATA__ or calendar-section is present
            element_wait = WebDriverWait(chrome_driver, ELEMENT_WAIT_TIMEOUT_SECONDS)
            script_check = (
                "return !!document.getElementById('__NEXT_DATA__') || "
                "document.querySelectorAll("
                "'[data-testid=\"calendar-section\"]').length > 0"
            )
            element_wait.until(lambda d: d.execute_script(script_check))

            # 1. Try fast-path via embedded NEXT_DATA
            fast_events = _scrape_via_next_data(chrome_driver)
            if fast_events:
                logger.info(
                    "Successfully scraped %d movies via fast-path", len(fast_events)
                )
                return fast_events

            # 2. Fallback to DOM-based extraction
            logger.info("NEXT_DATA not available; falling back to DOM extraction")
            movie_links = collect_movie_links_from_calendar_page(chrome_driver)
            scraped_movie_events = _scrape_all_movie_details(chrome_driver, movie_links)

            logger.info(
                "Successfully scraped %d movies via fallback", len(scraped_movie_events)
            )
            return scraped_movie_events

        except WebDriverException as error:
            logger.error("WebDriver error: %s", error)
            return []

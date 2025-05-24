from datetime import timedelta, datetime
import requests
from icalendar import Event, Calendar

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager


class Movie:
    def __init__(self, title, release_date, link, description):
        self.title = title
        self.release_date = release_date
        self.link = link
        self.description = description

    def set_title(self, title):
        self.title = title

    def set_release_date(self, date):
        self.release_date = date

    def set_description(self, description):
        self.description = description


def scrape_imdb_upcoming_movies_by_region(region: str):
    URL = f"https://www.imdb.com/calendar/?ref_=rlm&region={region}&type=MOVIE"
    CALENDAR_SECTION = '[data-testid="calendar-section"]'
    UPCOMING_MOVIES = '[data-testid="coming-soon-entry"]'

    scraped_movies: list[Movie] = []

    options = Options()
    options.add_argument("-headless")

    driver = webdriver.Firefox(
        service=FirefoxService(GeckoDriverManager().install()), options=options
    )
    driver.get(url=URL)
    calendar_sections = driver.find_elements(By.CSS_SELECTOR, CALENDAR_SECTION)
    for calender_section in calendar_sections:
        release_date = calender_section.find_element(By.CLASS_NAME, "ipc-title__text")
        movies = calender_section.find_elements(By.CSS_SELECTOR, UPCOMING_MOVIES)

        for movie in movies:
            TITLE_CLASS = "ipc-metadata-list-summary-item__t"
            title = movie.find_element(By.CLASS_NAME, TITLE_CLASS)

            scraped_movies.append(
                Movie(
                    title=title.text,
                    release_date=release_date.text,
                    link=title.get_attribute("href"),
                    description="",
                )
            )

    driver.quit()
    return scraped_movies


def fetch_movie_data(movies):

    DESCRIPTION_SECTION = '[data-testid="plot-xl"]'
    TITLE = '[data-testid="hero__primary-text"]'

    options = Options()
    options.add_argument("-headless")
    options.add_argument("--window-size=1440,1035")

    driver = webdriver.Firefox(
        service=FirefoxService(GeckoDriverManager().install()), options=options
    )
    for movie in movies:
        driver.get(movie.link)
        title_elem = driver.find_element(By.CSS_SELECTOR, TITLE)
        description_elem = driver.find_element(By.CSS_SELECTOR, DESCRIPTION_SECTION)
        movie.set_title(title_elem.text)
        movie.set_description(description_elem.text)

        driver.quit()

    return movies


def create_ical_object(movies):
    """ "Create an iOS iCalendar"""
    cal = Calendar()
    cal.add("prodid", "-//Upcoming Movies Calendar//example.com//")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", "Upcoming movies")

    for movie in movies:
        event = Event()
        event.add("summary", movie.title)
        event.add("description", movie.description)
        start_date = datetime.strptime(movie.release_date, "%Y-%m-%dT%H:%M:%S")
        end_date = start_date + timedelta(hours=23, minutes=59, seconds=59)
        event.add("dtstart", start_date)
        event.add("dtend", end_date)
        cal.add_component(event)

    return cal


if __name__ == "__main__":
    movies = scrape_imdb_upcoming_movies_by_region("SE")
    updated_movies = fetch_movie_data(movies)
    calendar = create_ical_object(updated_movies)

    with open("upcoming_movies.ics", "wb") as f:
        f.write(calendar.to_ical())

from datetime import timedelta, datetime
import requests
from icalendar import Event, Calendar

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager


IMDB_URL = 'https://www.imdb.com/calendar/?ref_=rlm&region=SE&type=MOVIE'
CALENDAR_SECTION = '[data-testid="calendar-section"]'
MOVIE_LINK_CLASS = '.ipc-metadata-list-summary-item__t'
UPCOMING_MOVIES = '[data-testid="coming-soon-entry"]'


def scrape_imdb_upcoming_movies_by_region(region: str):
    options = Options()
    options.add_argument('-headless')
    driver = webdriver.Firefox(service=FirefoxService(
        GeckoDriverManager().install()), options=options)

    driver.get(url=IMDB_URL)
    calendar_sections = driver.find_elements(By.CSS_SELECTOR, CALENDAR_SECTION)
    for calender_section in calendar_sections:
        release_date = calender_section.find_element(
            By.CLASS_NAME, 'ipc-title__text')
        print(release_date.text)
        movies = calender_section.find_elements(
            By.CSS_SELECTOR, UPCOMING_MOVIES)
        for movie in movies:
            title = movie.find_element(
                By.CLASS_NAME, 'ipc-metadata-list-summary-item__t')
            print(title.text)

        # movie_links = calender_section.find_elements(By.CSS_SELECTOR, MOVIE_LINK_CLASS)
        # href = link.get_attribute("href"):

    return ''


def create_ical_object(movies):
    """"Create an iOS iCalendar"""
    cal = Calendar()
    cal.add('prodid', '-//Upcoming Movies Calendar//example.com//')
    cal.add('version', '2.0')
    cal.add('x-wr-calname', 'Upcoming movies')

    for movie in movies:
        original_title = movie.get("originalTitle")
        release_date = movie.get("releaseDate")
        description = movie.get("shortDescription")

        if original_title and release_date:
            event = Event()
            event.add('summary', original_title)
            event.add('description', description)
            start_date = datetime.strptime(release_date, '%Y-%m-%dT%H:%M:%S')
            end_date = start_date + timedelta(hours=23, minutes=59, seconds=59)
            event.add('dtstart', start_date)
            event.add('dtend', end_date)
            cal.add_component(event)

    return cal


if __name__ == "__main__":
    scrape_imdb_upcoming_movies_by_region('SE')
    # items = fetch_upcoming_movies(id)
    # calendar = create_ical_object(items)

    # with open('upcoming_movies.ics', 'wb') as f:
    #     f.write(calendar.to_ical())

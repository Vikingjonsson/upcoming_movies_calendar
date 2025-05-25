from datetime import timedelta, datetime
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


def scrape_imdb_upcoming_movies_by_region(region: str):
    URL = f"https://www.imdb.com/calendar/?ref_=rlm&region={region}&type=MOVIE"
    scraped_movies: list[Movie] = []

    options = Options()
    options.add_argument("-headless")
    options.add_argument("--window-size=1440,1035")

    driver = webdriver.Firefox(
        service=FirefoxService(GeckoDriverManager().install()), options=options
    )
    driver.get(url=URL)

    calendar_sections = driver.find_elements(
        By.CSS_SELECTOR, '[data-testid="calendar-section"]'
    )

    movies_data = []

    for calender_section in calendar_sections:
        release_date_element = calender_section.find_element(
            By.CLASS_NAME, "ipc-title__text"
        )
        release_date = release_date_element.text.strip()
        upcoming_movies = calender_section.find_elements(
            By.CSS_SELECTOR, '[data-testid="coming-soon-entry"]'
        )
        for movie in upcoming_movies:

            title_element = movie.find_element(
                By.CLASS_NAME, "ipc-metadata-list-summary-item__t"
            )
            href_attribute = title_element.get_attribute("href")

            if href_attribute and release_date:
                movies_data.append(
                    {
                        "link": href_attribute.strip(),
                        "release_date": release_date.strip(),
                    }
                )

    # Visit each movie's detail page to scrape additional information
    for movie_data in movies_data:
        movie_link = movie_data.get("link")
        movie_release_date = movie_data.get("release_date")

        if not movie_link or not movie_release_date:
            continue

        driver.get(movie_link)

        hero_text_element = driver.find_element(
            By.CSS_SELECTOR, '[data-testid="hero__primary-text"]'
        )
        movie_plot_elem = driver.find_element(
            By.CSS_SELECTOR, '[data-testid="plot-xl"]'
        )

        hero_text = hero_text_element.text.strip()
        movie_plot = movie_plot_elem.text.strip()

        scraped_movies.append(
            Movie(
                title=hero_text,
                release_date=movie_release_date,
                link=movie_link,
                description=movie_plot,
            )
        )

    driver.quit()
    return scraped_movies


def create_ical_object(movies):
    """ "Create an iOS iCalendar"""
    calendar = Calendar()
    calendar.add("prodid", value="Upcoming Movies Calendar")
    calendar.add("version", "2.0")
    calendar.add("x-wr-calname", "Upcoming movies")

    for movie in movies:
        start_date = datetime.strptime(movie.release_date, "%b %d, %Y").date()
        end_date = start_date + timedelta(days=1)

        event = Event()
        event.add("dtstart", start_date)
        event.add("dtend", end_date)
        event.add("summary", movie.title)
        event.add("description", movie.description)
        event.add("url", movie.link)

        calendar.add_component(event)

    return calendar


if __name__ == "__main__":
    movies = scrape_imdb_upcoming_movies_by_region("SE")
    calendar = create_ical_object(movies)

    with open("upcoming_movies.ics", "wb") as f:
        f.write(calendar.to_ical())

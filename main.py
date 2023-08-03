
import requests
from icalendar import Event, Calendar
from datetime import datetime


def fetch_upcoming_movies():
    url = 'https://www.filmstaden.se/api/v2/movie/upcoming/sv/1/1024/true'
    headers = {
        'authority': 'www.filmstaden.se',
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,sv;q=0.8,cs;q=0.7,fr;q=0.6,da;q=0.5,la;q=0.4',
        'cache-control': 'no-cache',
        'cookie': 'ASP.NET_SessionId=fq4wmsnkunjzwh3fufpr21rc; cf_chl_2=6ee55371e0d53cd; cf_clearance=JwBCJ9cNRf9LLzieOwCvyeSnPgEjV4XsFU5U5Ky2kVM-1691063880-0-1-e637e02d.5e37a49e.1670c306-250.0.0; __cf_bm=iHaTX8qJmnHC22tWf91AKpTHM4kZEb1p5lEUPue94UY-1691063885-0-AfIMHHwWs/erlG6EfF2V4STn9DAlLlCTrItIvqdyt2Z1HPE+BmKEf1HcIv8ACietd9pwhXdOc/3DHSQV7uySL74=',
        'pragma': 'no-cache',
        'referer': 'https://www.filmstaden.se/filmer-och-trailers',
        'sec-ch-ua': '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': 'macOS',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    }

    response = requests.get(url=url, headers=headers, timeout=10)

    if response.status_code == 200:
        data = response.json()

        return data['items']
    return []


def create_ical_object(movies):
    cal = Calendar()
    cal.add('prodid', '-//My Upcoming Movies Calendar//example.com//')
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
            event.add('dtstart', datetime.strptime(
                release_date, '%Y-%m-%dT%H:%M:%S'))
            event.add('dtend', datetime.strptime(
                release_date, '%Y-%m-%dT%H:%M:%S'))
            cal.add_component(event)

    return cal


if __name__ == "__main__":
    items = fetch_upcoming_movies()
    calendar = create_ical_object(items)

    with open('upcoming_movies.ics', 'wb') as f:
        f.write(calendar.to_ical())

# Configuration for IMDB Movie Calendar Scraper

# Common IMDB region codes
REGIONS = {
    "US": "United States",
    "SE": "Sweden",
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "JP": "Japan",
    "AU": "Australia",
    "CA": "Canada",
    "IT": "Italy",
    "ES": "Spain",
    "NL": "Netherlands",
    "BR": "Brazil",
    "IN": "India",
    "KR": "South Korea",
    "CN": "China",
}

# Default configuration
DEFAULT_CONFIG = {
    "region": "SE",
    "output_filename": "upcoming_movies.ics",
    "calendar_name": "Upcoming Movies",
    "headless": True,
    "window_size": "1440,1035",
    "timeout": 10,
}

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

from upcoming_movies.config import DEFAULT_CONFIG

PAGE_LOAD_TIMEOUT_SECONDS: int = 30
BROWSER_WINDOW_SIZE: str = DEFAULT_CONFIG["window_size"]
BROWSER_USER_AGENT: str = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


def build_chrome_options() -> Options:
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
            service=chrome_service, options=build_chrome_options()
        )
        chrome_driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_SECONDS)
        yield chrome_driver
    finally:
        if chrome_driver:
            chrome_driver.quit()

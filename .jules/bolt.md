## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2023-10-24 - [Selenium Blocking Waits on Optional Elements]
**Learning:** Using `WebDriverWait` for optional elements (like missing plot descriptions for unreleased movies) causes the scraper to block for the full timeout duration (e.g., 10 seconds) every time the element doesn't exist, severely degrading performance.
**Action:** Use immediate `find_element` (which raises `NoSuchElementException` instantly) for optional DOM nodes when the page load strategy already guarantees DOM presence, avoiding unnecessary blocking.

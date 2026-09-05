## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2026-09-05 - [Bulk DOM Extraction via JavaScript]
**Learning:** In Selenium scrapers, making hundreds of synchronous `.find_element()` and `.text` calls is a massive performance bottleneck due to Webdriver IPC (Inter-Process Communication) overhead. Replacing these with a single `driver.execute_script()` call that performs the DOM traversal and data extraction in bulk directly within the browser context makes data extraction nearly instantaneous.
**Action:** When a scraper needs to extract large lists of items (e.g. iterating over all entries in a list/calendar), prioritize using a single JavaScript script execution instead of looping over Python Selenium WebElements.

## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2026-09-09 - [Bulk DOM Extraction via JS vs Selenium IPC]
**Learning:** Extracting DOM elements sequentially using Python's `find_element` and `get_attribute` in loops causes massive overhead due to N+1 synchronous IPC roundtrips between Python and the Chrome WebDriver.
**Action:** Use a single `driver.execute_script()` call to traverse the DOM and extract all required data directly within the browser context, returning it as a single bulk object.

## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2024-05-24 - [Selenium Bulk DOM Extraction]
**Learning:** Selenium `find_element` and `get_attribute` calls are synchronous IPC roundtrips to the WebDriver. Looping through DOM elements with Selenium commands leads to the N+1 problem and massive performance bottlenecks.
**Action:** Always use `driver.execute_script()` to inject JavaScript and fetch bulk data (like arrays of objects) in a single IPC roundtrip instead of iterating with Python Selenium commands.

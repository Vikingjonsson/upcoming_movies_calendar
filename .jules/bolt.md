## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2026-09-05 - [Bulk JavaScript DOM Extraction]
**Learning:** Using Selenium `find_element` inside loops incurs severe performance penalties because every call triggers a synchronous IPC (Inter-Process Communication) network roundtrip to the browser instance.
**Action:** When scraping repetitive DOM structures (like lists or tables), always use a single `driver.execute_script()` call to parse the entire DOM and return a structured JSON/dictionary array instead of using Python loops. Note: to get absolute URLs in JS like `get_attribute('href')` does in Selenium, access the `.href` DOM property rather than `getAttribute('href')`.

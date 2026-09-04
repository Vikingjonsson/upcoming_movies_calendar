## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2026-09-04 - [Bulk DOM Extraction via JavaScript]
**Learning:** Extracting large sets of elements using multiple synchronous `find_element` or `.text`/`.get_attribute` calls in Python leads to extremely slow performance due to the IPC round-trip overhead of the WebDriver protocol.
**Action:** For Selenium performance optimization, prioritize using `driver.execute_script()` to fetch data in bulk via JavaScript instead of making multiple synchronous calls from Python.

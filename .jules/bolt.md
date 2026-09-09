## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2025-02-12 - [Selenium Bulk DOM Extraction via JavaScript]
**Learning:** Fetching data in bulk via JavaScript `driver.execute_script()` is significantly faster than making multiple synchronous `find_element` or `.text` calls in Python, as it minimizes slow IPC roundtrips between the script and the browser.
**Action:** Prioritize using `driver.execute_script()` for extracting large amounts of data from the DOM in Selenium.

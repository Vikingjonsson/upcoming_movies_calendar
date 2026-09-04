## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2026-09-04 - [Selenium DOM extraction Bulk Fetching]
**Learning:** Using `driver.execute_script()` to fetch DOM data in bulk via JavaScript significantly reduces slow IPC roundtrips between the Python process and the browser, improving scraping speed.
**Action:** Use `execute_script()` for extracting multiple elements or attributes simultaneously instead of looping over `find_element` calls.

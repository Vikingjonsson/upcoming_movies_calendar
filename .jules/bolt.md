## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2024-05-18 - [Selenium Bulk DOM Extraction via JS]
**Learning:** Fetching DOM text and attributes sequentially in Python via `element.text` and `element.get_attribute('href')` causes severe performance bottlenecks due to excessive Selenium IPC roundtrips between the script and the browser.
**Action:** Always replace multiple synchronous `find_element` calls with a single `driver.execute_script()` block that extracts and maps DOM data in bulk using native JavaScript properties like `element.href` (which correctly resolves absolute URLs) and `.innerText`.

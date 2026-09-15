## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2023-11-20 - [JavaScript Execution for Bulk DOM Extraction]
**Learning:** In Selenium, making multiple synchronous `find_element` or `.text` calls inside loops leads to significant performance degradation due to IPC (Inter-Process Communication) overhead. You can bypass this completely by running a single `driver.execute_script()` block that fetches all required data directly from the DOM using JavaScript.
**Action:** Always prioritize using JavaScript for bulk data extraction from the DOM when fetching elements or text attributes, to minimize slow IPC roundtrips.

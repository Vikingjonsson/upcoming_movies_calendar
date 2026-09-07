## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2026-09-07 - [Bulk extraction via JavaScript]
**Learning:** In Selenium, calling `find_element` and `get_attribute` in a loop over many elements causes significant overhead due to IPC roundtrips between the Python process and the browser. Bulk extracting the same data by running a single JavaScript block with `driver.execute_script` and `querySelectorAll` returns all data in a single call and is substantially faster.
**Action:** Use `execute_script` to query lists of DOM elements instead of multiple nested `find_elements` calls for high performance extraction.

## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2026-09-06 - [Bulk DOM Extraction via JavaScript]
**Learning:** Selenium WebDriver's Python API makes slow IPC/HTTP calls for every single `find_element` and `text` extraction. Iterating over the DOM in Python for hundreds of elements creates severe N+1 bottlenecks.
**Action:** Use `driver.execute_script()` to traverse the DOM and extract text/attributes directly in the browser, returning the assembled data in a single IPC call.

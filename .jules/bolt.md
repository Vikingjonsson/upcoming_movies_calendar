## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2024-03-22 - [Selenium Performance: JavaScript Execution vs find_elements]
**Learning:** Making numerous synchronous calls to `.find_element()`, `.find_elements()`, `.text`, and `.get_attribute()` causes massive IPC overhead because each call makes a roundtrip between the Python script and the browser driver. This can be a huge performance bottleneck when parsing lists of elements.
**Action:** Prioritize using `driver.execute_script()` to fetch data in bulk via JavaScript instead of making multiple synchronous DOM calls.

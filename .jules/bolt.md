## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.
## 2026-09-19 - [Optimizing DOM extraction with execute_script]
**Learning:** Using Selenium's find_element and .text repeatedly incurs a massive IPC overhead due to multiple synchronous roundtrips between Python and the browser.
**Action:** Prioritize using driver.execute_script() to fetch data in bulk via JavaScript instead of making multiple synchronous find_element calls, using .innerText and .href properties to match Selenium's native extraction perfectly.
## 2024-05-24 - [Optimizing Datetime Parsing]
**Learning:** Parsing dates using `datetime.strptime` inside loops creates a CPU bottleneck. Since many movies share the exact same release date string, parsing the same string repeatedly is highly inefficient.
**Action:** Always wrap parsing functions like `parse_imdb_release_date` with `@functools.lru_cache` to cache results and eliminate redundant computation.

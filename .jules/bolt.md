## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.
## 2026-09-19 - [Optimizing DOM extraction with execute_script]
**Learning:** Using Selenium's find_element and .text repeatedly incurs a massive IPC overhead due to multiple synchronous roundtrips between Python and the browser.
**Action:** Prioritize using driver.execute_script() to fetch data in bulk via JavaScript instead of making multiple synchronous find_element calls, using .innerText and .href properties to match Selenium's native extraction perfectly.

## 2026-10-01 - [Combine DOM extractions with execute_script]
**Learning:** Combining multiple DOM extractions into a single driver.execute_script call significantly reduces IPC roundtrip latency compared to fetching elements sequentially with Selenium.
**Action:** Group multiple element extractions on a single page into one JavaScript block whenever possible.

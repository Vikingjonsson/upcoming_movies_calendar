## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2024-05-18 - [Bulk DOM Extraction]
**Learning:** In Selenium scraping scripts, making numerous synchronous IPC calls to retrieve individual elements, attributes, and text creates a massive bottleneck. Batch DOM extraction using `execute_script` allows processing all the required data directly in the browser and returning a clean dictionary, avoiding hundreds of network roundtrips to the browser driver.
**Action:** Prioritize `execute_script` for scraping large tables or lists in Selenium over loops with `find_element`, `text`, or `get_attribute` when optimizing performance.

## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2026-09-08 - [Bulk JS DOM Extraction vs Selenium IPC]
**Learning:** Making repetitive `.find_element` and `.text` calls inside a loop creates massive overhead due to Selenium's synchronous Inter-Process Communication (IPC) architecture. Extracting data individually from large lists creates O(N) IPC calls.
**Action:** Prioritize using `driver.execute_script()` to fetch list/tabular data in bulk via JavaScript. This consolidates hundreds of IPC roundtrips into a single call, vastly improving scraping performance.

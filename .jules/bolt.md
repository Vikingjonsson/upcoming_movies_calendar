## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.
## 2026-09-14 - [Selenium Bulk DOM Extraction]
**Learning:** Extracting DOM data through repetitive synchronous Selenium calls (like `find_element` and `.text`) introduces severe IPC roundtrip latency overhead, especially when scraping dozens of elements on complex pages.
**Action:** When scraping many text and attribute fields sequentially, inject JavaScript via `driver.execute_script()` for bulk retrieval, using `.innerText` to mirror Selenium's `.text` and DOM property `.href` to auto-resolve absolute URLs to exactly replicate `.get_attribute('href')`.

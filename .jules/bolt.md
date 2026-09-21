## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.
## 2026-09-19 - [Optimizing DOM extraction with execute_script]
**Learning:** Using Selenium's find_element and .text repeatedly incurs a massive IPC overhead due to multiple synchronous roundtrips between Python and the browser.
**Action:** Prioritize using driver.execute_script() to fetch data in bulk via JavaScript instead of making multiple synchronous find_element calls, using .innerText and .href properties to match Selenium's native extraction perfectly.
## 2026-09-21 - [Selenium execute_script and independent fallbacks]
**Learning:** When combining independent DOM queries into a single `execute_script` to reduce Selenium IPC roundtrips, ensure that `WebDriverWait` timeouts on one element do not entirely skip the extraction of others if they are independently available.
**Action:** Catch wait exceptions specifically (e.g., `WebDriverException`) and still execute the JavaScript block to preserve independent fallback mechanisms.

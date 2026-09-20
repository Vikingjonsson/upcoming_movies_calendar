## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.
## 2026-09-19 - [Optimizing DOM extraction with execute_script]
**Learning:** Using Selenium's find_element and .text repeatedly incurs a massive IPC overhead due to multiple synchronous roundtrips between Python and the browser.
**Action:** Prioritize using driver.execute_script() to fetch data in bulk via JavaScript instead of making multiple synchronous find_element calls, using .innerText and .href properties to match Selenium's native extraction perfectly.
## 2026-09-20 - [Safe Refactoring of Sequential DOM Extractions]
**Learning:** When replacing sequential Selenium DOM extractions (`find_element`, `text`) with a single bulk JavaScript execution (`execute_script`), missing elements return `null` in JavaScript instead of raising Selenium's `NoSuchElementException` or `WebDriverException`. A strict truthiness check (`if result.get("field"):`) in Python fails to distinguish between an intentionally empty text string (`""`) and a missing element (`None`).
**Action:** Always use strict `is not None` checks in Python when parsing dictionaries returned by bulk JavaScript extractions to perfectly preserve the original error handling and fallback logic.

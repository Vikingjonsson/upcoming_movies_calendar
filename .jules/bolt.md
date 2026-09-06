## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2023-10-18 - [Selenium Bulk DOM Extraction]
**Learning:** Calling Selenium's `.find_element`, `.find_elements`, `.text`, and `.get_attribute()` repetitively in Python loops is extremely slow due to individual IPC roundtrips between Python and the ChromeDriver.
**Action:** Always prefer fetching bulk DOM data at once using `driver.execute_script()` and iterating/mapping items natively in JavaScript. Return the full set back to Python in a single list/dict IPC boundary cross.

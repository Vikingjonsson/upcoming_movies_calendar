## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2024-05-15 - [Selenium DOM extraction optimization]
**Learning:** For Selenium performance optimization, prioritize using `driver.execute_script()` to fetch data in bulk via JavaScript instead of making multiple synchronous `find_element` or `.text` calls. This minimizes slow IPC roundtrips between the Python process and the browser. Also, note that Selenium's `element.get_attribute('href')` automatically resolves relative links to absolute URLs. To achieve the same behavior in JavaScript, use the DOM property `element.href` instead of `element.getAttribute('href')`.
**Action:** When extracting multiple elements from the DOM, use `execute_script` to batch the extraction into a single IPC call.

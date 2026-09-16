## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.

## 2026-09-16 - [Bulk JS DOM Extraction in Selenium]
**Learning:** Fetching many DOM elements in Selenium using loops over `find_element` and `.text` causes hundreds of slow IPC roundtrips between Python and the browser.
**Action:** Use `driver.execute_script()` to fetch data in bulk via JavaScript instead, drastically reducing IPC overhead. Remember to use `.innerText` instead of `.textContent` for visual parity, and `.href` instead of `.getAttribute('href')` to resolve absolute URLs.

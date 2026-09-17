## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2024-05-15 - [Selenium IPC Overhead in DOM Traversal]
**Learning:** Using Selenium's `find_element` and `.text` methods iteratively triggers significant Inter-Process Communication (IPC) overhead, drastically slowing down DOM traversal.
**Action:** When extracting bulk data from the DOM, use `driver.execute_script()` to run a single JavaScript query (`querySelectorAll`, `innerText`, etc.) and return all required data in a single IPC call.

## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.
## 2024-05-18 - [Selenium IPC Bottlenecks vs Bulk JS Execution]
**Learning:** This codebase uses Python Selenium for DOM extraction, where synchronous calls like `find_element` and `.text` cause severe performance bottlenecks due to IPC roundtrips between the Python process and the browser.
**Action:** Use `driver.execute_script()` to fetch DOM data in bulk via JavaScript instead of making multiple synchronous Selenium calls.

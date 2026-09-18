## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2026-09-18 - [Selenium Bulk DOM Extraction]
**Learning:** Making multiple synchronous find_element and .text calls in Python Selenium causes significant IPC overhead. Fetching data in bulk via driver.execute_script() using JavaScript is massively faster (e.g. from 3.9s to 0.02s for 100 items). Using element.innerText exactly matches Selenium's .text logic, and element.href correctly matches get_attribute('href') for relative link resolution.
**Action:** Use execute_script() with JavaScript for bulk DOM data extraction in Selenium instead of multiple individual Python calls.

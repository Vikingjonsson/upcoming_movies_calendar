## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.
## 2026-09-12 - [Selenium Text Extraction: innerText vs textContent]
**Learning:** When using `driver.execute_script()` to replace Python-side Selenium `element.text` calls, you should use JavaScript's `.innerText` rather than `.textContent`. `.textContent` returns all text including hidden elements and raw spacing, while `.innerText` properly respects CSS visibility and spacing, providing an exact 1:1 match for Selenium's native `.text` behavior.
**Action:** Always map Selenium `.text` directly to `.innerText` in bulk execute_script extractions.

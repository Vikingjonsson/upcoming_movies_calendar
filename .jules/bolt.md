## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.

## 2024-05-18 - [Scratchpad File Naming]
**Learning:** Prefixing scratchpad or temporary files with `test_` causes `pytest` to automatically collect and run them, triggering unintended side-effects (e.g., launching headless browsers and making network calls) during the test phase.
**Action:** Always name temporary or sandbox scripts without the `test_` prefix (e.g., `sandbox_selenium.py` instead of `test_selenium.py`).

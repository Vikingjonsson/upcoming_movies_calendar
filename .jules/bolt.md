## 2023-11-20 - [Selenium DOM extraction vs Image Loading]
**Learning:** You don't need to load images to extract their URLs. Disabling image loading in Chrome preferences (`profile.managed_default_content_settings.images=2`) and setting `page_load_strategy='eager'` prevents browser bandwidth usage but leaves `<img>` tags and their `src` attributes fully intact for DOM extraction.
**Action:** Always apply these settings when scraping raw data from DOM attributes without needing visual rendering.
## 2023-11-20 - [Javascript Backticks over Single Quotes]
**Learning:** When generating JavaScript code in Python f-strings that use CSS selectors, it is safer to wrap the selectors in backticks (`\``) rather than single quotes (`'`). If a CSS selector happens to contain a single quote (e.g. `[data-testid='value']`), using single quotes to wrap it will prematurely terminate the string and break the JavaScript execution.
**Action:** Always use backticks for Javascript string literals enclosing CSS selectors passed dynamically from Python.

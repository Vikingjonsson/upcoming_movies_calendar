---
description: Python standards, strict typing, top-of-file imports, and scraping performance guidelines.
globs: "**/*.py"
---

# Upcoming Movies Python Guidelines

- **Imports at Top**: All import statements must be strictly at the very top of each file. Never place code, variable definitions, or filter calls before imports. Do not use `# noqa: E402`.
- **Standard Library CLI**: Keep CLI lightweight using Python's built-in `argparse`. Do not introduce external CLI dependencies.
- **Strict Typing**: Maintain 100% type coverage compatible with `mypy --strict`. Ensure `py.typed` is packaged.
- **DOM Extraction Performance**: Batch DOM extractions in the scraper via `driver.execute_script()` to minimize synchronous Selenium IPC roundtrips between Python and the browser. Disable browser image loading (`profile.managed_default_content_settings.images=2`) and set `page_load_strategy='eager'`.
- **Verification**: Always run `pytest`, `ruff check .`, `ruff format --check .`, and `mypy src` after changes.

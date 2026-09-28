# Antigravity Workspace Guidelines: Upcoming Movies Calendar & Exporter

This repository provides a CLI tool to scrape upcoming movie releases from IMDB by region and export them to iCalendar (`.ics`) and JSON (`.json`) formats.

## Architecture

- **`src/upcoming_movies/cli.py`**: Clean, standard-library `argparse` CLI interface. Supports both interactive prompting and flag-driven execution.
- **`src/upcoming_movies/main.py`**: Package entrypoint re-exporting CLI execution.
- **`src/upcoming_movies/scraping/`**: Headless Selenium web scraping engine.
  - `scraper.py`: Core scraping routines.
  - `scraper_utils.py`: Date parsing, month mappings, and utility helpers.
- **`src/upcoming_movies/exporters/`**: Multi-format calendar/data exporters.
  - `ics_exporter.py`: iCalendar builder using `icalendar`.
  - `json_exporter.py`: JSON serializer and deserializer.
  - `__init__.py`: Exporters registry and format resolution.
- **`src/upcoming_movies/models.py`**: Strongly typed data models (`MovieCalendarEvent`, `ScheduledMovie`).
- **`src/upcoming_movies/config.py`**: Supported regions (`REGIONS`) and default configurations.
- **`src/upcoming_movies/py.typed`**: PEP 561 marker indicating full type annotation support.

## Developer Workflows

Always use the project's local virtual environment (`./venv`):

```bash
# Setup
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install -e .

# Run CLI
./venv/bin/upcoming-movies --help
./venv/bin/upcoming-movies -f json -r SE
./run.sh -f ics

# Verification
./venv/bin/pytest                     # Run test suite
./venv/bin/ruff check .                # Lint codebase
./venv/bin/ruff format --check .       # Check formatting
./venv/bin/mypy src                    # Strict type checking
```

## Agent Rules & Conventions

1. **Imports at Top of File**:
   - All `import` statements must remain strictly at the very top of each file.
   - Never place code, variable definitions, or function calls before imports.
   - Do not use `# noqa: E402`.

2. **Standard Library CLI**:
   - Keep the CLI lightweight using Python's built-in `argparse`.
   - Never introduce heavy CLI framework dependencies (e.g., Click, Typer) without explicit user approval.

3. **Strict Type Safety**:
   - Maintain 100% type coverage compatible with `mypy --strict`.
   - Ensure dataclasses and utility signatures are fully annotated.

4. **DOM Extraction Performance**:
   - Batch DOM extractions in the scraper via `driver.execute_script()` to minimize synchronous Selenium IPC roundtrips between Python and the browser.
   - Disable browser image loading (`profile.managed_default_content_settings.images=2`) and use `page_load_strategy='eager'`.

5. **Verification Before Handoff**:
   - Always run `pytest`, `ruff check .`, `ruff format --check .`, and `mypy src` after making changes.

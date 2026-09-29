---
name: movie-calendar
description: >-
  Workflows for scraping upcoming movie releases from IMDB, running the interactive or flag-driven CLI, and exporting to ICS, JSON, Markdown Cards, or Terminal Cards.
---

# Movie Calendar Workflow Skill

Use this skill when developing, testing, scraping, or exporting upcoming movie calendar releases.

## CLI Usage

```bash
# Interactive mode (prompts for region, format, date filter, style, and output file)
./venv/bin/upcoming-movies

# Display movies as visual cards in terminal (auto-cached)
./venv/bin/upcoming-movies --card-view
./venv/bin/upcoming-movies -f terminal --weekend
./venv/bin/upcoming-movies -f terminal -r US

# Force live re-scrape from IMDB (bypasses cache and updates it)
./venv/bin/upcoming-movies --refresh -f terminal --weekend

# Run completely without caching
./venv/bin/upcoming-movies --no-cache -f terminal --today

# Export Swedish releases to JSON
./venv/bin/upcoming-movies -f json -r SE

# Export weekend releases as Markdown Cards
./venv/bin/upcoming-movies -f cards -r SE --weekend

# Export as Antigravity carousel
./venv/bin/upcoming-movies -f cards -r SE --weekend --carousel

# Date filtering flags
./venv/bin/upcoming-movies -f json --today
./venv/bin/upcoming-movies -f json --from-date 2026-05-01 --to-date 2026-05-31

# Export to ICS (United States)
./venv/bin/upcoming-movies -f ics -r US -o us_movies.ics

# List supported regions
./venv/bin/upcoming-movies -l
```

## Verification Workflows

```bash
./venv/bin/pytest                     # Run full test suite (100+ tests)
./venv/bin/ruff check .                # Lint codebase
./venv/bin/ruff format --check .       # Check formatting
./venv/bin/mypy src                    # Strict type checking (100% type coverage)
```

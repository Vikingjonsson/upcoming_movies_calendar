---
name: movie-calendar
description: >-
  Workflows for scraping upcoming movie releases from IMDB, running the CLI, and exporting to ICS/JSON.
---

# Movie Calendar Workflow Skill

Use this skill when developing, testing, scraping, or exporting upcoming movie calendar releases.

## CLI Usage

```bash
# Direct CLI execution
./venv/bin/upcoming-movies -f json -r SE
./venv/bin/upcoming-movies -f ics -r US -o us_movies.ics
./run.sh -f ics

# List regions
./venv/bin/upcoming-movies -l
```

## Verification Workflows

```bash
./venv/bin/pytest                     # Run full test suite
./venv/bin/ruff check .                # Lint codebase
./venv/bin/ruff format --check .       # Check formatting
./venv/bin/mypy src                    # Strict type checking
```

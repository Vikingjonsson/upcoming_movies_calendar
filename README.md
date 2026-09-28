# Upcoming Movies Calendar & Exporter

A Python script that scrapes upcoming movie releases from IMDB and exports them to multiple formats, including iCalendar (.ics) and JSON (.json).

## Features

- Scrapes upcoming movies from IMDB by region
- Multi-format export:
  - iCalendar (`.ics`) compatible with calendar applications (Apple Calendar, Google Calendar, Outlook)
  - JSON (`.json`) for data interchange and downstream generation of other formats
- Interactive format selection prompt when no parameters are provided
- Shorthand command-line arguments for automated or script usage (`-f ics`, `-f json`)
- Robust error handling and logging
- Context manager for proper WebDriver cleanup

## Requirements

- Python 3.9+
- Google Chrome browser (for Selenium WebDriver)
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

   This installs the `upcoming-movies` command directly into your environment.

## Usage

You can use the installed `upcoming-movies` command, `./run.sh`, or `python main.py`.

### Interactive format prompt

Running without flags interactively prompts for the output format:

```bash
upcoming-movies
```

```text
Available output formats:
  1) iCalendar (.ics)     [shorthand: -f ics]
  2) JSON (.json)          [shorthand: -f json]
Select format [1-2] (default: 1): 1
```

### Direct CLI options

Export directly using short or long flags:

```bash
# Export to JSON for Sweden (default region: SE)
upcoming-movies -f json

# Export to iCalendar (.ics) for the United States
upcoming-movies -f ics -r US -o us_movies.ics

# Export with custom calendar name
upcoming-movies -f ics -c "My 2026 Cinema Calendar"
```

### List common regions

```bash
upcoming-movies -l
# or:
upcoming-movies --list-regions
```

### Direct Python / script usage

```bash
python main.py -f json -r US
./run.sh -f ics
PYTHONPATH=src python -m upcoming_movies -f ics
```

### Command-line options

- `-f, --format`: Output format (`ics` or `json`). Prompts interactively if omitted.
- `-r, --region`: IMDB region code (default: `SE` for Sweden).
- `-o, --output`: Output filename (default: `upcoming_movies.<format>`).
- `-c, --calendar-name`: Calendar name when exporting to ICS (default: `Upcoming Movies`).
- `-l, --list-regions`: List common IMDB region codes and exit.
- `--no-prompt`: Run non-interactively using default format (`ics`) if `-f` is omitted.
- `-q, --quiet`: Quiet mode (only print generated output filepath).
- `-v, --verbose`: Enable verbose debug logging.

## Common Region Codes

- US: United States
- SE: Sweden
- GB: United Kingdom
- DE: Germany
- FR: France
- JP: Japan
- AU: Australia

## Output Formats

### iCalendar (.ics)

Generates an `.ics` file containing:

- Movie titles as event summaries
- Release dates as event dates
- Movie plots as event descriptions
- IMDB URLs for each movie
- Movie poster images attached (when available)

### JSON (.json)

Generates a structured `.json` array of movie objects:

```json
[
  {
    "title": "Movie Title",
    "release_date": "2026-10-01",
    "imdb_url": "https://www.imdb.com/title/tt...",
    "plot_description": "Movie plot summary...",
    "poster_image_url": "https://m.media-amazon.com/images/..."
  }
]
```

## Error Handling

The script includes comprehensive error handling for:

- Missing web elements
- Network timeouts
- WebDriver issues
- File I/O operations
- Date parsing errors

## Logging

The script provides detailed logging information including:

- Progress updates during scraping
- Error messages with context
- Summary of results

Use the `--verbose` flag for additional debug information.

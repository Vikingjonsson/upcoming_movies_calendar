# Upcoming Movies Calendar

A Python script that scrapes upcoming movie releases from IMDB and creates an iCalendar (.ics) file that can be imported into calendar applications.

## Features

- Scrapes upcoming movies from IMDB by region
- Creates iCalendar files compatible with most calendar applications
- Robust error handling and logging
- Command-line interface with customizable options
- Context manager for proper WebDriver cleanup

## Requirements

- Python 3.7+
- Firefox browser (for Selenium WebDriver)
- Required Python packages (see requirements.txt)

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Using the convenience script (recommended):
```bash
./run.sh
```

### With custom options:
```bash
./run.sh --region US --output us_movies.ics --calendar-name "US Movies" --verbose
```

### Direct Python usage:
```bash
python main.py
```

### With virtual environment:
```bash
source venv/bin/activate
python main.py --region US --output us_movies.ics --calendar-name "US Movies" --verbose
```

### Command-line options:
- `--region`: IMDB region code (default: SE for Sweden)
- `--output`: Output filename for the iCalendar file (default: upcoming_movies.ics)
- `--calendar-name`: Name for the calendar (default: Upcoming Movies)
- `--verbose`: Enable verbose logging

## Common Region Codes

- US: United States
- SE: Sweden
- GB: United Kingdom
- DE: Germany
- FR: France
- JP: Japan
- AU: Australia

## Output

The script generates an .ics file that contains:
- Movie titles as event summaries
- Release dates as event dates
- Movie plots as event descriptions
- IMDB URLs for each movie

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

## Example

```bash
python main.py --region SE --output swedish_movies.ics --calendar-name "Swedish Movie Releases"
```

This will create a calendar file with upcoming movie releases in Sweden.

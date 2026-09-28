from __future__ import annotations

import argparse
import sys
import warnings

# Suppress urllib3 NotOpenSSLWarning before selenium/webdriver packages are imported
warnings.filterwarnings("ignore", module="urllib3")

from upcoming_movies.cli import build_parser, cli_main  # noqa: E402


def parse_command_line_arguments() -> argparse.Namespace:
    """Parse command line arguments (backward compatibility wrapper)."""
    return build_parser().parse_args()


def main() -> None:
    """Main entrypoint for upcoming_movies."""
    exit_code = cli_main()
    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()

"""Package main entrypoint."""

from __future__ import annotations

from upcoming_movies.cli import cli_main, main, parse_command_line_arguments

__all__ = ["cli_main", "main", "parse_command_line_arguments"]

if __name__ == "__main__":
    main()

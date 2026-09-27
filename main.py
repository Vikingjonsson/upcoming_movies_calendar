#!/usr/bin/env python3
"""Convenience launcher for the upcoming_movies package."""

from __future__ import annotations

import sys
from pathlib import Path

# Add src to sys.path so the package can be run directly from repo root
_src_dir = Path(__file__).resolve().parent / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from upcoming_movies.main import main

if __name__ == "__main__":
    main()

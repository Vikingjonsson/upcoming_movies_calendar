#!/usr/bin/env python3
"""Convenience launcher for the upcoming_movies package."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    src_dir = Path(__file__).resolve().parent / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    runpy.run_module("upcoming_movies", run_name="__main__")

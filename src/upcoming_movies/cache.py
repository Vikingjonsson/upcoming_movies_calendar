from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from upcoming_movies.exporters.json_exporter import (
    load_json_from_file,
    save_json_to_file,
)
from upcoming_movies.models import MovieCalendarEvent

logger = logging.getLogger(__name__)

DEFAULT_CACHE_TTL_HOURS = 24.0


def get_cache_dir() -> Path:
    """Return the platform-appropriate cache directory for upcoming movies."""
    cache_base = os.environ.get("XDG_CACHE_HOME")
    if cache_base:
        path = Path(cache_base) / "upcoming_movies"
    else:
        path = Path.home() / ".cache" / "upcoming_movies"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_cache_filepath(region: str) -> Path:
    """Return the cache file path for a specific region."""
    normalized_region = region.strip().upper()
    return get_cache_dir() / f"releases_{normalized_region}.json"


def get_cached_movies(
    region: str, max_age_hours: float = DEFAULT_CACHE_TTL_HOURS
) -> list[MovieCalendarEvent] | None:
    """Return cached movie events if cache exists and is younger than max_age_hours."""
    cache_path = get_cache_filepath(region)
    if not cache_path.is_file():
        return None

    try:
        mtime = cache_path.stat().st_mtime
        age_hours = (time.time() - mtime) / 3600.0
        if age_hours > max_age_hours:
            logger.debug(
                "Cache for region %s is stale (age: %.1f hrs > max: %.1f hrs)",
                region,
                age_hours,
                max_age_hours,
            )
            return None

        events = load_json_from_file(str(cache_path))
        logger.info(
            "Loaded %d movies for region %s from cache (%s)",
            len(events),
            region,
            cache_path,
        )
        return events
    except Exception as exc:
        logger.warning("Failed reading cache for %s (%s): %s", region, cache_path, exc)
        return None


def get_stale_cached_movies(region: str) -> list[MovieCalendarEvent] | None:
    """Return cached movies even if stale (used as offline fallback)."""
    cache_path = get_cache_filepath(region)
    if not cache_path.is_file():
        return None
    try:
        return load_json_from_file(str(cache_path))
    except Exception:
        return None


def save_cached_movies(region: str, events: list[MovieCalendarEvent]) -> Path:
    """Save movie events to the region cache file."""
    cache_path = get_cache_filepath(region)
    try:
        save_json_to_file(events, str(cache_path))
        logger.debug("Saved %d movies to cache %s", len(events), cache_path)
    except Exception as exc:
        logger.warning("Failed saving cache to %s: %s", cache_path, exc)
    return cache_path

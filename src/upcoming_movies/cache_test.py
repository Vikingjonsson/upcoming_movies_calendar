from __future__ import annotations

import os
import time
from datetime import date
from pathlib import Path

import pytest

from upcoming_movies.cache import (
    get_cache_dir,
    get_cache_filepath,
    get_cached_movies,
    get_stale_cached_movies,
    save_cached_movies,
)
from upcoming_movies.models import MovieCalendarEvent


def _sample_movie(title: str = "Test Film") -> MovieCalendarEvent:
    return MovieCalendarEvent(
        title=title,
        release_date=date(2026, 10, 2),
        imdb_url="https://imdb.com/title/tt1234567/",
        plot_description="Sample plot",
        poster_image_url="https://img.com/poster.jpg",
        genres=["Action", "Sci-Fi"],
    )


def test_get_cache_dir_custom_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    cache_dir = get_cache_dir()
    assert cache_dir == tmp_path / "upcoming_movies"
    assert cache_dir.is_dir()


def test_get_cache_filepath(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    fp = get_cache_filepath("se")
    assert fp.name == "releases_SE.json"


def test_save_and_get_cached_movies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    movies = [_sample_movie("Film 1"), _sample_movie("Film 2")]

    saved_path = save_cached_movies("SE", movies)
    assert saved_path.is_file()

    loaded = get_cached_movies("SE", max_age_hours=1.0)
    assert loaded is not None
    assert len(loaded) == 2
    assert loaded[0].title == "Film 1"
    assert loaded[0].genres == ["Action", "Sci-Fi"]


def test_get_cached_movies_stale(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    movies = [_sample_movie()]
    saved_path = save_cached_movies("SE", movies)

    # Set mtime to 48 hours ago
    old_time = time.time() - (48 * 3600)
    os.utime(saved_path, (old_time, old_time))

    # max_age 24h should reject it
    assert get_cached_movies("SE", max_age_hours=24.0) is None

    # But get_stale_cached_movies should still retrieve it
    stale = get_stale_cached_movies("SE")
    assert stale is not None
    assert len(stale) == 1
    assert stale[0].title == "Test Film"


def test_corrupt_cache_returns_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    cache_path = get_cache_filepath("SE")
    cache_path.write_text("invalid json syntax", encoding="utf-8")

    assert get_cached_movies("SE") is None
    assert get_stale_cached_movies("SE") is None

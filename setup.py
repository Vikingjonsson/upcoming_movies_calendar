from __future__ import annotations

from setuptools import find_packages, setup

setup(
    name="upcoming-movies",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    entry_points={
        "console_scripts": [
            "upcoming-movies=upcoming_movies.main:main",
        ],
    },
)

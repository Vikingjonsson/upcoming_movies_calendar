"""Markdown card exporter for upcoming movie events."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from upcoming_movies.models import MovieCalendarEvent

logger = logging.getLogger(__name__)


def format_movie_card(event: MovieCalendarEvent) -> str:
    """Format a single movie event into a rich markdown card."""
    formatted_date = event.release_date.strftime("%B %d, %Y (%A)")
    lines: list[str] = [
        f"### 🎬 [{event.title}]({event.imdb_url})",
        f"> **Release Date**: {formatted_date}  ",
    ]
    if event.genres:
        genre_tags = " ".join(f"`{g}`" for g in event.genres)
        lines.append(f"> **Genres**: {genre_tags}  ")

    lines.append(">")
    lines.append(f"> {event.plot_description}")

    if event.poster_image_url:
        lines.append(">")
        lines.append(f"> [![Poster]({event.poster_image_url})]({event.imdb_url})")

    lines.append("")
    return "\n".join(lines)


def build_cards_from_movie_events(
    movie_events: Sequence[MovieCalendarEvent],
    *,
    title: str = "Upcoming Movies",
    as_carousel: bool = False,
) -> str:
    """Serialize movie events into a markdown document of cards or carousel."""
    if not movie_events:
        return f"# {title}\n\n*No upcoming movies found.*\n"

    if as_carousel:
        slides: list[str] = []
        for event in movie_events:
            formatted_date = event.release_date.strftime("%B %d, %Y")
            slide_lines = [
                f"### 🎬 [{event.title}]({event.imdb_url})",
                f"**Release Date**: {formatted_date}  ",
            ]
            if event.genres:
                slide_lines.append(f"**Genres**: {', '.join(event.genres)}  ")
            if event.poster_image_url:
                slide_lines.append(f"![Poster]({event.poster_image_url})")
            slide_lines.append(f"\n{event.plot_description}\n")
            slides.append("\n".join(slide_lines))

        carousel_body = "\n<!-- slide -->\n".join(slides)
        return f"# {title}\n\n````carousel\n{carousel_body}\n````\n"

    cards = [format_movie_card(event) for event in movie_events]
    cards_content = "\n---\n\n".join(cards)
    return f"# {title}\n\n{cards_content}\n"


def save_cards_to_file(
    movie_events: Sequence[MovieCalendarEvent],
    output_filepath: str,
    *,
    title: str = "Upcoming Movies",
    as_carousel: bool = False,
    **_kwargs: object,
) -> None:
    """Save formatted markdown cards to a file."""
    content = build_cards_from_movie_events(
        movie_events, title=title, as_carousel=as_carousel
    )
    try:
        with open(output_filepath, "w", encoding="utf-8") as output_file:
            output_file.write(content)
        logger.info("Cards saved to %s (%d movies)", output_filepath, len(movie_events))
    except OSError as error:
        logger.error("Error saving cards to %s: %s", output_filepath, error)
        raise

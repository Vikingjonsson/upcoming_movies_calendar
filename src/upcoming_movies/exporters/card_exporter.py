"""Card exporter for upcoming movie events (Markdown, Carousel, and Terminal views)."""

from __future__ import annotations

import logging
import textwrap
from collections.abc import Sequence

from upcoming_movies.models import MovieCalendarEvent

logger = logging.getLogger(__name__)

DEFAULT_CARD_WIDTH: int = 70


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


def format_terminal_card(
    event: MovieCalendarEvent,
    index: int = 1,
    width: int = DEFAULT_CARD_WIDTH,
) -> str:
    """Format a movie event into a terminal card matching the UI specification."""
    border = "─" * width
    formatted_date = event.release_date.strftime("%B %d, %Y (%A)")
    genres_text = ", ".join(event.genres) if event.genres else "N/A"
    poster_text = event.poster_image_url if event.poster_image_url else "N/A"

    lines: list[str] = [
        border,
        f"[{index}] 🎬 {event.title}  [MOVIE]",
        f"   📅 Release: {formatted_date}",
        f"   🎭 Genres:  {genres_text}",
        f"   🔗 Link:    {event.imdb_url}",
        f"   🖼️  Poster:  {poster_text}",
        "",
    ]

    plot = (
        event.plot_description.strip()
        if event.plot_description
        else "No description available"
    )
    wrap_width = max(20, width - 3)
    wrapped_plot = textwrap.fill(
        plot,
        width=wrap_width,
        initial_indent="   ",
        subsequent_indent="   ",
    )
    lines.append(wrapped_plot)
    lines.append(border)

    return "\n".join(lines)


def build_terminal_cards_from_movie_events(
    movie_events: Sequence[MovieCalendarEvent],
    width: int = DEFAULT_CARD_WIDTH,
) -> str:
    """Serialize movie events into terminal card views separated by newlines."""
    if not movie_events:
        border = "─" * width
        return f"{border}\n* No upcoming movies found *\n{border}\n"

    cards = [
        format_terminal_card(event, index=idx, width=width)
        for idx, event in enumerate(movie_events, 1)
    ]
    return "\n".join(cards) + "\n"


def save_terminal_cards_to_file(
    movie_events: Sequence[MovieCalendarEvent],
    output_filepath: str,
    width: int = DEFAULT_CARD_WIDTH,
    **_kwargs: object,
) -> None:
    """Save formatted terminal cards to a file."""
    content = build_terminal_cards_from_movie_events(movie_events, width=width)
    try:
        with open(output_filepath, "w", encoding="utf-8") as output_file:
            output_file.write(content)
        logger.info(
            "Terminal cards saved to %s (%d movies)",
            output_filepath,
            len(movie_events),
        )
    except OSError as error:
        logger.error("Error saving terminal cards to %s: %s", output_filepath, error)
        raise

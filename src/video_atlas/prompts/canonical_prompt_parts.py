"""Shared prompt fragments for canonical VideoAtlas prompts."""

from __future__ import annotations

from ..schemas.canonical_registry import (
    ALLOWED_GENRES,
    SAMPLING_PROFILE_DESCRIPTIONS,
    SEGMENTATION_PROFILE_DESCRIPTIONS,
)


def _format_bullets(options: list[tuple[str, str]]) -> str:
    return "\n".join(f"- {name}\n  {description}" for name, description in options)


def render_genre_options() -> str:
    return "\n".join(f"- {genre}" for genre in sorted(ALLOWED_GENRES))


def render_segmentation_profile_options() -> str:
    return _format_bullets(list(SEGMENTATION_PROFILE_DESCRIPTIONS.items()))


def render_sampling_profile_options() -> str:
    return _format_bullets(list(SAMPLING_PROFILE_DESCRIPTIONS.items()))

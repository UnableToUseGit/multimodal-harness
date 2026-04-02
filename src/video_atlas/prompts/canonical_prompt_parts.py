"""Shared prompt fragments for canonical VideoAtlas prompts."""

from __future__ import annotations

from ..schemas.canonical_registry import (
    ALLOWED_GENRES,
    PROFILES,
    SAMPLING_PROFILE_DESCRIPTIONS,
    SEGMENTATION_PROFILE_DESCRIPTIONS,
)


def _format_bullets(options: list[tuple[str, str]]) -> str:
    return "\n".join(f"- {name}\n  {description}" for name, description in options)


def render_genre_options() -> str:
    return "\n".join(f"- {genre}" for genre in sorted(ALLOWED_GENRES))


def render_segmentation_profile_options() -> str:
    return _format_bullets(list(SEGMENTATION_PROFILE_DESCRIPTIONS.items()))


def render_profile_options() -> str:
    options: list[tuple[str, str]] = []
    for name, profile in PROFILES.items():
        options.append(
            (
                name,
                f"route={profile.route}; segmentation_policy={profile.segmentation_policy}; "
                f"caption_policy={profile.caption_policy}",
            )
        )
    return _format_bullets(options)


def render_sampling_profile_options() -> str:
    return _format_bullets(list(SAMPLING_PROFILE_DESCRIPTIONS.items()))

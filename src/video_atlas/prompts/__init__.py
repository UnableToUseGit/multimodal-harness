# -*- coding: utf-8 -*-
"""Prompt exports used by the atlas agents."""

from __future__ import annotations

from .specs import PromptRegistry, PromptRenderError, PromptSpec

from .canonical_prompts import (
    BOUNDARY_DETECTION_PROMPT,
    CAPTION_GENERATION_PROMPT,
    PLANNER_PROMPT,
    VIDEO_GLOBAL_PROMPT,
)
from .derived_prompts import (
    DERIVED_CANDIDATE_PROMPT,
    DERIVED_CAPTION_PROMPT,
    DERIVED_GROUNDING_PROMPT,
)

PROMPT_SPECS = (
    PLANNER_PROMPT,
    BOUNDARY_DETECTION_PROMPT,
    CAPTION_GENERATION_PROMPT,
    VIDEO_GLOBAL_PROMPT,
    DERIVED_CANDIDATE_PROMPT,
    DERIVED_GROUNDING_PROMPT,
    DERIVED_CAPTION_PROMPT,
)

PROMPT_REGISTRY = PromptRegistry()
for _prompt_spec in PROMPT_SPECS:
    PROMPT_REGISTRY.register(_prompt_spec)


def get_prompt(name: str) -> PromptSpec:
    return PROMPT_REGISTRY.get(name)


def list_prompts() -> tuple[PromptSpec, ...]:
    return tuple(PROMPT_REGISTRY.list_prompts())


def prompt_names() -> tuple[str, ...]:
    return tuple(prompt.name for prompt in PROMPT_REGISTRY.list_prompts())


__all__ = [
    "BOUNDARY_DETECTION_PROMPT",
    "CAPTION_GENERATION_PROMPT",
    "DERIVED_CANDIDATE_PROMPT",
    "DERIVED_CAPTION_PROMPT",
    "DERIVED_GROUNDING_PROMPT",
    "PROMPT_REGISTRY",
    "PROMPT_SPECS",
    "PromptRegistry",
    "PromptRenderError",
    "PromptSpec",
    "get_prompt",
    "list_prompts",
    "prompt_names",
    "VIDEO_GLOBAL_PROMPT",
    "PLANNER_PROMPT",
]

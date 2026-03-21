# -*- coding: utf-8 -*-
"""Prompt exports used by VideoAtlasAgent."""

from .canonical_prompts import (
    BOUNDARY_DETECTION_PROMPT,
    CAPTION_GENERATION_PROMPT,
    PLANNER_PROMPT,
    VIDEO_GLOBAL_PROMPT,
)
from .task_derivation_prompts import TASK_DERIVATION_PROMPT

__all__ = [
    "BOUNDARY_DETECTION_PROMPT",
    "CAPTION_GENERATION_PROMPT",
    "TASK_DERIVATION_PROMPT",
    "VIDEO_GLOBAL_PROMPT",
    "PLANNER_PROMPT",
]

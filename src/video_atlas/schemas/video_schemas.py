# -*- coding: utf-8 -*-
"""Backward-compatible schema exports."""

from .results import CreateVideoAtlasResult
from .strategy import (
    ALLOWED_EVIDENCE,
    ALLOWED_GENRES,
    ALLOWED_GRANULARITY,
    ALLOWED_STRUCTURE_MODES,
    CaptionSpec,
    DEFAULT_STRATEGY_PACKAGE,
    DESCRIPTION_SLOTS,
    SamplingConfig,
    SegmentSpec,
    VideoProcessSpec,
)
from .workspace import VideoGlobal, VideoSeg

__all__ = [
    "ALLOWED_EVIDENCE",
    "ALLOWED_GENRES",
    "ALLOWED_GRANULARITY",
    "ALLOWED_STRUCTURE_MODES",
    "CaptionSpec",
    "CreateVideoAtlasResult",
    "DEFAULT_STRATEGY_PACKAGE",
    "DESCRIPTION_SLOTS",
    "SamplingConfig",
    "SegmentSpec",
    "VideoGlobal",
    "VideoProcessSpec",
    "VideoSeg",
]

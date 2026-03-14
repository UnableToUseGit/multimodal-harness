# -*- coding: utf-8 -*-
"""Schemas used by VideoAtlasAgent."""

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
    "VideoGlobal",
    "VideoSeg",
    "SamplingConfig",
    "VideoProcessSpec",
    "SegmentSpec",
    "CaptionSpec",
    "DEFAULT_STRATEGY_PACKAGE",
    "ALLOWED_GENRES",
    "ALLOWED_STRUCTURE_MODES",
    "ALLOWED_GRANULARITY",
    "ALLOWED_EVIDENCE",
    "DESCRIPTION_SLOTS",
    "CreateVideoAtlasResult",
]

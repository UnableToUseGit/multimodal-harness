# -*- coding: utf-8 -*-
"""Backward-compatible schema exports."""

from .results import CreateVideoAtlasResult
from .segmentation_profiles import (
    ALLOWED_SAMPLING_PROFILES,
    ALLOWED_SEGMENTATION_PROFILES,
    DEFAULT_SEGMENTATION_PROFILE,
    SAMPLING_PROFILE_CONFIGS,
    SEGMENTATION_PROFILES,
    SegmentationProfile,
    resolve_sampling_profile,
    resolve_segmentation_profile,
)
from .strategy import (
    ALLOWED_EVIDENCE,
    ALLOWED_GENRES,
    ALLOWED_SIGNAL_PRIORITIES,
    BoundaryCandidate,
    BoundaryPostProcessSpec,
    CaptionSpec,
    DEFAULT_STRATEGY_PACKAGE,
    DetectionWindowSpec,
    DESCRIPTION_SLOTS,
    SamplingConfig,
    SegmentDraft,
    SegmentSpec,
    TitleSpec,
    VideoProcessSpec,
)
from .workspace import VideoGlobal, VideoSeg

__all__ = [
    "ALLOWED_EVIDENCE",
    "ALLOWED_GENRES",
    "ALLOWED_SIGNAL_PRIORITIES",
    "ALLOWED_SAMPLING_PROFILES",
    "ALLOWED_SEGMENTATION_PROFILES",
    "BoundaryCandidate",
    "BoundaryPostProcessSpec",
    "CaptionSpec",
    "CreateVideoAtlasResult",
    "DEFAULT_STRATEGY_PACKAGE",
    "DEFAULT_SEGMENTATION_PROFILE",
    "DetectionWindowSpec",
    "DESCRIPTION_SLOTS",
    "SAMPLING_PROFILE_CONFIGS",
    "SamplingConfig",
    "SegmentationProfile",
    "SEGMENTATION_PROFILES",
    "SegmentDraft",
    "SegmentSpec",
    "TitleSpec",
    "VideoGlobal",
    "VideoProcessSpec",
    "VideoSeg",
    "resolve_sampling_profile",
    "resolve_segmentation_profile",
]

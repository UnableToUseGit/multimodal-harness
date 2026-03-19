# -*- coding: utf-8 -*-
"""Schemas used by VideoAtlasAgent."""

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
from .task_derivation import (
    CanonicalAtlas,
    CanonicalSegment,
    CreateTaskDerivationResult,
    SegmentDerivationDecision,
    TaskDerivationPlan,
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
    "VideoGlobal",
    "VideoSeg",
    "SamplingConfig",
    "VideoProcessSpec",
    "SegmentSpec",
    "SegmentDraft",
    "CaptionSpec",
    "TitleSpec",
    "BoundaryCandidate",
    "BoundaryPostProcessSpec",
    "DetectionWindowSpec",
    "DEFAULT_STRATEGY_PACKAGE",
    "DEFAULT_SEGMENTATION_PROFILE",
    "ALLOWED_SAMPLING_PROFILES",
    "ALLOWED_GENRES",
    "ALLOWED_EVIDENCE",
    "ALLOWED_SIGNAL_PRIORITIES",
    "ALLOWED_SEGMENTATION_PROFILES",
    "DESCRIPTION_SLOTS",
    "SegmentationProfile",
    "SAMPLING_PROFILE_CONFIGS",
    "SEGMENTATION_PROFILES",
    "resolve_sampling_profile",
    "resolve_segmentation_profile",
    "CreateVideoAtlasResult",
    "CanonicalAtlas",
    "CanonicalSegment",
    "CreateTaskDerivationResult",
    "SegmentDerivationDecision",
    "TaskDerivationPlan",
]

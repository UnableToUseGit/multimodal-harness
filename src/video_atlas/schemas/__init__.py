# -*- coding: utf-8 -*-
"""Scheme exports used by VideoAtlas."""

from .canonical_registry import (
    ALLOWED_EVIDENCE,
    ALLOWED_GENRES,
    ALLOWED_SAMPLING_PROFILES,
    ALLOWED_SEGMENTATION_PROFILES,
    ALLOWED_SIGNAL_PRIORITIES,
    CAPTION_PROFILES,
    DEFAULT_CAPTION_PROFILE,
    DEFAULT_SEGMENTATION_PROFILE,
    SAMPLING_PROFILE_CONFIGS,
    SEGMENTATION_PROFILES,
    resolve_caption_profile,
    resolve_sampling_profile,
    resolve_segmentation_profile,
)
from .canonical_video_atlas import (
    CandidateBoundary,
    CaptionedSegment,
    CanonicalExecutionPlan,
    CaptionProfile,
    CaptionSpecification,
    FrameSamplingProfile,
    FinalizedSegment,
    SamplingConfig,
    SegmentationProfile,
    SegmentationSpecification,
)
from .task_derivation import (
    CanonicalAtlas,
    CanonicalSegment,
    CreateTaskDerivationResult,
    SegmentDerivationDecision,
    TaskDerivationPlan,
)
from .results import CreateVideoAtlasResult
from .workspace import VideoGlobal, VideoSeg

__all__ = [
    "ALLOWED_EVIDENCE",
    "ALLOWED_GENRES",
    "ALLOWED_SAMPLING_PROFILES",
    "ALLOWED_SEGMENTATION_PROFILES",
    "ALLOWED_SIGNAL_PRIORITIES",
    "CAPTION_PROFILES",
    "CandidateBoundary",
    "CaptionedSegment",
    "CanonicalExecutionPlan",
    "CanonicalAtlas",
    "CanonicalSegment",
    "CaptionProfile",
    "CaptionSpecification",
    "CreateTaskDerivationResult",
    "CreateVideoAtlasResult",
    "DEFAULT_CAPTION_PROFILE",
    "DEFAULT_SEGMENTATION_PROFILE",
    "FrameSamplingProfile",
    "FinalizedSegment",
    "SAMPLING_PROFILE_CONFIGS",
    "SEGMENTATION_PROFILES",
    "SamplingConfig",
    "SegmentDerivationDecision",
    "SegmentationProfile",
    "SegmentationSpecification",
    "TaskDerivationPlan",
    "VideoGlobal",
    "VideoSeg",
    "resolve_caption_profile",
    "resolve_sampling_profile",
    "resolve_segmentation_profile",
]

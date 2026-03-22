"""Canonical VideoAtlas dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class FrameSamplingProfile:
    fps: float = 0.5
    max_resolution: int = 480


SamplingConfig = FrameSamplingProfile


@dataclass(frozen=True)
class SegmentationProfile:
    signal_priority: str
    target_segment_length_sec: tuple[int, int]
    default_sampling_profile: str
    boundary_evidence_primary: tuple[str, ...]
    boundary_evidence_secondary: tuple[str, ...]
    segmentation_policy: str


@dataclass(frozen=True)
class CaptionProfile:
    caption_policy: str
    title_policy: str


def _default_segmentation_profile_name() -> str:
    from .canonical_registry import DEFAULT_SEGMENTATION_PROFILE

    return DEFAULT_SEGMENTATION_PROFILE


def _default_segmentation_profile() -> SegmentationProfile:
    from .canonical_registry import DEFAULT_SEGMENTATION_PROFILE, SEGMENTATION_PROFILES

    return SEGMENTATION_PROFILES[DEFAULT_SEGMENTATION_PROFILE]


def _default_caption_profile_name() -> str:
    from .canonical_registry import DEFAULT_CAPTION_PROFILE

    return DEFAULT_CAPTION_PROFILE


def _default_caption_profile() -> CaptionProfile:
    from .canonical_registry import CAPTION_PROFILES, DEFAULT_CAPTION_PROFILE

    return CAPTION_PROFILES[DEFAULT_CAPTION_PROFILE]


@dataclass
class SegmentationSpecification:
    profile_name: str = field(default_factory=_default_segmentation_profile_name)
    profile: SegmentationProfile = field(default_factory=_default_segmentation_profile)
    frame_sampling_profile: FrameSamplingProfile = field(default_factory=FrameSamplingProfile)


@dataclass
class CaptionSpecification:
    profile_name: str = field(default_factory=_default_caption_profile_name)
    profile: CaptionProfile = field(default_factory=_default_caption_profile)
    frame_sampling_profile: FrameSamplingProfile = field(default_factory=FrameSamplingProfile)


@dataclass
class CanonicalExecutionPlan:
    planner_confidence: float = 0.25
    genre_distribution: dict[str, float] = field(default_factory=lambda: {"other": 1.0})
    segmentation_specification: SegmentationSpecification = field(default_factory=SegmentationSpecification)
    caption_specification: CaptionSpecification = field(default_factory=CaptionSpecification)
    chunk_size_sec: int = 600
    chunk_overlap_sec: int = 20


@dataclass
class CandidateBoundary:
    timestamp: float
    boundary_rationale: str = ""
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class FinalizedSegment:
    start_time: float
    end_time: float
    boundary_rationale: str = ""
    boundary_confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    refinement_needed: bool = False


@dataclass
class CaptionedSegment:
    seg_id: str
    start_time: float
    end_time: float
    summary: str
    detail: str
    subtitles_text: str = ""
    token_usage: int = 0


@dataclass
class AtlasSegment:
    segment_id: str
    title: str
    start_time: float
    end_time: float
    summary: str
    caption: str
    folder_name: str
    readme_path: Path | None = None
    clip_path: Path | None = None
    subtitles_path: Path | None = None

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


@dataclass
class CanonicalAtlas:
    title: str
    abstract: str
    segments: list[AtlasSegment]
    root_path: Path
    readme_text: str = ""
    source_video_path: Path | None = None
    normalized_audio_path: Path | None = None
    execution_plan_path: Path | None = None

"""Strategy and generation configuration models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .segmentation_profiles import DEFAULT_SEGMENTATION_PROFILE


@dataclass
class SamplingConfig:
    fps: float = 0.5
    max_resolution: int = 480
    use_subtitles: bool = True


@dataclass
class SegmentSpec:
    segmentation_profile: str = DEFAULT_SEGMENTATION_PROFILE
    genre_str: str = ""
    signal_priority: str = "balanced"
    boundary_evidence_primary: str = ""
    boundary_evidence_secondary: str = ""
    segmentation_policy: str = ""


@dataclass
class CaptionSpec:
    genre_str: str = ""
    segmentation_profile: str = DEFAULT_SEGMENTATION_PROFILE
    signal_priority: str = "balanced"
    slots_weight: str = ""
    notes: str = ""


@dataclass
class TitleSpec:
    segmentation_profile: str = DEFAULT_SEGMENTATION_PROFILE
    genre_str: str = ""
    title_policy: str = ""
    notes: str = ""


@dataclass
class DetectionWindowSpec:
    chunk_size_sec: int = 600
    chunk_overlap_sec: int = 20


@dataclass
class BoundaryPostProcessSpec:
    target_segment_length_sec: list[int] = field(default_factory=lambda: [90, 480])
    min_boundary_confidence: float = 0.35
    merge_short_segment_below_sec: int = 30


@dataclass
class BoundaryCandidate:
    timestamp: float
    boundary_rationale: str = ""
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0
    title_hint: str = ""


@dataclass
class SegmentDraft:
    start_time: float
    end_time: float
    title_hint: str = ""
    boundary_rationale: str = ""
    boundary_confidence: float = 0.0
    evidence: list[str] = field(default_factory=list)
    refinement_needed: bool = False


@dataclass
class VideoProcessSpec:
    segment_spec: SegmentSpec
    title_spec: TitleSpec
    caption_spec: CaptionSpec
    detection_window_spec: DetectionWindowSpec
    boundary_postprocess_spec: BoundaryPostProcessSpec
    segmentation_sampling: SamplingConfig
    description_sampling: SamplingConfig
    normalized_strategy: dict[str, Any]


DEFAULT_STRATEGY_PACKAGE: dict[str, Any] = {
    "planner_confidence": 0.25,
    "genre_distribution": {"other": 1.0},
    "segmentation_profile": DEFAULT_SEGMENTATION_PROFILE,
    "segmentation": {
        "sampling_profile": "balanced",
        "policy_notes": "",
    },
    "title": {
        "notes": (
            "Generate stable canonical titles that name the segment's dominant phase, topic, or event. "
            "Prefer navigational labels over highlight-style headlines."
        ),
    },
    "description": {
        "slots_weight": {
            "cast_speaker": 0.18,
            "setting": 0.12,
            "core_events": 0.22,
            "topic_claims": 0.22,
            "outcome_progress": 0.18,
            "notable_cues": 0.08,
        },
        "sampling_profile": "balanced",
        "notes": (
            "Use a stable slot-based description. Prioritize who/where/what plus the main topic or key events. "
            "Do not narrate frame-by-frame; produce concise, segment-level summaries."
        ),
    },
}


ALLOWED_GENRES = {
    "narrative_film",
    "animation",
    "vlog_lifestyle",
    "podcast_interview",
    "lecture_talk",
    "tutorial_howto",
    "news_report",
    "documentary",
    "gameplay",
    "compilation_montage",
    "sports_event",
    "other",
}

ALLOWED_EVIDENCE = {
    "topic_shift_in_subtitles",
    "speaker_change",
    "scene_location_change",
    "shot_style_change",
    "on_screen_text_title_change",
    "music_or_audio_pattern_change",
    "step_transition",
    "time_jump_or_recap",
    "other",
}

ALLOWED_SIGNAL_PRIORITIES = {"visual", "language", "balanced"}

DESCRIPTION_SLOTS = [
    "cast_speaker",
    "setting",
    "core_events",
    "topic_claims",
    "outcome_progress",
    "notable_cues",
]

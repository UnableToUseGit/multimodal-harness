"""Strategy and generation configuration models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SamplingConfig:
    fps: float = 0.5
    max_resolution: int = 480
    use_subtitles: bool = True


@dataclass
class SegmentSpec:
    genre_str: str = ""
    mode_str: str = ""
    signal_audio_priority: str = "0.50"
    signal_visual_priority: str = "0.50"
    target_segment_length_sec: str = "[90, 480]"
    boundary_evidence_primary: str = ""
    boundary_evidence_secondary: str = ""


@dataclass
class CaptionSpec:
    genre_str: str = ""
    mode_str: str = ""
    signal_audio_priority: str = "0.50"
    signal_visual_priority: str = "0.50"
    slots_weight: str = ""
    notes: str = ""


@dataclass
class VideoProcessSpec:
    segment_spec: SegmentSpec
    caption_spec: CaptionSpec
    segmentation_sampling: SamplingConfig
    description_sampling: SamplingConfig
    normalized_strategy: dict[str, Any]


DEFAULT_STRATEGY_PACKAGE: dict[str, Any] = {
    "planner_confidence": 0.25,
    "genre_distribution": {"other": 0.6, "vlog_lifestyle": 0.2, "podcast_interview": 0.2},
    "structure_mode": {"primary": "other", "secondary": []},
    "signal_priority": {
        "audio_text": 0.6,
        "visual": 0.4,
        "rationale": "Probe unavailable; use a conservative hybrid strategy relying slightly more on subtitles/audio-text.",
    },
    "segmentation": {
        "granularity": "hybrid",
        "target_segment_length_sec": [90, 480],
        "boundary_evidence_primary": ["topic_shift_in_subtitles", "scene_location_change"],
        "boundary_evidence_secondary": ["speaker_change", "on_screen_text_title_change"],
        "sampling": {"fps": 0.5, "max_resolution": 384, "use_subtitles": True},
        "notes": (
            "Conservative segmentation: prefer fewer, self-contained segments. "
            "Avoid cutting on minor shot changes or filler. Only cut when there is clear topic/scene change."
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
        "sampling": {"fps": 0.2, "max_resolution": 384, "use_subtitles": True},
        "notes": (
            "Use a stable slot-based description. Prioritize who/where/what + main topic or key events. "
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

ALLOWED_STRUCTURE_MODES = {
    "turn_taking_qa",
    "lecture_slide_driven",
    "narrative_scene_based",
    "chronological_vlog",
    "step_by_step_procedure",
    "news_segmented",
    "compilation_blocks",
    "sports_play_by_play",
    "other",
}

ALLOWED_GRANULARITY = {"scene", "topic_block", "step_block", "hybrid"}

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

DESCRIPTION_SLOTS = [
    "cast_speaker",
    "setting",
    "core_events",
    "topic_claims",
    "outcome_progress",
    "notable_cues",
]

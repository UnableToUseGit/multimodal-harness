"""Derived VideoAtlas dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .canonical_atlas import AtlasSegment


@dataclass(frozen=True)
class DerivationPolicy:
    intent: str
    grounding_instruction: str


@dataclass
class DerivationResultInfo:
    derived_atlas_segment_count: int = 0
    derivation_reason: dict[str, DerivationPolicy] = field(default_factory=dict)
    derivation_source: dict[str, str] = field(default_factory=dict)


@dataclass
class DerivedSegmentDraft:
    derived_segment_id: str
    source_segment_id: str
    policy: DerivationPolicy
    start_time: float
    end_time: float
    title: str
    summary: str
    caption: str
    subtitles_text: str


@dataclass
class DerivedAtlas:
    task_request: str
    global_summary: str
    detailed_breakdown: str
    segments: list[AtlasSegment]
    derivation_result_info: DerivationResultInfo
    atlas_dir: Path
    source_canonical_atlas_dir: Path
    source_video_path: Path

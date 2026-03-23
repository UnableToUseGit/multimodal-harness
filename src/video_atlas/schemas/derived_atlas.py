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
class DerivedAtlas:
    global_summary: str
    detailed_breakdown: str
    segments: list[AtlasSegment]
    root_path: Path
    readme_text: str
    source_canonical_atlas_path: Path

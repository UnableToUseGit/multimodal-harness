"""Result objects returned from top-level workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .canonical_atlas import CanonicalExecutionPlan, SamplingConfig


@dataclass
class CreateVideoAtlasResult:
    success: bool = True
    segment_num: int = 0
    specification: CanonicalExecutionPlan = field(default_factory=CanonicalExecutionPlan)
    segmentation_sampling: SamplingConfig = field(default_factory=SamplingConfig)
    description_sampling: SamplingConfig = field(default_factory=SamplingConfig)


@dataclass
class CreateDerivedAtlasResult:
    success: bool = True
    task_request: str = ""
    source_segment_count: int = 0
    derived_segment_count: int = 0
    output_root_path: Path | None = None

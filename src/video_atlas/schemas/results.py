"""Result objects returned from top-level workflows."""

from __future__ import annotations

from dataclasses import dataclass, field

from .canonical_atlas import CanonicalExecutionPlan, SamplingConfig


@dataclass
class CreateVideoAtlasResult:
    success: bool = True
    segment_num: int = 0
    specification: CanonicalExecutionPlan = field(default_factory=CanonicalExecutionPlan)
    segmentation_sampling: SamplingConfig = field(default_factory=SamplingConfig)
    description_sampling: SamplingConfig = field(default_factory=SamplingConfig)

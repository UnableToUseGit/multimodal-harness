"""Result objects returned from top-level workflows."""

from __future__ import annotations

from dataclasses import dataclass, field

from .strategy import CaptionSpec, SamplingConfig, SegmentSpec


@dataclass
class CreateVideoAtlasResult:
    success: bool = True
    segment_num: int = 0
    segmentation_sampling: SamplingConfig = field(default_factory=SamplingConfig)
    description_sampling: SamplingConfig = field(default_factory=SamplingConfig)
    segment_spec: SegmentSpec = field(default_factory=SegmentSpec)
    caption_spec: CaptionSpec = field(default_factory=CaptionSpec)

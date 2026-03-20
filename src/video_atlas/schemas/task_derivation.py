"""Schemas for task-aware atlas derivation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CanonicalSegment:
    source_segment_id: str
    source_folder: str
    seg_title: str
    summary: str
    detail: str
    start_time: float
    end_time: float
    duration: float
    readme_path: Path
    subtitles_path: Path | None = None
    clip_path: Path | None = None


@dataclass
class CanonicalAtlas:
    root_path: Path
    root_readme: str
    source_video_path: Path | None
    execution_plan_path: Path | None
    segments: list[CanonicalSegment] = field(default_factory=list)


@dataclass
class SegmentDerivationDecision:
    source_segment_id: str
    source_folder: str
    relevance_score: float
    action: str
    derived_title: str
    derived_summary: str
    order: int
    rationale: str


@dataclass
class TaskDerivationPlan:
    task_title: str
    task_abstract: str
    selection_strategy: str
    derived_segments: list[SegmentDerivationDecision] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_title": self.task_title,
            "task_abstract": self.task_abstract,
            "selection_strategy": self.selection_strategy,
            "derived_segments": [asdict(item) for item in self.derived_segments],
        }


@dataclass
class CreateTaskDerivationResult:
    success: bool = True
    derived_segment_num: int = 0
    task_title: str = ""
    source_workspace: str = ""
    task_description: str = ""

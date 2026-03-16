from __future__ import annotations

import json
import shutil
from pathlib import Path

from ...schemas import CanonicalAtlas, CanonicalSegment, SegmentDerivationDecision, TaskDerivationPlan


def _slugify(title: str) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in title.strip())
    safe = "_".join([part for part in safe.split("_") if part])
    return safe[:80] or "segment"


class TaskDerivationWriterMixin:
    def _workspace_root(self) -> Path:
        return Path(self.workspace.root_path)

    def _write_workspace_text(self, relative_path: str | Path, content: str) -> None:
        target_path = self._workspace_root() / Path(relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")

    def _copy_if_exists(self, source_path: Path | None, relative_path: str | Path) -> None:
        if source_path is None or not source_path.exists():
            return
        target_path = self._workspace_root() / Path(relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)

    def _build_task_readme(self, plan: TaskDerivationPlan, task_description: str, kept_segments: list[tuple[SegmentDerivationDecision, CanonicalSegment]]) -> str:
        quickview = "\n".join(
            [
                f'- task_seg_{index:04d}: {segment.start_time:.1f} - {segment.end_time:.1f} seconds: {decision.derived_summary}'
                for index, (decision, segment) in enumerate(kept_segments, start=1)
            ]
        )
        return "\n".join(
            [
                f"# {plan.task_title or 'Task-Aware Video Atlas'}",
                "",
                f"**Task Description**: {task_description}",
                "",
                f"**Abstract**: {plan.task_abstract}",
                "",
                f"**Segments**: {len(kept_segments)}",
                "",
                "## Quickview",
                quickview or "- No derived segments.",
            ]
        )

    def _build_task_segment_readme(self, index: int, decision: SegmentDerivationDecision, segment: CanonicalSegment) -> str:
        return "\n".join(
            [
                "# Task Segment",
                "",
                f"**TaskSegID**: task_seg_{index:04d}",
                f"**SourceSegID**: {segment.source_segment_id}",
                f"**Start Time**: {segment.start_time}",
                f"**End Time**: {segment.end_time}",
                f"**Duration**: {segment.duration}",
                f"**Title**: {decision.derived_title}",
                f"**Summary**: {decision.derived_summary}",
                f"**Task Rationale**: {decision.rationale}",
                "",
                "## Source Context",
                f"**Original Title**: {segment.seg_title}",
                f"**Original Summary**: {segment.summary}",
                f"**Original Detail**: {segment.detail}",
                "",
                "# Additional Files",
                "- Source map: `./SOURCE_MAP.json`",
                "- Raw video clip for this segment: `./video_clip.mp4`",
                "- Subtitles for this segment: `./SUBTITLES.md`",
            ]
        )

    def _write_task_workspace(self, atlas: CanonicalAtlas, plan: TaskDerivationPlan, task_description: str) -> None:
        kept_decisions = [item for item in plan.derived_segments if item.action == "keep"]
        kept_decisions.sort(key=lambda item: item.order)
        segments_by_id = {segment.source_segment_id: segment for segment in atlas.segments}
        kept_segments = [(decision, segments_by_id[decision.source_segment_id]) for decision in kept_decisions if decision.source_segment_id in segments_by_id]

        self._write_workspace_text("README.md", self._build_task_readme(plan, task_description, kept_segments))
        self._write_workspace_text(
            "TASK.md",
            "\n".join(
                [
                    "# Task Derivation",
                    "",
                    f"**Task Description**: {task_description}",
                    "",
                    f"**Selection Strategy**: {plan.selection_strategy}",
                    "",
                    f"**Source Workspace**: {atlas.root_path}",
                ]
            ),
        )
        self._write_workspace_text("derivation.json", json.dumps(plan.to_dict(), indent=2))
        if atlas.source_video_path is not None:
            self._copy_if_exists(atlas.source_video_path, atlas.source_video_path.name)

        for index, (decision, segment) in enumerate(kept_segments, start=1):
            folder_name = f"task_seg_{index:04d}-{_slugify(decision.derived_title)}"
            segment_dir = Path("segments") / folder_name
            self._write_workspace_text(segment_dir / "README.md", self._build_task_segment_readme(index, decision, segment))
            self._write_workspace_text(
                segment_dir / "SOURCE_MAP.json",
                json.dumps(
                    {
                        "task_segment_id": f"task_seg_{index:04d}",
                        "source_workspace": str(atlas.root_path),
                        "source_segment_ids": [segment.source_segment_id],
                        "source_folders": [segment.source_folder],
                        "source_time_ranges": [{"start_time": segment.start_time, "end_time": segment.end_time}],
                        "action": decision.action,
                        "rationale": decision.rationale,
                    },
                    indent=2,
                ),
            )
            self._copy_if_exists(segment.clip_path, segment_dir / "video_clip.mp4")
            self._copy_if_exists(segment.subtitles_path, segment_dir / "SUBTITLES.md")

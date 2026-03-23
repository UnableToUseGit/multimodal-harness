from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
import json
import re
from pathlib import Path

from ...schemas import (
    AtlasSegment,
    CreateDerivedAtlasResult,
    DerivationPolicy,
    DerivationResultInfo,
    DerivedAtlas,
)


class DerivedPipelineMixin:
    def _candidate_prompt(self, task_request: str, canonical_atlas) -> str:
        segments = "\n".join(
            [
                f"- {segment.segment_id}: {segment.start_time:.1f}-{segment.end_time:.1f}s | "
                f"title={segment.title} | summary={segment.summary} | detail={segment.caption}"
                for segment in canonical_atlas.segments
            ]
        )
        return (
            "Select the canonical segments relevant to the task. "
            "Return JSON with a `candidates` array. Each candidate must include "
            "`segment_id`, `intent`, and `grounding_instruction`.\n\n"
            f"Task Request:\n{task_request}\n\nCanonical Segments:\n{segments}"
        )

    def _grounding_prompt(self, segment: AtlasSegment, policy: DerivationPolicy) -> str:
        return (
            "Refine a task-aware sub-clip. Return JSON with `start_time` and `end_time`. "
            "Use absolute times if confident, otherwise use offsets relative to the source segment start.\n\n"
            f"Source Segment ID: {segment.segment_id}\n"
            f"Source Segment Range: {segment.start_time:.1f}-{segment.end_time:.1f}\n"
            f"Intent: {policy.intent}\n"
            f"Grounding Instruction: {policy.grounding_instruction}\n"
            f"Summary: {segment.summary}\n"
            f"Detail: {segment.caption}"
        )

    def _caption_prompt(
        self,
        task_request: str,
        segment: AtlasSegment,
        policy: DerivationPolicy,
        start_time: float,
        end_time: float,
        subtitles_text: str,
    ) -> str:
        return (
            "Write metadata for a derived atlas segment. "
            "Return JSON with `title`, `summary`, and `caption`.\n\n"
            f"Task Request: {task_request}\n"
            f"Source Segment ID: {segment.segment_id}\n"
            f"Derived Range: {start_time:.1f}-{end_time:.1f}\n"
            f"Intent: {policy.intent}\n"
            f"Grounding Instruction: {policy.grounding_instruction}\n"
            f"Source Summary: {segment.summary}\n"
            f"Source Detail: {segment.caption}\n"
            f"Subtitles:\n{subtitles_text}"
        )

    def _load_subtitles_text(self, segment: AtlasSegment) -> str:
        if segment.subtitles_path is None or not segment.subtitles_path.exists():
            return ""
        return segment.subtitles_path.read_text(encoding="utf-8")

    def _prune_subtitles_text(self, subtitles_text: str, start_time: float, end_time: float) -> str:
        if not subtitles_text.strip():
            return ""

        kept_blocks: list[str] = []
        pattern = re.compile(
            r"Start Time:\s*(?P<start>[0-9.]+)\s*-->\s*End Time:\s*(?P<end>[0-9.]+)\s*Subtitle:\s*(?P<text>.*)",
            flags=re.DOTALL,
        )
        for block in [item.strip() for item in subtitles_text.split("\n\n") if item.strip()]:
            match = pattern.fullmatch(block)
            if match is None:
                continue
            item_start = float(match.group("start"))
            item_end = float(match.group("end"))
            if item_start >= start_time and item_end <= end_time:
                kept_blocks.append(block)
        return "\n\n".join(kept_blocks)

    def _resolve_refined_times(self, segment: AtlasSegment, response: dict) -> tuple[float, float] | None:
        raw_start = float(response.get("start_time", segment.start_time))
        raw_end = float(response.get("end_time", segment.end_time))
        if raw_end <= raw_start:
            return None

        if segment.start_time <= raw_start < raw_end <= segment.end_time:
            start_time = raw_start
            end_time = raw_end
        else:
            start_time = segment.start_time + raw_start
            end_time = segment.start_time + raw_end

        start_time = max(segment.start_time, start_time)
        end_time = min(segment.end_time, end_time)
        if end_time <= start_time:
            return None
        return start_time, end_time

    def _next_derived_segment_id(self, index: int) -> str:
        return f"derived_seg_{index:04d}"

    def _segment_readme_text(
        self,
        derived_segment_id: str,
        source_segment_id: str,
        title: str,
        summary: str,
        caption: str,
        intent: str,
        start_time: float,
        end_time: float,
    ) -> str:
        duration = end_time - start_time
        return "\n".join(
            [
                "# Derived Segment",
                "",
                f"**DerivedSegID**: {derived_segment_id}",
                f"**SourceSegID**: {source_segment_id}",
                f"**Start Time**: {start_time:.1f}",
                f"**End Time**: {end_time:.1f}",
                f"**Duration**: {duration:.1f}",
                f"**Title**: {title}",
                f"**Summary**: {summary}",
                f"**Detail Description**: {caption}",
                f"**Intent**: {intent}",
                "",
                "# Additional Files",
                "- Raw video for this segment: `./video_clip.mp4`",
                "- Subtitles for this segment: `./SUBTITLES.md`",
            ]
        )

    def _root_readme_text(self, task_request: str, global_summary: str, detailed_breakdown: str) -> str:
        return "\n".join(
            [
                "# Derived Atlas",
                "",
                "## Task Request",
                task_request,
                "",
                "## Global Summary",
                global_summary,
                "",
                "## Detailed Breakdown",
                detailed_breakdown,
            ]
        )

    def _derive_one_segment(self, item: tuple[int, AtlasSegment, DerivationPolicy], task_request: str, source_video_path: str) -> dict | None:
        index, segment, policy = item
        grounding_output = self.segmentor.generate_single(
            messages=self._prepare_messages(
                system_prompt="You refine task-aware clip boundaries.",
                user_prompt=self._grounding_prompt(segment, policy),
            )
        )
        grounded = self.parse_response(grounding_output["text"])
        resolved = self._resolve_refined_times(segment, grounded if isinstance(grounded, dict) else {})
        if resolved is None:
            return None
        start_time, end_time = resolved

        pruned_subtitles = self._prune_subtitles_text(self._load_subtitles_text(segment), start_time, end_time)
        caption_output = self.captioner.generate_single(
            messages=self._prepare_messages(
                system_prompt="You write metadata for a derived atlas segment.",
                user_prompt=self._caption_prompt(task_request, segment, policy, start_time, end_time, pruned_subtitles),
            )
        )
        caption_data = self.parse_response(caption_output["text"])
        if not isinstance(caption_data, dict):
            caption_data = {}

        derived_segment_id = self._next_derived_segment_id(index)
        title = str(caption_data.get("title", f"Derived Segment {index}"))
        summary = str(caption_data.get("summary", segment.summary))
        caption = str(caption_data.get("caption", segment.caption))
        folder_name = (
            f"{derived_segment_id.replace('_', '-')}-"
            f"{self._slugify_segment_title(title)}-{start_time:.2f}-{end_time:.2f}s"
        )
        segment_dir = Path("segments") / folder_name
        clip_relative_path = segment_dir / "video_clip.mp4"
        self._extract_clip(source_video_path, start_time, end_time, clip_relative_path)

        self._write_workspace_text(
            segment_dir / "README.md",
            self._segment_readme_text(
                derived_segment_id=derived_segment_id,
                source_segment_id=segment.segment_id,
                title=title,
                summary=summary,
                caption=caption,
                intent=policy.intent,
                start_time=start_time,
                end_time=end_time,
            ),
        )
        if pruned_subtitles:
            self._write_workspace_text(segment_dir / "SUBTITLES.md", pruned_subtitles)
        self._write_workspace_text(
            segment_dir / "SOURCE_MAP.json",
            json.dumps(
                {
                    "source_segment_id": segment.segment_id,
                    "derivation_policy": asdict(policy),
                },
                ensure_ascii=False,
                indent=2,
            ),
        )

        return {
            "segment": AtlasSegment(
                segment_id=derived_segment_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                summary=summary,
                caption=caption,
                folder_name=folder_name,
                readme_path=(self._workspace_root() / segment_dir / "README.md").resolve(),
                clip_path=(self._workspace_root() / clip_relative_path).resolve(),
                subtitles_path=((self._workspace_root() / segment_dir / "SUBTITLES.md").resolve() if pruned_subtitles else None),
            ),
            "policy": policy,
            "source_segment_id": segment.segment_id,
        }

    def _aggregate_derived_atlas(
        self,
        task_request: str,
        canonical_atlas,
        derived_segments: list[AtlasSegment],
        result_info: DerivationResultInfo,
    ) -> DerivedAtlas:
        total_duration = sum(segment.duration for segment in derived_segments)
        average_duration = total_duration / len(derived_segments) if derived_segments else 0.0
        global_summary = (
            f"Derived {len(derived_segments)} segments for the task. "
            f"Total duration is {total_duration:.1f} seconds and average duration is {average_duration:.1f} seconds."
        )
        detailed_breakdown = "\n".join(
            [
                f"- {segment.segment_id}: {segment.title} | "
                f"intent={result_info.derivation_reason.get(segment.segment_id).intent if result_info.derivation_reason.get(segment.segment_id) else ''} | "
                f"range={segment.start_time:.1f}-{segment.end_time:.1f}"
                for segment in derived_segments
            ]
        )
        return DerivedAtlas(
            global_summary=global_summary,
            detailed_breakdown=detailed_breakdown,
            segments=derived_segments,
            root_path=self._workspace_root(),
            readme_text=self._root_readme_text(task_request, global_summary, detailed_breakdown),
            source_canonical_atlas_path=canonical_atlas.root_path,
        )

    def _write_derived_workspace(self, task_request: str, derived_atlas: DerivedAtlas, result_info: DerivationResultInfo) -> None:
        self._write_workspace_text("README.md", derived_atlas.readme_text)
        self._write_workspace_text("TASK.md", task_request)
        self._write_workspace_text(
            "derivation.json",
            json.dumps(
                {
                    "task_request": task_request,
                    "global_summary": derived_atlas.global_summary,
                    "detailed_breakdown": derived_atlas.detailed_breakdown,
                    "derived_segment_count": len(derived_atlas.segments),
                    "source_canonical_atlas_path": str(derived_atlas.source_canonical_atlas_path),
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
        self._write_workspace_text(
            ".agentignore/DERIVATION_RESULT.json",
            json.dumps(asdict(result_info), ensure_ascii=False, indent=2),
        )

    def add(self, task_request: str, canonical_atlas, verbose: bool = False) -> CreateDerivedAtlasResult:
        del verbose
        planner_output = self.planner.generate_single(
            messages=self._prepare_messages(
                system_prompt="You select source segments for task-aware derivation.",
                user_prompt=self._candidate_prompt(task_request, canonical_atlas),
            )
        )
        planner_data = self.parse_response(planner_output["text"])
        candidates = planner_data.get("candidates", []) if isinstance(planner_data, dict) else []
        segment_map = {segment.segment_id: segment for segment in canonical_atlas.segments}
        work_items: list[tuple[int, AtlasSegment, DerivationPolicy]] = []
        for index, candidate in enumerate(candidates, start=1):
            if not isinstance(candidate, dict):
                continue
            segment_id = str(candidate.get("segment_id", "")).strip()
            segment = segment_map.get(segment_id)
            if segment is None:
                continue
            work_items.append(
                (
                    index,
                    segment,
                    DerivationPolicy(
                        intent=str(candidate.get("intent", "")).strip(),
                        grounding_instruction=str(candidate.get("grounding_instruction", "")).strip(),
                    ),
                )
            )

        if canonical_atlas.source_video_path is None:
            raise ValueError("Canonical atlas source_video_path is required for derived clip extraction")

        if self.num_workers > 1 and len(work_items) > 1:
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                raw_results = list(
                    executor.map(
                        lambda item: self._derive_one_segment(item, task_request, str(canonical_atlas.source_video_path)),
                        work_items,
                    )
                )
        else:
            raw_results = [
                self._derive_one_segment(item, task_request, str(canonical_atlas.source_video_path))
                for item in work_items
            ]

        derived_segments: list[AtlasSegment] = []
        result_info = DerivationResultInfo()
        for result in raw_results:
            if result is None:
                continue
            segment = result["segment"]
            derived_segments.append(segment)
            result_info.derivation_reason[segment.segment_id] = result["policy"]
            result_info.derivation_source[segment.segment_id] = result["source_segment_id"]
        result_info.derived_atlas_segment_count = len(derived_segments)

        derived_atlas = self._aggregate_derived_atlas(task_request, canonical_atlas, derived_segments, result_info)
        self._write_derived_workspace(task_request, derived_atlas, result_info)
        return CreateDerivedAtlasResult(
            success=True,
            task_request=task_request,
            source_segment_count=len(canonical_atlas.segments),
            derived_segment_count=len(derived_segments),
            output_root_path=self._workspace_root(),
        )

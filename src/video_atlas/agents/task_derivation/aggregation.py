from __future__ import annotations

from ...schemas import AtlasSegment, DerivationResultInfo, DerivedAtlas


class AggregationMixin:
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

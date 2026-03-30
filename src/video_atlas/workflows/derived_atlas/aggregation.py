from __future__ import annotations

from pathlib import Path

from ...persistence import format_hms_time_range, slugify_segment_title
from ...schemas import AtlasSegment, DerivedAtlas, DerivedSegmentDraft, DerivationResultInfo


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
        derived_segment_drafts: list[DerivedSegmentDraft],
        output_dir: Path,
    ) -> DerivedAtlas:
        derivation_result_info = DerivationResultInfo(
            derived_atlas_segment_count=len(derived_segment_drafts),
            derivation_reason={
                draft.derived_segment_id: draft.policy for draft in derived_segment_drafts
            },
            derivation_source={
                draft.derived_segment_id: draft.source_segment_id for draft in derived_segment_drafts
            },
        )
        derived_segments = [
            AtlasSegment(
                segment_id=draft.derived_segment_id,
                title=draft.title,
                start_time=draft.start_time,
                end_time=draft.end_time,
                summary=draft.summary,
                caption=draft.caption,
                subtitles_text=draft.subtitles_text,
                folder_name=(
                    f"{draft.derived_segment_id.replace('_', '-')}-"
                    f"{slugify_segment_title(draft.title)}-{format_hms_time_range(draft.start_time, draft.end_time)}"
                ),
            )
            for draft in derived_segment_drafts
        ]

        total_duration = sum(segment.duration for segment in derived_segments)
        average_duration = total_duration / len(derived_segments) if derived_segments else 0.0
        global_summary = (
            f"Derived {len(derived_segments)} segments for the task. "
            f"Total duration is {total_duration:.1f} seconds and average duration is {average_duration:.1f} seconds."
        )
        detailed_breakdown = "\n".join(
            [
                f"- {segment.segment_id}: {segment.title} | "
                f"intent={draft.policy.intent} | "
                f"range={segment.start_time:.1f}-{segment.end_time:.1f}"
                for segment, draft in zip(derived_segments, derived_segment_drafts)
            ]
        )
        return DerivedAtlas(
            task_request=task_request,
            global_summary=global_summary,
            detailed_breakdown=detailed_breakdown,
            segments=derived_segments,
            derivation_result_info=derivation_result_info,
            atlas_dir=output_dir,
            source_canonical_atlas_dir=canonical_atlas.atlas_dir,
            source_video_path=canonical_atlas.atlas_dir / canonical_atlas.relative_video_path,
        )

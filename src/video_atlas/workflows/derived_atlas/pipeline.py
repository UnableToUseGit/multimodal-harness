from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ...persistence import DerivedAtlasWriter
from ...schemas import CreateDerivedAtlasResult, DerivationResultInfo, CanonicalAtlas

class DerivedPipelineMixin:
    def create(self, task_request: str, canonical_atlas: CanonicalAtlas, verbose: bool = False) -> CreateDerivedAtlasResult:
        del verbose
        work_items = self._build_candidate_work_items(task_request, canonical_atlas)

        video_path = canonical_atlas.atlas_dir / canonical_atlas.relative_video_path
        if self.num_workers > 1 and len(work_items) > 1:
            with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                raw_results = list(
                    executor.map(
                        lambda item: self._derive_one_segment(item, task_request, video_path),
                        work_items,
                    )
                )
        else:
            raw_results = [
                self._derive_one_segment(item, task_request, video_path)
                for item in work_items
            ]

        derived_segments = []
        result_info = DerivationResultInfo()
        segment_artifacts: dict[str, dict[str, str]] = {}
        for result in raw_results:
            if result is None:
                continue
            segment = result["segment"]
            derived_segments.append(segment)
            result_info.derivation_reason[segment.segment_id] = result["policy"]
            result_info.derivation_source[segment.segment_id] = result["source_segment_id"]
            segment_artifacts[segment.segment_id] = {"subtitles_text": result.get("subtitles_text", "")}
        result_info.derived_atlas_segment_count = len(derived_segments)
        derived_atlas = self._aggregate_derived_atlas(task_request, canonical_atlas, derived_segments, result_info)
        DerivedAtlasWriter(caption_with_subtitles=True).write(
            derived_atlas=derived_atlas,
            result_info=result_info,
            task_request=task_request,
            source_video_path=str(canonical_atlas.source_video_path),
            workspace_root=Path(self.workspace.root_path),
            segment_artifacts=segment_artifacts,
        )
        return CreateDerivedAtlasResult(
            success=True,
            task_request=task_request,
            source_segment_count=len(canonical_atlas.segments),
            derived_segment_count=len(derived_segments),
            output_root_path=Path(self.workspace.root_path),
        )

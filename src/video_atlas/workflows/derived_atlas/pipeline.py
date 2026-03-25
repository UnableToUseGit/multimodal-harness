from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ...persistence import DerivedAtlasWriter
from ...schemas import CanonicalAtlas, CreateDerivedAtlasResult, DerivedAtlas

class DerivedPipelineMixin:
    def create(self, task_request: str, canonical_atlas: CanonicalAtlas, output_dir: Path, verbose: bool = False) -> DerivedAtlas:
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

        derived_segment_drafts = [result for result in raw_results if result is not None]
        derived_atlas = self._aggregate_derived_atlas(
            task_request=task_request,
            canonical_atlas=canonical_atlas,
            derived_segment_drafts=derived_segment_drafts,
            output_dir=output_dir,
        )
        DerivedAtlasWriter(caption_with_subtitles=True).write(derived_atlas=derived_atlas)
        
        return derived_atlas

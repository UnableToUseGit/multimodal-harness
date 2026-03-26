from __future__ import annotations

from typing import Optional
from pathlib import Path

from ..generators.base import BaseGenerator
from ..message_builder import build_video_messages_from_path
from ..parsing import parse_json_response
from .derived_atlas.aggregation import AggregationMixin
from .derived_atlas.candidate_generation import CandidateGenerationMixin
from .derived_atlas.derivation import DerivationMixin


class DerivedAtlasWorkflow(
    AggregationMixin,
    DerivationMixin,
    CandidateGenerationMixin,
):
    def __init__(
        self,
        planner: BaseGenerator,
        segmentor: BaseGenerator,
        captioner: BaseGenerator,
        num_workers: int = 1,
    ):
        self.planner = planner
        self.segmentor = segmentor
        self.captioner = captioner
        self.num_workers = max(1, int(num_workers))

    def _prepare_messages(self, system_prompt: str, user_prompt: str):
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    def _build_video_messages_from_path(
        self,
        system_prompt: str,
        user_prompt: str,
        video_path: Path | str,
        start_time: float,
        end_time: float,
    ):
        return build_video_messages_from_path(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            video_path=video_path,
            start_time=start_time,
            end_time=end_time,
        )

    def parse_response(self, generated_text: str) -> dict | list:
        return parse_json_response(generated_text)

    def create(self, task_request, canonical_atlas, output_dir: Path, verbose: bool = False):
        del verbose
        work_items = self._build_candidate_work_items(task_request, canonical_atlas)

        video_path = canonical_atlas.atlas_dir / canonical_atlas.relative_video_path
        if self.num_workers > 1 and len(work_items) > 1:
            from concurrent.futures import ThreadPoolExecutor

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

        from ..persistence import DerivedAtlasWriter

        DerivedAtlasWriter(caption_with_subtitles=True).write(derived_atlas=derived_atlas)
        return derived_atlas

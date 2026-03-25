from __future__ import annotations

from typing import Optional
from pathlib import Path

from ..generators.base import BaseGenerator
from ..message_builder import build_video_messages_from_path
from ..parsing import parse_json_response
from .derived_atlas.aggregation import AggregationMixin
from .derived_atlas.candidate_generation import CandidateGenerationMixin
from .derived_atlas.derivation import DerivationMixin
from .derived_atlas.pipeline import DerivedPipelineMixin


class DerivedAtlasWorkflow(
    AggregationMixin,
    DerivationMixin,
    CandidateGenerationMixin,
    DerivedPipelineMixin,
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

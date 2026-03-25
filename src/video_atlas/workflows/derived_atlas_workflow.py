from __future__ import annotations

from typing import Optional

from ..generators.base import BaseGenerator
from ..message_builder import build_video_messages_from_path
from ..parsing import parse_json_response
from ..workspaces.base import BaseWorkspace
from .base_agent import BaseAtlasAgent
from .task_derivation.aggregation import AggregationMixin
from .task_derivation.candidate_generation import CandidateGenerationMixin
from .task_derivation.derivation import DerivationMixin
from .task_derivation.pipeline import DerivedPipelineMixin


class DerivedAtlasAgent(
    AggregationMixin,
    DerivationMixin,
    CandidateGenerationMixin,
    DerivedPipelineMixin,
    BaseAtlasAgent,
):
    def __init__(
        self,
        planner: BaseGenerator,
        segmentor: BaseGenerator,
        captioner: BaseGenerator,
        workspace: Optional[BaseWorkspace],
        num_workers: int = 1,
    ):
        super().__init__(generator=planner, workspace=workspace)
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
        video_path: str,
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

from __future__ import annotations

from typing import Optional

from ..generators.base import BaseGenerator
from ..workspaces.base import BaseWorkspace
from .base_agent import BaseAtlasAgent
from .canonical_atlas.response_parsing import ResponseParsingMixin
from .canonical_atlas.workspace_io import WorkspaceIOMixin
from .task_derivation.pipeline import DerivedPipelineMixin


class DerivedAtlasAgent(
    DerivedPipelineMixin,
    ResponseParsingMixin,
    WorkspaceIOMixin,
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

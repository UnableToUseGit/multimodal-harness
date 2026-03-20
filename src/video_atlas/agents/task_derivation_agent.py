from __future__ import annotations

from typing import Optional

from .base_agent import BaseAtlasAgent
from .task_derivation.message_generation import TaskMessageGenerationMixin
from .task_derivation.pipeline import TaskDerivationPipelineMixin
from .task_derivation.planning import TaskDerivationPlanningMixin
from .task_derivation.writer import TaskDerivationWriterMixin
from .video_atlas.response_parsing import ResponseParsingMixin
from ..workspaces.base import BaseWorkspace


class TaskDerivationAgent(
    TaskDerivationPipelineMixin,
    TaskDerivationPlanningMixin,
    TaskDerivationWriterMixin,
    TaskMessageGenerationMixin,
    ResponseParsingMixin,
    BaseAtlasAgent,
):
    """
    Derive a task-aware workspace from an existing canonical VideoAtlas workspace.

    Public interface:
        add(source_workspace=..., task_description=...)
    """

    def __init__(
        self,
        generator,
        workspace: Optional["BaseWorkspace"] = None,
    ):
        super().__init__(generator=generator, workspace=workspace)

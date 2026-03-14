from __future__ import annotations

from typing import Optional

from ..core.tree import BaseTree
from ..generators.base import BaseGenerator
from ..workspaces.base import BaseWorkspace
from .base_agent import BaseAtlasAgent
from .video_atlas.message_generation import MessageGenerationMixin
from .video_atlas.pipeline import PipelineMixin
from .video_atlas.probe import ProbeMixin
from .video_atlas.response_parsing import ResponseParsingMixin
from .video_atlas.segmentation import SegmentationMixin
from .video_atlas.strategy_builder import StrategyBuilderMixin
from .video_atlas.workspace_io import WorkspaceIOMixin


class VideoAtlasAgent(
    PipelineMixin,
    SegmentationMixin,
    ProbeMixin,
    StrategyBuilderMixin,
    MessageGenerationMixin,
    ResponseParsingMixin,
    WorkspaceIOMixin,
    BaseAtlasAgent,
):
    """
    VideoAtlasAgent - Video Atlas Agent

    Handles video probing, segmentation, context generation, and organization into a structured video atlas.

    Architecture:
    - tree: READ-ONLY view of the file system structure (VideoAtlasTree)
    - workspace: Executes Linux commands and manages local workspace files
    - planner: LLM for video probing and global planning
    - segmentor: LLM for segment-level processing (segmentation + description)

    Public interface:
        add() - The single unified entry point for creating the atlas.
    """

    def __init__(
        self,
        planner: BaseGenerator,
        segmentor: BaseGenerator,
        workspace: Optional[BaseWorkspace] = None,
        tree: BaseTree = None,
    ):
        super().__init__(generator=planner, tree=tree, workspace=workspace)
        self.planner = planner
        self.segmentor = segmentor

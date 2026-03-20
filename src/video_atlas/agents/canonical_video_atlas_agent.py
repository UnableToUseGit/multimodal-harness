from __future__ import annotations

from typing import Optional

from ..generators.base import BaseGenerator
from ..transcription.base import BaseTranscriber
from ..workspaces.base import BaseWorkspace
from .base_agent import BaseAtlasAgent
from .video_atlas.atlas_assembly import AtlasAssemblyMixin
from .video_atlas.message_generation import MessageGenerationMixin
from .video_atlas.execution_plan_builder import ExecutionPlanBuilderMixin
from .video_atlas.plan import PlanMixin
from .video_atlas.pipeline import PipelineMixin
from .video_atlas.response_parsing import ResponseParsingMixin
from .video_atlas.video_parsing import VideoParsingMixin
from .video_atlas.workspace_io import WorkspaceIOMixin


class CanonicalVideoAtlasAgent(
    PipelineMixin,
    AtlasAssemblyMixin,
    VideoParsingMixin,
    PlanMixin,
    ExecutionPlanBuilderMixin,
    MessageGenerationMixin,
    ResponseParsingMixin,
    WorkspaceIOMixin,
    BaseAtlasAgent,
):
    """
    CanonicalVideoAtlasAgent - Canonical Video Atlas Agent

    Handles video planning, parsing, and assembly into a canonical structured video atlas.

    Architecture:
    - workspace: Executes Linux commands and manages local workspace files
    - planner: LLM for video probing and global planning
    - segmentor: LLM for segment-level processing (segmentation)
    - captioner: LLM for segment-level descriptions

    Public interface:
        add() - The single unified entry point for creating the canonical atlas.
    """

    def __init__(
        self,
        planner: BaseGenerator,
        segmentor: BaseGenerator,
        captioner: Optional[BaseGenerator] = None,
        transcriber: Optional[BaseTranscriber] = None,
        generate_subtitles_if_missing: bool = True,
        chunk_size_sec: int = 600,
        chunk_overlap_sec: int = 20,
        workspace: Optional[BaseWorkspace] = None,
        caption_with_subtitles: bool = True,
    ):
        super().__init__(generator=planner, workspace=workspace)
        self.planner = planner
        self.segmentor = segmentor
        self.captioner = captioner or segmentor
        self.transcriber = transcriber
        self.generate_subtitles_if_missing = generate_subtitles_if_missing
        self.chunk_size_sec = chunk_size_sec
        self.chunk_overlap_sec = chunk_overlap_sec
        self.caption_with_subtitles = caption_with_subtitles


VideoAtlasAgent = CanonicalVideoAtlasAgent

from __future__ import annotations

from typing import Optional

from ..generators.base import BaseGenerator
from ..transcription.base import BaseTranscriber
from ..workspaces.base import BaseWorkspace
from .base_agent import BaseAtlasAgent
from .canonical_atlas.atlas_assembly import AtlasAssemblyMixin
from .canonical_atlas.message_generation import MessageGenerationMixin
from .canonical_atlas.execution_plan_builder import ExecutionPlanBuilderMixin
from .canonical_atlas.plan import PlanMixin
from .canonical_atlas.pipeline import PipelineMixin
from .canonical_atlas.response_parsing import ResponseParsingMixin
from .canonical_atlas.video_parsing import VideoParsingMixin
from .canonical_atlas.workspace_io import WorkspaceIOMixin


class CanonicalAtlasAgent(
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
    CanonicalAtlasAgent - Canonical Atlas Agent

    Handles video planning, parsing, and assembly into a canonical structured atlas.

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
        captioner: BaseGenerator,
        workspace: Optional[BaseWorkspace],
        transcriber: Optional[BaseTranscriber] = None,
        generate_subtitles_if_missing: bool = True,
        chunk_size_sec: int = 600,
        chunk_overlap_sec: int = 20,
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

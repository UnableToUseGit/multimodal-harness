from __future__ import annotations

from typing import Optional

from ..generators.base import BaseGenerator
from ..transcription.base import BaseTranscriber

from ..message_builder import build_video_messages_from_path
from ..parsing import parse_json_response
from ..workspaces.base import BaseWorkspace

from .canonical_atlas.atlas_assembly import AtlasAssemblyMixin
from .canonical_atlas.message_generation import MessageGenerationMixin
from .canonical_atlas.execution_plan_builder import ExecutionPlanBuilderMixin
from .canonical_atlas.plan import PlanMixin
from .canonical_atlas.pipeline import PipelineMixin
from .canonical_atlas.response_parsing import ResponseParsingMixin
from .canonical_atlas.video_parsing import VideoParsingMixin
from .canonical_atlas.workspace_io import WorkspaceIOMixin


class CanonicalAtlasWorkflow(
    PipelineMixin,
    AtlasAssemblyMixin,
    VideoParsingMixin,
    PlanMixin,
    ExecutionPlanBuilderMixin,
    MessageGenerationMixin,
    ResponseParsingMixin,
    WorkspaceIOMixin
):
    """
    CanonicalAtlasWorkflow - Canonical Atlas Workflow

    Handles video planning, parsing, and assembly into a canonical structured atlas.

    Architecture:
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
        transcriber: Optional[BaseTranscriber] = None,
        generate_subtitles_if_missing: bool = True,
        chunk_size_sec: int = 600,
        chunk_overlap_sec: int = 20,
        caption_with_subtitles: bool = True,
    ):
        self.planner = planner
        self.segmentor = segmentor
        self.captioner = captioner or segmentor
        self.transcriber = transcriber
        self.generate_subtitles_if_missing = generate_subtitles_if_missing
        self.chunk_size_sec = chunk_size_sec
        self.chunk_overlap_sec = chunk_overlap_sec
        self.caption_with_subtitles = caption_with_subtitles


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
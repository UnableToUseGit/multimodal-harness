from __future__ import annotations

import logging
from typing import Optional

from ..generators.base import BaseGenerator
from ..transcription.base import BaseTranscriber

from ..message_builder import build_text_messages, build_video_messages_from_path
from ..parsing import parse_json_response

from .canonical_atlas.execution_plan_builder import ExecutionPlanBuilderMixin
from .canonical_atlas.plan import PlanMixin
from .canonical_atlas.pipeline import PipelineMixin
from .canonical_atlas.structure_composition import compose_canonical_structure
from .canonical_atlas.video_parsing import VideoParsingMixin


class CanonicalAtlasWorkflow(
    PipelineMixin,
    VideoParsingMixin,
    PlanMixin,
    ExecutionPlanBuilderMixin,
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
        text_segmentor: Optional[BaseGenerator],
        multimodal_segmentor: Optional[BaseGenerator],
        structure_composer: Optional[BaseGenerator],
        captioner: Optional[BaseGenerator],
        transcriber: Optional[BaseTranscriber] = None,
        generate_subtitles_if_missing: bool = True,
        chunk_size_sec: int = 600,
        chunk_overlap_sec: int = 20,
        text_chunk_size_sec: Optional[int] = None,
        text_chunk_overlap_sec: Optional[int] = None,
        multimodal_chunk_size_sec: Optional[int] = None,
        multimodal_chunk_overlap_sec: Optional[int] = None,
        caption_with_subtitles: bool = True,
    ):
        self.planner = planner
        self.text_segmentor = text_segmentor
        self.multimodal_segmentor = multimodal_segmentor
        self.structure_composer = structure_composer
        self.captioner = captioner
        self.transcriber = transcriber
        self.generate_subtitles_if_missing = generate_subtitles_if_missing
        self.chunk_size_sec = chunk_size_sec
        self.chunk_overlap_sec = chunk_overlap_sec
        self.text_chunk_size_sec = text_chunk_size_sec if text_chunk_size_sec is not None else chunk_size_sec
        self.text_chunk_overlap_sec = text_chunk_overlap_sec if text_chunk_overlap_sec is not None else chunk_overlap_sec
        self.multimodal_chunk_size_sec = (
            multimodal_chunk_size_sec if multimodal_chunk_size_sec is not None else chunk_size_sec
        )
        self.multimodal_chunk_overlap_sec = (
            multimodal_chunk_overlap_sec if multimodal_chunk_overlap_sec is not None else chunk_overlap_sec
        )
        self.caption_with_subtitles = caption_with_subtitles
        self.logger = logging.getLogger(self.__class__.__name__)

    def _log_info(self, message: str, *args) -> None:
        self.logger.info(message, *args)

    def _log_warning(self, message: str, *args) -> None:
        self.logger.warning(message, *args)

    def _log_error(self, message: str, *args) -> None:
        self.logger.error(message, *args)


    def _prepare_messages(self, system_prompt: str, user_prompt: str):
        return build_text_messages(system_prompt=system_prompt, user_prompt=user_prompt)

    def _build_video_messages_from_path(
        self,
        system_prompt: str,
        user_prompt: str,
        video_path: str,
        start_time: float,
        end_time: float,
        video_sampling=None,
    ):
        return build_video_messages_from_path(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            video_path=video_path,
            start_time=start_time,
            end_time=end_time,
            video_sampling=video_sampling,
        )

    def parse_response(self, generated_text: str) -> dict | list:
        return parse_json_response(generated_text)

    def _compose_canonical_structure(
        self,
        units,
        concise_description: str = "",
        genres: list[str] | None = None,
        structure_request: str = "",
    ):
        return compose_canonical_structure(
            self.structure_composer,
            units=units,
            concise_description=concise_description,
            genres=genres,
            structure_request=structure_request,
        )

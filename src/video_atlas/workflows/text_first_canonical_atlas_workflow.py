from __future__ import annotations

import logging
from typing import Optional

from ..generators.base import BaseGenerator
from ..transcription.base import BaseTranscriber
from .text_first_canonical.pipeline import TextFirstPipelineMixin


class TextFirstCanonicalAtlasWorkflow(TextFirstPipelineMixin):
    def __init__(
        self,
        planner: Optional[BaseGenerator],
        text_segmentor: Optional[BaseGenerator],
        structure_composer: Optional[BaseGenerator],
        captioner: Optional[BaseGenerator],
        transcriber: Optional[BaseTranscriber] = None,
        generate_subtitles_if_missing: bool = True,
        chunk_size_sec: int = 1200,
        chunk_overlap_sec: int = 120,
        caption_with_subtitles: bool = True,
        verbose: bool = False,
    ) -> None:
        self.planner = planner
        self.text_segmentor = text_segmentor
        self.structure_composer = structure_composer
        self.captioner = captioner
        self.transcriber = transcriber
        self.generate_subtitles_if_missing = generate_subtitles_if_missing
        self.chunk_size_sec = chunk_size_sec
        self.chunk_overlap_sec = chunk_overlap_sec
        self.caption_with_subtitles = caption_with_subtitles
        self.verbose = verbose
        self.logger = logging.getLogger(self.__class__.__name__)

    def _log_info(self, message: str, *args) -> None:
        self.logger.info(message, *args)

    def _log_warning(self, message: str, *args) -> None:
        self.logger.warning(message, *args)

    def _log_error(self, message: str, *args) -> None:
        self.logger.error(message, *args)

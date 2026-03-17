from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from .audio_prep import extract_audio_ffmpeg
from .base import BaseTranscriber
from .srt_writer import transcript_segments_to_srt


def generate_subtitles_for_video(
    video_path: str | Path,
    subtitle_path: str | Path,
    transcriber: BaseTranscriber,
    logger: logging.Logger | None = None,
    audio_extractor: Callable[[str | Path, str | Path], Path] = extract_audio_ffmpeg,
) -> Path:
    active_logger = logger or logging.getLogger(__name__)
    video_file = Path(video_path)
    subtitle_file = Path(subtitle_path)
    subtitle_file.parent.mkdir(parents=True, exist_ok=True)
    audio_path = subtitle_file.parent / f"{video_file.stem}.wav"

    active_logger.info("Extracting audio from %s", video_file)
    audio_extractor(video_file, audio_path)
    active_logger.info("Transcribing audio from %s", audio_path)
    transcript_segments = transcriber.transcribe_audio(audio_path)
    active_logger.info("Writing generated subtitles to %s", subtitle_file)
    subtitle_file.write_text(transcript_segments_to_srt(transcript_segments), encoding="utf-8")
    return subtitle_file

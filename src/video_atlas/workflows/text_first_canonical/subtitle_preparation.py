from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from ...transcription import BaseTranscriber, generate_subtitles_for_video, transcript_segments_to_srt


@dataclass(frozen=True)
class SubtitleAssets:
    srt_file_path: Path
    generated_audio_path: Path | None = None


def resolve_subtitle_assets(
    *,
    input_dir: Path,
    subtitle_path: Path | None,
    audio_path: Path | None,
    video_path: Path | None,
    transcriber: BaseTranscriber | None,
    generate_subtitles_if_missing: bool,
    logger: logging.Logger | None,
) -> SubtitleAssets:
    if subtitle_path is not None:
        if not subtitle_path.exists():
            raise FileNotFoundError(f"Subtitle file does not exist: {subtitle_path}")
        return SubtitleAssets(srt_file_path=subtitle_path)

    if not generate_subtitles_if_missing:
        raise ValueError("unable to prepare subtitle assets")

    if transcriber is None:
        raise ValueError("unable to prepare subtitle assets")

    active_logger = logger or logging.getLogger(__name__)
    srt_file_path = input_dir / "subtitles.srt"

    if video_path is not None:
        if not video_path.exists():
            raise FileNotFoundError(f"Video file does not exist: {video_path}")
        generated_srt, generated_audio = generate_subtitles_for_video(
            video_path,
            srt_file_path,
            transcriber=transcriber,
            logger=active_logger,
        )
        return SubtitleAssets(srt_file_path=generated_srt, generated_audio_path=generated_audio)

    if audio_path is not None:
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file does not exist: {audio_path}")
        active_logger.info("Transcribing audio from %s", audio_path)
        transcript_segments = transcriber.transcribe_audio(audio_path)
        srt_file_path.parent.mkdir(parents=True, exist_ok=True)
        active_logger.info("Writing generated subtitles to %s", srt_file_path)
        srt_file_path.write_text(transcript_segments_to_srt(transcript_segments), encoding="utf-8")
        return SubtitleAssets(srt_file_path=srt_file_path, generated_audio_path=audio_path)

    raise ValueError("unable to prepare subtitle assets")

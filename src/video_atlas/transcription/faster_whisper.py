from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .base import BaseTranscriber
from .types import TranscriptSegment


@dataclass
class FasterWhisperConfig:
    model_size_or_path: str = "small"
    device: str = "cpu"
    compute_type: str = "int8"
    language: str | None = None
    beam_size: int = 1
    vad_filter: bool = True
    vad_parameters: dict[str, Any] = field(default_factory=dict)
    use_batched_inference: bool = False
    batch_size: int = 8


class FasterWhisperTranscriber(BaseTranscriber):
    """Optional faster-whisper backed subtitle transcriber."""

    def __init__(self, config: FasterWhisperConfig | dict[str, Any] | None = None):
        if config is None:
            self.config = FasterWhisperConfig()
        elif isinstance(config, dict):
            self.config = FasterWhisperConfig(**config)
        else:
            self.config = config
        self._model = None
        self._batched_pipeline = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise RuntimeError("faster-whisper is not installed. Install it before using FasterWhisperTranscriber.") from exc

        self._model = WhisperModel(
            self.config.model_size_or_path,
            device=self.config.device,
            compute_type=self.config.compute_type,
        )
        return self._model

    def _load_batched_pipeline(self):
        if self._batched_pipeline is not None:
            return self._batched_pipeline
        model = self._load_model()
        try:
            from faster_whisper import BatchedInferencePipeline
        except ImportError as exc:
            raise RuntimeError("faster-whisper BatchedInferencePipeline is unavailable.") from exc
        self._batched_pipeline = BatchedInferencePipeline(model=model)
        return self._batched_pipeline

    def transcribe_audio(self, audio_path: str | Path) -> list[TranscriptSegment]:
        transcription_kwargs: dict[str, Any] = {
            "language": self.config.language,
            "beam_size": self.config.beam_size,
            "word_timestamps": False,
        }
        if self.config.vad_filter:
            transcription_kwargs["vad_filter"] = True
            if self.config.vad_parameters:
                transcription_kwargs["vad_parameters"] = dict(self.config.vad_parameters)

        try:
            if self.config.use_batched_inference:
                pipeline = self._load_batched_pipeline()
                segments, _ = pipeline.transcribe(
                    str(audio_path),
                    batch_size=self.config.batch_size,
                    **transcription_kwargs,
                )
            else:
                model = self._load_model()
                segments, _ = model.transcribe(str(audio_path), **transcription_kwargs)
        except ValueError as exc:
            if "empty sequence" in str(exc):
                return []
            raise

        return [
            TranscriptSegment(start=float(segment.start), end=float(segment.end), text=segment.text.strip())
            for segment in list(segments)
            if getattr(segment, "text", "").strip()
        ]

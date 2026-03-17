from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .types import TranscriptSegment


class BaseTranscriber(ABC):
    """Base interface for audio-to-transcript implementations."""

    @abstractmethod
    def transcribe_audio(self, audio_path: str | Path) -> list[TranscriptSegment]:
        raise NotImplementedError

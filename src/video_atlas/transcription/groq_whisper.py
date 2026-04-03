from __future__ import annotations

from dataclasses import dataclass, field
import math
import os
from pathlib import Path
import subprocess
import tempfile
import time
from typing import Any

import requests

from .base import BaseTranscriber
from .types import TranscriptSegment


@dataclass
class GroqWhisperConfig:
    sample_rate: int = 16000
    channels: int = 1
    api_base: str = "https://api.groq.com/openai/v1"
    model: str = "whisper-large-v3"
    api_key_env: str = "GROQ_API_KEY"
    language: str | None = None
    response_format: str = "verbose_json"
    timestamp_granularities: list[str] = field(default_factory=lambda: ["segment"])
    max_chunk_size_mb: int = 20
    audio_bitrate: str = "64k"
    retry_on_rate_limit: bool = True
    request_timeout_sec: float = 300.0


def parse_groq_transcription_result(raw_result: dict[str, Any]) -> list[TranscriptSegment]:
    segments = raw_result.get("segments")
    if not isinstance(segments, list):
        text = str(raw_result.get("text", "") or "").strip()
        return [TranscriptSegment(start=0.0, end=0.0, text=text)] if text else []

    transcript_segments: list[TranscriptSegment] = []
    for item in segments:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "") or "").strip()
        if not text:
            continue
        transcript_segments.append(
            TranscriptSegment(
                start=float(item.get("start", 0.0) or 0.0),
                end=float(item.get("end", 0.0) or 0.0),
                text=text,
            )
        )
    return transcript_segments


class GroqWhisperTranscriber(BaseTranscriber):
    def __init__(
        self,
        config: GroqWhisperConfig | dict[str, Any] | None = None,
        *,
        session: requests.Session | None = None,
    ):
        if config is None:
            self.config = GroqWhisperConfig()
        elif isinstance(config, dict):
            self.config = GroqWhisperConfig(**config)
        else:
            self.config = config
        self.session = session or requests.Session()

    def _api_key(self) -> str:
        api_key = os.environ.get(self.config.api_key_env, "").strip()
        if not api_key:
            raise RuntimeError(
                f"Missing Groq API key. Set the environment variable {self.config.api_key_env} before transcription."
            )
        return api_key

    def _transcode_audio_for_upload(self, input_audio: Path, work_dir: Path) -> Path:
        output_path = work_dir / "groq_upload.mp3"
        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(input_audio),
            "-vn",
            "-ac",
            str(self.config.channels),
            "-ar",
            str(self.config.sample_rate),
            "-b:a",
            self.config.audio_bitrate,
            str(output_path),
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return output_path

    def _get_duration_sec(self, audio_path: Path) -> float:
        command = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ]
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float((result.stdout or "0").strip() or 0.0)

    def _split_audio_if_needed(self, audio_path: Path, work_dir: Path) -> list[tuple[Path, float]]:
        max_bytes = self.config.max_chunk_size_mb * 1024 * 1024
        file_size = audio_path.stat().st_size
        if file_size <= max_bytes:
            return [(audio_path, 0.0)]

        duration_sec = self._get_duration_sec(audio_path)
        if duration_sec <= 0:
            raise RuntimeError(f"Unable to determine audio duration for chunking: {audio_path}")

        num_chunks = max(1, math.ceil(file_size / max_bytes))
        chunk_duration = math.ceil(duration_sec / num_chunks) + 2

        chunks: list[tuple[Path, float]] = []
        start_time = 0.0
        chunk_index = 0
        while start_time < duration_sec:
            chunk_path = work_dir / f"chunk_{chunk_index:03d}.mp3"
            command = [
                "ffmpeg",
                "-y",
                "-i",
                str(audio_path),
                "-ss",
                str(start_time),
                "-t",
                str(chunk_duration),
                "-c",
                "copy",
                str(chunk_path),
            ]
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            chunks.append((chunk_path, start_time))
            chunk_index += 1
            start_time += chunk_duration
        return chunks

    def _transcribe_chunk_once(self, chunk_path: Path) -> list[TranscriptSegment]:
        with chunk_path.open("rb") as audio_file:
            files = {"file": (chunk_path.name, audio_file, "audio/mpeg")}
            data: list[tuple[str, str]] = [
                ("model", self.config.model),
                ("response_format", self.config.response_format),
            ]
            if self.config.language:
                data.append(("language", self.config.language))
            for granularity in self.config.timestamp_granularities:
                data.append(("timestamp_granularities[]", granularity))

            response = self.session.post(
                f"{self.config.api_base.rstrip('/')}/audio/transcriptions",
                headers={"Authorization": f"Bearer {self._api_key()}"},
                files=files,
                data=data,
                timeout=self.config.request_timeout_sec,
            )

        if response.status_code == 429:
            raise requests.HTTPError("rate_limited", response=response)
        response.raise_for_status()
        return parse_groq_transcription_result(response.json())

    def _transcribe_chunk(self, chunk_path: Path) -> list[TranscriptSegment]:
        try:
            return self._transcribe_chunk_once(chunk_path)
        except requests.HTTPError as exc:
            if not self.config.retry_on_rate_limit:
                raise
            response = exc.response
            if response is None or response.status_code != 429:
                raise
            retry_after = response.headers.get("Retry-After")
            wait_sec = float(retry_after) if retry_after else 30.0
            time.sleep(wait_sec)
            return self._transcribe_chunk_once(chunk_path)

    def transcribe_audio(self, audio_path: str | Path) -> list[TranscriptSegment]:
        source_path = Path(audio_path)
        with tempfile.TemporaryDirectory(prefix="video_atlas_groq_") as tmp_dir:
            work_dir = Path(tmp_dir)
            prepared_audio = self._transcode_audio_for_upload(source_path, work_dir)
            chunks = self._split_audio_if_needed(prepared_audio, work_dir)

            merged_segments: list[TranscriptSegment] = []
            for chunk_path, start_offset in chunks:
                chunk_segments = self._transcribe_chunk(chunk_path)
                for segment in chunk_segments:
                    merged_segments.append(
                        TranscriptSegment(
                            start=segment.start + start_offset,
                            end=segment.end + start_offset,
                            text=segment.text,
                        )
                    )
            return merged_segments

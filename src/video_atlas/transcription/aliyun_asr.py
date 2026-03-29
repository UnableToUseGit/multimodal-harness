from __future__ import annotations

import json
import os
from http import HTTPStatus
from urllib import request

from .aliyun_types import AliyunAsrConfig
from .types import TranscriptSegment


def parse_aliyun_transcription_result(raw_result: dict) -> list[TranscriptSegment]:
    transcript_items = raw_result.get("transcripts") or []
    if not transcript_items:
        return []

    sentences = transcript_items[0].get("sentences") or []
    segments: list[TranscriptSegment] = []
    for sentence in sentences:
        text = str(sentence.get("text", "")).strip()
        if not text:
            continue
        segments.append(
            TranscriptSegment(
                start=float(sentence["begin_time"]) / 1000.0,
                end=float(sentence["end_time"]) / 1000.0,
                text=text,
            )
        )
    return segments


class AliyunAsrClient:
    def __init__(self, config: AliyunAsrConfig):
        self.config = config

    def transcribe_from_url(self, file_url: str) -> list[TranscriptSegment]:
        try:
            import dashscope
            from dashscope.audio.asr import Transcription
        except ImportError as exc:
            raise RuntimeError("dashscope is not installed. Install it before using AliyunAsrTranscriber.") from exc

        api_key = os.getenv(self.config.api_key_env)
        if not api_key:
            raise RuntimeError(f"Aliyun API key environment variable {self.config.api_key_env!r} is not set.")

        dashscope.base_http_api_url = self.config.api_base
        dashscope.api_key = api_key

        task_response = Transcription.async_call(
            model=self.config.model,
            file_urls=[file_url],
            diarization_enabled=self.config.diarization_enabled,
            language_hints=list(self.config.language_hints),
        )
        transcription_response = Transcription.wait(task=task_response.output.task_id)
        if transcription_response.status_code != HTTPStatus.OK:
            message = getattr(transcription_response.output, "message", None) or "unknown aliyun transcription failure"
            raise RuntimeError(f"Aliyun transcription request failed: {message}")

        for transcription in transcription_response.output["results"]:
            if transcription.get("subtask_status") != "SUCCEEDED":
                continue
            with request.urlopen(transcription["transcription_url"]) as response:
                raw_result = json.loads(response.read().decode("utf-8"))
            return parse_aliyun_transcription_result(raw_result)

        raise RuntimeError("Aliyun transcription did not return a successful subtask result.")

from __future__ import annotations

from ..generators import OpenAICompatibleGenerator
from ..transcription import FasterWhisperTranscriber
from .models import ModelRuntimeConfig, TranscriberRuntimeConfig


def build_generator(config: ModelRuntimeConfig):
    if config.provider != "openai_compatible":
        raise ValueError(f"Unsupported generator provider: {config.provider}")
    return OpenAICompatibleGenerator(
        {
            "model_name": config.model_name,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "max_tokens": config.max_tokens,
            "extra_body": dict(config.extra_body),
        }
    )


def build_transcriber(config: TranscriberRuntimeConfig):
    if not config.enabled:
        return None
    if config.backend != "faster_whisper":
        raise ValueError(f"Unsupported transcriber backend: {config.backend}")
    return FasterWhisperTranscriber(
        {
            "model_size_or_path": config.model_size_or_path,
            "device": config.device,
            "compute_type": config.compute_type,
            "language": config.language,
            "vad_filter": config.vad_filter,
            "vad_parameters": {"min_silence_duration_ms": config.min_silence_duration_ms},
            "use_batched_inference": config.use_batched_inference,
            "batch_size": config.batch_size,
        }
    )

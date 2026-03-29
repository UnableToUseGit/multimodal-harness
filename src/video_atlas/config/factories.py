from __future__ import annotations

from ..generators import OpenAICompatibleGenerator
from ..transcription import AliyunAsrTranscriber, FasterWhisperTranscriber
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
    if config.backend == "faster_whisper":
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
    if config.backend == "aliyun_asr":
        return AliyunAsrTranscriber(
            {
                "sample_rate": config.sample_rate,
                "channels": config.channels,
                "api_base": config.aliyun_api_base,
                "model": config.aliyun_model,
                "language_hints": list(config.aliyun_language_hints),
                "diarization_enabled": config.aliyun_diarization_enabled,
                "oss_endpoint": config.aliyun_oss_endpoint,
                "oss_bucket_name": config.aliyun_oss_bucket_name,
                "oss_access_key_id_env": config.aliyun_oss_access_key_id_env,
                "oss_access_key_secret_env": config.aliyun_oss_access_key_secret_env,
                "api_key_env": config.aliyun_api_key_env,
                "oss_prefix": config.aliyun_oss_prefix,
                "signed_url_expires_sec": config.aliyun_signed_url_expires_sec,
                "poll_interval_sec": config.aliyun_poll_interval_sec,
                "poll_timeout_sec": config.aliyun_poll_timeout_sec,
                "retain_remote_artifacts": config.retain_remote_artifacts,
            }
        )
    raise ValueError(f"Unsupported transcriber backend: {config.backend}")

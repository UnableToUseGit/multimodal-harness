from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


@dataclass
class ModelRuntimeConfig:
    provider: str = "openai_compatible"
    model_name: str = ""
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 1600
    extra_body: dict[str, Any] = field(default_factory=dict)


@dataclass
class TranscriberRuntimeConfig:
    enabled: bool = True
    backend: str = "faster_whisper"
    sample_rate: int = 16000
    channels: int = 1
    model_size_or_path: str = "small"
    device: str = "cpu"
    compute_type: str = "int8"
    language: str | None = None
    vad_filter: bool = True
    min_silence_duration_ms: int = 500
    use_batched_inference: bool = False
    batch_size: int = 8
    aliyun_api_base: str = "https://dashscope.aliyuncs.com/api/v1"
    aliyun_model: str = "fun-asr"
    aliyun_language_hints: list[str] = field(default_factory=list)
    aliyun_diarization_enabled: bool = True
    aliyun_oss_endpoint: str | None = None
    aliyun_oss_bucket_name: str | None = None
    aliyun_oss_access_key_id_env: str = "OSS_ACCESS_KEY_ID"
    aliyun_oss_access_key_secret_env: str = "OSS_ACCESS_KEY_SECRET"
    aliyun_api_key_env: str = "ALIYUN_API_KEY"
    aliyun_oss_prefix: str = "audios/"
    aliyun_signed_url_expires_sec: int = 3600
    aliyun_poll_interval_sec: float = 2.0
    aliyun_poll_timeout_sec: float = 900.0
    retain_remote_artifacts: bool = False


@dataclass
class CanonicalRuntimeConfig:
    caption_with_subtitles: bool = True
    generate_subtitles_if_missing: bool = True
    verbose: bool = False
    chunk_size_sec: int = 600
    chunk_overlap_sec: int = 20


@dataclass
class CanonicalPipelineConfig:
    planner: ModelRuntimeConfig
    segmentor: ModelRuntimeConfig
    captioner: ModelRuntimeConfig | None = None
    transcriber: TranscriberRuntimeConfig = field(default_factory=TranscriberRuntimeConfig)
    runtime: CanonicalRuntimeConfig = field(default_factory=CanonicalRuntimeConfig)


@dataclass
class DerivedRuntimeConfig:
    verbose: bool = False
    num_workers: int = 1


@dataclass
class DerivedPipelineConfig:
    planner: ModelRuntimeConfig
    segmentor: ModelRuntimeConfig
    captioner: ModelRuntimeConfig
    runtime: DerivedRuntimeConfig = field(default_factory=DerivedRuntimeConfig)


def _read_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_canonical_pipeline_config(path: str | Path) -> CanonicalPipelineConfig:
    raw = _read_json(path)
    return CanonicalPipelineConfig(
        planner=ModelRuntimeConfig(**raw["planner"]),
        segmentor=ModelRuntimeConfig(**raw["segmentor"]),
        captioner=ModelRuntimeConfig(**raw["captioner"]) if raw.get("captioner") else None,
        transcriber=TranscriberRuntimeConfig(**raw.get("transcriber", {})),
        runtime=CanonicalRuntimeConfig(**raw.get("runtime", {})),
    )


def load_derived_pipeline_config(path: str | Path) -> DerivedPipelineConfig:
    raw = _read_json(path)
    return DerivedPipelineConfig(
        planner=ModelRuntimeConfig(**raw["planner"]),
        segmentor=ModelRuntimeConfig(**raw["segmentor"]),
        captioner=ModelRuntimeConfig(**raw["captioner"]),
        runtime=DerivedRuntimeConfig(**raw.get("runtime", {})),
    )

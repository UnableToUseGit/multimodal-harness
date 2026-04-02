from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Any
import json
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ModelRuntimeConfig:
    provider: str = "openai_compatible"
    model_name: str = ""
    connection: str = "default"
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
    text_chunk_size_sec: int = 1200
    text_chunk_overlap_sec: int = 120
    multimodal_chunk_size_sec: int = 600
    multimodal_chunk_overlap_sec: int = 60
    chunk_size_sec: int = 600
    chunk_overlap_sec: int = 20


@dataclass
class AcquisitionRuntimeConfig:
    enabled: bool = True
    prefer_youtube_subtitles: bool = True
    youtube_output_template: str = "%(id)s.%(ext)s"
    max_youtube_video_duration_sec: int = 1500
    youtube_cookies_file: str | None = None
    youtube_cookies_from_browser: str | None = None


@dataclass
class CanonicalPipelineConfig:
    planner: ModelRuntimeConfig
    segmentor: ModelRuntimeConfig | None = None
    text_segmentor: ModelRuntimeConfig | None = None
    multimodal_segmentor: ModelRuntimeConfig | None = None
    structure_composer: ModelRuntimeConfig | None = None
    captioner: ModelRuntimeConfig | None = None
    transcriber: TranscriberRuntimeConfig = field(default_factory=TranscriberRuntimeConfig)
    runtime: CanonicalRuntimeConfig = field(default_factory=CanonicalRuntimeConfig)
    acquisition: AcquisitionRuntimeConfig = field(default_factory=AcquisitionRuntimeConfig)


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


def _build_model_runtime_config(raw: dict[str, Any]) -> ModelRuntimeConfig:
    return ModelRuntimeConfig(**raw)


def _build_canonical_runtime_config(raw: dict[str, Any]) -> CanonicalRuntimeConfig:
    text_chunk_size_sec = int(raw.get("text_chunk_size_sec", raw.get("chunk_size_sec", 600)))
    text_chunk_overlap_sec = int(raw.get("text_chunk_overlap_sec", raw.get("chunk_overlap_sec", 20)))
    multimodal_chunk_size_sec = int(raw.get("multimodal_chunk_size_sec", raw.get("chunk_size_sec", 600)))
    multimodal_chunk_overlap_sec = int(raw.get("multimodal_chunk_overlap_sec", raw.get("chunk_overlap_sec", 20)))

    return CanonicalRuntimeConfig(
        caption_with_subtitles=raw.get("caption_with_subtitles", True),
        generate_subtitles_if_missing=raw.get("generate_subtitles_if_missing", True),
        verbose=raw.get("verbose", False),
        text_chunk_size_sec=text_chunk_size_sec,
        text_chunk_overlap_sec=text_chunk_overlap_sec,
        multimodal_chunk_size_sec=multimodal_chunk_size_sec,
        multimodal_chunk_overlap_sec=multimodal_chunk_overlap_sec,
        chunk_size_sec=int(raw.get("chunk_size_sec", text_chunk_size_sec)),
        chunk_overlap_sec=int(raw.get("chunk_overlap_sec", text_chunk_overlap_sec)),
    )


def _build_acquisition_runtime_config(raw: dict[str, Any]) -> AcquisitionRuntimeConfig:
    merged = dict(raw)
    merged.setdefault("youtube_cookies_file", os.environ.get("VIDEO_ATLAS_YOUTUBE_COOKIES_FILE"))
    merged.setdefault("youtube_cookies_from_browser", os.environ.get("VIDEO_ATLAS_YOUTUBE_COOKIES_FROM_BROWSER"))
    return AcquisitionRuntimeConfig(**merged)


def load_canonical_pipeline_config(path: str | Path) -> CanonicalPipelineConfig:
    raw = _read_json(path)
    legacy_segmentor = raw.get("segmentor")
    text_segmentor_raw = raw.get("text_segmentor") or legacy_segmentor
    multimodal_segmentor_raw = raw.get("multimodal_segmentor") or legacy_segmentor or text_segmentor_raw
    segmentor_raw = legacy_segmentor or text_segmentor_raw or multimodal_segmentor_raw

    return CanonicalPipelineConfig(
        planner=_build_model_runtime_config(raw["planner"]),
        segmentor=_build_model_runtime_config(segmentor_raw) if segmentor_raw else None,
        text_segmentor=_build_model_runtime_config(text_segmentor_raw) if text_segmentor_raw else None,
        multimodal_segmentor=_build_model_runtime_config(multimodal_segmentor_raw) if multimodal_segmentor_raw else None,
        structure_composer=_build_model_runtime_config(raw.get("structure_composer")) if raw.get("structure_composer") else _build_model_runtime_config(raw["planner"]),
        captioner=_build_model_runtime_config(raw["captioner"]) if raw.get("captioner") else None,
        transcriber=TranscriberRuntimeConfig(**raw.get("transcriber", {})),
        runtime=_build_canonical_runtime_config(raw.get("runtime", {})),
        acquisition=_build_acquisition_runtime_config(raw.get("acquisition", {})),
    )


def load_derived_pipeline_config(path: str | Path) -> DerivedPipelineConfig:
    raw = _read_json(path)
    return DerivedPipelineConfig(
        planner=ModelRuntimeConfig(**raw["planner"]),
        segmentor=ModelRuntimeConfig(**raw["segmentor"]),
        captioner=ModelRuntimeConfig(**raw["captioner"]),
        runtime=DerivedRuntimeConfig(**raw.get("runtime", {})),
    )

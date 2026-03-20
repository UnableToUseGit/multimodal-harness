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
    model_size_or_path: str = "small"
    device: str = "cpu"
    compute_type: str = "int8"
    language: str | None = None
    vad_filter: bool = True
    min_silence_duration_ms: int = 500
    use_batched_inference: bool = False
    batch_size: int = 8


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
class TaskDerivationRuntimeConfig:
    verbose: bool = False


@dataclass
class TaskDerivationConfig:
    generator: ModelRuntimeConfig
    runtime: TaskDerivationRuntimeConfig = field(default_factory=TaskDerivationRuntimeConfig)


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


def load_task_derivation_config(path: str | Path) -> TaskDerivationConfig:
    raw = _read_json(path)
    return TaskDerivationConfig(
        generator=ModelRuntimeConfig(**raw["generator"]),
        runtime=TaskDerivationRuntimeConfig(**raw.get("runtime", {})),
    )

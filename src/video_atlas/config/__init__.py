"""Configuration objects and loaders for runnable scripts."""

from __future__ import annotations

from importlib import import_module

_EXPORT_MAP = {
    "CanonicalPipelineConfig": "video_atlas.config.models",
    "CanonicalRuntimeConfig": "video_atlas.config.models",
    "DerivedPipelineConfig": "video_atlas.config.models",
    "DerivedRuntimeConfig": "video_atlas.config.models",
    "ModelRuntimeConfig": "video_atlas.config.models",
    "TranscriberRuntimeConfig": "video_atlas.config.models",
    "build_generator": "video_atlas.config.factories",
    "build_transcriber": "video_atlas.config.factories",
    "load_canonical_pipeline_config": "video_atlas.config.models",
    "load_derived_pipeline_config": "video_atlas.config.models",
}

__all__ = list(_EXPORT_MAP.keys())


def __getattr__(name: str):
    module_name = _EXPORT_MAP.get(name)
    if module_name is None:
        raise AttributeError(f"module 'video_atlas.config' has no attribute {name!r}")

    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value

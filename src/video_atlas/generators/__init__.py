"""Generator exports for the VideoAtlas package."""

from __future__ import annotations

from importlib import import_module

_EXPORT_MAP = {
    "BaseGenerator": "video_atlas.generators.base",
    "GeneratorConfig": "video_atlas.generators.config",
}

__all__ = list(_EXPORT_MAP.keys())


def __getattr__(name: str):
    module_name = _EXPORT_MAP.get(name)
    if module_name is None:
        raise AttributeError(f"module 'video_atlas.generators' has no attribute {name!r}")

    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value

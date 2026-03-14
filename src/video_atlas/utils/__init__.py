"""Utility exports for the VideoAtlas package."""

from __future__ import annotations

from importlib import import_module

_EXPORT_MAP = {
    "get_frame_indices": "video_atlas.utils.frames",
    "get_subtitle_in_segment": "video_atlas.utils.subtitles",
    "get_video_property": "video_atlas.utils.video_metadata",
    "parse_srt": "video_atlas.utils.subtitles",
    "prepare_video_input": "video_atlas.utils.frames",
    "process_one_frame": "video_atlas.utils.frames",
    "read_json": "video_atlas.utils.video_metadata",
}

__all__ = list(_EXPORT_MAP.keys())


def __getattr__(name: str):
    module_name = _EXPORT_MAP.get(name)
    if module_name is None:
        raise AttributeError(f"module 'video_atlas.utils' has no attribute {name!r}")

    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value

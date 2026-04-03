# -*- coding: utf-8 -*-
"""Workflow exports for MM Harness."""

from __future__ import annotations

from importlib import import_module

_EXPORT_MAP = {
    "TextFirstCanonicalAtlasWorkflow": "video_atlas.workflows.text_first_canonical_atlas_workflow"
}

__all__ = list(_EXPORT_MAP.keys())


def __getattr__(name: str):
    module_name = _EXPORT_MAP.get(name)
    if module_name is None:
        raise AttributeError(f"module 'video_atlas.workflows' has no attribute {name!r}")

    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value

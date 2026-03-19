# -*- coding: utf-8 -*-
"""Exports for the VideoAtlas package."""

from __future__ import annotations

from importlib import import_module

__version__ = "0.1.0"

_EXPORT_MAP = {
    "ALLOWED_EVIDENCE": "video_atlas.schemas",
    "ALLOWED_GENRES": "video_atlas.schemas",
    "ALLOWED_SAMPLING_PROFILES": "video_atlas.schemas",
    "ALLOWED_SEGMENTATION_PROFILES": "video_atlas.schemas",
    "ALLOWED_SIGNAL_PRIORITIES": "video_atlas.schemas",
    "BaseAtlasAgent": "video_atlas.agents",
    "BaseGenerator": "video_atlas.generators",
    "BaseTree": "video_atlas.core",
    "BaseWorkspace": "video_atlas.workspaces",
    "BoundaryCandidate": "video_atlas.schemas",
    "BoundaryPostProcessSpec": "video_atlas.schemas",
    "CONTEXT_GENERATION_PROMPT": "video_atlas.prompts",
    "CaptionSpec": "video_atlas.schemas",
    "CanonicalAtlas": "video_atlas.schemas",
    "CanonicalVideoAtlasAgent": "video_atlas.agents",
    "CanonicalSegment": "video_atlas.schemas",
    "CreateVideoAtlasResult": "video_atlas.schemas",
    "CreateTaskDerivationResult": "video_atlas.schemas",
    "DEFAULT_SEGMENTATION_PROFILE": "video_atlas.schemas",
    "DEFAULT_STRATEGY_PACKAGE": "video_atlas.schemas",
    "DetectionWindowSpec": "video_atlas.schemas",
    "DESCRIPTION_SLOTS": "video_atlas.schemas",
    "FSNode": "video_atlas.core",
    "LocalWorkspace": "video_atlas.workspaces",
    "NodeType": "video_atlas.core",
    "OpenAICompatibleGenerator": "video_atlas.generators",
    "BaseTranscriber": "video_atlas.transcription",
    "FasterWhisperConfig": "video_atlas.transcription",
    "FasterWhisperTranscriber": "video_atlas.transcription",
    "SamplingConfig": "video_atlas.schemas",
    "SAMPLING_PROFILE_CONFIGS": "video_atlas.schemas",
    "SegmentationProfile": "video_atlas.schemas",
    "SEGMENTATION_PROFILES": "video_atlas.schemas",
    "SegmentDraft": "video_atlas.schemas",
    "SegmentDerivationDecision": "video_atlas.schemas",
    "SegmentSpec": "video_atlas.schemas",
    "TASK_DERIVATION_PROMPT": "video_atlas.prompts",
    "TaskDerivationAgent": "video_atlas.agents",
    "TaskDerivationPlan": "video_atlas.schemas",
    "TITLE_GENERATION_PROMPT": "video_atlas.prompts",
    "TitleSpec": "video_atlas.schemas",
    "VIDEO_GLOBAL_PROMPT": "video_atlas.prompts",
    "VIDEO_PROBE_PROMPT": "video_atlas.prompts",
    "VIDEO_SEGMENT_PROMPT": "video_atlas.prompts",
    "VideoAtlasAgent": "video_atlas.agents",
    "VideoAtlasTree": "video_atlas.core",
    "VideoGlobal": "video_atlas.schemas",
    "VideoProcessSpec": "video_atlas.schemas",
    "VideoSeg": "video_atlas.schemas",
    "get_frame_indices": "video_atlas.utils",
    "get_subtitle_in_segment": "video_atlas.utils",
    "get_video_property": "video_atlas.utils",
    "generate_subtitles_for_video": "video_atlas.transcription",
    "parse_srt": "video_atlas.utils",
    "prepare_video_input": "video_atlas.utils",
    "read_json": "video_atlas.utils",
    "resolve_sampling_profile": "video_atlas.schemas",
    "resolve_segmentation_profile": "video_atlas.schemas",
}

__all__ = ["__version__", *_EXPORT_MAP.keys()]


def __getattr__(name: str):
    module_name = _EXPORT_MAP.get(name)
    if module_name is None:
        raise AttributeError(f"module 'video_atlas' has no attribute {name!r}")

    module = import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value

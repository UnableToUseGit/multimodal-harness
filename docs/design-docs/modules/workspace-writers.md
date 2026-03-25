# Workspace Writers

## Purpose

`src/video_atlas/persistence/writers.py` contains writer classes that persist atlas domain objects into the repository's workspace format.

This module is responsible for converting instantiated schema objects into the expected on-disk directory layout and file contents.

## Why This Module Exists

Both canonical and derived pipelines produce in-memory result objects that must be materialized as workspaces:

- root `README.md`
- per-segment directories
- per-segment `README.md`
- per-segment clip files
- optional subtitles
- workflow metadata files such as `derivation.json` and `.agentignore/...`

This persistence step is separate from agent reasoning. The agent decides what the atlas is. The writer decides how that atlas is serialized and written.

## Public Classes

## `CanonicalAtlasWriter`

**Purpose**

Persist a `CanonicalAtlas` into the canonical workspace layout.

**Constructor Inputs**

- `write_text`: callback used to write text files to the workspace
- `extract_clip`: callback used to materialize segment clip files
- `clip_exists`: callback used to avoid re-extracting an existing clip
- `caption_with_subtitles`: whether per-segment subtitles should be written

**Write Inputs**

- `atlas: CanonicalAtlas`
- `source_video_path: str`
- `segment_artifacts: dict[str, dict[str, str]] | None`

**Behavior**

- writes root `README.md`
- writes each segment `README.md`
- writes each segment `SUBTITLES.md` when enabled and available
- writes each segment `video_clip.mp4`

## `DerivedAtlasWriter`

**Purpose**

Persist a `DerivedAtlas` and `DerivationResultInfo` into the derived workspace layout.

**Constructor Inputs**

- `write_text`: callback used to write text files to the workspace
- `extract_clip`: callback used to materialize derived clip files
- `caption_with_subtitles`: whether per-segment subtitles should be written

**Write Inputs**

- `derived_atlas: DerivedAtlas`
- `result_info: DerivationResultInfo`
- `task_request: str`
- `source_video_path: str`
- `segment_artifacts: dict[str, dict[str, str]] | None`

**Behavior**

- writes root `README.md`
- writes `TASK.md`
- writes `derivation.json`
- writes `.agentignore/DERIVATION_RESULT.json`
- writes each derived segment `README.md`
- writes each derived segment `SOURCE_MAP.json`
- writes each derived segment `SUBTITLES.md` when enabled and available
- writes each derived segment `video_clip.mp4`

## Boundaries

This module does:

- serialize atlas/result objects into workspace files
- organize directory layout
- call clip extraction callbacks with the final time range

This module does not:

- call LLMs
- parse LLM outputs
- decide segmentation or derivation policy
- decide which prompt to use
- perform agent orchestration

## Current Usage

- canonical atlas assembly uses `CanonicalAtlasWriter`
- derived atlas pipeline uses `DerivedAtlasWriter`

# Architecture

This repository centers on one pipeline: `VideoAtlasAgent`.

## System Goal

`VideoAtlas` is a video parsing service for turning long, hard-to-use videos into an LLM-friendly file-directory representation.

The system exists to transform raw video input into a structured workspace that downstream applications, agents, and humans can use directly.

The output workspace is not just a summary dump. It is a stable artifact surface that typically includes:

- a root `README.md` with the global overview of the full video
- a `segments/` directory containing one folder per segment
- a per-segment `README.md` with summary, timing, and detailed description
- optional per-segment subtitles and video clips
- optional probe, planning, and other intermediate artifacts for debugging and inspection

This workspace layout is a primary product surface of the system. Downstream consumers should be able to navigate the generated files reliably without depending on internal Python objects or prompt-level implementation details.

## Core Flow

1. `LocalWorkspace` prepares and mutates the output workspace.
2. `VideoAtlasTree` provides a read-only structural view.
3. `VideoAtlasAgent` probes the source video, plans a processing strategy, segments the video, generates per-segment context, and writes a global summary.
4. `video_utils.py` handles frame extraction, subtitle parsing, and video metadata.
5. Prompts and schemas define the contract between orchestration code and the backing multimodal generator.

## Module Boundaries

- `agents/`: public agent entrypoints and top-level orchestration only
- `agents/video_atlas/`: internal pipeline stages for parsing, strategy building, probing, segmentation, and workspace writes
- `utils/`: media and subtitle helpers only, split by concern instead of one catch-all module
- `prompts/`: prompt text only
- `schemas/`: data contracts only, including workspace-facing markdown models and strategy/result models
- `core/`: read-only workspace and tree models only
- `workspaces/`: filesystem mutation and command execution only
- `generators/`: abstract LLM interface only

Avoid mixing these responsibilities.

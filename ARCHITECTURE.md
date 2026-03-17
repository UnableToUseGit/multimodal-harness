# Architecture

This repository centers on two related pipelines: `CanonicalVideoAtlasAgent` and `TaskDerivationAgent`.

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

The system also supports a second-stage task-aware derivation flow. A canonical content-aware atlas can be used as source material for generating a new task-aware workspace tailored to a business need such as highlights, issue extraction, or role-specific review.

When subtitle files are not provided, the system may also generate `subtitles.srt` automatically from the source video through a separate transcription flow before canonical parsing continues. The normalized extracted audio may be kept in the canonical workspace root for inspection.

## Core Flow

1. `LocalWorkspace` prepares and mutates output workspaces.
2. `VideoAtlasTree` provides a read-only structural view over generated workspaces.
3. `CanonicalVideoAtlasAgent` probes the source video, plans a processing strategy, segments the video, generates per-segment context, and writes a canonical content-aware atlas.
4. `TaskDerivationAgent` loads a canonical atlas, evaluates segment relevance for a task, and writes a derived task-aware workspace with source provenance.
5. The transcription flow can extract audio, run ASR, and write `subtitles.srt` when subtitle files are missing.
6. `video_utils.py` and split utility modules handle frame extraction, subtitle parsing, and video metadata.
7. Config objects and checked-in workflow config files define how planner, segmentor, captioner, and transcriber runtimes are assembled for scripts.
8. Prompts and schemas define the contract between orchestration code and the backing multimodal generator.

## Module Boundaries

- `agents/`: public agent entrypoints and top-level orchestration only
- `agents/video_atlas/`: internal pipeline stages for parsing, strategy building, probing, segmentation, and workspace writes
- `agents/task_derivation/`: internal pipeline stages for canonical atlas loading, task planning, and derived workspace writing
- `config/`: runtime config schemas and factories for assembling multi-stage agents from config files
- `transcription/`: audio extraction, ASR abstraction, and subtitle writing for missing-subtitle workflows
- `utils/`: media and subtitle helpers only, split by concern instead of one catch-all module
- `prompts/`: prompt text only
- `schemas/`: data contracts only, including workspace-facing markdown models, strategy/result models, and task-derivation models
- `core/`: read-only workspace and tree models only
- `workspaces/`: filesystem mutation and command execution only
- `generators/`: abstract LLM interface only

Avoid mixing these responsibilities.

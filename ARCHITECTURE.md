# Architecture

This repository centers on two related pipelines: `CanonicalAtlasAgent` and `DerivedAtlasAgent`.

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
2. `CanonicalVideoAtlasAgent` first plans execution from sampled probes, then parses the video into finalized segments plus local captions, then assembles the final atlas with global description, segment titles, and workspace artifacts.
3. `DerivedAtlasAgent` loads a canonical atlas or a canonical workspace, evaluates segment relevance for a task, re-grounds selected segments into tighter clips, and writes a derived task-aware workspace with source provenance.
4. The transcription flow can extract audio, run ASR, and write `subtitles.srt` when subtitle files are missing.
5. Utility modules handle frame extraction, subtitle parsing, and video metadata.
6. The review workbench can load canonical and task-derived workspaces and expose their clips, subtitles, captions, and source mappings in a browser for manual evaluation.
7. Config objects and checked-in workflow config files define how planner, segmentor, captioner, and transcriber runtimes are assembled for scripts.
8. Prompts and schemas define the contract between orchestration code and the backing multimodal generator.

## Module Boundaries

- `agents/`: public agent entrypoints and top-level orchestration only
- `agents/video_atlas/`: internal canonical pipeline stages for planning, execution-plan construction, video parsing, atlas assembly, and workspace writes
- The canonical segmentation flow is stage-oriented:
  - the planner inspects sampled probes and emits only `planner_confidence`, `genre_distribution`, `segmentation_profile`, and `sampling_profile`
  - execution-plan construction resolves those planner outputs into a concrete `CanonicalExecutionPlan`
  - video parsing operates on chunked windows with overlap, returns candidate boundaries, stabilizes the timeline, and generates local captions
  - atlas assembly generates global description plus final segment titles and then writes the final workspace artifacts
- `agents/task_derivation/`: internal pipeline stages for canonical atlas loading, candidate generation, re-grounding, aggregation, and derived workspace writing
- `config/`: runtime config schemas and factories for assembling multi-stage agents from config files
- `transcription/`: audio extraction, ASR abstraction, and subtitle writing for missing-subtitle workflows
- `review/`: local review app loading workspace artifacts for browser-based manual evaluation
- `utils/`: media and subtitle helpers only, split by concern instead of one catch-all module
- `prompts/`: prompt text only
- `schemas/`: data contracts only, including canonical profiles/execution plans/runtime segment data, workspace-facing markdown models, task-derivation models, and result models
- `workspaces/`: filesystem mutation and command execution only
- `generators/`: abstract LLM interface only

Avoid mixing these responsibilities.

# Task-Aware Derivation

## Goal

Generate a task-aware workspace from an existing canonical content-aware VideoAtlas workspace without rerunning the full video parsing pipeline.

## Inputs

- one canonical VideoAtlas workspace directory
- one task description in natural language
- one generator implementation conforming to the text-generation contract used by agents

## Expected Flow

1. Load the canonical workspace and parse its root `README.md` plus segment-level `README.md` files.
2. Evaluate canonical segments against the task description.
3. In v1, allow `keep` or `drop` decisions only.
4. For kept segments, allow task-aware reordering and retitling.
5. Write a new derived workspace containing:
   - a root `README.md`
   - a `TASK.md`
   - a `derivation.json`
   - `segments/task_seg_*/`
   - per-derived-segment `SOURCE_MAP.json`
6. Preserve provenance from each derived segment back to the canonical segment it came from.

## V1 Constraints

- The source of truth remains the canonical content-aware atlas.
- V1 does not split segments, merge segments, or re-run visual grounding on candidate clips.
- The derivation pipeline should be able to operate from canonical atlas text and existing segment artifacts alone.
- The derived workspace is a task-specific view, not a replacement for the canonical workspace.

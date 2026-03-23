# Derived Atlas Prompts

This document records the prompt contracts used by the derived atlas pipeline in `src/video_atlas/prompts/derived_prompts.py`.

## `DERIVED_CANDIDATE_PROMPT`

**Purpose / Role**

Used in the `CandidateGeneration` stage to select which canonical segments should participate in task-aware derivation.

**Inputs**

- `task_request`
- canonical segment list with:
  - `segment_id`
  - time range
  - title
  - summary
  - detail

**Outputs**

Strict JSON with a `candidates` array. Each candidate contains:

- `segment_id`
- `intent`
- `grounding_instruction`

## `DERIVED_GROUNDING_PROMPT`

**Purpose / Role**

Used in the `Derivation` stage to refine one selected canonical segment into a tighter sub-clip.

**Inputs**

- source `segment_id`
- source segment start/end time
- `intent`
- `grounding_instruction`
- source `summary`
- source `detail`

**Outputs**

Strict JSON with:

- `start_time`
- `end_time`

The returned range may be absolute or source-segment-relative. The pipeline is responsible for resolving and clamping it to the source segment bounds.

## `DERIVED_CAPTION_PROMPT`

**Purpose / Role**

Used in the `Derivation` stage after re-grounding to generate task-aware textual metadata for the refined sub-clip.

**Inputs**

- `task_request`
- source `segment_id`
- derived `start_time` / `end_time`
- `intent`
- `grounding_instruction`
- source `summary`
- source `detail`
- pruned `subtitles`

**Outputs**

Strict JSON with:

- `title`
- `summary`
- `caption`

## Notes

- These prompts are intentionally kept separate from the derivation pipeline code so prompt editing and prompt review do not require touching orchestration logic.
- Prompt exports are re-exported from `src/video_atlas/prompts/__init__.py`.

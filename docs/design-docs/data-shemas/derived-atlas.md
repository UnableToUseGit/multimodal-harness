# Data Model Specification

## Scope

This document defines the data schemas and workspace metadata used by the derived atlas generation pipeline.

## Schema Index

- `DerivationPolicy`
- `DerivationResultInfo`
- `DerivedAtlas`
- `CreateDerivedAtlasResult`

## `DerivationPolicy`

### Purpose

Captures why and how a selected canonical segment should be derived for the task.

### Produced By

- `DerivedAtlasAgent` / `CandidateGeneration`

### Consumed By

- `DerivedAtlasAgent` / `Derivation`
- `DerivedAtlasAgent` / `Aggregation`

### Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `intent` | `str` | yes | High-level statement of what information the derived segment should contribute to the task. |
| `grounding_instruction` | `str` | yes | Natural-language instruction used by the grounding stage to refine the source segment into a tighter sub-clip. |

## `DerivationResultInfo`

### Purpose

Stores derivation bookkeeping for review and debugging.

### Produced By

- `DerivedAtlasAgent` / `Derivation`

### Consumed By

- `DerivedAtlasAgent` / `Aggregation`
- review/debug tooling through `.agentignore/DERIVATION_RESULT.json`

### Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `derived_atlas_segment_count` | `int` | yes | Number of derived atlas segments written to the workspace. |
| `derivation_reason` | `dict[str, DerivationPolicy]` | yes | Maps each derived segment id to the policy used to derive it. |
| `derivation_source` | `dict[str, str]` | yes | Maps each derived segment id to its source canonical segment id. |

### Field Notes

- keys in both maps are derived segment ids such as `derived_seg_0001`

## `DerivedAtlas`

### Purpose

Represents the final task-aware atlas assembled from the selected canonical source segments.

### Produced By

- `DerivedAtlasAgent` / `Aggregation`

### Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `global_summary` | `str` | yes | Code-generated aggregate summary containing derived segment count, total duration, and average duration. |
| `detailed_breakdown` | `str` | yes | Stable human-readable breakdown of each derived segment, including intent and precise start/end times. |
| `segments` | `list[AtlasSegment]` | yes | Derived atlas segments after re-grounding and re-captioning. |
| `root_path` | `Path` | yes | Root path of the derived workspace. |
| `readme_text` | `str` | yes | Final text written to the derived workspace `README.md`. |
| `source_canonical_atlas_path` | `Path` | yes | Root path of the source canonical atlas workspace. |

## `CreateDerivedAtlasResult`

### Purpose

Top-level result returned by the public `DerivedAtlasAgent.add(...)` workflow.

### Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `success` | `bool` | yes | Whether the workflow completed successfully. |
| `task_request` | `str` | yes | Original task request passed to the derived workflow. |
| `source_segment_count` | `int` | yes | Number of canonical segments considered as source material. |
| `derived_segment_count` | `int` | yes | Number of derived segments written to the output workspace. |
| `output_root_path` | `Path \| None` | no | Root path of the derived workspace. |

## Workspace Metadata

### Root Files

| Path | Description |
|---|---|
| `README.md` | Human-readable overview of the derived atlas. |
| `TASK.md` | Raw task request text. |
| `derivation.json` | Review-facing metadata for the derived workspace. |
| `.agentignore/DERIVATION_RESULT.json` | Detailed derivation bookkeeping. |

### `derivation.json` Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `task_request` | `str` | yes | Task used to derive the workspace. |
| `global_summary` | `str` | yes | Aggregate summary copied from `DerivedAtlas`. |
| `detailed_breakdown` | `str` | yes | Per-derived-segment breakdown copied from `DerivedAtlas`. |
| `derived_segment_count` | `int` | yes | Count of derived segments. |
| `source_canonical_atlas_path` | `str` | yes | String form of the source canonical atlas root path. |

### Per-Segment README Fields

Each derived segment `README.md` contains:

- `DerivedSegID`
- `SourceSegID`
- `Start Time`
- `End Time`
- `Duration`
- `Title`
- `Summary`
- `Detail Description`
- `Intent`

# Data Model Specification

## Scope
This document outlines the data schemas specific to the Derived Atlas Generation Pipeline.

## Conventions
- Schema names use PascalCase, e.g. `CanonicalExecutionPlan`
- Field names use snake_case, e.g. `source_video_path`
- Optional fields are marked explicitly
- Enum values use lowercase strings unless otherwise stated
- Timestamps use ISO 8601 strings
- Paths are local workspace-relative paths unless otherwise noted

## Schema Index
- `DerivationPolicy`
- `DerivationResultInfo`
- `DerivedAtlas`

## `DerivationPolicy`

### Purpose
This schema is the domain model of generated policy for derivation.

### Produced By
- Derived Atlas Agent / **CandidateGeneration** stage

### Consumed By
- Derived Atlas Agent / **Derivation** stage
- Derived Atlas Agent / **Aggregation** stage

### Fields
| Field | Type | Required | Description |
|---|---|---:|---|
| intent | str | yes | The high-level goal of the derivation (i.e., "what information should the derived segment provide").|
| grounding_instruction | str | yes | a natural language description used for `segmentor` to grounding sub-clips aligh the intent. |


## `DerivationResultInfo`

### Purpose
This schema conatins necessary information for derivation analysis and review.

### Produced By
- Derived Atlas Agent / **Derivation** stage

### Consumed By
- Derived Atlas Agent / **Aggregation** stage

### Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| derived_atlas_segment_count | int | yes | the count of derived AtlasSegments |
| derivation_reason | dict[str, `DerivationPolicy`] | yes | record the derivation policy for each derived AtlasSegment |
| derivation_source | dict[str, str] | yes | record the source AtlasSegment segment_id for each derived AtlasSegment |

### Field Notes
- The key of `derivation_reason` and `derivation_source` is the segmen_id of derived AtlasSegment.

## `DerivedAtlas`

### Purpose
This schema present the final format of derived atlas.

### Produced By
- Derived Atlas Agent / **Aggregation** stage

### Consumed By
None

### Fields
| Field | Type | Required | Description |
|---|---|---:|---|
| global_summary | str | yes | Provides aggregate statistics, including the total count of derived segments, their cumulative duration, and the average segment duration. |
| detailed_breakdown | str | yes | Specifies the contribution of each derived AtlasSegment to the task. For every segment, it lists the specific information provided, along with its precise temporal boundaries (e.g., start/end timestamps in ISO 8601 strings). |
| segments | list[`AtlasSegment`] | yes | a list of derived AtlasSegment |
| root_path | Path | yes | the path of DerivedAtlas will be written in |
| readme_text | str | yes | the final string will be written README.md |
| source_canonical_atlas_path | Path | yes | the path of its source canonical atlas |

### Fields Notes
None

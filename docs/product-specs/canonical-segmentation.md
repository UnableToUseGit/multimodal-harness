# Canonical Segmentation

`CanonicalVideoAtlasAgent` should build a stable, fully covered segment timeline for the source video. The canonical atlas is not a highlight extractor. Its segmentation should optimize for downstream derivation and navigation.

## Goals

- cover the full video timeline with no dropped gaps
- prefer stable, self-contained segments over micro-cuts
- keep segment boundaries defensible and easy to inspect
- preserve enough granularity for later task-aware derivation

## Pipeline Contract

The canonical segmentation pipeline should follow four stages:

1. Plan from sampled probes and produce the minimal planner output.
2. Run chunked boundary detection with overlap.
3. Post-process boundary candidates into stable draft segments.
4. Assemble the final atlas by generating the global description plus final segment titles and then writing workspace artifacts.

## Planner Outputs Used By Later Stages

Planner outputs are execution-plan priors, not content facts. The planner identifies the segmentation family and shared sampling profile, while the execution-plan builder expands stable defaults such as signal priority, boundary evidence, caption policy, and target segment length.

- `planner_confidence`
- `segmentation_profile`: the single profile identifier that selects the canonical segmentation template
- `genre_distribution`: lightweight descriptive metadata that helps title/caption generation but does not replace the profile
- target segment length is derived from `segmentation_profile` and used internally for post-processing and refinement
- `sampling_profile`: controls a shared frame-sampling profile that is resolved in code and used by both parsing and caption generation

## Boundary Detection

Boundary detection should operate on a detection window with a smaller core range:

- the model may inspect the full window for context
- only boundaries inside the core range may be accepted
- overlap exists to reduce edge instability across adjacent windows

Detection-window parameters such as chunk size and overlap are orchestration/runtime settings, not post-processing settings.

The boundary detector should return candidate boundaries, not final segment metadata:

- `timestamp`
- `confidence`
- `evidence`
- `boundary_rationale`

The detector must allow empty outputs for a chunk. Lack of a boundary in one chunk is not a pipeline failure.

## Post-Processing

Post-processing is responsible for turning raw boundary candidates into usable canonical draft segments.

- remove invalid or duplicated timestamps
- filter low-confidence boundaries
- merge obviously too-short segments when appropriate
- mark overly long segments as candidates for later refinement

## Atlas Assembly

Final titles and global description are generated after final segment ranges and local captions are known.

- final titles should be stable navigation labels, not highlight headlines
- assembly should see all parsed segment descriptions together so titles can reflect global context
- workspace artifacts such as segment `README.md`, segment `SUBTITLES.md`, segment clips, and root `README.md` should be written only after final titles are available

## Efficiency Requirements

Runtime efficiency is a first-class requirement.

- probe sampling should stay configurable
- the planner should choose one shared `sampling_profile`, with concrete fps/resolution resolved in code
- segment processing should continue to run concurrently across finalized segments
- title generation should happen in the global assembly pass, not during boundary detection

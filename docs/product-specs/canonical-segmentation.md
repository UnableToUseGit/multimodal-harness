# Canonical Segmentation

`CanonicalVideoAtlasAgent` should build a stable, fully covered segment timeline for the source video. The canonical atlas is not a highlight extractor. Its segmentation should optimize for downstream derivation and navigation.

## Goals

- cover the full video timeline with no dropped gaps
- prefer stable, self-contained segments over micro-cuts
- keep segment boundaries defensible and easy to inspect
- preserve enough granularity for later task-aware derivation

## Pipeline Contract

The canonical segmentation pipeline should follow four stages:

1. Probe the source video and produce global priors.
2. Run chunked boundary detection with overlap.
3. Post-process boundary candidates into stable draft segments.
4. Generate final segment titles and captions after segment ranges are fixed.

## Probe Outputs Used By Later Stages

Probe outputs are strategy priors, not content facts. Probe identifies the segmentation family and supplies runtime-sensitive controls, while the profile registry expands stable defaults such as signal priority and boundary evidence.

- `segmentation_profile`: the single profile identifier that selects the canonical segmentation template
- `genre_distribution`: lightweight descriptive metadata that helps title/caption generation but does not replace the profile
- `segmentation.policy_notes`: optional video-specific override text layered on top of the profile's default segmentation policy
- target segment length is derived from `segmentation_profile` and used internally for post-processing and refinement
- `title.notes`: title-generation guidance for finalized segments
- `segmentation.sampling_profile`: controls segmentor video sampling efficiency via a discrete profile mapped in code
- `description.slots_weight`
- `description.notes`
- `description.sampling_profile`: controls caption/title generation video sampling efficiency via a discrete profile mapped in code

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
- optional `title_hint`

The detector must allow empty outputs for a chunk. Lack of a boundary in one chunk is not a pipeline failure.

## Post-Processing

Post-processing is responsible for turning raw boundary candidates into usable canonical draft segments.

- remove invalid or duplicated timestamps
- filter low-confidence boundaries
- merge obviously too-short segments when appropriate
- mark overly long segments as candidates for later refinement

## Title Generation

Final titles are generated after final segment ranges are known.

- boundary-time `title_hint` is optional and weak
- final titles should be stable navigation labels, not highlight headlines
- title generation may use lightweight neighboring context and global priors

## Efficiency Requirements

Runtime efficiency is a first-class requirement.

- probe sampling should stay configurable
- segmentor sampling should remain independent from caption/title sampling
- segment processing should continue to run concurrently across finalized segments
- title generation should reuse the lower-cost caption/title path instead of forcing a second heavy segmentation pass

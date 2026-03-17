# Review Workbench

## Goal

Provide a local operator-facing workbench for evaluating canonical and task-derived VideoAtlas outputs without relying on editor-native video playback.

## Inputs

- one canonical workspace under `local/workspaces/canonical_<case_name>/`
- optional one task-derived workspace under `local/workspaces/task_<case_name>/`

## Expected Flow

1. Start the local review app with one or both workspace paths.
2. Open the local browser URL printed by the script.
3. Select a workspace and navigate its `segments/` list.
4. For each segment, inspect the clip, subtitles, README-derived caption fields, and timing metadata together.
5. If a task-derived workspace is loaded, compare a task segment against its linked canonical source segment and source map.

## Minimum Capabilities

- list canonical and task-derived segments
- play segment clips and source videos in a browser
- inspect segment subtitles and README text side by side
- surface timing metadata for segmentation review
- expose task derivation metadata such as `SOURCE_MAP.json` when present

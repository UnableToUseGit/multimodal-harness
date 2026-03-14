# New User Onboarding

## Goal

Help a new contributor run the full path from raw video input to an LLM-friendly workspace safely and predictably.

## Inputs

- one `.mp4` file
- optional one `.srt` subtitle file
- a generator implementation conforming to `BaseGenerator`

## Expected Flow

1. Install dependencies.
2. Prepare a workspace directory.
3. Copy the video and optional subtitle file into the workspace.
4. Instantiate `VideoAtlasAgent` with planner, segmentor, tree, and workspace.
5. Run `add(...)`.
6. Inspect generated `README.md`, `segments/`, and `.agentignore/PROBE_RESULT.json`.
7. Confirm the output directory now acts as a structured context surface for downstream LLM workflows.

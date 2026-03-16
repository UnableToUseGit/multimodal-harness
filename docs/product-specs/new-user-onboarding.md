# New User Onboarding

## Goal

Help a new contributor run the full path from raw video input to an LLM-friendly workspace safely and predictably.

## Inputs

- one `.mp4` file
- optional one `.srt` subtitle file
- a generator implementation conforming to `BaseGenerator`

## Expected Flow

1. Install dependencies.
2. Place the raw video and optional subtitle file under `local/inputs/<case_name>/`.
3. Prepare a canonical workspace directory under `local/workspaces/canonical_<case_name>/`.
4. Run `scripts/run_video_atlas.py` with a planner model, output workspace, and the input case directory.
5. If task-aware derivation is needed, run `scripts/run_task_derivation.py` with the canonical workspace and a task description.
6. Inspect generated `README.md`, `segments/`, and `.agentignore/PROBE_RESULT.json`.
7. Confirm the output directory now acts as a structured context surface for downstream LLM workflows.

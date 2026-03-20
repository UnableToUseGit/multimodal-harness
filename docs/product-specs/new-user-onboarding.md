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
4. Update the checked-in config file under `configs/canonical/` with the planner, segmentor, captioner, and transcriber settings you want to use.
5. Run `scripts/run_video_atlas.py` with that config, the output workspace, and the input case directory.
6. If task-aware derivation is needed, update the config under `configs/task_derivation/` and run `scripts/run_task_derivation.py` with the canonical workspace and a task description.
7. Run `scripts/run_review_app.py` against the canonical workspace, and optionally the task-derived workspace, to inspect clips, subtitles, and captions together in a browser.
8. Inspect generated `README.md`, `segments/`, and `.agentignore/EXECUTION_PLAN.json`.
9. Confirm the output directory now acts as a structured context surface for downstream LLM workflows.

If no subtitle file is provided, the canonical generation script may auto-generate `subtitles.srt` before parsing continues. The normalized extracted audio is also kept in the canonical workspace root as a `.wav` file for inspection. This requires the local transcription runtime, such as `faster-whisper`, to be installed in the execution environment.

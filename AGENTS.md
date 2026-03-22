# Repository Guidelines

## What This Repo Is

`VideoAtlas` provides a video parsing service that turns long, hard-to-use videos into an LLM-friendly file-directory representation.

The core goal is not just to summarize a video, but to reorganize it into structured artifacts that downstream applications can consume reliably, such as:

- a global overview in `README.md`
- segment-level folders under `segments/`
- per-segment summaries, detailed descriptions, clips, and optional subtitles
- probe outputs and intermediate planning artifacts for inspection

The repository also supports task-aware derivation: starting from a canonical content-aware atlas, derive a second workspace that keeps, drops, reorders, and retitles segments for a specific business task.

The repository exists to make long-video understanding operational: take raw video input, extract structured context, and write it into a workspace that humans and language models can both navigate easily.

## Project Structure & Module Organization

This repository is the home of the `VideoAtlas` pipeline. Keep the code surface small and keep repository context in the `docs/` tree.

- `src/video_atlas/agents/`: agent entrypoints and public agent classes.
- `src/video_atlas/agents/video_atlas/`: internal `CanonicalVideoAtlasAgent` stages such as planning, execution-plan building, video parsing, atlas assembly, response parsing, and workspace IO.
- `src/video_atlas/agents/task_derivation/`: internal `TaskDerivationAgent` stages such as canonical atlas loading, task planning, and derived workspace writing.
- `src/video_atlas/generators/`: abstract generator interface and config models.
- `src/video_atlas/prompts/`: prompt templates used by `CanonicalVideoAtlasAgent`.
- `src/video_atlas/schemas/`: canonical execution-plan models, runtime segment/caption data models, workspace markdown models, task-derivation models, and result objects.
- `src/video_atlas/config/`: runnable pipeline config schemas, loaders, and factories for scripts.
- `src/video_atlas/transcription/`: audio extraction, ASR abstraction, and `.srt` generation for missing-subtitle workflows.
- `src/video_atlas/review/`: local browser-based review tooling for inspecting workspace clips, subtitles, captions, and source mappings.
- `src/video_atlas/utils/`: video helpers split by concern, such as frame extraction, subtitle parsing, and video metadata.
- `src/video_atlas/workspaces/`: local command execution abstraction.
- `src/video_atlas/cli/`: minimal local development CLI.
- `configs/`: checked-in runnable config files for canonical and task-derivation workflows.
- `tests/`: smoke tests and future automated checks.
- `scripts/`: local validation helpers.
- `docs/design-docs/`: architecture beliefs and design decisions.
- `docs/product-specs/`: user-facing behavior and workflow expectations.
- `docs/exec-plans/`: active plans, completed plans, and tracked debt.
- Root docs: `ARCHITECTURE.md`, `docs/DESIGN.md`, `docs/PLANS.md`, `docs/SECURITY.md`.

There is currently no web/API layer and no bundled example assets.

## Build, Test, and Development Commands

### Environment Setup

- `conda activate videoatlas`: enter the dedicated development environment.
- Required Python packages should be installed manually inside this environment.
- `ffmpeg` is already installed and can be used directly.

Recommended order for a fresh shell:

1. `conda activate videoatlas`
2. `proxy_status`
3. run `proxy_on` if external network access is needed
4. run `set_mirror` before package or model downloads
5. install dependencies
6. run validation commands

### Network Helpers

For mainland China network constraints, use the shell helpers already defined in `.bashrc`:

- `proxy_status`: check whether outbound proxy is enabled.
- `proxy_on`: enable proxy access before installing or downloading from external services.
- `proxy_off`: disable proxy access.
- `set_mirror`: configure mirrors for `pip`, `conda`, `npm`, and Hugging Face downloads.
- `test_mirror`: inspect current mirror configuration.
- `unset_mirror`: clear mirror configuration when no longer needed.

### Install Commands

- `pip install -r requirements.txt`: install runtime dependencies.
- `pip install -e .`: install the package in editable mode.

Dependency policy:

- add new dependencies only when necessary
- record shared dependencies in the repository instead of leaving them as ad hoc local installs
- if installs fail, check `proxy_status` and `test_mirror` before debugging elsewhere

### Validation Commands

- `PYTHONPATH=src python3 -m compileall src/video_atlas`: checks syntax and module-level import integrity.
- `PYTHONPATH=src python3 -m video_atlas.cli check-import`: smoke test the package entrypoint.
- `PYTHONPATH=src python3 -m video_atlas.cli config`: inspect whether API config is loaded from env or `.env`.
- `PYTHONPATH=src python3 -m unittest discover -s tests`: run the minimal automated smoke tests.
- `PYTHONPATH=src python3 scripts/run_review_app.py --canonical-workspace ... [--task-workspace ...]`: launch the local browser-based review workbench for manual evaluation.
- `PYTHONPATH=src python3 scripts/run_video_atlas.py --config configs/canonical/default.json --input-path ... --output-workspace ...`: run a real canonical VideoAtlas generation test against an OpenAI-compatible API.
- `PYTHONPATH=src python3 scripts/run_task_derivation.py --config configs/task_derivation/default.json --source-workspace ... --output-workspace ... --task-description ...`: run a real task-derivation test against an OpenAI-compatible API.

### Runtime Configuration

- Set environment-level API connection config through environment variables: `VIDEO_ATLAS_API_BASE`, `VIDEO_ATLAS_API_KEY`.
- For local development, fill in the project-root `.env` file or copy `.env.example` to `.env`, but never commit the real `.env`.
- Application code should read runtime config through `src/video_atlas/settings.py` instead of scattered direct `os.environ` access.
- Pass workflow-level model selection through checked-in config files under `configs/`, not through `settings.py`.
- Prefer checked-in workflow configs under `configs/` for model/runtime parameters. Use CLI flags only for input/output paths and a small number of temporary overrides.
- Keep environment-level connection settings such as `api_base` and `api_key` in `settings.py` and environment variables, not in checked-in workflow config files.
- Keep workflow-level execution settings such as model selection, temperatures, token limits, VAD, and batching in `configs/`.
- Keep CLI usage narrow: it should select config files, provide input/output paths, and allow a small number of temporary overrides. It should not be the primary carrier for full model/runtime configuration.

### Local Test Data Convention

- Keep local videos, subtitles, and generated workspaces under the project-root `local/` directory.
- Recommended layout:
  - `local/inputs/<case_name>/` for raw inputs such as `.mp4` and optional `.srt`
  - `local/workspaces/canonical_<case_name>/` for canonical content-aware atlas outputs
  - `local/workspaces/task_<case_name>/` for task-aware derived atlas outputs
- Treat `local/` as machine-local working data only. It should stay out of version control.

If you change the `CanonicalVideoAtlasAgent` pipeline, the `TaskDerivationAgent` pipeline, workspace-writing behavior, or video utility logic, also validate with a small local `.mp4` and optional `.srt`.

### Notes

- This repository has a minimal smoke test suite under `tests/`, but no formal full-coverage test suite, `Makefile`, or task runner yet.
- Before downloading models, packages, or external assets, verify proxy and mirror setup first.
- Before major changes, read `ARCHITECTURE.md`, `docs/design-docs/index.md`, `docs/PLANS.md`, and the relevant file under `docs/product-specs/`.

## Coding Style & Naming Conventions

- Use Python 3.10+ and 4-space indentation.
- Follow PEP 8 naming: `snake_case` for functions/modules, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep new modules aligned with the core VideoAtlas workflow; avoid adding unrelated product surfaces before a clear need exists.
- Prefer type hints on public methods and dataclass/Pydantic fields.
- Keep comments sparse and functional; explain non-obvious behavior only.
- For internal runtime messaging, use the workspace/agent logger instead of direct `print` calls. CLI commands and top-level scripts may print final user-facing summaries.
- When subtitle files are missing, prefer generating `subtitles.srt` through the transcription pipeline instead of embedding ad hoc ASR logic into the main video pipeline.
- When subtitles are auto-generated, keep the extracted normalized audio file in the canonical workspace root next to `subtitles.srt` for inspection and reruns.

## Testing Guidelines

There is no formal automated test suite yet. Use lightweight validation for now.

For changes:

- run `PYTHONPATH=src python3 -m compileall src/video_atlas`
- run a targeted import smoke test with `PYTHONPATH=src python3 -m video_atlas.cli check-import`
- run `PYTHONPATH=src python3 -m unittest discover -s tests`
- if you change runtime behavior, perform a small manual validation with a local `.mp4` and optional `.srt`

If you add tests later, place them under `tests/` and name files `test_*.py`.

Documentation updates are part of the definition of done for behavior-changing work.

- If development workflow, install steps, config flow, or validation commands change, update `AGENTS.md` in the same change.
- If system boundaries, workspace artifact contracts, core flow, or module responsibilities change, update `ARCHITECTURE.md` in the same change.
- If user-visible behavior, processing expectations, or implementation plans change materially, update the matching file under `docs/product-specs/` or `docs/exec-plans/` in the same change.

## Commit & Pull Request Guidelines

This workspace is managed with git. Use small, reviewable commits and clear branch boundaries.

Recommended commit style: Conventional Commits, for example:

- `feat: add generator adapter for multimodal backend`
- `fix: handle missing subtitles in planner inputs`

Use a separate branch per task to reduce conflicts and make validation easier.

PRs should include:

- a short summary of behavior changes
- affected paths, such as `src/video_atlas/agents/canonical_atlas_agent.py`
- validation performed
- sample input/output notes if video processing behavior changed

## Operational Safety

- Do not commit API keys, proxy settings, local video assets, or generated workspace outputs.
- Keep large media files and temporary parsing outputs outside version control unless they are intentionally curated fixtures.
- Treat `LocalWorkspace` command execution as privileged; review shell command construction and path handling carefully.
- Be careful when interpolating filenames, subtitles, or generated text into shell commands or output paths.
- Before downloading packages, models, or external assets, confirm proxy and mirror configuration for the current shell.

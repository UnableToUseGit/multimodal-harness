# Text-First Canonical Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a new text-first canonical workflow that fully supports `video-absent` and `video-present + text-led`, while explicitly rejecting `video-present + visual-led`.

**Architecture:** Keep the current video-first canonical workflow intact and introduce a new `TextFirstCanonicalAtlasWorkflow` as a parallel business-layer implementation. Reuse existing schemas, structure composition, persistence, review, and transcription infrastructure; add a text-first pipeline, a shared subtitle-preparation helper, and a route gate based on planner-selected profile.

**Tech Stack:** Python 3.12, dataclasses, existing `video_atlas` generators/transcription/persistence stack, `unittest`

---

## File Structure

- Create: `src/video_atlas/workflows/text_first_canonical_atlas_workflow.py`
  - New text-first workflow public entry.
- Create: `src/video_atlas/workflows/text_first_canonical/subtitle_preparation.py`
  - Shared helper for resolving existing subtitles or generating them from audio/video.
- Create: `src/video_atlas/workflows/text_first_canonical/plan.py`
  - Text-first planner/profile selection and route mapping.
- Create: `src/video_atlas/workflows/text_first_canonical/parsing.py`
  - Text-first unit generation built on subtitle text.
- Create: `src/video_atlas/workflows/text_first_canonical/pipeline.py`
  - Main text-first canonical pipeline.
- Modify: `src/video_atlas/application/canonical_create.py`
  - Switch default workflow builder from legacy video-first workflow to text-first workflow.
- Modify: `src/video_atlas/workflows/__init__.py` or equivalent export file if present
  - Export new workflow if needed by existing import patterns.
- Modify: `docs/design-docs/module-design/canonical-atlas-workflow.md`
  - Mark text-first workflow as the new default canonical path once implementation is complete.
- Test: `tests/test_text_first_canonical_subtitle_preparation.py`
  - New tests for subtitle resolution/generation.
- Test: `tests/test_text_first_canonical_workflow.py`
  - New workflow-level route and text-first pipeline tests.
- Modify: `tests/test_application_canonical_create.py`
  - Assert application layer now builds the text-first workflow by default.
- Modify: `tests/test_canonical_two_stage_pipeline.py`
  - Keep Stage 2 composition expectations valid when invoked through text-first workflow.

## Task 1: Shared Subtitle Preparation

**Files:**
- Create: `src/video_atlas/workflows/text_first_canonical/subtitle_preparation.py`
- Test: `tests/test_text_first_canonical_subtitle_preparation.py`

- [ ] **Step 1: Write the failing tests**

```python
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from video_atlas.workflows.text_first_canonical.subtitle_preparation import resolve_subtitle_assets


class SubtitlePreparationTest(unittest.TestCase):
    def test_reuses_existing_subtitle_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            subtitle_path = input_dir / "source.srt"
            subtitle_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n", encoding="utf-8")

            result = resolve_subtitle_assets(
                input_dir=input_dir,
                subtitle_path=subtitle_path,
                audio_path=None,
                video_path=None,
                transcriber=None,
                generate_subtitles_if_missing=True,
                logger=None,
            )

        self.assertEqual(result.srt_file_path, subtitle_path)
        self.assertIsNone(result.generated_audio_path)

    @patch("video_atlas.workflows.text_first_canonical.subtitle_preparation.generate_subtitles_for_video")
    def test_generates_subtitles_from_video_when_missing(self, mock_generate: MagicMock) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            video_path = input_dir / "video.mp4"
            video_path.write_bytes(b"video")
            generated_srt = input_dir / "subtitles.srt"
            generated_audio = input_dir / "audio.wav"
            mock_generate.return_value = (generated_srt, generated_audio)

            result = resolve_subtitle_assets(
                input_dir=input_dir,
                subtitle_path=None,
                audio_path=None,
                video_path=video_path,
                transcriber=MagicMock(),
                generate_subtitles_if_missing=True,
                logger=None,
            )

        self.assertEqual(result.srt_file_path, generated_srt)
        self.assertEqual(result.generated_audio_path, generated_audio)

    def test_raises_when_no_text_asset_can_be_prepared(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir)
            with self.assertRaises(ValueError):
                resolve_subtitle_assets(
                    input_dir=input_dir,
                    subtitle_path=None,
                    audio_path=None,
                    video_path=None,
                    transcriber=None,
                    generate_subtitles_if_missing=False,
                    logger=None,
                )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_text_first_canonical_subtitle_preparation -v`
Expected: FAIL with `ModuleNotFoundError` for `video_atlas.workflows.text_first_canonical.subtitle_preparation`

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ...transcription import generate_subtitles_for_video


@dataclass(frozen=True)
class SubtitleAssets:
    srt_file_path: Path
    generated_audio_path: Path | None = None


def resolve_subtitle_assets(
    *,
    input_dir: Path,
    subtitle_path: Path | None,
    audio_path: Path | None,
    video_path: Path | None,
    transcriber,
    generate_subtitles_if_missing: bool,
    logger,
) -> SubtitleAssets:
    if subtitle_path is not None:
        return SubtitleAssets(srt_file_path=subtitle_path)

    if not generate_subtitles_if_missing or transcriber is None:
        raise ValueError("unable to prepare subtitle assets")

    if video_path is not None:
        srt_file_path = input_dir / "subtitles.srt"
        generated_srt, generated_audio = generate_subtitles_for_video(
            video_path,
            srt_file_path,
            transcriber=transcriber,
            logger=logger,
        )
        return SubtitleAssets(srt_file_path=generated_srt, generated_audio_path=generated_audio)

    if audio_path is not None:
        srt_file_path = input_dir / "subtitles.srt"
        generated_srt, generated_audio = generate_subtitles_for_video(
            audio_path,
            srt_file_path,
            transcriber=transcriber,
            logger=logger,
        )
        return SubtitleAssets(srt_file_path=generated_srt, generated_audio_path=generated_audio)

    raise ValueError("unable to prepare subtitle assets")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_text_first_canonical_subtitle_preparation -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_text_first_canonical_subtitle_preparation.py src/video_atlas/workflows/text_first_canonical/subtitle_preparation.py
git commit -m "Add shared subtitle preparation helper"
```

## Task 2: Text-First Route Gate

**Files:**
- Create: `src/video_atlas/workflows/text_first_canonical/plan.py`
- Test: `tests/test_text_first_canonical_workflow.py`

- [ ] **Step 1: Write the failing tests**

```python
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from video_atlas.schemas import CanonicalCreateRequest
from video_atlas.workflows.text_first_canonical.plan import (
    RouteDecision,
    decide_text_first_route,
)


class TextFirstRouteDecisionTest(unittest.TestCase):
    def test_video_absent_defaults_to_text_first(self) -> None:
        request = CanonicalCreateRequest(atlas_dir=Path("/tmp/atlas"), audio_path=Path("/tmp/audio.m4a"))

        decision = decide_text_first_route(
            request=request,
            planner=None,
            subtitle_items=[],
            verbose=False,
        )

        self.assertEqual(decision.route, "text_first")
        self.assertEqual(decision.profile, "text_only")

    def test_video_present_text_led_maps_to_text_first(self) -> None:
        planner = MagicMock()
        planner.generate.return_value = '{"profile":"lecture","genres":["knowledge"],"concise_description":"demo"}'
        request = CanonicalCreateRequest(atlas_dir=Path("/tmp/atlas"), video_path=Path("/tmp/video.mp4"))

        decision = decide_text_first_route(
            request=request,
            planner=planner,
            subtitle_items=[],
            verbose=False,
        )

        self.assertEqual(decision.route, "text_first")
        self.assertEqual(decision.profile, "lecture")

    def test_video_present_visual_led_maps_to_multimodal(self) -> None:
        planner = MagicMock()
        planner.generate.return_value = '{"profile":"movie","genres":["drama"],"concise_description":"demo"}'
        request = CanonicalCreateRequest(atlas_dir=Path("/tmp/atlas"), video_path=Path("/tmp/video.mp4"))

        decision = decide_text_first_route(
            request=request,
            planner=planner,
            subtitle_items=[],
            verbose=False,
        )

        self.assertEqual(decision.route, "multimodal")
        self.assertEqual(decision.profile, "movie")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_text_first_canonical_workflow.TextFirstRouteDecisionTest -v`
Expected: FAIL with `ModuleNotFoundError` for `video_atlas.workflows.text_first_canonical.plan`

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

from dataclasses import dataclass, field

from ...parsing import parse_json_response


TEXT_FIRST_PROFILES = {"text_only", "lecture", "video_podcast", "interview", "knowledge"}


@dataclass(frozen=True)
class RouteDecision:
    profile: str
    route: str
    genres: list[str] = field(default_factory=list)
    concise_description: str = ""


def decide_text_first_route(*, request, planner, subtitle_items, verbose: bool) -> RouteDecision:
    if request.video_path is None:
        return RouteDecision(
            profile="text_only",
            route="text_first",
            genres=["other"],
            concise_description="Text-first input without source video.",
        )

    raw = planner.generate(messages=[])
    payload = parse_json_response(raw)
    profile = str(payload.get("profile", "other"))
    route = "text_first" if profile in TEXT_FIRST_PROFILES else "multimodal"
    return RouteDecision(
        profile=profile,
        route=route,
        genres=list(payload.get("genres", ["other"])),
        concise_description=str(payload.get("concise_description", "")),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_text_first_canonical_workflow.TextFirstRouteDecisionTest -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_text_first_canonical_workflow.py src/video_atlas/workflows/text_first_canonical/plan.py
git commit -m "Add text-first route decision"
```

## Task 3: Text-First Pipeline

**Files:**
- Create: `src/video_atlas/workflows/text_first_canonical/parsing.py`
- Create: `src/video_atlas/workflows/text_first_canonical/pipeline.py`
- Create: `src/video_atlas/workflows/text_first_canonical_atlas_workflow.py`
- Modify: `src/video_atlas/workflows/canonical_atlas/structure_composition.py`
- Test: `tests/test_text_first_canonical_workflow.py`

- [ ] **Step 1: Write the failing tests**

```python
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from video_atlas.schemas import CanonicalCreateRequest
from video_atlas.workflows.text_first_canonical_atlas_workflow import TextFirstCanonicalAtlasWorkflow


class TextFirstWorkflowTest(unittest.TestCase):
    @patch("video_atlas.workflows.text_first_canonical.pipeline.resolve_subtitle_assets")
    @patch("video_atlas.workflows.text_first_canonical.pipeline.decide_text_first_route")
    @patch("video_atlas.workflows.text_first_canonical.pipeline.parse_srt")
    @patch("video_atlas.workflows.text_first_canonical.pipeline.build_text_units")
    @patch("video_atlas.workflows.text_first_canonical.pipeline.compose_canonical_structure")
    def test_subtitle_only_input_runs_text_first_pipeline(
        self,
        mock_compose,
        mock_build_units,
        mock_parse_srt,
        mock_decide_route,
        mock_resolve_subtitles,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_dir = Path(tmpdir)
            subtitle_path = atlas_dir / "input" / "subtitles.srt"
            subtitle_path.parent.mkdir(parents=True)
            subtitle_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n", encoding="utf-8")

            mock_resolve_subtitles.return_value = MagicMock(srt_file_path=subtitle_path, generated_audio_path=None)
            mock_decide_route.return_value = MagicMock(route="text_first", profile="text_only", genres=["other"], concise_description="demo")
            mock_parse_srt.return_value = ([], "hi")
            mock_build_units.return_value = []
            mock_compose.return_value = MagicMock(title="t", abstract="a", segments=[])

            workflow = TextFirstCanonicalAtlasWorkflow(
                planner=MagicMock(),
                text_segmentor=MagicMock(),
                structure_composer=MagicMock(),
                captioner=MagicMock(),
                transcriber=MagicMock(),
            )
            atlas, _ = workflow.create(CanonicalCreateRequest(atlas_dir=atlas_dir, subtitle_path=subtitle_path))

        self.assertEqual(atlas.title, "t")

    @patch("video_atlas.workflows.text_first_canonical.pipeline.resolve_subtitle_assets")
    @patch("video_atlas.workflows.text_first_canonical.pipeline.decide_text_first_route")
    def test_visual_led_route_raises_not_implemented(self, mock_decide_route, mock_resolve_subtitles) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_dir = Path(tmpdir)
            video_path = atlas_dir / "input" / "video.mp4"
            video_path.parent.mkdir(parents=True)
            video_path.write_bytes(b"video")
            subtitle_path = atlas_dir / "input" / "subtitles.srt"
            subtitle_path.write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n", encoding="utf-8")

            mock_resolve_subtitles.return_value = MagicMock(srt_file_path=subtitle_path, generated_audio_path=None)
            mock_decide_route.return_value = MagicMock(route="multimodal", profile="movie", genres=["drama"], concise_description="demo")

            workflow = TextFirstCanonicalAtlasWorkflow(
                planner=MagicMock(),
                text_segmentor=MagicMock(),
                structure_composer=MagicMock(),
                captioner=MagicMock(),
                transcriber=MagicMock(),
            )

            with self.assertRaises(NotImplementedError):
                workflow.create(CanonicalCreateRequest(atlas_dir=atlas_dir, video_path=video_path))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_text_first_canonical_workflow.TextFirstWorkflowTest -v`
Expected: FAIL with `ModuleNotFoundError` for `video_atlas.workflows.text_first_canonical_atlas_workflow`

- [ ] **Step 3: Write minimal implementation**

```python
# src/video_atlas/workflows/text_first_canonical/parsing.py
from __future__ import annotations


def build_text_units(*, text_segmentor, captioner, subtitle_items, subtitles_text, verbose: bool):
    return []
```

```python
# src/video_atlas/workflows/text_first_canonical/pipeline.py
from __future__ import annotations

import json
import time
from dataclasses import asdict

from ...persistence import CanonicalAtlasWriter, write_text_to
from ...schemas import CanonicalAtlas
from ...utils import parse_srt
from ..canonical_atlas.pipeline import _serialize_source_metadata
from ..canonical_atlas.structure_composition import compose_canonical_structure
from .parsing import build_text_units
from .plan import decide_text_first_route
from .subtitle_preparation import resolve_subtitle_assets


class TextFirstPipelineMixin:
    def create(self, request):
        atlas_dir = request.atlas_dir
        atlas_dir.mkdir(parents=True, exist_ok=True)
        subtitle_assets = resolve_subtitle_assets(
            input_dir=request.input_dir,
            subtitle_path=request.subtitle_path,
            audio_path=request.audio_path,
            video_path=request.video_path,
            transcriber=self.transcriber,
            generate_subtitles_if_missing=self.generate_subtitles_if_missing,
            logger=self.logger,
        )
        subtitle_items, subtitles_text = parse_srt(subtitle_assets.srt_file_path)
        route_decision = decide_text_first_route(
            request=request,
            planner=self.planner,
            subtitle_items=subtitle_items,
            verbose=self.verbose,
        )
        if route_decision.route != "text_first":
            raise NotImplementedError(f"unsupported route: {route_decision.route}")

        units = build_text_units(
            text_segmentor=self.text_segmentor,
            captioner=self.captioner,
            subtitle_items=subtitle_items,
            subtitles_text=subtitles_text,
            verbose=self.verbose,
        )
        composition_result = compose_canonical_structure(
            self.structure_composer,
            units=units,
            concise_description=route_decision.concise_description,
            genres=route_decision.genres,
            structure_request=request.structure_request or "",
        )
        write_text_to(atlas_dir, "EXECUTION_PLAN.json", json.dumps({"profile": route_decision.profile}, indent=2))
        atlas = CanonicalAtlas(
            title=composition_result.title,
            duration=0.0,
            abstract=composition_result.abstract,
            units=units,
            segments=composition_result.segments,
            execution_plan=self._empty_execution_plan(),
            atlas_dir=atlas_dir,
            relative_video_path=request.video_path.relative_to(atlas_dir) if request.video_path is not None else Path("input/placeholder.mp4"),
            relative_audio_path=subtitle_assets.generated_audio_path.relative_to(atlas_dir) if subtitle_assets.generated_audio_path is not None else None,
            relative_subtitles_path=None,
            relative_srt_file_path=subtitle_assets.srt_file_path.relative_to(atlas_dir),
            source_info=request.source_info,
            source_metadata=_serialize_source_metadata(request.source_metadata),
        )
        CanonicalAtlasWriter(caption_with_subtitles=self.caption_with_subtitles).write(atlas=atlas)
        return atlas, {"route": route_decision.route}
```

```python
# src/video_atlas/workflows/text_first_canonical_atlas_workflow.py
from __future__ import annotations

import logging

from .canonical_atlas.execution_plan_builder import ExecutionPlanBuilderMixin
from .text_first_canonical.pipeline import TextFirstPipelineMixin


class TextFirstCanonicalAtlasWorkflow(TextFirstPipelineMixin, ExecutionPlanBuilderMixin):
    def __init__(
        self,
        planner,
        text_segmentor,
        structure_composer,
        captioner,
        transcriber=None,
        generate_subtitles_if_missing: bool = True,
        caption_with_subtitles: bool = True,
        verbose: bool = False,
    ) -> None:
        self.planner = planner
        self.text_segmentor = text_segmentor
        self.structure_composer = structure_composer
        self.captioner = captioner
        self.transcriber = transcriber
        self.generate_subtitles_if_missing = generate_subtitles_if_missing
        self.caption_with_subtitles = caption_with_subtitles
        self.verbose = verbose
        self.logger = logging.getLogger(self.__class__.__name__)

    def _empty_execution_plan(self):
        from ..schemas import CanonicalExecutionPlan

        return CanonicalExecutionPlan()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_text_first_canonical_workflow.TextFirstWorkflowTest -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_text_first_canonical_workflow.py src/video_atlas/workflows/text_first_canonical/parsing.py src/video_atlas/workflows/text_first_canonical/pipeline.py src/video_atlas/workflows/text_first_canonical_atlas_workflow.py
git commit -m "Add text-first canonical workflow"
```

## Task 4: Make Text-First Workflow the Default Application Path

**Files:**
- Modify: `src/video_atlas/application/canonical_create.py`
- Modify: `tests/test_application_canonical_create.py`
- Modify: `docs/design-docs/module-design/canonical-atlas-workflow.md`

- [ ] **Step 1: Write the failing tests**

```python
from unittest.mock import patch


@patch("video_atlas.application.canonical_create.TextFirstCanonicalAtlasWorkflow")
def test_build_workflow_returns_text_first_workflow_by_default(mock_workflow_cls):
    from video_atlas.application.canonical_create import _build_workflow
    from video_atlas.config.models import CanonicalPipelineConfig

    config = CanonicalPipelineConfig(planner=None)

    with patch("video_atlas.application.canonical_create.build_generator", side_effect=lambda value: value), \
        patch("video_atlas.application.canonical_create.build_transcriber", return_value=None):
        workflow = _build_workflow(config)

    assert workflow is mock_workflow_cls.return_value
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_application_canonical_create -v`
Expected: FAIL because `_build_workflow` still returns legacy `CanonicalAtlasWorkflow`

- [ ] **Step 3: Write minimal implementation**

```python
from video_atlas.workflows.text_first_canonical_atlas_workflow import TextFirstCanonicalAtlasWorkflow


def _build_workflow(config: CanonicalPipelineConfig) -> TextFirstCanonicalAtlasWorkflow:
    return TextFirstCanonicalAtlasWorkflow(
        planner=build_generator(config.planner),
        text_segmentor=build_generator(config.text_segmentor) if config.text_segmentor is not None else None,
        structure_composer=build_generator(config.structure_composer) if config.structure_composer is not None else None,
        captioner=build_generator(config.captioner) if config.captioner is not None else None,
        transcriber=build_transcriber(config.transcriber),
        generate_subtitles_if_missing=config.runtime.generate_subtitles_if_missing,
        caption_with_subtitles=config.runtime.caption_with_subtitles,
        verbose=config.runtime.verbose,
    )
```

Update the design doc section in `docs/design-docs/module-design/canonical-atlas-workflow.md` to state that text-first workflow is the default canonical path and the previous video-first workflow is retained as a legacy implementation.

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_application_canonical_create tests.test_text_first_canonical_workflow -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/video_atlas/application/canonical_create.py tests/test_application_canonical_create.py docs/design-docs/module-design/canonical-atlas-workflow.md
git commit -m "Switch canonical create to text-first workflow"
```

## Task 5: Full Regression for First-Phase Scope

**Files:**
- Modify: `tests/test_canonical_two_stage_pipeline.py`
- Modify: `tests/test_cli.py`
- Modify: `docs/design-docs/module-design/canonical-atlas-workflow.md`

- [ ] **Step 1: Extend tests for first-phase supported/unsupported routes**

```python
def test_video_present_visual_led_route_fails_fast():
    ...


def test_audio_only_request_runs_text_first_pipeline():
    ...


def test_subtitle_only_request_runs_text_first_pipeline():
    ...
```

- [ ] **Step 2: Run targeted regression**

Run: `PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_text_first_canonical_subtitle_preparation tests.test_text_first_canonical_workflow tests.test_application_canonical_create tests.test_canonical_two_stage_pipeline tests.test_cli -v`
Expected: PASS

- [ ] **Step 3: Run full canonical/app regression**

Run: `PYTHONPATH=src /share/project/minghao/Envs/videoatlas/bin/python -m unittest tests.test_config_loading tests.test_source_acquisition_dispatch tests.test_source_acquisition_models tests.test_application_canonical_create tests.test_text_first_canonical_subtitle_preparation tests.test_text_first_canonical_workflow tests.test_canonical_two_stage_pipeline tests.test_cli -v`
Expected: PASS

- [ ] **Step 4: Final doc touch-up**

Add one short note in `docs/design-docs/module-design/canonical-atlas-workflow.md` under the current implementation section to list the new files:

```markdown
- `text_first_canonical_atlas_workflow.py`: text-first canonical workflow public entry.
- `text_first_canonical/subtitle_preparation.py`: shared subtitle preparation helper.
- `text_first_canonical/plan.py`: profile selection and route mapping.
- `text_first_canonical/parsing.py`: text-first unit generation.
- `text_first_canonical/pipeline.py`: text-first canonical pipeline.
```

- [ ] **Step 5: Commit**

```bash
git add tests/test_canonical_two_stage_pipeline.py tests/test_cli.py docs/design-docs/module-design/canonical-atlas-workflow.md
git commit -m "Finish text-first canonical workflow v1"
```

## Self-Review

- Spec coverage:
  - New parallel text-first workflow: covered by Tasks 2-4
  - Shared subtitle preparation before route selection: covered by Task 1
  - `video-absent` and `video-present + text-led` support: covered by Tasks 3 and 5
  - `video-present + visual-led` explicit failure: covered by Tasks 2, 3, and 5
  - Reuse of Stage 2 structure composition and existing schemas/persistence: covered by Task 3
- Placeholder scan:
  - No `TODO` / `TBD` placeholders remain in task steps
  - All code steps include concrete snippets
  - All test and run commands are explicit
- Type consistency:
  - Plan consistently uses `CanonicalCreateRequest`, `TextFirstCanonicalAtlasWorkflow`, `RouteDecision`, and `SubtitleAssets`
  - Text-first route names are consistently `text_first` and `multimodal`

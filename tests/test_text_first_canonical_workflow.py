from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from video_atlas.prompts import get_prompt
from video_atlas.schemas import AtlasSegment, CanonicalCompositionResult, CanonicalCreateRequest
from video_atlas.transcription import TranscriptSegment
from video_atlas.workflows.text_first_canonical_atlas_workflow import TextFirstCanonicalAtlasWorkflow
from video_atlas.workflows.text_first_canonical.plan import build_text_first_execution_plan


def _planner_text_payload(planner: MagicMock) -> str:
    content = planner.generate_single.call_args.kwargs["messages"][1]["content"]
    if isinstance(content, list):
        return "\n".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        )
    return str(content)


class TextFirstPlanningTest(unittest.TestCase):
    def test_text_first_planner_prompt_is_registered(self) -> None:
        prompt = get_prompt("TEXT_FIRST_PLANNER_PROMPT")

        self.assertEqual(prompt.name, "TEXT_FIRST_PLANNER_PROMPT")
        self.assertIn("profile", prompt.output_contract)
        self.assertIn("input_kind", prompt.input_fields)
        self.assertIn("subtitle_probe", prompt.input_fields)

    def test_video_absent_builds_text_first_execution_plan(self) -> None:
        request = CanonicalCreateRequest(atlas_dir=Path("/tmp/atlas"), audio_path=Path("/tmp/audio.m4a"))
        planner = MagicMock()
        planner.generate_single.return_value = {
            "text": '{"profile":"podcast","genres":["podcast_interview"],"concise_description":"demo"}',
            "json": None,
        }

        plan = build_text_first_execution_plan(
            request=request,
            planner=planner,
            subtitle_items=[],
            output_language="en",
            verbose=False,
        )

        self.assertEqual(plan.profile_name, "podcast")
        self.assertEqual(plan.profile.route, "text_first")
        planner.generate_single.assert_called_once()

    def test_planner_is_required_when_video_is_present(self) -> None:
        request = CanonicalCreateRequest(atlas_dir=Path("/tmp/atlas"), video_path=Path("/tmp/video.mp4"))

        with self.assertRaises(ValueError):
            build_text_first_execution_plan(
                request=request,
                planner=None,
                subtitle_items=[],
                output_language="en",
                verbose=False,
            )

    def test_video_present_text_led_builds_text_first_execution_plan(self) -> None:
        planner = MagicMock()
        planner.generate_single.return_value = {
            "text": '{"profile":"lecture","genres":["lecture_talk"],"concise_description":"demo"}',
            "json": None,
        }
        request = CanonicalCreateRequest(atlas_dir=Path("/tmp/atlas"), video_path=Path("/tmp/video.mp4"))
        subtitle_items = [{"start": 0.0, "end": 1.0, "text": "hello world"}]

        plan = build_text_first_execution_plan(
            request=request,
            planner=planner,
            subtitle_items=subtitle_items,
            output_language="en",
            verbose=False,
        )

        self.assertEqual(plan.profile_name, "lecture")
        self.assertEqual(plan.profile.route, "text_first")
        self.assertEqual(plan.genres, ["lecture_talk"])
        self.assertEqual(plan.concise_description, "demo")
        self.assertIn("hello world", _planner_text_payload(planner))

    def test_video_present_uses_profile_even_if_payload_route_conflicts(self) -> None:
        planner = MagicMock()
        planner.generate_single.return_value = {
            "text": '{"profile":"lecture","route":"multimodal","genres":["lecture_talk"],"concise_description":"demo"}',
            "json": None,
        }
        request = CanonicalCreateRequest(atlas_dir=Path("/tmp/atlas"), video_path=Path("/tmp/video.mp4"))
        subtitle_items = [{"start": 10.0, "end": 11.0, "text": "route should ignore this field"}]

        plan = build_text_first_execution_plan(
            request=request,
            planner=planner,
            subtitle_items=subtitle_items,
            output_language="en",
            verbose=False,
        )

        self.assertEqual(plan.profile_name, "lecture")
        self.assertEqual(plan.profile.route, "text_first")
        self.assertEqual(plan.genres, ["lecture_talk"])
        self.assertEqual(plan.concise_description, "demo")
        self.assertIn("route should ignore this field", _planner_text_payload(planner))

    def test_video_present_visual_led_builds_multimodal_execution_plan(self) -> None:
        planner = MagicMock()
        planner.generate_single.return_value = {
            "text": '{"profile":"movie","genres":["narrative_film"],"concise_description":"demo"}',
            "json": None,
        }
        request = CanonicalCreateRequest(atlas_dir=Path("/tmp/atlas"), video_path=Path("/tmp/video.mp4"))

        plan = build_text_first_execution_plan(
            request=request,
            planner=planner,
            subtitle_items=[],
            output_language="en",
            verbose=False,
        )

        self.assertEqual(plan.profile_name, "movie")
        self.assertEqual(plan.profile.route, "multimodal")
        self.assertEqual(plan.genres, ["narrative_film"])
        self.assertEqual(plan.concise_description, "demo")

    def test_planner_uses_prompt_spec_and_subtitle_sampling(self) -> None:
        planner = MagicMock()
        planner.generate_single.return_value = {
            "text": '{"profile":"podcast","genres":["podcast_interview"],"concise_description":"demo"}',
            "json": None,
        }
        request = CanonicalCreateRequest(atlas_dir=Path("/tmp/atlas"), audio_path=Path("/tmp/audio.m4a"))
        subtitle_items = [
            {"start": float(index), "end": float(index) + 0.5, "text": f"subtitle line {index}"}
            for index in range(30)
        ]

        build_text_first_execution_plan(
            request=request,
            planner=planner,
            subtitle_items=subtitle_items,
            output_language="en",
            verbose=False,
        )

        messages = planner.generate_single.call_args.kwargs["messages"]
        prompt = get_prompt("TEXT_FIRST_PLANNER_PROMPT")
        self.assertEqual(messages[0]["content"], prompt.render_system())

        payload = _planner_text_payload(planner)
        self.assertIn("All generated text must be in English.", payload)
        self.assertIn("subtitle line 0", payload)
        self.assertIn("subtitle line 15", payload)
        self.assertIn("subtitle line 29", payload)
        self.assertNotIn("subtitle line 8", payload)
        self.assertIn("STRICT OUTPUT JSON SCHEMA", payload)

    def test_execution_plan_carries_output_language(self) -> None:
        planner = MagicMock()
        planner.generate_single.return_value = {
            "text": '{"profile":"podcast","genres":["podcast_interview"],"concise_description":"demo"}',
            "json": None,
        }

        plan = build_text_first_execution_plan(
            request=CanonicalCreateRequest(atlas_dir=Path("/tmp/atlas"), audio_path=Path("/tmp/audio.m4a")),
            planner=planner,
            subtitle_items=[],
            output_language="zh",
            verbose=False,
        )

        self.assertEqual(plan.output_language, "zh")


class TextFirstWorkflowTest(unittest.TestCase):
    def test_build_text_units_uses_chunked_boundary_detection(self) -> None:
        from video_atlas.schemas import CanonicalExecutionPlan
        from video_atlas.workflows.text_first_canonical.parsing import build_text_units

        text_segmentor = MagicMock()
        text_segmentor.generate_single.return_value = {"text": "[]", "json": None}
        captioner = MagicMock()
        captioner.generate_single.return_value = {
            "text": '{"summary":"opening","caption":"opening"}',
            "json": None,
        }
        execution_plan = CanonicalExecutionPlan(
            profile_name="podcast",
            chunk_size_sec=60,
            chunk_overlap_sec=10,
        )
        subtitle_items = [
            {"start": 0.0, "end": 5.0, "text": "opening"},
            {"start": 65.0, "end": 70.0, "text": "next section"},
        ]

        units = build_text_units(
            text_segmentor=text_segmentor,
            captioner=captioner,
            execution_plan=execution_plan,
            subtitle_items=subtitle_items,
            subtitles_text="...",
            verbose=False,
        )

        self.assertGreaterEqual(text_segmentor.generate_single.call_count, 2)
        self.assertGreaterEqual(len(units), 1)

    def test_audio_only_input_runs_text_first_pipeline(self) -> None:
        planner = MagicMock()
        planner.generate_single.return_value = {
            "text": '{"profile":"podcast","genres":["podcast_interview"],"concise_description":"audio demo"}',
            "json": None,
        }
        transcriber = MagicMock()
        transcriber.transcribe_audio.return_value = [TranscriptSegment(start=0.0, end=1.0, text="audio hello world")]
        text_segmentor = MagicMock()
        text_segmentor.generate_single.return_value = {"text": "[]", "json": None}
        captioner = MagicMock()
        captioner.generate_single.return_value = {
            "text": '{"summary":"audio hello world","caption":"audio hello world"}',
            "json": None,
        }

        with patch(
            "video_atlas.workflows.text_first_canonical.pipeline.compose_canonical_structure"
        ) as mock_compose:
            with tempfile.TemporaryDirectory() as tmpdir:
                atlas_dir = Path(tmpdir)
                input_dir = atlas_dir / "input"
                input_dir.mkdir(parents=True)
                audio_path = input_dir / "audio.m4a"
                audio_path.write_bytes(b"audio")

                mock_compose.return_value = CanonicalCompositionResult(
                    title="Audio Atlas",
                    abstract="Audio abstract",
                    segments=[
                        AtlasSegment(
                            segment_id="seg_0001",
                            unit_ids=["unit_0001"],
                            title="Opening",
                            start_time=0.0,
                            end_time=1.0,
                            summary="audio hello world",
                            composition_rationale="demo",
                            folder_name="seg-0001-opening-00:00:00-00:00:01",
                        )
                    ],
                )

                workflow = TextFirstCanonicalAtlasWorkflow(
                    planner=planner,
                    text_segmentor=text_segmentor,
                    structure_composer=MagicMock(),
                    captioner=captioner,
                    transcriber=transcriber,
                )
                atlas, cost_info = workflow.create(
                    CanonicalCreateRequest(atlas_dir=atlas_dir, audio_path=audio_path)
                )

                self.assertEqual(atlas.title, "Audio Atlas")
                self.assertEqual(len(atlas.units), 1)
                self.assertEqual(atlas.units[0].title, "audio hello world")
                self.assertEqual(atlas.segments[0].unit_ids, ["unit_0001"])
                self.assertIn("parsing_cost_time", cost_info)
                self.assertTrue((atlas_dir / "README.md").exists())
                self.assertTrue((atlas_dir / "units" / atlas.units[0].folder_name / "README.md").exists())
                self.assertTrue((atlas_dir / "segments" / atlas.segments[0].folder_name / "README.md").exists())
                planner.generate_single.assert_called_once()

    def test_subtitle_only_input_runs_text_first_pipeline(self) -> None:
        planner = MagicMock()
        planner.generate_single.return_value = {
            "text": '{"profile":"podcast","genres":["podcast_interview"],"concise_description":"subtitle demo"}',
            "json": None,
        }
        text_segmentor = MagicMock()
        text_segmentor.generate_single.return_value = {"text": "[]", "json": None}
        captioner = MagicMock()
        captioner.generate_single.return_value = {
            "text": '{"summary":"hello world","caption":"hello world"}',
            "json": None,
        }
        with patch(
            "video_atlas.workflows.text_first_canonical.pipeline.compose_canonical_structure"
        ) as mock_compose:
            with tempfile.TemporaryDirectory() as tmpdir:
                atlas_dir = Path(tmpdir)
                input_dir = atlas_dir / "input"
                input_dir.mkdir(parents=True)
                subtitle_path = input_dir / "subtitles.srt"
                subtitle_path.write_text(
                    "1\n00:00:00,000 --> 00:00:01,000\nhello world\n",
                    encoding="utf-8",
                )

                mock_compose.return_value = CanonicalCompositionResult(
                    title="Text Atlas",
                    abstract="Text abstract",
                    segments=[
                        AtlasSegment(
                            segment_id="seg_0001",
                            unit_ids=["unit_0001"],
                            title="Opening",
                            start_time=0.0,
                            end_time=1.0,
                            summary="hello world",
                            composition_rationale="demo",
                            folder_name="seg-0001-opening-00:00:00-00:00:01",
                        )
                    ],
                )

                workflow = TextFirstCanonicalAtlasWorkflow(
                    planner=planner,
                    text_segmentor=text_segmentor,
                    structure_composer=MagicMock(),
                    captioner=captioner,
                    transcriber=MagicMock(),
                )
                atlas, cost_info = workflow.create(
                    CanonicalCreateRequest(atlas_dir=atlas_dir, subtitle_path=subtitle_path)
                )

                self.assertEqual(atlas.title, "Text Atlas")
                self.assertIsNotNone(atlas.execution_plan)
                self.assertEqual(len(atlas.units), 1)
                self.assertEqual(atlas.units[0].title, "hello world")
                self.assertEqual(atlas.segments[0].unit_ids, ["unit_0001"])
                self.assertIn("parsing_cost_time", cost_info)
                self.assertTrue((atlas_dir / "README.md").exists())
                self.assertTrue((atlas_dir / "units" / atlas.units[0].folder_name / "README.md").exists())
                self.assertTrue((atlas_dir / "segments" / atlas.segments[0].folder_name / "README.md").exists())
                self.assertTrue((atlas_dir / "segments" / atlas.segments[0].folder_name / atlas.units[0].folder_name / "README.md").exists())
                workflow.planner.generate_single.assert_called_once()

    def test_video_present_text_led_uses_text_route(self) -> None:
        planner = MagicMock()
        planner.generate_single.return_value = {
            "text": json.dumps(
                {
                    "profile": "lecture",
                    "genres": ["knowledge"],
                    "concise_description": "demo",
                }
            ),
            "json": None,
        }

        with patch(
            "video_atlas.workflows.text_first_canonical.pipeline.compose_canonical_structure"
        ) as mock_compose:
            with patch(
                "video_atlas.workflows.text_first_canonical.pipeline.CanonicalAtlasWriter.write"
            ) as mock_writer:
                with patch(
                    "video_atlas.utils.get_video_property",
                    return_value={"duration": 12.0, "resolution": "1280x720"},
                ):
                    with tempfile.TemporaryDirectory() as tmpdir:
                        atlas_dir = Path(tmpdir)
                        input_dir = atlas_dir / "input"
                        input_dir.mkdir(parents=True)
                        video_path = input_dir / "video.mp4"
                        video_path.write_bytes(b"video")
                        subtitle_path = input_dir / "subtitles.srt"
                        subtitle_path.write_text(
                            "1\n00:00:00,000 --> 00:00:01,000\nhello world\n",
                            encoding="utf-8",
                        )

                        mock_compose.return_value = CanonicalCompositionResult(
                            title="Lecture Atlas",
                            abstract="Lecture abstract",
                            segments=[
                                AtlasSegment(
                                    segment_id="seg_0001",
                                    unit_ids=["unit_0001"],
                                    title="Opening",
                                    start_time=0.0,
                                    end_time=1.0,
                                    summary="hello world",
                                    composition_rationale="demo",
                                    folder_name="seg-0001-opening-00:00:00-00:00:01",
                                )
                            ],
                        )

                        text_segmentor = MagicMock()
                        text_segmentor.generate_single.return_value = {"text": "[]", "json": None}
                        captioner = MagicMock()
                        captioner.generate_single.return_value = {
                            "text": '{"summary":"hello world","caption":"hello world"}',
                            "json": None,
                        }
                        workflow = TextFirstCanonicalAtlasWorkflow(
                            planner=planner,
                            text_segmentor=text_segmentor,
                            structure_composer=MagicMock(),
                            captioner=captioner,
                            transcriber=MagicMock(),
                        )
                        atlas, _ = workflow.create(
                            CanonicalCreateRequest(
                                atlas_dir=atlas_dir,
                                video_path=video_path,
                                subtitle_path=subtitle_path,
                            )
                        )

                        self.assertEqual(atlas.title, "Lecture Atlas")
                        self.assertEqual(atlas.relative_video_path, Path("input") / "video.mp4")
                        self.assertEqual(atlas.segments[0].unit_ids, ["unit_0001"])
                        self.assertEqual(mock_writer.call_count, 1)
                        planner.generate_single.assert_called_once()
                        self.assertIn("hello world", _planner_text_payload(planner))

    def test_visual_led_route_raises_not_implemented(self) -> None:
        planner = MagicMock()
        planner.generate_single.return_value = {
            "text": json.dumps(
                {
                    "profile": "movie",
                    "genres": ["drama"],
                    "concise_description": "demo",
                }
            ),
            "json": None,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            atlas_dir = Path(tmpdir)
            input_dir = atlas_dir / "input"
            input_dir.mkdir(parents=True)
            video_path = input_dir / "video.mp4"
            video_path.write_bytes(b"video")
            subtitle_path = input_dir / "subtitles.srt"
            subtitle_path.write_text(
                "1\n00:00:00,000 --> 00:00:01,000\nhello world\n",
                encoding="utf-8",
            )

            workflow = TextFirstCanonicalAtlasWorkflow(
                planner=planner,
                text_segmentor=MagicMock(),
                structure_composer=MagicMock(),
                captioner=MagicMock(),
                transcriber=MagicMock(),
            )

            with patch("video_atlas.workflows.text_first_canonical.pipeline.build_text_units") as mock_build_units, patch(
                "video_atlas.workflows.text_first_canonical.pipeline.compose_canonical_structure"
            ) as mock_compose:
                with self.assertRaises(NotImplementedError):
                    workflow.create(
                        CanonicalCreateRequest(
                            atlas_dir=atlas_dir,
                            video_path=video_path,
                            subtitle_path=subtitle_path,
                        )
                    )
            mock_build_units.assert_not_called()
            mock_compose.assert_not_called()
            planner.generate_single.assert_called_once()


if __name__ == "__main__":
    unittest.main()
